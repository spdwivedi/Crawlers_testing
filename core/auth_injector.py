"""
core/auth_injector.py
=====================
Universal 20-Tool Authentication Injector & Ephemeral Cookie Shredder — Rule 6.

Translates encrypted CredentialVault accounts and smart AccountRouter leases
into tailor-made auth bundles for all 20 scraping tools (Batch 1-4).
Manages temporary Netscape cookies.txt generation and secure zero-fill file shredding.
"""
from __future__ import annotations

import contextlib
import logging
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

from core.account_router import AccountRouter, get_account_router
from core.credential_vault import (
    DEFAULT_DOMAINS,
    CredentialVault,
    get_credential_vault,
)
from core.crypto_engine import CryptoEngine, get_crypto_engine
from core.totp_helper import TOTPHelper
from core.vault_importer import VaultImporter

logger = logging.getLogger("auth_injector")

TEMP_COOKIE_DIR = Path(__file__).resolve().parent.parent / "vault_store" / "temp_cookies"


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize_playwright_cookie(
    cookie: dict[str, Any],
    default_domain: str = "",
) -> dict[str, Any]:
    """Normalize a cookie dict into Playwright's strict schema."""
    name = str(cookie.get("name", "")).strip()
    val = str(cookie.get("value", ""))
    norm: dict[str, Any] = {"name": name, "value": val}

    domain = cookie.get("domain") or default_domain
    if domain:
        norm["domain"] = str(domain)

    norm["path"] = str(cookie.get("path", "/"))

    if "secure" in cookie:
        norm["secure"] = bool(cookie["secure"])
    if "httpOnly" in cookie:
        norm["httpOnly"] = bool(cookie["httpOnly"])

    expires = cookie.get("expires") or cookie.get("expiry") or cookie.get("expirationDate")
    if expires is not None:
        try:
            val_f = float(expires)
            if val_f > 0:
                norm["expires"] = val_f
        except (ValueError, TypeError):
            pass

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


def format_netscape_cookies_txt(cookies: list[dict[str, Any]]) -> str:
    """
    Format a list of cookie dictionaries into a standards-compliant Netscape HTTP Cookie file.

    Columns:
      1. domain (e.g. .instagram.com)
      2. include_subdomains (TRUE/FALSE)
      3. path (e.g. /)
      4. secure (TRUE/FALSE)
      5. expiration (unix timestamp integer)
      6. name
      7. value
    Lines for httpOnly cookies begin with '#HttpOnly_'.
    """
    lines = [
        "# Netscape HTTP Cookie File",
        "# http://curl.haxx.se/rfc/cookie_spec.html",
        "# This is a generated file! Do not edit.",
        "",
    ]
    for c in cookies:
        if not isinstance(c, dict):
            continue
        name = str(c.get("name", "")).strip()
        val = str(c.get("value", ""))
        if not name:
            continue

        domain = str(c.get("domain", "")).strip() or "localhost"
        include_sub = "TRUE" if (domain.startswith(".") or c.get("include_subdomains", False) or c.get("domain_specified", False)) else "FALSE"
        path = str(c.get("path", "/")).strip() or "/"
        secure = "TRUE" if c.get("secure", False) else "FALSE"

        expires_raw = c.get("expires") or c.get("expiry") or c.get("expirationDate") or 0
        try:
            expires_val = int(float(expires_raw))
        except (ValueError, TypeError):
            expires_val = int(time.time() + 86400 * 30)

        if expires_val <= 0:
            expires_val = int(time.time() + 86400 * 30)

        is_http_only = bool(c.get("httpOnly", False))
        prefix = "#HttpOnly_" if is_http_only else ""

        line = f"{prefix}{domain}\t{include_sub}\t{path}\t{secure}\t{expires_val}\t{name}\t{val}"
        lines.append(line)

    lines.append("")  # Trailing newline
    return "\n".join(lines)


class AuthInjector:
    """
    Universal 20-tool authentication injector, translator, and ephemeral artifact manager.
    """

    def __init__(
        self,
        vault: CredentialVault | None = None,
        router: AccountRouter | None = None,
        importer: VaultImporter | None = None,
        crypto: CryptoEngine | None = None,
        temp_cookie_dir: Path | None = None,
    ) -> None:
        self.vault = vault or get_credential_vault()
        self.router = router or get_account_router(vault=self.vault)
        self.importer = importer or VaultImporter(vault=self.vault)
        self.crypto = crypto or get_crypto_engine()
        self.temp_cookie_dir = temp_cookie_dir or TEMP_COOKIE_DIR
        self.temp_cookie_dir.mkdir(parents=True, exist_ok=True)

    format_netscape_cookies_txt = staticmethod(format_netscape_cookies_txt)

    def prepare_tool_auth(
        self,
        tool_id: str,
        platform: str = "",
        account_id: str = "",
        required_target: str = "",
        strategy: str = "least_recently_used",
        run_id: str = "",
        write_ephemeral_cookie_file: bool = True,
    ) -> dict[str, Any]:
        """
        Resolve an account and construct universal auth bundles for the specified tool.

        Args:
            tool_id: Target tool identifier (e.g. '01_curl_cffi', '06_playwright', '11_yt_dlp_ffmpeg')
            platform: Platform name ('instagram', 'facebook', 'leetcode', etc.)
            account_id: Explicit account ID (bypasses router matching if provided)
            required_target: Private target handle/group to match via follower graph
            strategy: Routing strategy ('least_recently_used', 'lowest_quota_usage', 'health_weighted_random')
            run_id: Scraper action run identifier for audit logs
            write_ephemeral_cookie_file: If True, writes a Netscape cookies.txt file for CLI tools

        Returns:
            Dictionary containing native configuration bundles for all 20 scraper tools,
            ephemeral file paths for cleanup, and a safe zero-plaintext audit summary.
        """
        # 1. Account Resolution
        account: dict[str, Any] | None = None

        if account_id:
            account = self.vault.get_account_decrypted(account_id, tool_id=tool_id, run_id=run_id)
            if not account:
                return {
                    "authenticated": False,
                    "reason": "account_not_found",
                    "tool_id": tool_id,
                    "platform": platform,
                    "account_id": account_id,
                    "required_target": required_target,
                }
            # Attach live TOTP code if secret exists
            totp_secret = account.get("credentials", {}).get("totp_secret")
            if totp_secret:
                try:
                    account["live_totp"] = TOTPHelper.get_totp_for_account(
                        vault=self.vault,
                        account_id=account_id,
                        tool_id=tool_id,
                        run_id=run_id,
                    )
                except Exception:
                    account["live_totp"] = None
        else:
            account = self.router.acquire_account(
                platform=platform,
                required_target=required_target,
                strategy=strategy,
                decrypt_secrets=True,
                include_live_totp=True,
                tool_id=tool_id,
                run_id=run_id,
            )
            if not account:
                return {
                    "authenticated": False,
                    "reason": "no_matching_active_account",
                    "tool_id": tool_id,
                    "platform": platform,
                    "required_target": required_target,
                }

        # 2. Extract Decrypted Credentials & Artifacts
        resolved_acc_id = account["account_id"]
        platform_res = account["platform"]
        default_domain = DEFAULT_DOMAINS.get(platform_res.lower(), f"{platform_res.lower()}.com")
        creds = account.get("credentials", {})

        cookie_jar: list[dict[str, Any]] = creds.get("cookie_jar") or []
        session_tokens: dict[str, str] = creds.get("session_tokens") or {}
        storage_state: dict[str, Any] = creds.get("storage_state") or {}
        api_headers: dict[str, str] = creds.get("api_headers") or {}
        proxy_config: dict[str, Any] = creds.get("proxy_config") or {}
        fingerprint: dict[str, Any] = account.get("fingerprint_profile") or {}
        live_totp: dict[str, Any] | None = account.get("live_totp")

        username = creds.get("username", "")
        password = creds.get("password", "")

        # 3. Build Key-Value Cookies Dict & Header String
        cookies_dict: dict[str, str] = {}
        for c in cookie_jar:
            if isinstance(c, dict) and c.get("name"):
                cookies_dict[str(c["name"])] = str(c.get("value", ""))

        for k, v in session_tokens.items():
            if k not in cookies_dict:
                cookies_dict[k] = str(v)

        cookie_header_str = "; ".join(f"{k}={v}" for k, v in cookies_dict.items())

        # 4. Build Browser Environment & HTTP Headers
        user_agent = (
            fingerprint.get("userAgent")
            or fingerprint.get("user_agent")
            or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
        accept_lang = fingerprint.get("language") or "en-US,en;q=0.9"

        headers: dict[str, str] = {
            "User-Agent": user_agent,
            "Accept-Language": accept_lang,
        }
        if cookie_header_str:
            headers["Cookie"] = cookie_header_str

        # Auto-inject CSRF and Authorization tokens if present
        if "csrftoken" in cookies_dict:
            headers["X-CSRFToken"] = cookies_dict["csrftoken"]
        elif "csrftoken" in session_tokens:
            headers["X-CSRFToken"] = session_tokens["csrftoken"]

        if "auth_token" in session_tokens:
            tok = session_tokens["auth_token"]
            if not tok.startswith("Bearer "):
                headers["Authorization"] = f"Bearer {tok}"
            else:
                headers["Authorization"] = tok

        if api_headers:
            headers.update(api_headers)

        # 5. Build Proxy URL Mapping
        proxy_url = proxy_config.get("url") or proxy_config.get("server") or ""
        if not proxy_url and proxy_config.get("host") and proxy_config.get("port"):
            proto = proxy_config.get("protocol", "http")
            u = proxy_config.get("username")
            p = proxy_config.get("password")
            if u and p:
                proxy_url = f"{proto}://{u}:{p}@{proxy_config['host']}:{proxy_config['port']}"
            else:
                proxy_url = f"{proto}://{proxy_config['host']}:{proxy_config['port']}"

        proxies = {"http": proxy_url, "https": proxy_url} if proxy_url else {}

        # 6. Bundle 1: HTTP Client Bundle (curl_cffi, selectolax, httpx, trafilatura, scrapling)
        http_bundle = {
            "cookies_dict": cookies_dict,
            "headers": headers,
            "proxies": proxies,
            "impersonate": "chrome124",
        }

        # 7. Bundle 2: Scrapy Bundle
        # Scrapy's CookiesMiddleware manages cookies via request.cookies; remove raw Cookie header
        scrapy_headers = {k: v for k, v in headers.items() if k.lower() != "cookie"}
        scrapy_bundle = {
            "cookies": cookies_dict,
            "headers": scrapy_headers,
            "meta": {"proxy": proxy_url} if proxy_url else {},
        }

        # 8. Bundle 3: Playwright / Patchright / Camoufox / Crawl4AI Bundle
        norm_pw_cookies = [
            _normalize_playwright_cookie(c, default_domain=default_domain)
            for c in cookie_jar
            if isinstance(c, dict) and c.get("name")
        ]
        origins_list = storage_state.get("origins", []) if isinstance(storage_state, dict) else []
        width = int(fingerprint.get("innerWidth") or 1920)
        height = int(fingerprint.get("innerHeight") or 1080)
        viewport = {"width": width, "height": height}

        pw_context_kwargs: dict[str, Any] = {
            "storage_state": {
                "cookies": norm_pw_cookies,
                "origins": origins_list,
            },
            "user_agent": user_agent,
            "viewport": viewport,
            "locale": fingerprint.get("language") or "en-US",
            "timezone_id": fingerprint.get("timeZone") or "UTC",
            "extra_http_headers": {k: v for k, v in headers.items() if k.lower() not in ("user-agent", "cookie")},
        }
        if proxy_config:
            pw_context_kwargs["proxy"] = proxy_config

        playwright_bundle = {
            "context_kwargs": pw_context_kwargs,
        }

        # 9. Bundle 4: CDP / Nodriver Bundle
        cdp_cookies = [
            {
                "name": str(c["name"]),
                "value": str(c.get("value", "")),
                "domain": str(c.get("domain", default_domain)),
                "path": str(c.get("path", "/")),
                "secure": bool(c.get("secure", False)),
                "httpOnly": bool(c.get("httpOnly", False)),
            }
            for c in cookie_jar
            if isinstance(c, dict) and c.get("name")
        ]
        cdp_bundle = {
            "cdp_cookies": cdp_cookies,
            "browser_args": [
                f"--user-agent={user_agent}",
                f"--window-size={width},{height}",
            ],
        }

        # 10. Bundle 5: CLI / Media Bundle (yt-dlp, instaloader, gallery-dl, singlefile, mitmproxy)
        ephemeral_files: list[str] = []
        cookiefile_path = ""
        if write_ephemeral_cookie_file and cookie_jar:
            short_token = run_id or uuid.uuid4().hex[:8]
            cookie_file = self.temp_cookie_dir / f"ephemeral_{tool_id}_{short_token}.cookies.txt"
            netscape_str = format_netscape_cookies_txt(cookie_jar)
            cookie_file.write_text(netscape_str, encoding="utf-8")
            cookiefile_path = str(cookie_file)
            ephemeral_files.append(cookiefile_path)

        cli_media_bundle = {
            "cookiefile_path": cookiefile_path,
            "yt_dlp_opts": {
                "cookiefile": cookiefile_path,
                "http_headers": {"User-Agent": user_agent},
            } if cookiefile_path else {"http_headers": {"User-Agent": user_agent}},
            "instaloader_cookies": cookies_dict,
            "gallery_dl_args": ["--cookies", cookiefile_path, "--user-agent", user_agent] if cookiefile_path else ["--user-agent", user_agent],
        }

        # 11. Bundle 6: 2FA TOTP & Raw Credentials
        totp_bundle = {
            "live_totp": live_totp,
        }

        credentials_raw = {
            "username": username,
            "password": password,
        }

        # 12. Safe Masked Summary (Rule 6 compliant — zero secrets logged)
        safe_summary = {
            "authenticated": True,
            "account_id": resolved_acc_id,
            "platform": platform_res,
            "username_masked": account.get("username_masked") or account.get("account_label", ""),
            "tool_id": tool_id,
            "target_matched": required_target,
            "cookies_count": len(cookies_dict),
            "origins_count": len(origins_list),
            "token_keys": sorted(list(session_tokens.keys())),
            "has_totp": bool(live_totp),
            "ephemeral_cookie_created": bool(cookiefile_path),
        }

        return {
            "authenticated": True,
            "account_id": resolved_acc_id,
            "platform": platform_res,
            "tool_id": tool_id,
            "http_bundle": http_bundle,
            "scrapy_bundle": scrapy_bundle,
            "playwright_bundle": playwright_bundle,
            "cdp_bundle": cdp_bundle,
            "cli_media_bundle": cli_media_bundle,
            "totp_bundle": totp_bundle,
            "credentials_raw": credentials_raw,
            "ephemeral_files": ephemeral_files,
            "safe_summary": safe_summary,
        }

    def shred_ephemeral_artifacts(self, auth_bundle: dict[str, Any]) -> int:
        """
        Securely shred and delete all temporary files created for this authenticated session.
        Overwrites file contents with null bytes before unlinking.

        Args:
            auth_bundle: Dictionary returned by prepare_tool_auth()

        Returns:
            Number of files successfully shredded.
        """
        shredded_count = 0
        file_paths = auth_bundle.get("ephemeral_files", [])

        for path_str in list(file_paths):
            try:
                p = Path(path_str)
                if p.exists() and p.is_file():
                    size = p.stat().st_size
                    # Zero-fill overwrite
                    with open(p, "wb") as f:
                        f.write(b"\x00" * max(size, 4096))
                        f.flush()
                    p.unlink(missing_ok=True)
                    shredded_count += 1
            except Exception as e:
                logger.warning("Failed to shred ephemeral artifact %s: %s", path_str, e)

        auth_bundle["ephemeral_files"] = []
        return shredded_count

    @contextlib.contextmanager
    def authenticated_session(
        self,
        tool_id: str,
        platform: str = "",
        account_id: str = "",
        required_target: str = "",
        strategy: str = "least_recently_used",
        run_id: str = "",
    ) -> Iterator[dict[str, Any]]:
        """
        Context manager that leases an account, generates tool auth bundles, and guarantees
        ephemeral file shredding upon scope exit (even if exceptions occur).

        Usage:
            with injector.authenticated_session(tool_id="11_yt_dlp_ffmpeg", platform="instagram") as auth:
                if auth["authenticated"]:
                    cmd = ["yt-dlp", "--cookies", auth["cli_media_bundle"]["cookiefile_path"], ...]
        """
        bundle = self.prepare_tool_auth(
            tool_id=tool_id,
            platform=platform,
            account_id=account_id,
            required_target=required_target,
            strategy=strategy,
            run_id=run_id,
            write_ephemeral_cookie_file=True,
        )
        try:
            yield bundle
        finally:
            self.shred_ephemeral_artifacts(bundle)


# Convenience module-level singleton
_INJECTOR: AuthInjector | None = None


def get_auth_injector(
    vault: CredentialVault | None = None,
    router: AccountRouter | None = None,
) -> AuthInjector:
    global _INJECTOR
    if _INJECTOR is None or vault is not None or router is not None:
        _INJECTOR = AuthInjector(vault=vault, router=router)
    return _INJECTOR
