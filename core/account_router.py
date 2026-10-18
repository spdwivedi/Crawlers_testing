"""
core/account_router.py
======================
Smart Account Pool Router, Private-Follower Matcher, Quota Manager & Cooldown Engine.

Key Capabilities:
  1. Pre-Flight Maintenance:
       - release_expired_cooldowns: Automatically transitions expired cooldown accounts back to active
       - reset_stale_daily_quotas: Resets daily quota counters on date change (UTC)
  2. Intelligent Account Acquisition (acquire_account):
       - Private target follower matching (account_target_access INNER JOIN)
       - Auth method capability filtering (cookie_jar, session_tokens, storage_state, etc.)
       - Multiple rotation strategies: 'least_recently_used', 'lowest_quota_usage', 'health_weighted_random'
       - Atomic lease and usage accounting
       - Ephemeral RFC 6238 2FA TOTP code generation on acquisition
  3. Outcome Feedback & Cooldown Quarantine (report_account_outcome):
       - State machine for 'success', 'rate_limited' (cooldown), 'checkpoint_required', 'session_expired', 'banned'
       - Health score adjustments and cooldown scheduling
  4. Pool Diagnostics & Target Coverage Inspector (get_pool_diagnostics):
       - Zero-secret summary of active, ready, cooling, and quota-exhausted accounts
       - Private target coverage statistics
"""
from __future__ import annotations

import json
import random
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.credential_vault import CredentialVault, get_credential_vault
from core.totp_helper import TOTPHelper


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _today_utc_str() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


class AccountRouter:
    """
    Intelligent routing and session health management engine for crawler credential pools.
    """

    def __init__(self, vault: CredentialVault | None = None) -> None:
        self.vault = vault or get_credential_vault()

    # ─────────────────────────────────────────────────────────────
    # Pre-Flight Maintenance
    # ─────────────────────────────────────────────────────────────

    def release_expired_cooldowns(self) -> int:
        """
        Scan vault_accounts for accounts in 'cooldown' whose cooldown_until_epoch
        has passed, and atomically restore them to 'active' status.
        
        Returns:
            Count of accounts released from cooldown.
        """
        now_ts = time.time()
        now_iso = _iso_now()

        with self.vault._get_connection() as conn:
            cur = conn.execute(
                """
                UPDATE vault_accounts
                SET status = 'active',
                    cooldown_until_epoch = 0.0,
                    updated_at = ?
                WHERE status = 'cooldown'
                  AND cooldown_until_epoch > 0
                  AND cooldown_until_epoch <= ?
                """,
                (now_iso, now_ts),
            )
            count = cur.rowcount

            if count > 0:
                conn.execute(
                    """
                    INSERT INTO vault_audit_log (timestamp, account_id, platform, event_type, notes)
                    VALUES (?, 'system', 'all', 'cooldown_released', ?)
                    """,
                    (now_iso, f"Automatically released {count} accounts from expired cooldown quarantine"),
                )

        if count > 0:
            self.vault.export_public_stats()

        return count

    def reset_stale_daily_quotas(self) -> int:
        """
        Reset requests_today counter for accounts where last_used_at is from a prior UTC day.
        
        Returns:
            Count of accounts whose daily quotas were reset.
        """
        today_prefix = _today_utc_str()
        now_iso = _iso_now()

        with self.vault._get_connection() as conn:
            cur = conn.execute(
                """
                UPDATE vault_accounts
                SET requests_today = 0,
                    updated_at = ?
                WHERE requests_today > 0
                  AND last_used_at IS NOT NULL
                  AND substr(last_used_at, 1, 10) < ?
                """,
                (now_iso, today_prefix),
            )
            count = cur.rowcount

        return count

    # ─────────────────────────────────────────────────────────────
    # Account Acquisition & Routing
    # ─────────────────────────────────────────────────────────────

    def acquire_account(
        self,
        platform: str,
        required_target: str = "",
        required_access_role: str = "",
        required_auth_method: str = "",
        strategy: str = "least_recently_used",
        min_health_score: int = 30,
        decrypt_secrets: bool = True,
        include_live_totp: bool = True,
        tool_id: str = "",
        run_id: str = "",
    ) -> dict[str, Any] | None:
        """
        Select and lease an optimal account from the credential vault based on
        platform, private follower target access, quota, health, and rotation strategy.
        
        Args:
            platform: Platform name ('instagram', 'facebook', 'leetcode', etc.)
            required_target: Optional handle of private profile/group (e.g., '@private_vip')
            required_access_role: Optional specific role ('follower', 'friend', 'member')
            required_auth_method: Optional auth method requirement ('cookie_jar', 'totp_2fa', etc.)
            strategy: 'least_recently_used', 'lowest_quota_usage', or 'health_weighted_random'
            min_health_score: Minimum health score threshold (default 30)
            decrypt_secrets: Whether to decrypt auth payloads for immediate scraping use
            include_live_totp: If account has TOTP, whether to attach current 6-digit code
            tool_id: Calling tool identifier for audit trail
            run_id: Action run identifier for audit trail
            
        Returns:
            Dictionary containing account details (decrypted or masked), or None if no eligible account.
        """
        # Run pre-flight maintenance
        self.release_expired_cooldowns()
        self.reset_stale_daily_quotas()

        platform_clean = platform.strip().lower()
        now_ts = time.time()
        now_iso = _iso_now()

        # Build candidate query
        params: list[Any] = [platform_clean, min_health_score, now_ts]
        
        if required_target:
            target_clean = required_target.strip().lower()
            sql = """
                SELECT DISTINCT va.*
                FROM vault_accounts va
                INNER JOIN account_target_access ata ON va.account_id = ata.account_id
                WHERE LOWER(va.platform) = LOWER(?)
                  AND va.status = 'active'
                  AND va.health_score >= ?
                  AND (va.cooldown_until_epoch <= 0 OR va.cooldown_until_epoch <= ?)
                  AND va.requests_today < va.daily_quota_limit
                  AND LOWER(ata.target_handle) = LOWER(?)
            """
            params.append(target_clean)
            if required_access_role:
                sql += " AND LOWER(ata.access_role) = LOWER(?)"
                params.append(required_access_role.strip().lower())
        else:
            sql = """
                SELECT va.*
                FROM vault_accounts va
                WHERE LOWER(va.platform) = LOWER(?)
                  AND va.status = 'active'
                  AND va.health_score >= ?
                  AND (va.cooldown_until_epoch <= 0 OR va.cooldown_until_epoch <= ?)
                  AND va.requests_today < va.daily_quota_limit
            """

        with self.vault._get_connection() as conn:
            cur = conn.execute(sql, params)
            candidates = [dict(r) for r in cur.fetchall()]

        if not candidates:
            return None

        # Filter by required_auth_method in Python if requested
        if required_auth_method:
            req_m = required_auth_method.strip().lower()
            filtered_candidates = []
            for c in candidates:
                try:
                    methods = [m.lower() for m in json.loads(c.get("auth_methods_json", "[]"))]
                    if req_m in methods:
                        filtered_candidates.append(c)
                except Exception:
                    pass
            candidates = filtered_candidates

        if not candidates:
            return None

        # Apply rotation & ranking strategy
        chosen: dict[str, Any]
        strategy_clean = strategy.strip().lower()

        if strategy_clean == "lowest_quota_usage":
            # Ratio of requests_today to daily_quota_limit ascending, then health descending
            def _quota_key(c: dict[str, Any]) -> tuple[float, int, str]:
                ratio = float(c["requests_today"]) / max(int(c["daily_quota_limit"]), 1)
                health_inv = -int(c["health_score"])
                last_used = c["last_used_at"] or ""
                return (ratio, health_inv, last_used)

            chosen = min(candidates, key=_quota_key)

        elif strategy_clean == "health_weighted_random":
            # Up to top 10 highest-health candidates
            sorted_by_health = sorted(candidates, key=lambda c: int(c["health_score"]), reverse=True)
            top_pool = sorted_by_health[:10]
            weights = [max(int(c["health_score"]), 1) for c in top_pool]
            chosen = random.choices(top_pool, weights=weights, k=1)[0]

        else:
            # Default: 'least_recently_used'
            # Accounts never used (last_used_at IS NULL) prioritized first, then oldest last_used_at
            def _lru_key(c: dict[str, Any]) -> tuple[int, str, int]:
                never_used = 0 if c["last_used_at"] is None else 1
                last_used = c["last_used_at"] or ""
                health_inv = -int(c["health_score"])
                return (never_used, last_used, health_inv)

            chosen = min(candidates, key=_lru_key)

        account_id = chosen["account_id"]

        # Atomic lease update: increment requests_today, total_requests, update last_used_at
        with self.vault._get_connection() as conn:
            if not decrypt_secrets:
                conn.execute(
                    """
                    UPDATE vault_accounts
                    SET requests_today = requests_today + 1,
                        total_requests = total_requests + 1,
                        last_used_at = ?,
                        updated_at = ?
                    WHERE account_id = ?
                    """,
                    (now_iso, now_iso, account_id),
                )
            audit_note = (
                f"Acquired account using strategy '{strategy_clean}' "
                f"(target='{required_target or 'none'}', role='{required_access_role or 'any'}', "
                f"auth='{required_auth_method or 'any'}')"
            )
            conn.execute(
                """
                INSERT INTO vault_audit_log (timestamp, account_id, platform, event_type, tool_id, run_id, notes)
                VALUES (?, ?, ?, 'acquired_for_run', ?, ?, ?)
                """,
                (now_iso, account_id, chosen["platform"], tool_id, run_id, audit_note),
            )

        # Retrieve result record
        if decrypt_secrets:
            result = self.vault.get_account_decrypted(account_id, tool_id=tool_id, run_id=run_id)
        else:
            result = self.vault.get_account_masked(account_id)

        if not result:
            return None

        # Attach ephemeral live 2FA TOTP code if requested and available
        if include_live_totp and "totp_2fa" in result.get("auth_methods", []):
            try:
                totp_data = TOTPHelper.get_totp_for_account(
                    vault=self.vault,
                    account_id=account_id,
                    tool_id=tool_id,
                    run_id=run_id,
                )
                result["live_totp"] = totp_data
            except Exception:
                result["live_totp"] = None

        # Attach routing metadata
        result["routing_meta"] = {
            "strategy_used": strategy_clean,
            "matched_target": required_target,
            "matched_access_role": required_access_role,
            "matched_auth_method": required_auth_method,
            "leased_at": now_iso,
        }

        self.vault.export_public_stats()
        return result

    # ─────────────────────────────────────────────────────────────
    # Outcome Feedback & Cooldown Quarantine
    # ─────────────────────────────────────────────────────────────

    def report_account_outcome(
        self,
        account_id: str,
        outcome: str,
        cooldown_seconds: int = 1800,
        tool_id: str = "",
        run_id: str = "",
        notes: str = "",
    ) -> dict[str, Any] | None:
        """
        Record the execution result of an account run and adjust state machine status,
        health score, and rate-limit cooldown quarantine timers.
        
        Outcomes:
          - 'success': status='active', health +2, cooldown reset
          - 'rate_limited': status='cooldown', health -15, cooldown timer set
          - 'checkpoint_required': status='checkpoint_required', health -40
          - 'session_expired': status='expired', health -30
          - 'banned': status='disabled', health=0
        """
        existing = self.vault._get_raw_row(account_id)
        if not existing:
            return None

        current_health = int(existing["health_score"])
        outcome_clean = outcome.strip().lower()
        now_ts = time.time()
        now_iso = _iso_now()

        if outcome_clean == "success":
            new_status = "active"
            new_health = min(100, current_health + 2)
            new_cooldown = 0.0

        elif outcome_clean == "rate_limited":
            new_status = "cooldown"
            new_health = max(0, current_health - 15)
            new_cooldown = round(now_ts + max(int(cooldown_seconds), 1), 3)

        elif outcome_clean == "checkpoint_required":
            new_status = "checkpoint_required"
            new_health = max(0, current_health - 40)
            new_cooldown = 0.0

        elif outcome_clean == "session_expired":
            new_status = "expired"
            new_health = max(0, current_health - 30)
            new_cooldown = 0.0

        elif outcome_clean == "banned":
            new_status = "disabled"
            new_health = 0
            new_cooldown = 0.0

        else:
            new_status = existing["status"]
            new_health = current_health
            new_cooldown = float(existing["cooldown_until_epoch"])

        with self.vault._get_connection() as conn:
            conn.execute(
                """
                UPDATE vault_accounts
                SET status = ?,
                    health_score = ?,
                    cooldown_until_epoch = ?,
                    updated_at = ?
                WHERE account_id = ?
                """,
                (new_status, new_health, new_cooldown, now_iso, account_id),
            )
            audit_msg = (
                f"Outcome reported: {outcome_clean} | health: {current_health} -> {new_health} | "
                f"status: {existing['status']} -> {new_status} | cooldown_until: {new_cooldown} "
                f"{('| ' + notes) if notes else ''}"
            )
            conn.execute(
                """
                INSERT INTO vault_audit_log (timestamp, account_id, platform, event_type, tool_id, run_id, notes)
                VALUES (?, ?, ?, 'outcome_reported', ?, ?, ?)
                """,
                (now_iso, account_id, existing["platform"], tool_id, run_id, audit_msg),
            )

        self.vault.export_public_stats()
        return self.vault.get_account_masked(account_id)

    # ─────────────────────────────────────────────────────────────
    # Pool Diagnostics & Private Target Coverage Inspector
    # ─────────────────────────────────────────────────────────────

    def get_pool_diagnostics(self, platform: str = "") -> dict[str, Any]:
        """
        Produce a zero-secret health, capacity, and private target coverage report.
        """
        self.release_expired_cooldowns()
        self.reset_stale_daily_quotas()

        now_ts = time.time()
        platform_clean = platform.strip().lower()

        with self.vault._get_connection() as conn:
            # Base account rows
            if platform_clean:
                acc_rows = conn.execute(
                    "SELECT * FROM vault_accounts WHERE LOWER(platform) = LOWER(?)",
                    (platform_clean,),
                ).fetchall()
                target_rows = conn.execute(
                    """
                    SELECT ata.target_handle, ata.account_id, va.status, va.requests_today, va.daily_quota_limit
                    FROM account_target_access ata
                    JOIN vault_accounts va ON ata.account_id = va.account_id
                    WHERE LOWER(ata.platform) = LOWER(?)
                    """,
                    (platform_clean,),
                ).fetchall()
            else:
                acc_rows = conn.execute("SELECT * FROM vault_accounts").fetchall()
                target_rows = conn.execute(
                    """
                    SELECT ata.target_handle, ata.account_id, va.status, va.requests_today, va.daily_quota_limit
                    FROM account_target_access ata
                    JOIN vault_accounts va ON ata.account_id = va.account_id
                    """
                ).fetchall()

        total_accounts = len(acc_rows)
        active_ready = 0
        cooldown_count = 0
        quota_exhausted = 0
        attention_required = 0
        remaining_capacity = 0
        health_scores: list[int] = []

        for r in acc_rows:
            st = r["status"]
            health_scores.append(int(r["health_score"]))
            today_req = int(r["requests_today"])
            quota = int(r["daily_quota_limit"])
            cooldown_epoch = float(r["cooldown_until_epoch"])

            if st == "active":
                if cooldown_epoch > now_ts:
                    cooldown_count += 1
                elif today_req >= quota:
                    quota_exhausted += 1
                else:
                    active_ready += 1
                    remaining_capacity += max(0, quota - today_req)
            elif st == "cooldown":
                cooldown_count += 1
            elif st in ("checkpoint_required", "expired", "disabled"):
                attention_required += 1

        avg_health = round(sum(health_scores) / total_accounts, 1) if total_accounts > 0 else 100.0

        # Private target coverage
        coverage: dict[str, dict[str, int]] = {}
        for tr in target_rows:
            handle = tr["target_handle"]
            if handle not in coverage:
                coverage[handle] = {
                    "total_followers": 0,
                    "active_ready_followers": 0,
                    "remaining_target_capacity": 0,
                }
            coverage[handle]["total_followers"] += 1
            if tr["status"] == "active" and tr["requests_today"] < tr["daily_quota_limit"]:
                coverage[handle]["active_ready_followers"] += 1
                coverage[handle]["remaining_target_capacity"] += max(0, tr["daily_quota_limit"] - tr["requests_today"])

        return {
            "platform_filter": platform_clean or "all",
            "total_accounts": total_accounts,
            "active_ready_accounts": active_ready,
            "cooldown_accounts": cooldown_count,
            "quota_exhausted_accounts": quota_exhausted,
            "attention_required_accounts": attention_required,
            "remaining_daily_capacity": remaining_capacity,
            "avg_health_score": avg_health,
            "private_target_coverage": coverage,
            "generated_at": _iso_now(),
        }


# Singleton Router Instance
_DEFAULT_ROUTER: AccountRouter | None = None


def get_account_router(vault: CredentialVault | None = None) -> AccountRouter:
    """Return the singleton AccountRouter instance."""
    global _DEFAULT_ROUTER
    if _DEFAULT_ROUTER is None:
        _DEFAULT_ROUTER = AccountRouter(vault=vault)
    return _DEFAULT_ROUTER
