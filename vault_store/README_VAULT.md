# 🔐 Crawlers_testing Credential Vault (`vault_store/`)
**Stage 3: Credential Vault & Session Security Active — Rule 6 Compliance**

---

## Overview

The `vault_store/` directory houses encrypted authentication assets, browser session cookies, API tokens, proxy credentials, and 2FA secrets utilized by crawler tools.

All sensitive data stored in this directory is encrypted using authenticated **AES-256-GCM** with keys derived via **PBKDF2-HMAC-SHA256 (600,000 iterations)** through `core/crypto_engine.py`.

---

## Security Architecture & Policies

1. **Zero-Plaintext Policy (Rule 6):**
   - No plaintext passwords, API keys, or raw authentication cookies are ever written to disk or recorded in execution logs.
   - All ciphertexts are formatted with authenticated version headers: `v1:aes256gcm:<base64url(nonce + ciphertext + tag)>`.

2. **Master Key & Salt Isolation:**
   - The master secret (`VAULT_MASTER_KEY`) and cryptographic salt (`VAULT_KDF_SALT`) are isolated in the local `.env` file.
   - `.env` is strictly excluded in `.gitignore` and enforced by the Git Pre-Commit Secret Guard in `core/git_manager.py`.
   - A sanitized `.env.example` file is provided for environment provisioning.

3. **Database File Exclusion:**
   - SQLite databases in this directory (`*.sqlite`, `*.sqlite-wal`, `*.sqlite-shm`, `*.db`) are strictly Git-ignored.
   - Temporary decrypted cookie jars in `temp_cookies/` are strictly Git-ignored.

4. **Git-Tracked Public Telemetry:**
   - Non-sensitive aggregate metrics (e.g., total account count, active session count, rotation status) are compiled into `vault_store/vault_stats_public.json` for repository status tracking without exposing secrets.
