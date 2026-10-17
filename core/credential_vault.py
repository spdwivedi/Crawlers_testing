"""
core/credential_vault.py
========================
Zero-Plaintext Encrypted SQLite Credential Vault & Follower Mapping — Rule 6.

Key Capabilities:
  1. WAL-mode SQLite storage at vault_store/credentials_vault.sqlite (Git-ignored).
  2. 6-Method Authentication Schema:
       - user_pass: Encrypted username & password
       - totp_2fa: Encrypted TOTP base32 secret
       - cookie_jar: Encrypted cookie array [{name, value, domain, ...}]
       - session_tokens: Encrypted auth token dictionary
       - storage_state: Encrypted Playwright/Camoufox localStorage & cookies
       - api_headers / proxy_config: Encrypted headers & sticky proxy endpoints
  3. Cryptographic Row-Binding (associated_data=account_id) preventing ciphertext swapping.
  4. Private-Target Follower Relationship Mapping (account_target_access).
  5. Audit Log Trail without secret exposure (vault_audit_log).
  6. Git-Tracked Non-Sensitive Aggregate Stats Snapshot (vault_store/vault_stats_public.json).
"""
from __future__ import annotations

import json
import sqlite3
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.crypto_engine import CryptoEngine, get_crypto_engine

ROOT = Path(__file__).resolve().parents[1]
VAULT_STORE_DIR = ROOT / "vault_store"
VAULT_DB_PATH = VAULT_STORE_DIR / "credentials_vault.sqlite"
VAULT_STATS_PATH = VAULT_STORE_DIR / "vault_stats_public.json"

DEFAULT_DOMAINS = {
    "instagram": "instagram.com",
    "facebook": "facebook.com",
    "leetcode": "leetcode.com",
    "twitter": "x.com",
    "x": "x.com",
    "reddit": "reddit.com",
    "github": "github.com",
    "linkedin": "linkedin.com",
}


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class CredentialVault:
    """
    Production-grade SQLite Credential Vault with authenticated AES-256-GCM encryption.
    All secrets are stored as v1:aes256gcm tokens row-bound to account_id.
    """

    def __init__(self, db_path: Path = VAULT_DB_PATH, crypto: CryptoEngine | None = None) -> None:
        self.db_path = db_path
        self.crypto = crypto or get_crypto_engine()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        """Open a SQLite connection configured for concurrent WAL operation."""
        conn = sqlite3.connect(str(self.db_path), timeout=5.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA synchronous = NORMAL;")
        conn.execute("PRAGMA busy_timeout = 5000;")
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def _init_db(self) -> None:
        """Create vault tables and indexes if they do not exist."""
        with self._get_connection() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS vault_accounts (
                    account_id TEXT PRIMARY KEY,
                    platform TEXT NOT NULL,
                    domain TEXT NOT NULL,
                    account_label TEXT,
                    username_masked TEXT,
                    username_blind_hash TEXT,
                    auth_methods_json TEXT NOT NULL,
                    enc_username TEXT,
                    enc_password TEXT,
                    enc_totp_secret TEXT,
                    enc_cookie_jar_json TEXT,
                    enc_session_tokens_json TEXT,
                    enc_storage_state_json TEXT,
                    enc_api_headers_json TEXT,
                    enc_proxy_config_json TEXT,
                    fingerprint_profile_json TEXT,
                    status TEXT NOT NULL DEFAULT 'active',
                    health_score INTEGER NOT NULL DEFAULT 100,
                    daily_quota_limit INTEGER NOT NULL DEFAULT 50,
                    requests_today INTEGER NOT NULL DEFAULT 0,
                    total_requests INTEGER NOT NULL DEFAULT 0,
                    cooldown_until_epoch REAL NOT NULL DEFAULT 0.0,
                    last_used_at TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS account_target_access (
                    access_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    account_id TEXT NOT NULL REFERENCES vault_accounts(account_id) ON DELETE CASCADE,
                    platform TEXT NOT NULL,
                    target_handle TEXT NOT NULL,
                    access_role TEXT NOT NULL DEFAULT 'follower',
                    verified_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS vault_audit_log (
                    audit_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    account_id TEXT NOT NULL,
                    platform TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    tool_id TEXT,
                    run_id TEXT,
                    notes TEXT
                );

                CREATE INDEX IF NOT EXISTS idx_target_lookup 
                    ON account_target_access(platform, target_handle, access_role);

                CREATE INDEX IF NOT EXISTS idx_accounts_platform_status 
                    ON vault_accounts(platform, status);

                CREATE INDEX IF NOT EXISTS idx_accounts_blind_hash 
                    ON vault_accounts(username_blind_hash);

                CREATE INDEX IF NOT EXISTS idx_audit_account 
                    ON vault_audit_log(account_id, timestamp);
                """
            )
        # Ensure public stats JSON file exists
        if not VAULT_STATS_PATH.exists():
            self.export_public_stats()

    # ─────────────────────────────────────────────────────────────
    # Core Account Management
    # ─────────────────────────────────────────────────────────────

    def add_account(
        self,
        platform: str,
        domain: str = "",
        username: str = "",
        password: str = "",
        account_label: str = "",
        totp_secret: str = "",
        cookie_jar: list[dict] | None = None,
        session_tokens: dict | None = None,
        storage_state: dict | None = None,
        api_headers: dict | None = None,
        proxy_config: dict | None = None,
        fingerprint_profile: dict | None = None,
        follows_targets: list[str] | None = None,
        access_role: str = "follower",
        status: str = "active",
        health_score: int = 100,
        daily_quota_limit: int = 50,
        account_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Encrypt and store an account credential profile with row-bound AES-256-GCM.
        
        Args:
            platform: Platform identifier ('instagram', 'facebook', 'leetcode', etc.)
            domain: Domain name (defaults to well-known platform domain if empty)
            username: Plaintext username (encrypted before storing)
            password: Plaintext password (encrypted before storing)
            account_label: Human-friendly alias
            totp_secret: Plaintext TOTP 2FA secret (encrypted before storing)
            cookie_jar: List of cookie dictionaries (encrypted before storing)
            session_tokens: Key-value session token dictionary (encrypted before storing)
            storage_state: Playwright/Camoufox storage state dict (encrypted before storing)
            api_headers: Custom HTTP headers/API keys dict (encrypted before storing)
            proxy_config: Proxy configuration dict (encrypted before storing)
            fingerprint_profile: Non-sensitive sticky browser fingerprint dict
            follows_targets: List of target accounts/groups this account has access to
            access_role: Target access relationship ('follower', 'friend', 'member', etc.)
            status: Account status ('active', 'cooldown', 'rate_limited', etc.)
            health_score: Initial health rating (0-100)
            daily_quota_limit: Max daily operations limit
            account_id: Optional explicit account ID, or auto-generated
            
        Returns:
            Safe masked account summary dictionary (0 secrets exposed).
        """
        platform_norm = platform.strip().lower()
        domain_norm = domain.strip().lower() if domain else DEFAULT_DOMAINS.get(platform_norm, f"{platform_norm}.com")
        
        if not account_id:
            prefix = platform_norm[:5]
            account_id = f"acc_{prefix}_{int(time.time())}_{uuid.uuid4().hex[:6]}"

        now = _iso_now()
        username_str = str(username).strip()
        username_masked = self.crypto.mask_secret(username_str) if username_str else ""
        blind_hash = self.crypto.blind_index_hash(f"{platform_norm}:{username_str.lower()}") if username_str else ""

        # Determine active authentication methods
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

        # Authenticated Row-Bound Encryption (associated_data = account_id)
        enc_user = self.crypto.encrypt_str(username_str, associated_data=account_id) if username_str else None
        enc_pass = self.crypto.encrypt_str(str(password), associated_data=account_id) if password else None
        enc_totp = self.crypto.encrypt_str(str(totp_secret).strip(), associated_data=account_id) if totp_secret else None
        enc_cookies = self.crypto.encrypt_json(cookie_jar, associated_data=account_id) if cookie_jar is not None else None
        enc_tokens = self.crypto.encrypt_json(session_tokens, associated_data=account_id) if session_tokens is not None else None
        enc_storage = self.crypto.encrypt_json(storage_state, associated_data=account_id) if storage_state is not None else None
        enc_headers = self.crypto.encrypt_json(api_headers, associated_data=account_id) if api_headers is not None else None
        enc_proxy = self.crypto.encrypt_json(proxy_config, associated_data=account_id) if proxy_config is not None else None

        fingerprint_json = json.dumps(fingerprint_profile or {}, separators=(",", ":"))
        methods_json = json.dumps(active_methods, separators=(",", ":"))

        with self._get_connection() as conn:
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
                    account_id, platform_norm, domain_norm, account_label or username_masked,
                    username_masked, blind_hash, methods_json, enc_user, enc_pass,
                    enc_totp, enc_cookies, enc_tokens, enc_storage, enc_headers, enc_proxy,
                    fingerprint_json, status, health_score, daily_quota_limit, now, now,
                ),
            )

            # Link initial private target followers
            linked_count = 0
            if follows_targets:
                for target in follows_targets:
                    norm_target = str(target).strip().lower()
                    if norm_target:
                        conn.execute(
                            """
                            INSERT INTO account_target_access (
                                account_id, platform, target_handle, access_role, verified_at
                            ) VALUES (?, ?, ?, ?, ?)
                            """,
                            (account_id, platform_norm, norm_target, access_role, now),
                        )
                        linked_count += 1

            # Log audit entry
            conn.execute(
                """
                INSERT INTO vault_audit_log (timestamp, account_id, platform, event_type, notes)
                VALUES (?, ?, ?, 'created', ?)
                """,
                (now, account_id, platform_norm, f"Created account profile with {len(active_methods)} auth methods and {linked_count} target links"),
            )

        self.export_public_stats()
        return self.get_account_masked(account_id)  # type: ignore[return-value]

    def update_account(
        self,
        account_id: str,
        password: str | None = None,
        totp_secret: str | None = None,
        cookie_jar: list[dict] | None = None,
        session_tokens: dict | None = None,
        storage_state: dict | None = None,
        api_headers: dict | None = None,
        proxy_config: dict | None = None,
        fingerprint_profile: dict | None = None,
        status: str | None = None,
        health_score: int | None = None,
        daily_quota_limit: int | None = None,
        account_label: str | None = None,
        cooldown_until_epoch: float | None = None,
    ) -> dict[str, Any] | None:
        """
        Update account credentials and state. Re-encrypts updated secret fields with row-bound GCM.
        """
        existing = self._get_raw_row(account_id)
        if not existing:
            return None

        now = _iso_now()
        updates: dict[str, Any] = {"updated_at": now}

        if password is not None:
            updates["enc_password"] = self.crypto.encrypt_str(str(password), associated_data=account_id)
        if totp_secret is not None:
            updates["enc_totp_secret"] = self.crypto.encrypt_str(str(totp_secret), associated_data=account_id)
        if cookie_jar is not None:
            updates["enc_cookie_jar_json"] = self.crypto.encrypt_json(cookie_jar, associated_data=account_id)
        if session_tokens is not None:
            updates["enc_session_tokens_json"] = self.crypto.encrypt_json(session_tokens, associated_data=account_id)
        if storage_state is not None:
            updates["enc_storage_state_json"] = self.crypto.encrypt_json(storage_state, associated_data=account_id)
        if api_headers is not None:
            updates["enc_api_headers_json"] = self.crypto.encrypt_json(api_headers, associated_data=account_id)
        if proxy_config is not None:
            updates["enc_proxy_config_json"] = self.crypto.encrypt_json(proxy_config, associated_data=account_id)
        if fingerprint_profile is not None:
            updates["fingerprint_profile_json"] = json.dumps(fingerprint_profile, separators=(",", ":"))
        if status is not None:
            updates["status"] = status
        if health_score is not None:
            updates["health_score"] = int(health_score)
        if daily_quota_limit is not None:
            updates["daily_quota_limit"] = int(daily_quota_limit)
        if account_label is not None:
            updates["account_label"] = account_label
        if cooldown_until_epoch is not None:
            updates["cooldown_until_epoch"] = float(cooldown_until_epoch)

        # Recalculate auth methods if secrets were modified
        merged_row = dict(existing)
        merged_row.update(updates)
        active_methods: list[str] = []
        if merged_row.get("enc_username") and merged_row.get("enc_password"):
            active_methods.append("user_pass")
        if merged_row.get("enc_totp_secret"):
            active_methods.append("totp_2fa")
        if merged_row.get("enc_cookie_jar_json"):
            active_methods.append("cookie_jar")
        if merged_row.get("enc_session_tokens_json"):
            active_methods.append("session_tokens")
        if merged_row.get("enc_storage_state_json"):
            active_methods.append("storage_state")
        if merged_row.get("enc_api_headers_json"):
            active_methods.append("api_headers")
        if merged_row.get("enc_proxy_config_json"):
            active_methods.append("proxy_config")
        updates["auth_methods_json"] = json.dumps(active_methods, separators=(",", ":"))

        set_clause = ", ".join(f"{k} = ?" for k in updates.keys())
        params = list(updates.values()) + [account_id]

        with self._get_connection() as conn:
            conn.execute(f"UPDATE vault_accounts SET {set_clause} WHERE account_id = ?", params)
            conn.execute(
                """
                INSERT INTO vault_audit_log (timestamp, account_id, platform, event_type, notes)
                VALUES (?, ?, ?, 'updated', ?)
                """,
                (now, account_id, existing["platform"], f"Updated fields: {list(updates.keys())}"),
            )

        self.export_public_stats()
        return self.get_account_masked(account_id)

    def delete_account(self, account_id: str) -> bool:
        """Permanently delete an account from the vault (cascade removes targets)."""
        existing = self._get_raw_row(account_id)
        if not existing:
            return False

        now = _iso_now()
        with self._get_connection() as conn:
            conn.execute("DELETE FROM vault_accounts WHERE account_id = ?", (account_id,))
            conn.execute(
                """
                INSERT INTO vault_audit_log (timestamp, account_id, platform, event_type, notes)
                VALUES (?, ?, ?, 'deleted', 'Account removed from vault')
                """,
                (now, account_id, existing["platform"]),
            )

        self.export_public_stats()
        return True

    # ─────────────────────────────────────────────────────────────
    # Query & Decryption Operations
    # ─────────────────────────────────────────────────────────────

    def _get_raw_row(self, account_id: str) -> sqlite3.Row | None:
        with self._get_connection() as conn:
            cur = conn.execute("SELECT * FROM vault_accounts WHERE account_id = ?", (account_id,))
            return cur.fetchone()

    def get_account_masked(self, account_id: str) -> dict[str, Any] | None:
        """
        Retrieve account summary without decrypting sensitive secrets.
        Safe for API responses, UI display, and operational logging.
        """
        row = self._get_raw_row(account_id)
        if not row:
            return None

        # Fetch follower targets
        targets = self.get_target_access_for_account(account_id)

        try:
            methods = json.loads(row["auth_methods_json"])
        except Exception:
            methods = []

        try:
            fingerprint = json.loads(row["fingerprint_profile_json"])
        except Exception:
            fingerprint = {}

        return {
            "account_id": row["account_id"],
            "platform": row["platform"],
            "domain": row["domain"],
            "account_label": row["account_label"] or row["username_masked"],
            "username_masked": row["username_masked"],
            "auth_methods": methods,
            "status": row["status"],
            "health_score": row["health_score"],
            "daily_quota_limit": row["daily_quota_limit"],
            "requests_today": row["requests_today"],
            "total_requests": row["total_requests"],
            "cooldown_until_epoch": row["cooldown_until_epoch"],
            "is_available": (row["status"] == "active" and row["cooldown_until_epoch"] <= time.time()),
            "fingerprint_profile": fingerprint,
            "follows_targets": targets,
            "last_used_at": row["last_used_at"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }

    def get_account_decrypted(
        self,
        account_id: str,
        tool_id: str = "",
        run_id: str = "",
    ) -> dict[str, Any] | None:
        """
        Decrypt and return authentication credentials for an authorized scraper run.
        Logs an access event in vault_audit_log with the calling tool_id and run_id.
        
        Raises:
            ValueError: If ciphertext verification or row-binding integrity check fails.
        """
        row = self._get_raw_row(account_id)
        if not row:
            return None

        now = _iso_now()

        # Decrypt secrets with associated_data=account_id binding
        decrypted_user = self.crypto.decrypt_str(row["enc_username"], associated_data=account_id) if row["enc_username"] else ""
        decrypted_pass = self.crypto.decrypt_str(row["enc_password"], associated_data=account_id) if row["enc_password"] else ""
        decrypted_totp = self.crypto.decrypt_str(row["enc_totp_secret"], associated_data=account_id) if row["enc_totp_secret"] else ""
        decrypted_cookies = self.crypto.decrypt_json(row["enc_cookie_jar_json"], associated_data=account_id) if row["enc_cookie_jar_json"] else []
        decrypted_tokens = self.crypto.decrypt_json(row["enc_session_tokens_json"], associated_data=account_id) if row["enc_session_tokens_json"] else {}
        decrypted_storage = self.crypto.decrypt_json(row["enc_storage_state_json"], associated_data=account_id) if row["enc_storage_state_json"] else {}
        decrypted_headers = self.crypto.decrypt_json(row["enc_api_headers_json"], associated_data=account_id) if row["enc_api_headers_json"] else {}
        decrypted_proxy = self.crypto.decrypt_json(row["enc_proxy_config_json"], associated_data=account_id) if row["enc_proxy_config_json"] else {}

        # Log decryption audit entry
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO vault_audit_log (timestamp, account_id, platform, event_type, tool_id, run_id, notes)
                VALUES (?, ?, ?, 'decrypted_for_run', ?, ?, ?)
                """,
                (
                    now, account_id, row["platform"], tool_id, run_id,
                    f"Decrypted auth payloads for tool '{tool_id}' run '{run_id}'",
                ),
            )
            # Update last_used_at and usage counts
            conn.execute(
                """
                UPDATE vault_accounts
                SET last_used_at = ?, requests_today = requests_today + 1, total_requests = total_requests + 1
                WHERE account_id = ?
                """,
                (now, account_id),
            )

        masked_info = self.get_account_masked(account_id) or {}
        return {
            **masked_info,
            "credentials": {
                "username": decrypted_user,
                "password": decrypted_pass,
                "totp_secret": decrypted_totp,
                "cookie_jar": decrypted_cookies,
                "session_tokens": decrypted_tokens,
                "storage_state": decrypted_storage,
                "api_headers": decrypted_headers,
                "proxy_config": decrypted_proxy,
            },
        }

    def list_accounts_masked(
        self,
        platform: str = "",
        status: str = "",
        target_handle: str = "",
        auth_method: str = "",
        limit: int = 200,
        offset: int = 0,
    ) -> dict[str, Any]:
        """
        Paginated listing of accounts with optional filters (platform, status, target_handle, auth_method).
        """
        query = "SELECT DISTINCT va.* FROM vault_accounts va"
        params: list[Any] = []
        where_clauses: list[str] = []

        if target_handle:
            query += " JOIN account_target_access ata ON va.account_id = ata.account_id"
            where_clauses.append("ata.target_handle = ?")
            params.append(str(target_handle).strip().lower())

        if platform:
            where_clauses.append("va.platform = ?")
            params.append(platform.strip().lower())

        if status:
            where_clauses.append("va.status = ?")
            params.append(status.strip().lower())

        if auth_method:
            where_clauses.append("va.auth_methods_json LIKE ?")
            params.append(f"%{auth_method.strip()}%")

        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)

        query += " ORDER BY va.created_at DESC"

        # Count query
        count_sql = f"SELECT COUNT(*) FROM ({query})"
        with self._get_connection() as conn:
            total_count = conn.execute(count_sql, params).fetchone()[0]

            query += " LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            rows = conn.execute(query, params).fetchall()

        accounts = []
        for r in rows:
            acc = self.get_account_masked(r["account_id"])
            if acc:
                accounts.append(acc)

        return {
            "total": total_count,
            "limit": limit,
            "offset": offset,
            "accounts": accounts,
        }

    # ─────────────────────────────────────────────────────────────
    # Follower & Target Access Relationship Mapping
    # ─────────────────────────────────────────────────────────────

    def link_target_access(
        self,
        account_id: str,
        target_handles: list[str],
        access_role: str = "follower",
    ) -> int:
        """
        Map target accounts/groups/channels that this vault account can view or scrape.
        """
        existing = self._get_raw_row(account_id)
        if not existing:
            raise ValueError(f"Account {account_id} not found")

        platform = existing["platform"]
        now = _iso_now()
        linked = 0

        with self._get_connection() as conn:
            for handle in target_handles:
                h_norm = str(handle).strip().lower()
                if not h_norm:
                    continue
                # Check duplicate link
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
                    linked += 1

            if linked > 0:
                conn.execute(
                    """
                    INSERT INTO vault_audit_log (timestamp, account_id, platform, event_type, notes)
                    VALUES (?, ?, ?, 'target_linked', ?)
                    """,
                    (now, account_id, platform, f"Linked {linked} targets as '{access_role}'"),
                )

        self.export_public_stats()
        return linked

    def unlink_target_access(self, account_id: str, target_handles: list[str]) -> int:
        """Remove target relationships for an account."""
        existing = self._get_raw_row(account_id)
        if not existing:
            return 0

        removed = 0
        now = _iso_now()
        with self._get_connection() as conn:
            for handle in target_handles:
                h_norm = str(handle).strip().lower()
                cur = conn.execute(
                    "DELETE FROM account_target_access WHERE account_id = ? AND target_handle = ?",
                    (account_id, h_norm),
                )
                removed += cur.rowcount

            if removed > 0:
                conn.execute(
                    """
                    INSERT INTO vault_audit_log (timestamp, account_id, platform, event_type, notes)
                    VALUES (?, ?, ?, 'target_unlinked', ?)
                    """,
                    (now, account_id, existing["platform"], f"Unlinked {removed} targets"),
                )

        self.export_public_stats()
        return removed

    def get_target_access_for_account(self, account_id: str) -> list[dict[str, str]]:
        """List all targets and roles mapped to a given account."""
        with self._get_connection() as conn:
            rows = conn.execute(
                """
                SELECT target_handle, access_role, verified_at
                FROM account_target_access
                WHERE account_id = ?
                ORDER BY target_handle ASC
                """,
                (account_id,),
            ).fetchall()
            return [
                {
                    "target_handle": r["target_handle"],
                    "access_role": r["access_role"],
                    "verified_at": r["verified_at"],
                }
                for r in rows
            ]

    # ─────────────────────────────────────────────────────────────
    # Public Non-Sensitive Stats Snapshot (Git-Tracked)
    # ─────────────────────────────────────────────────────────────

    def export_public_stats(self) -> dict[str, Any]:
        """
        Aggregate zero-secret metrics and write to vault_store/vault_stats_public.json.
        """
        with self._get_connection() as conn:
            # Total accounts
            total_accounts = conn.execute("SELECT COUNT(*) FROM vault_accounts").fetchone()[0]

            # By platform
            plat_rows = conn.execute(
                "SELECT platform, COUNT(*) as cnt FROM vault_accounts GROUP BY platform"
            ).fetchall()
            by_platform = {r["platform"]: r["cnt"] for r in plat_rows}

            # By status
            status_rows = conn.execute(
                "SELECT status, COUNT(*) as cnt FROM vault_accounts GROUP BY status"
            ).fetchall()
            by_status = {r["status"]: r["cnt"] for r in status_rows}

            # Auth methods breakdown
            method_counts: dict[str, int] = {}
            meth_rows = conn.execute("SELECT auth_methods_json FROM vault_accounts").fetchall()
            for r in meth_rows:
                try:
                    for m in json.loads(r[0]):
                        method_counts[m] = method_counts.get(m, 0) + 1
                except Exception:
                    pass

            # Target counts
            total_target_links = conn.execute("SELECT COUNT(*) FROM account_target_access").fetchone()[0]
            distinct_targets = conn.execute(
                "SELECT COUNT(DISTINCT target_handle) FROM account_target_access"
            ).fetchone()[0]

            # Total audit events
            total_audit_events = conn.execute("SELECT COUNT(*) FROM vault_audit_log").fetchone()[0]

        stats = {
            "total_accounts": total_accounts,
            "by_platform": by_platform,
            "by_status": by_status,
            "by_auth_method": method_counts,
            "total_target_links": total_target_links,
            "total_distinct_targets": distinct_targets,
            "total_audit_events": total_audit_events,
            "last_updated_at": _iso_now(),
        }

        VAULT_STATS_PATH.parent.mkdir(parents=True, exist_ok=True)
        VAULT_STATS_PATH.write_text(json.dumps(stats, indent=2), encoding="utf-8")
        return stats

    def get_audit_trail(self, account_id: str = "", limit: int = 50) -> list[dict[str, Any]]:
        """Retrieve recent zero-secret audit events."""
        with self._get_connection() as conn:
            if account_id:
                rows = conn.execute(
                    """
                    SELECT * FROM vault_audit_log
                    WHERE account_id = ?
                    ORDER BY audit_id DESC LIMIT ?
                    """,
                    (account_id, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT * FROM vault_audit_log
                    ORDER BY audit_id DESC LIMIT ?
                    """,
                    (limit,),
                ).fetchall()

            return [
                {
                    "audit_id": r["audit_id"],
                    "timestamp": r["timestamp"],
                    "account_id": r["account_id"],
                    "platform": r["platform"],
                    "event_type": r["event_type"],
                    "tool_id": r["tool_id"],
                    "run_id": r["run_id"],
                    "notes": r["notes"],
                }
                for r in rows
            ]


# Singleton vault instance
_DEFAULT_VAULT: CredentialVault | None = None


def get_credential_vault() -> CredentialVault:
    """Return the singleton CredentialVault instance."""
    global _DEFAULT_VAULT
    if _DEFAULT_VAULT is None:
        _DEFAULT_VAULT = CredentialVault()
    return _DEFAULT_VAULT
