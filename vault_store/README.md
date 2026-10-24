# Encrypted Credential Vault & Ephemeral Session Store (`vault_store/`)

The `vault_store/` directory houses the encrypted SQLite database, public non-sensitive telemetry snapshots, and temporary cookie shredding buffers enforcing Antigravity Governance Rule 6 (Zero-Plaintext Security).

---

## 🔒 Security Policy & Git Exclusion

> [!CAUTION]
> **Strict Git Exclusion Rule:**
> Plaintext credentials, passwords, session tokens, 2FA recovery seeds, and `vault_store/*.sqlite*` files are strictly excluded from Git via `.gitignore`. The pre-commit scanner in `core/git_manager.py` automatically blocks any attempt to commit vault databases, master keys, or raw cipher tokens.

```
vault_store/
├── credentials_vault.sqlite           # AES-256-GCM Encrypted Account DB (Strictly Git-Ignored)
├── credentials_vault.sqlite-wal       # SQLite WAL buffer (Git-Ignored)
├── credentials_vault.sqlite-shm       # SQLite Shared Memory index (Git-Ignored)
├── README.md                          # Subsystem architectural specification (Git-Tracked)
├── README_VAULT.md                    # Operational vault runbook & security guide (Git-Tracked)
├── vault_stats_public.json            # Non-sensitive aggregate metrics (Git-Tracked)
└── temp_cookies/                      # Ephemeral Netscape cookies directory (Git-Ignored)
    └── ephemeral_*.cookies.txt        # Lifespan: with authenticated_session(): block only
```

---

## 🛡️ Core Cryptographic Guarantees

### 1. AES-256-GCM Authenticated Encryption
Every password, session cookie jar, proxy secret, and 2FA seed is encrypted with a 256-bit symmetric key derived via PBKDF2-HMAC-SHA256 (600,000 iterations). Tokens are serialized as:
```text
v1:aes256gcm:<base64url(nonce[12] + ciphertext + tag[16])>
```
Authenticated encryption ensures confidentiality while detecting any unauthorized ciphertext tampering or bit-flipping attacks.

### 2. Row-Binding Cryptographic Proof (Associated Data)
Ciphertexts are cryptographically bound to their specific `account_id` via Associated Data (AD):
$$\text{Tag} = \text{AES-GCM-Tag}(K_{\text{enc}}, \text{Nonce}, \text{Plaintext}, \text{AD}=\text{account\_id})$$
If an attacker attempts to copy ciphertext between rows in the SQLite database (e.g. transplanting an admin token into a low-privilege row), decryption immediately aborts with `ValueError: GCM tag mismatch`, preventing row-swapping injection attacks.

### 3. Deterministic Blind Index Hashing
Account deduplication and target matching are evaluated in $O(1)$ time via deterministic HMAC-SHA256 blind indexing:
$$\text{BlindHash} = \text{HMAC-SHA256}(K_{\text{blind}}, \text{platform} \mathbin{\Vert} \text{":"} \mathbin{\Vert} \text{username})$$
This allows the database to enforce unique constraints and look up accounts without storing plaintext usernames.

### 4. Ephemeral Cookie Zero-Fill Shredding (3-Step Destruction)
Tools requiring physical Netscape `.cookies.txt` files receive dynamically synthesized temporary files inside `vault_store/temp_cookies/`. Upon context exit, `core/auth_injector.py` executes a 3-step forensic destruction:
1. **0x00 Overwrite:** Overwrites the entire file payload with null bytes (`b"\x00" * file_size`).
2. **Disk Flush:** Calls `f.flush()` followed by `os.fsync(f.fileno())` to force write-through cache eviction on physical media.
3. **Inode Unlink:** Calls `test_file.unlink()` to remove the filesystem pointer, leaving zero forensic trace.

### 5. RFC 6238 2FA TOTP Engine (`core/totp_helper.py`)
- Normalizes Base32 secret keys by stripping spaces, hyphens, and adding padding.
- Emits live 6-digit numeric codes with 30-second time-window countdowns and $\pm 1$ period clock-skew tolerance.
- **Memory-Only Extraction:** The TOTP helper extracts seeds only in volatile memory and returns the 6-digit token, ensuring raw secret keys are never leaked to logs or API responses.

---

## 📊 Public Non-Sensitive Telemetry (`vault_stats_public.json`)

To enable dashboard monitoring (Tab 5) and CI/CD verification without exposing credentials, non-sensitive aggregated metrics are exported to `vault_stats_public.json`:
- `total_accounts`: Count of managed accounts.
- `active_ready`: Count of un-quarantined accounts.
- `cooldown_quarantined`: Count of accounts resting in rate-limit cooldown.
- `protected_2fa_seeds`: Count of accounts with multi-factor authentication.
- `private_target_coverage`: Count of targets with valid leased session access.

For complete cryptographic proofs, refer to [docs/02_database_and_security/03_cryptography_and_zero_leak_security_spec.md](../docs/02_database_and_security/03_cryptography_and_zero_leak_security_spec.md).
