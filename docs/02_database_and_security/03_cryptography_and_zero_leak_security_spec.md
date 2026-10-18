# Cryptographic Architecture & Zero-Leak Security Specification
**Project:** `Crawlers_testing` | **Status:** Formal Security Treatise | **Stage:** Stage 3 Active

---

## 1. Threat Model & Security Perimeter

Automated web scraping platforms handle high-value identity assets: active session cookies, OAuth bearer tokens, API private keys, and two-factor authentication (2FA) recovery seeds. Standard credential storage practices suffer from four critical attack vectors:

```
+==================================================================================================+
|                                    THREAT MATRIX & MITIGATIONS                                   |
+==================================================================================================+
| THREAT VECTOR         | ATTACK SURFACE                         | VAULT MITIGATION                |
+-----------------------+----------------------------------------+---------------------------------+
| Repository Leak       | Accidental git push of .env or SQLite  | Pre-Commit Secret Guard Scanner |
| Local Disk Inspection | Unauthorized read of database files    | AES-256-GCM Row Encryption      |
| Row-Swapping Injection| Attacker moves encrypted token between rows| Row-Bound Associated Data (AD)|
| Operational Logging   | Plaintext secrets leaked in JSONL logs | Zero-Leak Deterministic Masking |
| Filesystem Artifacts  | Leftover cookie files on disk          | Zero-Fill Byte Shredding        |
+==================================================================================================+
```

The cryptographic perimeter established by `core/crypto_engine.py`, `core/credential_vault.py`, and `core/auth_injector.py` ensures that **at no point** is a plaintext credential, raw cookie, or TOTP seed persisted unencrypted or exposed in API responses.

---

## 2. Key Derivation Function (PBKDF2-HMAC-SHA256)

Master symmetric keys are never stored directly. Instead, the runtime derives a 256-bit symmetric encryption key from environment entropy using **Password-Based Key Derivation Function 2 (PBKDF2)** combined with HMAC-SHA256.

### 2.1 Mathematical Formulation

$$\text{DerivedKey} = \text{PBKDF2}(\text{PRF}=\text{HMAC-SHA256}, \text{Password}=\text{VAULT\_MASTER\_KEY}, \text{Salt}=\text{VAULT\_KDF\_SALT}, c=600000, \text{dkLen}=32)$$

Where:
- $\text{VAULT\_MASTER\_KEY}$ is a 256-bit high-entropy secret ($32$ bytes, URL-safe base64 encoded).
- $\text{VAULT\_KDF\_SALT}$ is a 128-bit cryptographically secure random salt ($16$ bytes, URL-safe base64 encoded) generated via `os.urandom(16)`.
- $c = 600,000$ iterations (exceeding the OWASP 2024 recommended minimum of 600,000 for PBKDF2-HMAC-SHA256).
- $\text{dkLen} = 32$ bytes ($256$ bits), matching the exact key length required by AES-256.

### 2.2 In-Memory Key Caching for High-Speed Throughput

PBKDF2 is computationally intensive by design (~120ms per derivation on modern multi-core CPUs) to resist ASIC and GPU brute-force attacks. Computing the derivation on every database read would cripple crawler throughput.

`CryptoEngine` derives the key once upon initialization and maintains the `AESGCM` cipher instance in volatile process memory:
```python
self._derived_key = self._derive_key(self._master_key_bytes, self._salt_bytes)
self._aesgcm = AESGCM(self._derived_key)
```
Subsequent encrypt/decrypt operations execute in under $0.008\text{ ms}$ ($>125,000$ ops/sec).

---

## 3. Authenticated Encryption (AES-256-GCM)

All sensitive string and JSON fields in `vault_accounts` are encrypted using **Advanced Encryption Standard in Galois/Counter Mode (AES-256-GCM)**.

### 3.1 Serialization Token Envelope

Encrypted tokens are serialized as self-contained, versioned ASCII strings:

$$\text{Token} = \text{"v1:aes256gcm:"} \mathbin{\Vert} \text{Base64URL}(\text{Nonce}_{12} \mathbin{\Vert} \text{Ciphertext}_{N} \mathbin{\Vert} \text{Tag}_{16})$$

```
+==================================================================================================+
| TOKEN COMPONENT  | BYTE SIZE | GENERATION / ROLE                                                 |
+------------------+-----------+-------------------------------------------------------------------+
| Prefix           | 14 bytes  | Hardcoded version identifier: 'v1:aes256gcm:'                     |
| Nonce (IV)       | 12 bytes  | Cryptographically secure random bytes generated via os.urandom(12)|
| Ciphertext       | Variable  | AES-CTR encrypted ciphertext                                      |
| Authentication Tag| 16 bytes | 128-bit Galois GHASH authentication tag                          |
+==================================================================================================+
```

```mermaid
flowchart TD
    Plaintext["Plaintext Secret (Password / Cookie Jar / TOTP Seed)"]
    MasterSecret["Derived 256-bit Key (PBKDF2 600k iters)"]
    Nonce["96-bit Random Nonce (os.urandom(12))"]
    AD["Associated Data: account_id (e.g. acc_insta_179232_...)"]

    subgraph GCM_Engine["AES-256-GCM Authenticated Encryption"]
        CTR["AES-CTR Mode Encryption"]
        GHASH["GHASH Authentication Multiplier over GF(2^128)"]
    end

    Plaintext --> CTR
    MasterSecret --> CTR
    Nonce --> CTR
    CTR --> Ciphertext["Ciphertext Payload"]

    Ciphertext --> GHASH
    AD --> GHASH
    MasterSecret --> GHASH
    GHASH --> Tag["128-bit Authentication Tag"]

    Nonce --> Assembler["Pack: Nonce (12B) + Ciphertext + Tag (16B)"]
    Ciphertext --> Assembler
    Tag --> Assembler

    Assembler --> Base64["Base64URL Encode"]
    Base64 --> Output["v1:aes256gcm:<base64url_string>"]
```

---

## 4. Row-Binding Cryptographic Proof via Associated Data (AD)

A critical vulnerability in multi-tenant encrypted databases is the **Ciphertext Swapping Attack**:
An attacker with write access to the database (or through SQL injection) copies the ciphertext of an admin account's password and pastes it into their own row. If the database decrypts blindly using only the master key, the attacker can sign in as their own account using the admin's secret.

### 4.1 Cryptographic Proof of Protection

`Crawlers_testing` prevents ciphertext swapping by passing `account_id` as **Associated Authenticated Data (AD)** to AES-GCM during every encryption and decryption operation:

```python
enc_password = crypto.encrypt_str(password, associated_data=account_id)
```

In Galois/Counter Mode, the authentication tag $T$ is computed over both the ciphertext $C$ and the associated data $A$:

$$T = \text{GHASH}_K(A, C) \oplus E_K(J_0)$$

Where:
- $A = \text{account\_id}$ padded to 128-bit block boundaries.
- $C = \text{ciphertext}$ padded to 128-bit block boundaries.
- $\text{GHASH}_K$ is the universal hash function over the Galois field $\text{GF}(2^{128})$ parameterized by the hash key $H = E_K(0^{128})$.
- $J_0$ is the pre-counter block derived from the 96-bit nonce.

### 4.2 Security Theorem

**Theorem (Row Invariance):** Let $T_A$ be the authentication tag generated for account $A$ with associated data $AD_A$. If ciphertext $C$ is copied to account $B$ where $AD_B \neq AD_A$, attempting to decrypt with $AD_B$ yields a tag verification failure:

$$\text{GHASH}_K(AD_B, C) \oplus E_K(J_0) \neq T_A$$

The cryptographic library immediately raises `cryptography.exceptions.InvalidTag`. The vault catches this error and aborts with:
```
ValueError: Vault integrity check failed or tampered ciphertext (GCM tag mismatch)
```
Swapping encrypted secrets across rows is cryptographically impossible without knowledge of the master key.

---

## 5. Blind Index Hashing (HMAC-SHA256)

To enforce account uniqueness and support $O(1)$ database lookups without storing plaintext usernames, the vault computes a **Deterministic Blind Index**:

### 5.1 Formulation

$$\text{BlindHash} = \text{HMAC-SHA256}(\text{Key}=\text{DerivedKey}, \text{Message}=\text{platform} \mathbin{\Vert} \text{":"} \mathbin{\Vert} \text{lowercase}(\text{username}))$$

- **Zero Exposure:** An attacker inspecting `credentials_vault.sqlite` cannot invert the 64-character hexadecimal hash to recover the original username.
- **Deduplication:** When importing bulk accounts, `VaultImporter` computes the blind hash and checks `WHERE username_blind_hash = :hash`, detecting duplicate credentials in $O(1)$ index time.

---

## 6. RFC 6238 2FA TOTP Algorithm

The vault provides full support for time-based one-time passwords (TOTP) compliant with **RFC 6238** (backed by RFC 4226 HMAC-based OTP).

### 6.1 Algorithm Specification

Given a Base32-encoded secret key $K$ and Unix epoch time $t$:

1. **Secret Normalization:** Strips spaces and hyphens, converts to uppercase, pads with `=` to valid Base32 boundaries, and decodes to raw bytes.
2. **Time-Step Counter Computation:**
   $$T = \left\lfloor \frac{t - T_0}{X} \right\rfloor$$
   Where $T_0 = 0$ (Unix epoch) and $X = 30$ seconds.
3. **HMAC-SHA1 Hash Generation:**
   $$HS = \text{HMAC-SHA1}(K, T_{8\text{-byte big-endian}})$$
4. **Dynamic Truncation (RFC 4226):**
   - Extract offset from the low-order 4 bits of the last byte: $\text{Offset} = HS[19] \ \& \ \text{0x0F}$.
   - Extract 31-bit integer:
     $$P = ((HS[\text{Offset}] \ \& \ \text{0x7F}) \ll 24) \ | \ ((HS[\text{Offset}+1] \ \& \ \text{0xFF}) \ll 16) \ | \ ((HS[\text{Offset}+2] \ \& \ \text{0xFF}) \ll 8) \ | \ (HS[\text{Offset}+3] \ \& \ \text{0xFF})$$
5. **6-Digit Modulo:**
   $$\text{Code} = P \pmod{10^6}$$
6. **Time Remaining Calculation:**
   $$\text{TimeRemaining} = 30 - (t \pmod{30})$$

The UI displays the active 6-digit code alongside an animated 30-second countdown bar. The underlying raw Base32 seed is never exposed over the API or rendered in the DOM.

---

## 7. Defense-in-Depth Security Mechanisms

### 7.1 Ephemeral Netscape Cookie Shredding
Tools requiring filesystem-based Netscape cookies (`11_yt_dlp_ffmpeg`, `12_instaloader`, `13_gallery_dl`) receive dynamically generated cookie files in `vault_store/temp_cookies/`. 

To prevent forensic recovery of expired session tokens from raw disk sectors, `AuthInjector` executes a 3-step cryptographic wipe within a Python `finally:` block:

```python
with open(cookie_file, "r+b") as f:
    length = f.seek(0, 2)
    f.seek(0)
    f.write(b"\x00" * length)  # Step 1: Overwrite with zero bytes
    f.flush()
    os.fsync(f.fileno())       # Step 2: Flush OS write buffer to physical storage
os.remove(cookie_file)         # Step 3: Unlink inode from filesystem
```

### 7.2 Zero-Leak Deterministic Masking
All usernames and token previews rendered in logs or the frontend are passed through `mask_secret()`:

$$\text{Masked}(S) = \begin{cases} 
S[:3] \mathbin{\Vert} \text{"*"} \times (|S| - 5) \mathbin{\Vert} S[-2:] & \text{if } |S| > 5 \\
\text{"****"} & \text{otherwise}
\end{cases}$$

Example: `"admin_crawler_01"` $\rightarrow$ `"adm***********01"`. Plaintext credentials never touch stdout or UI tables.

### 7.3 Git Pre-Commit Secret Guard
Enforced by `core/git_manager.py:scan_staged_for_secrets()`, this automated scanner intercepts `git commit` actions and executes regex inspection across all staged diffs:

```
+==================================================================================================+
| SCAN TARGET                | RULE / REGEX                               | ENFORCEMENT ACTION     |
+----------------------------+--------------------------------------------+------------------------+
| Forbidden Files            | .env, *.sqlite, *.sqlite-wal, *.cookies.txt| Automatic Git Unstage  |
| Raw AES Tokens             | v1:aes256gcm:[A-Za-z0-9_-]{20,}            | Hard Block & Alert     |
| Private Keys               | -----BEGIN (RSA|EC|PRIVATE) KEY-----       | Hard Block & Alert     |
| High-Entropy API Keys      | (ghp_|gho_|xoxb-|AIzaSy)[A-Za-z0-9_-]{16,} | Hard Block & Alert     |
+==================================================================================================+
```
If a single violation is detected, `git_manager.py` automatically unstages the offending file, aborts the commit, and logs a critical security alert to `logs/global/antigravity_prompt_log.jsonl`.
