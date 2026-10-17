"""
core/totp_helper.py
===================
RFC 6238 Time-Based One-Time Password (TOTP) Helper for 2FA Scraper Authentication.

Key Capabilities:
  1. Base32 Secret Normalization (cleaning spaces, hyphens, lowercase, padding).
  2. Live 6-Digit TOTP Code Generation with period countdown (time_remaining_sec).
  3. Time-Window TOTP Code Verification (with configurable ±1 step tolerance).
  4. Vault-Integrated Retrieval (get_totp_for_account) that decrypts only the
     seed in memory and returns only the ephemeral 6-digit code (never leaks the seed).
"""
from __future__ import annotations

import base64
import re
import time
from typing import Any

import pyotp

from core.credential_vault import CredentialVault, get_credential_vault


class TOTPHelper:
    """Helper utility for RFC 6238 TOTP operations."""

    @staticmethod
    def normalize_base32_secret(secret: str) -> str:
        """
        Normalize a base32 TOTP secret string.
        Strips whitespace, hyphens, and converts to uppercase.
        Pads with '=' if length is not a multiple of 8.
        """
        if not secret:
            raise ValueError("TOTP secret cannot be empty")

        cleaned = re.sub(r"[\s\-]", "", str(secret)).upper()
        # Verify characters are valid RFC 4648 Base32
        if not re.match(r"^[A-Z2-7=]+$", cleaned):
            raise ValueError(f"Invalid Base32 characters in TOTP secret: {cleaned}")

        # Remove existing trailing padding to calculate cleanly
        unpadded = cleaned.rstrip("=")
        # Base32 strings must be a multiple of 8 chars in length
        remainder = len(unpadded) % 8
        if remainder != 0:
            unpadded += "=" * (8 - remainder)

        return unpadded

    @classmethod
    def generate_totp_code(
        cls,
        secret: str,
        timestamp: float | None = None,
        period_sec: int = 30,
        digits: int = 6,
    ) -> dict[str, Any]:
        """
        Generate current RFC 6238 TOTP 6-digit code.
        
        Returns:
            {
                "code": "123456",
                "time_remaining_sec": int (1-30),
                "period_sec": 30,
                "valid": True
            }
        """
        norm_secret = cls.normalize_base32_secret(secret)
        ts = time.time() if timestamp is None else float(timestamp)
        totp = pyotp.TOTP(norm_secret, digits=digits, interval=period_sec)
        code = totp.at(ts)
        time_remaining = int(period_sec - (ts % period_sec))

        return {
            "code": code,
            "time_remaining_sec": time_remaining,
            "period_sec": period_sec,
            "valid": True,
        }

    @classmethod
    def verify_totp_code(
        cls,
        secret: str,
        code: str,
        valid_window: int = 1,
        period_sec: int = 30,
        digits: int = 6,
    ) -> bool:
        """
        Verify a TOTP code against a secret within valid_window (±1 period).
        """
        try:
            norm_secret = cls.normalize_base32_secret(secret)
            clean_code = str(code).strip()
            totp = pyotp.TOTP(norm_secret, digits=digits, interval=period_sec)
            return bool(totp.verify(clean_code, valid_window=valid_window))
        except Exception:
            return False

    @classmethod
    def get_totp_for_account(
        cls,
        vault: CredentialVault | None = None,
        account_id: str = "",
        tool_id: str = "",
        run_id: str = "",
    ) -> dict[str, Any]:
        """
        Decrypt ONLY the TOTP secret for an account and return the live 6-digit code.
        The raw secret string is NEVER returned, protecting against credential leakage.
        """
        v = vault or get_credential_vault()
        raw_row = v._get_raw_row(account_id)
        if not raw_row:
            raise ValueError(f"Account {account_id} not found in vault")

        enc_totp = raw_row["enc_totp_secret"]
        if not enc_totp:
            raise ValueError(f"Account {account_id} does not have TOTP 2FA secret configured")

        # Decrypt secret with associated_data=account_id
        decrypted_secret = v.crypto.decrypt_str(enc_totp, associated_data=account_id)
        totp_info = cls.generate_totp_code(decrypted_secret)

        # Log audit trail (zero secrets logged)
        with v._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO vault_audit_log (timestamp, account_id, platform, event_type, tool_id, run_id, notes)
                VALUES (datetime('now'), ?, ?, 'totp_generated', ?, ?, ?)
                """,
                (
                    account_id,
                    raw_row["platform"],
                    tool_id,
                    run_id,
                    f"Generated live 6-digit TOTP code for tool '{tool_id}' run '{run_id}'",
                ),
            )

        return {
            "account_id": account_id,
            "platform": raw_row["platform"],
            "code": totp_info["code"],
            "time_remaining_sec": totp_info["time_remaining_sec"],
            "period_sec": totp_info["period_sec"],
            "valid": True,
        }


# Convenience module-level aliases
normalize_base32_secret = TOTPHelper.normalize_base32_secret
generate_totp_code = TOTPHelper.generate_totp_code
verify_totp_code = TOTPHelper.verify_totp_code
get_totp_for_account = TOTPHelper.get_totp_for_account
