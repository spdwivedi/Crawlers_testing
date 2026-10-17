"""
core/vault_importer.py
======================
High-Speed Bulk Account Importer & Multi-Format Cookie / Session Parsers — Rule 6.

Key Capabilities:
  1. Multi-Format Cookie Parsers:
       - parse_netscape_cookies_txt: Parses Netscape HTTP cookie files (including #HttpOnly_)
       - parse_json_cookie_jar: Parses JSON cookie arrays and Playwright storage_state dicts
  2. High-Speed Single-Transaction Batch Importer (bulk_import_accounts):
       - Encrypts 1,000+ accounts in memory with row-bound AES-256-GCM
       - Executes all database inserts and target mappings inside a single SQLite transaction
       - Completes 1,000 accounts in <2 seconds
       - Intelligent deduplication via (platform, username_blind_hash)
  3. CSV & JSONL Stream Ingestion (import_from_csv, import_from_jsonl)
  4. Safe Masked Inventory & Encrypted Ciphertext Backup Exporters
"""
from __future__ import annotations

import csv
import io
import json
import sqlite3
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.credential_vault import (
    DEFAULT_DOMAINS,
    VAULT_DB_PATH,
    CredentialVault,
    get_credential_vault,
)
from core.crypto_engine import CryptoEngine, get_crypto_engine

KNOWN_SESSION_COOKIE_NAMES = {
    "sessionid",
    "csrftoken",
    "ds_user_id",
    "c_user",
    "xs",
    "leetcode_session",
    "auth_token",
    "twid",
    "li_at",
    "reddit_session",
    "session",
    "token",
}


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class VaultImporter:
    """High-speed bulk credential ingestion and multi-format cookie parser engine."""

    def __init__(
        self,
        vault: CredentialVault | None = None,
        crypto: CryptoEngine | None = None,
    ) -> None:
        self.vault = vault or get_credential_vault()
        self.crypto = crypto or get_crypto_engine()

    # ─────────────────────────────────────────────────────────────
    # Cookie & Session Parsers
    # ─────────────────────────────────────────────────────────────

    @staticmethod
    def parse_netscape_cookies_txt(content: str) -> dict[str, Any]:
        """
        Parse Netscape HTTP Cookie file content (as exported by extensions or curl).
        
        Handles:
          - Standard 7 tab-separated columns:
            domain, flag (subdomains), path, secure, expiration, name, value
          - Lines starting with '#HttpOnly_' correctly set httpOnly=True
          - Lines starting with pure '#' are treated as comments and skipped
          - Auto-extracts well-known authentication and session tokens
        """
        cookies: list[dict[str, Any]] = []
        extracted_tokens: dict[str, str] = {}
        domains: set[str] = set()

        for raw_line in content.splitlines():
            line = raw_line.strip()
            if not line:
                continue

            is_http_only = False
            if line.startswith("#HttpOnly_"):
                is_http_only = True
                line = line[len("#HttpOnly_"):].strip()
            elif line.startswith("#"):
                continue

            parts = [p.strip() for p in line.split("\t") if p.strip() != ""]
            if len(parts) < 7:
                # Try fallback splitting on multiple spaces if tabs were converted
                parts = [p.strip() for p in line.split() if p.strip()]
                if len(parts) < 7:
                    continue

            domain = parts[0]
            flag = parts[1].upper() == "TRUE"
            path = parts[2]
            secure = parts[3].upper() == "TRUE"

            try:
                expires = int(parts[4])
            except ValueError:
                expires = None

            name = parts[5]
            value = parts[6]

            domains.add(domain.lstrip("."))

            cookie_obj = {
                "name": name,
                "value": value,
                "domain": domain,
                "path": path,
                "expires": expires,
                "httpOnly": is_http_only,
                "secure": secure,
                "sameSite": "Lax",
            }
            cookies.append(cookie_obj)

            # Check if this cookie represents a well-known session token
            if name.lower() in KNOWN_SESSION_COOKIE_NAMES:
                extracted_tokens[name] = value

        return {
            "cookies": cookies,
            "extracted_tokens": extracted_tokens,
            "domains": sorted(list(domains)),
        }

    @staticmethod
    def parse_json_cookie_jar(content: str | list | dict) -> dict[str, Any]:
        """
        Parse JSON cookie arrays (EditThisCookie / DevTools) or Playwright storage_state dicts.
        """
        if isinstance(content, str):
            try:
                data = json.loads(content)
            except Exception as e:
                raise ValueError(f"Invalid JSON cookie jar format: {e}") from e
        else:
            data = content

        raw_cookies: list[dict[str, Any]] = []
        storage_state: dict[str, Any] = {}
        extracted_tokens: dict[str, str] = {}
        domains: set[str] = set()

        if isinstance(data, dict):
            if "cookies" in data:
                raw_cookies = data.get("cookies", [])
                storage_state = data
            else:
                # May be a single cookie dictionary
                raw_cookies = [data]
        elif isinstance(data, list):
            raw_cookies = data
            storage_state = {"cookies": raw_cookies, "origins": []}

        normalized_cookies: list[dict[str, Any]] = []
        for c in raw_cookies:
            if not isinstance(c, dict):
                continue
            name = str(c.get("name", "")).strip()
            value = str(c.get("value", "")).strip()
            domain = str(c.get("domain", "")).strip()
            path = str(c.get("path", "/")).strip()

            if domain:
                domains.add(domain.lstrip("."))

            cookie_obj = {
                "name": name,
                "value": value,
                "domain": domain,
                "path": path,
                "expires": c.get("expirationDate") or c.get("expires"),
                "httpOnly": bool(c.get("httpOnly", False)),
                "secure": bool(c.get("secure", False)),
                "sameSite": c.get("sameSite", "Lax"),
            }
            normalized_cookies.append(cookie_obj)

            if name.lower() in KNOWN_SESSION_COOKIE_NAMES:
                extracted_tokens[name] = value

        return {
            "cookies": normalized_cookies,
            "storage_state": storage_state,
            "extracted_tokens": extracted_tokens,
            "domains": sorted(list(domains)),
        }

    # ─────────────────────────────────────────────────────────────
    # High-Speed Bulk Importer
    # ─────────────────────────────────────────────────────────────

    def bulk_import_accounts(
        self,
        records: list[dict[str, Any]],
        on_conflict: str = "update",
    ) -> dict[str, Any]:
        """
        Import hundreds or thousands of accounts in a single SQLite transaction.
        
        Args:
            records: List of account dictionaries.
            on_conflict: 'update' to update existing records, or 'skip' to skip duplicates.
            
        Returns:
            {
                "total_processed": int,
                "inserted": int,
                "updated": int,
                "skipped": int,
                "targets_linked": int,
                "elapsed_ms": int
            }
        """
        t0 = time.perf_counter()
        now = _iso_now()
        now_epoch = int(time.time())

        inserted = 0
        updated = 0
        skipped = 0
        targets_linked = 0

        # Open single connection and perform all operations within one transaction
        with self.vault._get_connection() as conn:
            # Pre-fetch existing accounts to map (platform, blind_hash) -> account_id
            cur = conn.execute("SELECT account_id, platform, username_blind_hash FROM vault_accounts")
            existing_map: dict[tuple[str, str], str] = {
                (r[1], r[2]): r[0] for r in cur.fetchall() if r[2]
            }

            for rec in records:
                platform = str(rec.get("platform", "")).strip().lower()
                if not platform:
                    continue

                username_str = str(rec.get("username", "")).strip()
                domain = str(rec.get("domain", "")).strip().lower() or DEFAULT_DOMAINS.get(
                    platform, f"{platform}.com"
                )
                account_label = str(rec.get("account_label", "")).strip()

                username_masked = self.crypto.mask_secret(username_str) if username_str else ""
                blind_hash = (
                    self.crypto.blind_index_hash(f"{platform}:{username_str.lower()}")
                    if username_str
                    else ""
                )

                # Determine if updating existing or inserting new
                existing_key = (platform, blind_hash) if blind_hash else None
                is_existing = existing_key is not None and existing_key in existing_map

                if is_existing:
                    if on_conflict == "skip":
                        skipped += 1
                        continue
                    account_id = existing_map[existing_key]  # type: ignore[index]
                else:
                    account_id = (
                        str(rec.get("account_id", "")).strip()
                        or f"acc_{platform[:5]}_{now_epoch}_{uuid.uuid4().hex[:6]}"
                    )

                # Parse cookies / storage state if provided as raw strings
                cookie_jar = rec.get("cookie_jar") or rec.get("cookies")
                if isinstance(cookie_jar, str):
                    if cookie_jar.strip().startswith("[") or cookie_jar.strip().startswith("{"):
                        parsed = self.parse_json_cookie_jar(cookie_jar)
                    else:
                        parsed = self.parse_netscape_cookies_txt(cookie_jar)
                    cookie_jar = parsed["cookies"]
                    if not rec.get("session_tokens") and parsed["extracted_tokens"]:
                        rec["session_tokens"] = parsed["extracted_tokens"]

                password = rec.get("password")
                totp_secret = rec.get("totp_secret")
                session_tokens = rec.get("session_tokens")
                storage_state = rec.get("storage_state")
                api_headers = rec.get("api_headers")
                proxy_config = rec.get("proxy_config")
                fingerprint_profile = rec.get("fingerprint_profile")
                status = str(rec.get("status", "active")).strip().lower()
                health_score = int(rec.get("health_score", 100))
                daily_quota_limit = int(rec.get("daily_quota_limit", 50))

                # Identify active auth methods
                active_methods: list[str] = []
                if username_str and password:
                    active_methods.append("user_pass")
                if totp_secret:
                    active_methods.append("totp_2fa")
                if cookie_jar:
                    active_methods.append("cookie_jar")
                if session_tokens:
                    active_methods.append("session_tokens")
                if storage_state:
                    active_methods.append("storage_state")
                if api_headers:
                    active_methods.append("api_headers")
                if proxy_config:
                    active_methods.append("proxy_config")

                # In-memory row-bound encryption (hardware-accelerated AES-GCM)
                enc_user = self.crypto.encrypt_str(username_str, associated_data=account_id) if username_str else None
                enc_pass = self.crypto.encrypt_str(str(password), associated_data=account_id) if password else None
                enc_totp = self.crypto.encrypt_str(str(totp_secret).strip(), associated_data=account_id) if totp_secret else None
                enc_cookies = self.crypto.encrypt_json(cookie_jar, associated_data=account_id) if cookie_jar is not None else None
                enc_tokens = self.crypto.encrypt_json(session_tokens, associated_data=account_id) if session_tokens is not None else None
                enc_storage = self.crypto.encrypt_json(storage_state, associated_data=account_id) if storage_state is not None else None
                enc_headers = self.crypto.encrypt_json(api_headers, associated_data=account_id) if api_headers is not None else None
                enc_proxy = self.crypto.encrypt_json(proxy_config, associated_data=account_id) if proxy_config is not None else None

                methods_json = json.dumps(active_methods, separators=(",", ":"))
                fingerprint_json = json.dumps(fingerprint_profile or {}, separators=(",", ":"))

                if is_existing:
                    # Update existing record
                    conn.execute(
                        """
                        UPDATE vault_accounts SET
                            domain = ?,
                            account_label = COALESCE(NULLIF(?, ''), account_label),
                            username_masked = ?,
                            auth_methods_json = ?,
                            enc_username = COALESCE(?, enc_username),
                            enc_password = COALESCE(?, enc_password),
                            enc_totp_secret = COALESCE(?, enc_totp_secret),
                            enc_cookie_jar_json = COALESCE(?, enc_cookie_jar_json),
                            enc_session_tokens_json = COALESCE(?, enc_session_tokens_json),
                            enc_storage_state_json = COALESCE(?, enc_storage_state_json),
                            enc_api_headers_json = COALESCE(?, enc_api_headers_json),
                            enc_proxy_config_json = COALESCE(?, enc_proxy_config_json),
                            fingerprint_profile_json = COALESCE(?, fingerprint_profile_json),
                            status = ?,
                            health_score = ?,
                            daily_quota_limit = ?,
                            updated_at = ?
                        WHERE account_id = ?
                        """,
                        (
                            domain, account_label, username_masked, methods_json,
                            enc_user, enc_pass, enc_totp, enc_cookies, enc_tokens,
                            enc_storage, enc_headers, enc_proxy, fingerprint_json,
                            status, health_score, daily_quota_limit, now, account_id,
                        ),
                    )
                    updated += 1
                else:
                    # Insert new record
                    conn.execute(
                        """
                        INSERT INTO vault_accounts (
                            account_id, platform, domain, account_label, username_masked,
                            username_blind_hash, auth_methods_json, enc_username, enc_password,
                            enc_totp_secret, enc_cookie_jar_json, enc_session_tokens_json,
                            enc_storage_state_json, enc_api_headers_json, enc_proxy_config_json,
                            fingerprint_profile_json, status, health_score, daily_quota_limit,
                            requests_today, total_requests, cooldown_until_epoch,
                            last_used_at, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 0, 0.0, NULL, ?, ?)
                        """,
                        (
                            account_id, platform, domain, account_label or username_masked,
                            username_masked, blind_hash, methods_json, enc_user, enc_pass,
                            enc_totp, enc_cookies, enc_tokens, enc_storage, enc_headers,
                            enc_proxy, fingerprint_json, status, health_score, daily_quota_limit,
                            now, now,
                        ),
                    )
                    if existing_key:
                        existing_map[existing_key] = account_id
                    inserted += 1

                # Link target accounts / private followers
                follows_targets = rec.get("follows_targets")
                access_role = str(rec.get("access_role", "follower")).strip() or "follower"
                if isinstance(follows_targets, str):
                    # Support pipe '|' or comma ',' separated strings
                    if "|" in follows_targets:
                        follows_targets = [t.strip() for t in follows_targets.split("|") if t.strip()]
                    else:
                        follows_targets = [t.strip() for t in follows_targets.split(",") if t.strip()]

                if follows_targets and isinstance(follows_targets, list):
                    for target in follows_targets:
                        h_norm = str(target).strip().lower()
                        if h_norm:
                            chk = conn.execute(
                                "SELECT 1 FROM account_target_access WHERE account_id = ? AND target_handle = ?",
                                (account_id, h_norm),
                            ).fetchone()
                            if not chk:
                                conn.execute(
                                    """
                                    INSERT INTO account_target_access (
                                        account_id, platform, target_handle, access_role, verified_at
                                    ) VALUES (?, ?, ?, ?, ?)
                                    """,
                                    (account_id, platform, h_norm, access_role, now),
                                )
                                targets_linked += 1

            # Record batch audit trail entry
            conn.execute(
                """
                INSERT INTO vault_audit_log (timestamp, account_id, platform, event_type, notes)
                VALUES (?, 'batch', 'all', 'batch_import', ?)
                """,
                (
                    now,
                    f"Bulk imported {len(records)} accounts (inserted={inserted}, updated={updated}, skipped={skipped}, targets_linked={targets_linked})",
                ),
            )

        # Refresh public stats once for entire batch
        self.vault.export_public_stats()

        elapsed_ms = int((time.perf_counter() - t0) * 1000)
        return {
            "total_processed": len(records),
            "inserted": inserted,
            "updated": updated,
            "skipped": skipped,
            "targets_linked": targets_linked,
            "elapsed_ms": elapsed_ms,
        }

    # ─────────────────────────────────────────────────────────────
    # File Stream Ingestion (JSONL & CSV)
    # ─────────────────────────────────────────────────────────────

    def import_from_jsonl(
        self,
        jsonl_text_or_path: str | Path,
        on_conflict: str = "update",
    ) -> dict[str, Any]:
        """Import accounts from a JSONL file path or raw multi-line JSONL string."""
        records: list[dict[str, Any]] = []
        path = Path(jsonl_text_or_path)
        if path.exists() and path.is_file():
            content = path.read_text(encoding="utf-8")
        else:
            content = str(jsonl_text_or_path)

        for line in content.splitlines():
            line_s = line.strip()
            if line_s:
                try:
                    records.append(json.loads(line_s))
                except Exception:
                    pass

        return self.bulk_import_accounts(records, on_conflict=on_conflict)

    def import_from_csv(
        self,
        csv_text_or_path: str | Path,
        on_conflict: str = "update",
    ) -> dict[str, Any]:
        """Import accounts from a CSV file path or raw CSV string."""
        records: list[dict[str, Any]] = []
        path = Path(csv_text_or_path)
        if path.exists() and path.is_file():
            content = path.read_text(encoding="utf-8")
        else:
            content = str(csv_text_or_path)

        reader = csv.DictReader(io.StringIO(content))
        for row in reader:
            clean_row: dict[str, Any] = {}
            for k, v in row.items():
                if k is None:
                    continue
                k_norm = k.strip()
                v_clean = v.strip() if isinstance(v, str) else v
                clean_row[k_norm] = v_clean if v_clean != "" else None

            # Parse follows_targets pipe string if present
            if clean_row.get("follows_targets"):
                targets_str = str(clean_row["follows_targets"])
                clean_row["follows_targets"] = [
                    t.strip() for t in targets_str.split("|") if t.strip()
                ]

            records.append(clean_row)

        return self.bulk_import_accounts(records, on_conflict=on_conflict)

    # ─────────────────────────────────────────────────────────────
    # Exporters (Masked Inventory & Encrypted Backup)
    # ─────────────────────────────────────────────────────────────

    def export_masked_inventory(self, limit: int = 10_000) -> list[dict[str, Any]]:
        """
        Export all accounts with zero plaintext secrets (masked usernames & metadata only).
        """
        res = self.vault.list_accounts_masked(limit=limit)
        return res.get("accounts", [])

    def export_encrypted_backup(self) -> dict[str, Any]:
        """
        Export raw ciphertext records for backup/migration without decrypting secrets.
        """
        with self.vault._get_connection() as conn:
            acc_rows = conn.execute("SELECT * FROM vault_accounts ORDER BY created_at ASC").fetchall()
            target_rows = conn.execute("SELECT * FROM account_target_access ORDER BY access_id ASC").fetchall()

            accounts = [dict(r) for r in acc_rows]
            targets = [dict(r) for r in target_rows]

        return {
            "version": 1,
            "exported_at": _iso_now(),
            "total_accounts": len(accounts),
            "total_targets": len(targets),
            "accounts": accounts,
            "target_access": targets,
        }

    def restore_encrypted_backup(self, backup_data: dict[str, Any], on_conflict: str = "update") -> dict[str, Any]:
        """
        Restore encrypted ciphertext backup records preserving original account_ids and ciphertexts.
        """
        accounts = backup_data.get("accounts", [])
        targets = backup_data.get("target_access", [])

        restored_accounts = 0
        restored_targets = 0

        with self.vault._get_connection() as conn:
            for acc in accounts:
                cols = list(acc.keys())
                placeholders = ", ".join("?" for _ in cols)
                col_names = ", ".join(cols)
                if on_conflict == "update":
                    update_clause = ", ".join(f"{c} = excluded.{c}" for c in cols if c != "account_id")
                    sql = f"INSERT INTO vault_accounts ({col_names}) VALUES ({placeholders}) ON CONFLICT(account_id) DO UPDATE SET {update_clause}"
                else:
                    sql = f"INSERT OR IGNORE INTO vault_accounts ({col_names}) VALUES ({placeholders})"
                conn.execute(sql, list(acc.values()))
                restored_accounts += 1

            for tgt in targets:
                # Remove access_id if present to allow autoincrement
                tgt_data = dict(tgt)
                tgt_data.pop("access_id", None)
                cols = list(tgt_data.keys())
                placeholders = ", ".join("?" for _ in cols)
                col_names = ", ".join(cols)
                conn.execute(
                    f"INSERT INTO account_target_access ({col_names}) VALUES ({placeholders})",
                    list(tgt_data.values()),
                )
                restored_targets += 1

        self.vault.export_public_stats()
        return {
            "restored_accounts": restored_accounts,
            "restored_targets": restored_targets,
        }
