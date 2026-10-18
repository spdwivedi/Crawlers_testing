"""
core/browser_session_recorder.py
================================
Interactive & Programmatic Browser Session Recorder — Rule 6.

Launches Playwright or Patchright Chromium in visible or headless mode,
captures full session state (cookies, localStorage, session tokens, fingerprint),
and encrypts all artifacts into CredentialVault with row-bound AES-256-GCM.
"""
from __future__ import annotations

import json
import logging
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from core.credential_vault import (
    DEFAULT_DOMAINS,
    CredentialVault,
    get_credential_vault,
)
from core.crypto_engine import CryptoEngine, get_crypto_engine

logger = logging.getLogger("browser_session_recorder")

HIGH_VALUE_AUTH_COOKIE_NAMES = {
    "sessionid",
    "csrftoken",
    "ds_user_id",
    "c_user",
    "xs",
    "leetcode_session",
    "auth_token",
    "cf_clearance",
    "li_at",
    "reddit_session",
}


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize_playwright_cookie(
    cookie: dict[str, Any],
    default_domain: str = "",
    default_url: str = "",
) -> dict[str, Any]:
    """Normalize a cookie dict into Playwright's strict schema."""
    name = str(cookie.get("name", "")).strip()
    val = str(cookie.get("value", ""))
    norm: dict[str, Any] = {"name": name, "value": val}

    domain = cookie.get("domain") or default_domain
    if domain:
        norm["domain"] = str(domain)
    elif default_url:
        norm["url"] = default_url

    norm["path"] = str(cookie.get("path", "/"))

    if "secure" in cookie:
        norm["secure"] = bool(cookie["secure"])
    if "httpOnly" in cookie:
        norm["httpOnly"] = bool(cookie["httpOnly"])

    # Expiry normalization (float epoch seconds)
    expires = cookie.get("expires") or cookie.get("expiry") or cookie.get("expirationDate")
    if expires is not None:
        try:
            val_f = float(expires)
            if val_f > 0:
                norm["expires"] = val_f
        except (ValueError, TypeError):
            pass

    # SameSite normalization
    same_site = cookie.get("sameSite")
    if same_site:
        s_lower = str(same_site).lower()
        if "strict" in s_lower:
            norm["sameSite"] = "Strict"
        elif "lax" in s_lower:
            norm["sameSite"] = "Lax"
        elif "none" in s_lower or "no_restriction" in s_lower:
            norm["sameSite"] = "None"

    return norm


class BrowserSessionRecorder:
    """
    Records interactive or headless browser sessions and encrypts state into CredentialVault.
    """

    def __init__(
        self,
        vault: CredentialVault | None = None,
        crypto: CryptoEngine | None = None,
    ) -> None:
        self.vault = vault or get_credential_vault()
        self.crypto = crypto or get_crypto_engine()

    def record_browser_session(
        self,
        platform: str,
        login_url: str,
        account_label: str = "",
        account_id: str | None = None,
        interactive: bool = False,
        engine: str = "playwright",
        wait_seconds: int = 30,
        follows_targets: list[str] | None = None,
        seed_cookies: list[dict[str, Any]] | None = None,
        seed_local_storage: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """
        Launch browser, capture cookies, localStorage, session tokens, and environment fingerprint,
        and securely store everything in the encrypted credential vault.

        Args:
            platform: Platform name ('instagram', 'facebook', 'leetcode', etc.)
            login_url: Destination URL for login or authenticated session
            account_label: Human-friendly alias for this account/session
            account_id: Existing account ID to update, or None to generate a new one
            interactive: If True, opens visible browser window and waits for user login
            engine: 'playwright' or 'patchright' (falls back cleanly if unavailable)
            wait_seconds: Max seconds to wait for login/interaction before capture
            follows_targets: Target handles/accounts followed by this session
            seed_cookies: Initial cookies to seed into the browser context
            seed_local_storage: Initial localStorage key-value items to seed into origin

        Returns:
            Safe masked summary dictionary with zero plaintext secrets exposed.
        """
        platform_norm = platform.strip().lower()
        engine_clean = engine.strip().lower()

        # Engine selector with clean fallback
        if engine_clean == "patchright":
            try:
                from patchright.sync_api import sync_playwright as sync_engine
            except ImportError:
                from playwright.sync_api import sync_playwright as sync_engine
        else:
            from playwright.sync_api import sync_playwright as sync_engine

        parsed_url = urlparse(login_url)
        default_domain = parsed_url.hostname or DEFAULT_DOMAINS.get(platform_norm, f"{platform_norm}.com")

        with sync_engine() as p:
            browser = p.chromium.launch(headless=not interactive)
            context = browser.new_context()

            # Seed cookies if provided
            if seed_cookies:
                normalized_seed = [
                    _normalize_playwright_cookie(c, default_domain=default_domain, default_url=login_url)
                    for c in seed_cookies
                    if c.get("name")
                ]
                if normalized_seed:
                    context.add_cookies(normalized_seed)

            page = context.new_page()
            page.goto(login_url, wait_until="domcontentloaded")

            # Seed localStorage if provided
            if seed_local_storage:
                for k, v in seed_local_storage.items():
                    page.evaluate(
                        "(args) => window.localStorage.setItem(args.key, args.val)",
                        {"key": str(k), "val": str(v)},
                    )
                page.reload(wait_until="domcontentloaded")

            # Interactive wait loop
            if interactive:
                logger.info(
                    "Interactive session open. Please complete login in the visible browser window (waiting up to %ds)...",
                    wait_seconds,
                )
                start_wait = time.time()
                while time.time() - start_wait < wait_seconds:
                    if page.is_closed():
                        break
                    try:
                        current_cookies = context.cookies()
                        c_names = {str(c.get("name", "")).lower() for c in current_cookies}
                        if c_names.intersection(HIGH_VALUE_AUTH_COOKIE_NAMES):
                            # Session tokens appeared! Allow 1s for any background requests to settle
                            time.sleep(1.0)
                            break
                    except Exception:
                        break
                    time.sleep(1.0)
            else:
                # Settle for programmatic mode
                time.sleep(0.5)

            # Full Browser State Extraction
            storage_state = context.storage_state()
            cookies_captured = storage_state.get("cookies", [])
            origins_captured = storage_state.get("origins", [])

            # Extract environment fingerprint
            try:
                fingerprint_profile = page.evaluate(
                    """() => {
                        return {
                            userAgent: navigator.userAgent,
                            innerWidth: window.innerWidth,
                            innerHeight: window.innerHeight,
                            language: navigator.language,
                            timeZone: Intl.DateTimeFormat().resolvedOptions().timeZone
                        };
                    }"""
                )
            except Exception:
                fingerprint_profile = {
                    "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                    "innerWidth": 1920,
                    "innerHeight": 1080,
                    "language": "en-US",
                    "timeZone": "UTC",
                }

            # Scan cookies for well-known session tokens
            session_tokens: dict[str, str] = {}
            for c in cookies_captured:
                c_name = str(c.get("name", "")).strip()
                if c_name.lower() in HIGH_VALUE_AUTH_COOKIE_NAMES:
                    session_tokens[c_name] = str(c.get("value", ""))

            browser.close()

        # Encrypted Vault Persistence
        resolved_account_id = account_id
        is_update = False
        if resolved_account_id:
            existing = self.vault._get_raw_row(resolved_account_id)
            if existing:
                is_update = True

        if is_update and resolved_account_id:
            self.vault.update_account(
                account_id=resolved_account_id,
                cookie_jar=cookies_captured,
                storage_state=storage_state,
                session_tokens=session_tokens,
                fingerprint_profile=fingerprint_profile,
                account_label=account_label or None,
                status="active",
            )
            if follows_targets:
                self.vault.link_target_access(resolved_account_id, follows_targets)
        else:
            default_label = account_label or f"{platform.title()} Browser Session"
            derived_user = session_tokens.get("c_user") or session_tokens.get("ds_user_id") or account_label or f"{platform_norm}_session"
            added = self.vault.add_account(
                platform=platform_norm,
                domain=default_domain,
                username=derived_user,
                account_label=default_label,
                cookie_jar=cookies_captured,
                storage_state=storage_state,
                session_tokens=session_tokens,
                fingerprint_profile=fingerprint_profile,
                follows_targets=follows_targets or [],
                status="active",
                health_score=100,
                daily_quota_limit=50,
                account_id=resolved_account_id,
            )
            resolved_account_id = added["account_id"]

        # Audit Log Entry
        with self.vault._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO vault_audit_log (timestamp, account_id, platform, event_type, tool_id, run_id, notes)
                VALUES (?, ?, ?, 'browser_session_recorded', 'browser_session_recorder', '', ?)
                """,
                (
                    _iso_now(),
                    resolved_account_id,
                    platform_norm,
                    f"Recorded browser session: {len(cookies_captured)} cookies, {len(origins_captured)} origins, tokens: {list(session_tokens.keys())}",
                ),
            )

        self.vault.export_public_stats()

        return {
            "account_id": resolved_account_id,
            "platform": platform_norm,
            "domain": default_domain,
            "account_label": account_label or f"{platform_norm.title()} Session",
            "cookies_captured_count": len(cookies_captured),
            "origins_captured_count": len(origins_captured),
            "extracted_token_keys": sorted(list(session_tokens.keys())),
            "fingerprint_profile": fingerprint_profile,
            "follows_targets": follows_targets or [],
            "status": "active",
        }


# Convenience module-level singleton
_RECORDER: BrowserSessionRecorder | None = None


def get_browser_session_recorder(
    vault: CredentialVault | None = None,
    crypto: CryptoEngine | None = None,
) -> BrowserSessionRecorder:
    global _RECORDER
    if _RECORDER is None or vault is not None or crypto is not None:
        _RECORDER = BrowserSessionRecorder(vault=vault, crypto=crypto)
    return _RECORDER
