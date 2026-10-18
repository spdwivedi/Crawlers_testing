# Encrypted Credential Vault & Session Store (`vault_store/`)

The `vault_store/` directory houses the encrypted SQLite database, public non-sensitive telemetry snapshots, and temporary cookie shredding buffers enforcing Antigravity Governance Rule 6 (Zero-Plaintext Security).

---

## 🔒 Security Policy & Git Exclusion

> [!CAUTION]
> **Strict Git Exclusion Rule:**
> Plaintext credentials, passwords, session tokens, 2FA recovery seeds, and `vault_store/*.sqlite*` files are strictly excluded from Git via `.gitignore`. The pre-commit scanner in `core/git_manager.py` blocks any attempt to commit vault databases or raw tokens.

```
vault_store/
├── credentials_vault.sqlite           # AES-256-GCM Encrypted Account DB (Strictly Git-Ignored)
├── credentials_vault.sqlite-wal       # SQLite WAL buffer (Git-Ignored)
├── credentials_vault.sqlite-shm       # SQLite Shared Memory index (Git-Ignored)
├── README.md                          # Security architecture reference (Git-Tracked)
├── README_VAULT.md                    # In-depth vault documentation (Git-Tracked)
├── vault_stats_public.json            # Non-sensitive aggregate metrics (Git-Tracked)
└── temp_cookies/                      # Ephemeral Netscape cookies directory (Git-Ignored)
    └── ephemeral_*.cookies.txt        # Lifespan: with authenticated_session(): block only
```

---

## 🛡️ Core Cryptographic Guarantees

1. **AES-256-GCM Authenticated Encryption:**
   Every password, cookie jar, and session token is encrypted with a 256-bit symmetric key derived via PBKDF2-HMAC-SHA256 (600,000 iterations). Tokens are serialized as `v1:aes256gcm:<base64url(nonce[12] + ciphertext + tag[16])>`.
2. **Row-Binding Cryptographic Proof:**
   Ciphertexts are cryptographically bound to their specific `account_id` via Associated Data (AD). If an attacker copies an encrypted password from Account A to Account B, decryption immediately aborts with `ValueError: GCM tag mismatch`.
3. **Deterministic Blind Index Hashing:**
   Account deduplication is evaluated in $O(1)$ time via deterministic HMAC-SHA256 hashes ($\text{BlindHash} = \text{HMAC}(Key, \text{platform} \mathbin{\Vert} \text{":"} \mathbin{\Vert} \text{username})$) without storing plaintext usernames.
4. **Ephemeral Cookie Zero-Fill Shredding:**
   Tools requiring physical Netscape cookie files receive temporary files inside `vault_store/temp_cookies/`. Upon context exit, `AuthInjector` overwrites the file bytes with `0x00`, flushes the disk buffer via `os.fsync()`, and unlinks the inode from physical storage.
5. **Public Non-Sensitive Stats Snapshot:**
   Aggregated account counts, health scores, and target coverage metrics are exported to `vault_stats_public.json` without exposing domains, usernames, or secrets.

For complete cryptographic proofs and database schemas, refer to [docs/02_database_and_security/03_cryptography_and_zero_leak_security_spec.md](../docs/02_database_and_security/03_cryptography_and_zero_leak_security_spec.md).
