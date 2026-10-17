"""
core/crypto_engine.py
=====================
Zero-Plaintext AES-256-GCM Cryptographic Engine & Vault Key Derivation — Rule 6.

Key Capabilities:
  1. Automatic .env Master Secret & Salt Provisioning (ensure_master_key).
  2. PBKDF2-HMAC-SHA256 Key Derivation (600,000 iterations) with memory caching.
  3. Authenticated AES-256-GCM Encryption & Tamper Detection (v1:aes256gcm: tokens).
  4. Encrypted JSON Serialization (for cookie jars, headers, browser storage_state).
  5. Secret Masking for Safe Telemetry & Logs (mask_secret).
  6. Blind Index HMAC-SHA256 Hashing for deduplication without plaintext exposure.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import re
from pathlib import Path
from typing import Any

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
ENV_FILE = ROOT / ".env"
ENV_EXAMPLE_FILE = ROOT / ".env.example"

TOKEN_PREFIX = "v1:aes256gcm:"
PBKDF2_ITERATIONS = 600_000


def ensure_master_key() -> tuple[str, str]:
    """
    Ensure VAULT_MASTER_KEY and VAULT_KDF_SALT exist in .env.
    If .env is missing or either key is not set, automatically generate
    cryptographically secure keys and write them to .env.
    Also ensures a safe .env.example template exists.
    
    Returns:
        (master_key_b64, salt_b64)
    """
    # Create .env.example if missing
    if not ENV_EXAMPLE_FILE.exists():
        example_content = (
            "# ─────────────────────────────────────────────────────────────\n"
            "# Crawlers_testing - Vault Environment Template (.env.example)\n"
            "# Copy this file to .env. REAL SECRETS MUST NEVER BE COMMITTED!\n"
            "# ─────────────────────────────────────────────────────────────\n"
            "VAULT_MASTER_KEY=placeholder_base64url_32bytes_secret_here\n"
            "VAULT_KDF_SALT=placeholder_base64url_16bytes_salt_here\n"
        )
        ENV_EXAMPLE_FILE.write_text(example_content, encoding="utf-8")

    load_dotenv(dotenv_path=ENV_FILE, override=False)
    master_key = os.getenv("VAULT_MASTER_KEY")
    salt = os.getenv("VAULT_KDF_SALT")

    needs_write = False
    existing_lines: list[str] = []
    if ENV_FILE.exists():
        existing_lines = ENV_FILE.read_text(encoding="utf-8").splitlines()

    # Parse existing file to retain any other variables
    env_dict: dict[str, str] = {}
    for line in existing_lines:
        line_s = line.strip()
        if line_s and not line_s.startswith("#") and "=" in line_s:
            k, v = line_s.split("=", 1)
            env_dict[k.strip()] = v.strip()

    if not master_key:
        master_key = env_dict.get("VAULT_MASTER_KEY")
    if not salt:
        salt = env_dict.get("VAULT_KDF_SALT")

    if not master_key:
        # 32 random bytes = 256 bits, base64url encoded
        master_key = base64.urlsafe_b64encode(os.urandom(32)).decode("ascii")
        env_dict["VAULT_MASTER_KEY"] = master_key
        needs_write = True

    if not salt:
        # 16 random bytes = 128 bits, base64url encoded
        salt = base64.urlsafe_b64encode(os.urandom(16)).decode("ascii")
        env_dict["VAULT_KDF_SALT"] = salt
        needs_write = True

    if needs_write or not ENV_FILE.exists():
        lines = [
            "# ─────────────────────────────────────────────────────────────",
            "# Crawlers_testing - Local Master Vault Secrets (.env)",
            "# NEVER COMMIT THIS FILE OR LOG ITS CONTENTS — Rule 6 Compliance",
            "# ─────────────────────────────────────────────────────────────",
        ]
        for k, v in env_dict.items():
            lines.append(f"{k}={v}")
        ENV_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
        # Ensure environment has the keys loaded
        os.environ["VAULT_MASTER_KEY"] = master_key
        os.environ["VAULT_KDF_SALT"] = salt

    return master_key, salt


class CryptoEngine:
    """
    AES-256-GCM Cryptographic Engine for Crawlers_testing.
    
    Uses PBKDF2-HMAC-SHA256 with 600,000 iterations to derive a 256-bit symmetric
    key from the master secret, and caches the derived key in memory for high-speed
    throughput on bulk datasets.
    """

    def __init__(
        self,
        master_key: str | None = None,
        salt: str | None = None,
    ) -> None:
        if not master_key or not salt:
            env_key, env_salt = ensure_master_key()
            master_key = master_key or env_key
            salt = salt or env_salt

        self._master_key_b64 = master_key
        self._salt_b64 = salt

        # Decode master key and salt bytes
        try:
            self._master_key_bytes = base64.urlsafe_b64decode(self._master_key_b64.encode("ascii"))
        except Exception:
            self._master_key_bytes = self._master_key_b64.encode("utf-8")

        try:
            self._salt_bytes = base64.urlsafe_b64decode(self._salt_b64.encode("ascii"))
        except Exception:
            self._salt_bytes = self._salt_b64.encode("utf-8")

        # Key derivation with memory caching
        self._derived_key = self._derive_key(self._master_key_bytes, self._salt_bytes)
        self._aesgcm = AESGCM(self._derived_key)

    @staticmethod
    def _derive_key(master_bytes: bytes, salt_bytes: bytes) -> bytes:
        """Derive 256-bit key via PBKDF2-HMAC-SHA256 (600,000 iterations)."""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt_bytes,
            iterations=PBKDF2_ITERATIONS,
        )
        return kdf.derive(master_bytes)

    def encrypt_str(self, plaintext: str, associated_data: str = "") -> str:
        """
        Encrypt plaintext string using AES-256-GCM with fresh 12-byte nonce.
        
        Args:
            plaintext: Raw secret string to encrypt.
            associated_data: Optional authenticated metadata bound to the ciphertext.
            
        Returns:
            Versioned token string: 'v1:aes256gcm:<base64url>'
        """
        if not isinstance(plaintext, str):
            raise TypeError("plaintext must be a str")

        nonce = os.urandom(12)
        ad_bytes = associated_data.encode("utf-8") if associated_data else None
        ciphertext_and_tag = self._aesgcm.encrypt(nonce, plaintext.encode("utf-8"), ad_bytes)
        combined = nonce + ciphertext_and_tag
        token_payload = base64.urlsafe_b64encode(combined).decode("ascii")
        return f"{TOKEN_PREFIX}{token_payload}"

    def decrypt_str(self, token: str, associated_data: str = "") -> str:
        """
        Decrypt and authenticate token using AES-256-GCM.
        
        Args:
            token: Versioned token string 'v1:aes256gcm:<base64url>'.
            associated_data: Optional authenticated metadata bound during encryption.
            
        Returns:
            Decrypted plaintext string.
            
        Raises:
            ValueError: If token format is invalid or tampering / tag mismatch occurs.
        """
        if not isinstance(token, str):
            raise TypeError("token must be a str")

        if not token.startswith(TOKEN_PREFIX):
            raise ValueError(f"Invalid token format or unsupported version (expected prefix '{TOKEN_PREFIX}')")

        payload_b64 = token[len(TOKEN_PREFIX):]
        try:
            combined = base64.urlsafe_b64decode(payload_b64.encode("ascii"))
        except Exception as e:
            raise ValueError("Vault integrity check failed: invalid base64 encoding") from e

        if len(combined) < 12 + 16:  # 12-byte nonce + 16-byte tag minimum
            raise ValueError("Vault integrity check failed: payload too short")

        nonce = combined[:12]
        ciphertext_and_tag = combined[12:]
        ad_bytes = associated_data.encode("utf-8") if associated_data else None

        try:
            decrypted_bytes = self._aesgcm.decrypt(nonce, ciphertext_and_tag, ad_bytes)
            return decrypted_bytes.decode("utf-8")
        except InvalidTag as e:
            raise ValueError("Vault integrity check failed or tampered ciphertext (GCM tag mismatch)") from e
        except Exception as e:
            raise ValueError("Vault integrity check failed or tampered ciphertext") from e

    def encrypt_json(self, data: Any, associated_data: str = "") -> str:
        """Serialize data to JSON and encrypt via AES-256-GCM."""
        serialized = json.dumps(data, separators=(",", ":"), ensure_ascii=False)
        return self.encrypt_str(serialized, associated_data=associated_data)

    def decrypt_json(self, token: str, associated_data: str = "") -> Any:
        """Decrypt AES-256-GCM token and parse as JSON."""
        decrypted_str = self.decrypt_str(token, associated_data=associated_data)
        try:
            return json.loads(decrypted_str)
        except Exception as e:
            raise ValueError("Vault integrity check failed: decrypted data is not valid JSON") from e

    def mask_secret(self, value: str, visible_prefix: int = 3, visible_suffix: int = 2) -> str:
        """
        Mask a sensitive string for safe logging and UI display.
        Example: 'session_987654321' -> 'ses**********21'
        """
        if not value:
            return ""
        if len(value) <= (visible_prefix + visible_suffix):
            return "*" * len(value) if len(value) > 2 else "****"
        masked_count = len(value) - visible_prefix - visible_suffix
        return f"{value[:visible_prefix]}{'*' * masked_count}{value[-visible_suffix:]}"

    def blind_index_hash(self, value: str) -> str:
        """
        Compute deterministic HMAC-SHA256 blind index hash for deduplication and lookup.
        Does not reveal the secret value while allowing exact matching in SQLite.
        """
        if not isinstance(value, str):
            value = str(value)
        return hmac.new(self._master_key_bytes, value.encode("utf-8"), hashlib.sha256).hexdigest()


# Singleton engine instance
_DEFAULT_ENGINE: CryptoEngine | None = None


def get_crypto_engine() -> CryptoEngine:
    """Return the singleton CryptoEngine initialized from .env."""
    global _DEFAULT_ENGINE
    if _DEFAULT_ENGINE is None:
        _DEFAULT_ENGINE = CryptoEngine()
    return _DEFAULT_ENGINE


# Convenience module-level wrappers
def encrypt_str(plaintext: str, associated_data: str = "") -> str:
    return get_crypto_engine().encrypt_str(plaintext, associated_data)


def decrypt_str(token: str, associated_data: str = "") -> str:
    return get_crypto_engine().decrypt_str(token, associated_data)


def encrypt_json(data: Any, associated_data: str = "") -> str:
    return get_crypto_engine().encrypt_json(data, associated_data)


def decrypt_json(token: str, associated_data: str = "") -> Any:
    return get_crypto_engine().decrypt_json(token, associated_data)


def mask_secret(value: str, visible_prefix: int = 3, visible_suffix: int = 2) -> str:
    return get_crypto_engine().mask_secret(value, visible_prefix, visible_suffix)


def blind_index_hash(value: str) -> str:
    return get_crypto_engine().blind_index_hash(value)
