---
jupytext:
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.19.0
kernelspec:
  name: python3
  display_name: Python 3 (ipykernel)
  language: python
---

# Password & Passphrase Management: Engineering Team Handbook

+++

---

Owner: Vadim Rudakov, rudakow.wadim@gmail.com  
Version: 0.1.1  
Birth: 2026-01-18  
Last Modified: 2026-01-21

---

+++

:::{warning} SECURITY DISCLAIMER
:class: dropdown
This handbook contains detailed operational procedures that, if used verbatim
by your organization, may create security vulnerabilities. Readers MUST:

1. **Customize all examples** to your environment (do NOT use example values)
2. **Sanitize before internal use** (remove author-specific details)
3. **Conduct threat modeling** before implementing any procedure
4. **Never publish your customized version** (keep internal documentation private)

The author assumes NO LIABILITY for security incidents resulting from improper
use of these procedures. This is EDUCATIONAL MATERIAL, not a copy-paste implementation guide.

If an attacker uses this handbook to target you, the fault lies in:
- Using example values verbatim (e.g., "Production Server 01")
- Publishing your customized version
- Not conducting organization-specific threat modeling

**Who Should Read This**

✅ **Intended Audience**:
- Security engineers designing password management systems
- DevOps leads implementing secret management
- Compliance officers mapping to [ISO/IEC 27001](wiki:ISO%2FIEC_27001) / NIST requirements

❌ **NOT Intended For**:
- Copy-paste implementation without customization
- Organizations lacking security expertise to adapt procedures
- Publishing internal procedures based on this template
:::

+++

## **Document Purpose**

+++

This handbook establishes **mandatory** password and passphrase management protocols for engineering teams handling 
- production infrastructure, 
- cryptographic keys, and 
- sensitive credentials.

**Scope**: This document covers:
- Password managers (selection, configuration, team workflows)
- Physical backup strategies (paper, hardware tokens)
- Passphrase generation and entropy requirements
- Team collaboration and secret sharing
- Emergency access and disaster recovery
- Compliance with ISO 27001, NIST SP 800-63B, CIS Controls v8

**Out of Scope**:
- Application-level authentication (OAuth, SAML)
- Database credential rotation
- API key management at scale (use dedicated secrets manager)

+++

## **Security Philosophy**

+++

### The Three-Layer Defense Model

+++

```
┌─────────────────────────────────────────────────────────────┐
│ Layer 1: HUMAN MEMORY (Master Password)                    │
│         Protection: Memorization + optional physical backup │
└────────────────────┬────────────────────────────────────────┘
                     │ unlocks
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ Layer 2: ENCRYPTED VAULT (Password Manager Database)       │
│         Protection: AES-256 encryption + MFA               │
└────────────────────┬────────────────────────────────────────┘
                     │ contains
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ Layer 3: INDIVIDUAL SECRETS (Passwords, GPG passphrases)   │
│         Protection: Each secret has unique value           │
└─────────────────────────────────────────────────────────────┘
```

**Core Principles**:

1. **Zero-Knowledge Architecture**: Password manager provider CANNOT decrypt your vault (even if legally compelled)
2. **Cryptographic Randomness**: NEVER use memorable passwords for infrastructure credentials
3. **Individual Accountability**: Each engineer has unique credentials (no shared "root" passwords)
4. **Defense in Depth**: Multiple independent backup mechanisms prevent single points of failure
5. **Assume Breach**: Design storage strategy assuming attackers may gain filesystem access

+++

## **Section 1: Password Manager Selection**

+++

### 1.1 Mandatory Requirements

+++

All password managers used by the engineering team MUST meet these criteria:

| **Requirement** | **Verification Method** | **Rationale** |
|----------------|------------------------|---------------|
| **Zero-Knowledge Encryption** | Review security whitepaper; verify provider cannot reset master password | Protects against insider threats and legal demands |
| **SOC2 Type II Certified** | Check compliance page (e.g., bitwarden.com/compliance/) | Third-party audit of security controls |
| **End-to-End Encryption** | Verify [AES-256](/security/password_management/aes_256_advanced_encryption_standard_with_a_256_bit.ipynb) or ChaCha20 cipher | Industry standard for data at rest |
| **Multi-Factor Authentication** | Test TOTP, U2F, or WebAuthn support | Prevents password manager compromise via master password alone |
| **Offline Access** | Disconnect internet; verify vault decryption works | Critical for disaster scenarios (ISP outage, cloud service down) |
| **CLI Access** | Verify `bw`, `op`, or equivalent CLI tool exists | Required for automation (CI/CD integration) |
| **Audit Logging** | Check event logs for login attempts, vault access | Compliance requirement (ISO 27001 A.12.4.1) |
| **Open Source (Preferred)** | Review source code on GitHub/GitLab | Community security review; reduces vendor lock-in risk |

+++

### 1.2 Approved Password Managers

+++

| **Solution** | **Type** | **SOC2** | **Self-Hosted** | **CLI** | **Team Features** | **Best For** |
|-------------|----------|---------|----------------|---------|------------------|--------------|
| **Bitwarden** | Cloud/Self-hosted | ✅ | ✅ | ✅ `bw` | Collections, org vault | ✅ **Teams (recommended)** |
| **1Password** | Cloud | ✅ | ❌ | ✅ `op` | Shared vaults, travel mode | Enterprise with budget |
| **KeePassXC** | Local-only | N/A | ✅ (file-based) | ✅ `keepassxc-cli` | Manual file sync | ✅ **Solo developers, air-gapped** |
| **Vaultwarden** | Self-hosted | N/A | ✅ | ✅ `bw` (compatible) | Bitwarden-compatible | Teams with self-hosting requirement |
| **Pass** | Local-only | N/A | ✅ (Git-based) | ✅ `pass` | Git-based sharing | CLI power users |

**Prohibited Solutions**:
- ❌ Browser built-in password managers (Chrome, Firefox) - No encryption at rest, no audit logs
- ❌ Plaintext files (even if encrypted with `gpg`) - No versioning, no team features
- ❌ Spreadsheets (Excel, Google Sheets) - No encryption, accidental sharing risk
- ❌ Sticky notes, paper notebooks (as primary storage) - Physical security risk, no backup

+++

### 1.3 Recommended Configuration: Bitwarden for Teams

+++

Self-Hosted via Vaultwarden.

**Why Bitwarden**:
- Open source (auditable)
- SOC2 Type II certified
- Self-hosting option (Vaultwarden for small teams)
- CLI tool (`bw`) for automation
- Per-user licensing ($10/year, free for self-hosted)

+++

### 1.4 Alternative: KeePassXC for Air-Gapped Environments

+++

**Use Case**: Environments without internet access (defense, finance, research)

**Installation**:

```bash
# Fedora
sudo dnf install keepassxc

# Debian
sudo apt install keepassxc

# Verify
keepassxc-cli --version
# Expected: 2.7.x or higher
```

**Team Workflow** (Git-based synchronization):

```bash
# 1. Create shared KeePass database
keepassxc-cli db-create team_passwords.kdbx
# Enter master password (shared among team via secure channel)

# 2. Store in private Git repository
git init password-vault
cd password-vault
cp /path/to/team_passwords.kdbx .
git add team_passwords.kdbx
git commit -m "Initialize password vault"
git remote add origin git@your-git-server.com:team/passwords.git
git push -u origin main

# 3. Team members clone repository
git clone git@your-git-server.com:team/passwords.git
keepassxc team_passwords.kdbx
# Enter shared master password

# 4. Update workflow (manual coordination required)
# Engineer A: Adds new credential
keepassxc-cli add team_passwords.kdbx /Production/NewServer
git add team_passwords.kdbx
git commit -m "Add NewServer credentials"
git push

# Engineer B: Pulls latest changes
git pull
# Resolve conflicts manually if multiple engineers edit simultaneously
```

**Trade-offs**:
- ✅ **Gain**: No cloud dependency, full control
- ❌ **Cost**: Manual synchronization, merge conflicts, shared master password

+++

## Section 2: Passphrase Generation

+++

### 2.1 Passphrase vs Password: Critical Distinction

+++

| **Credential Type** | **Use Case** | **Generation Method** | **Storage** | **Example** |
|--------------------|--------------|-----------------------|-------------|-------------|
| **Master Password** | Unlocks password manager | Diceware (human-memorable) | Human memory + paper backup | `correct-horse-battery-staple-mountain-river` |
| **GPG Passphrase** | Unlocks GPG private key | Diceware or random (24+ chars) | Password manager + paper backup | `retro-shaving-uncooked-snowman-guru-hatchet` |
| **Infrastructure Password** | Server sudo, database auth | Cryptographic random (32+ chars) | Password manager ONLY | `xK9m#Qp2$vL8@nR4wT3!zY7&mA5^sD1` |
| **API Key/Token** | Service authentication | Provider-generated | Password manager + CI/CD vault | `sk_live_51H7...` (Stripe) |

**Key Principle**: Only the **master password** should be designed for memorization. All other credentials should be cryptographically random.

+++

### 2.2 Entropy Requirements

+++

**Minimum Entropy Targets** (based on threat model):

| **Asset** | **Minimum Entropy** | **Diceware Words** | **Random Chars** | **Attack Resistance** |
|-----------|--------------------|--------------------|------------------|----------------------|
| Master Password | 77 bits | 6 words | 12 chars (mixed) | Online attack (rate-limited) |
| GPG Passphrase | 103 bits | 8 words | 24 chars (mixed) | Offline attack (GPU cracking) |
| Production Password | 128 bits | N/A | 32 chars (random) | Quantum-resistant (NIST recommendation) |

**Entropy Calculation**:

```python
# Diceware (EFF wordlist: 7,776 words)
# Entropy per word = log2(7776) ≈ 12.925 bits
# 6 words = 6 × 12.925 = 77.55 bits
# 8 words = 8 × 12.925 = 103.4 bits

# Random characters (94 printable ASCII)
# Entropy per char = log2(94) ≈ 6.555 bits
# 12 chars = 12 × 6.555 = 78.66 bits
# 24 chars = 24 × 6.555 = 157.32 bits
# 32 chars = 32 × 6.555 = 209.76 bits
```

**Verification Script**:

```bash
# Calculate entropy of a passphrase
calculate_entropy() {
    local passphrase="$1"
    local length=${#passphrase}
    
    # Count character classes
    local has_lower=$(echo "$passphrase" | grep -q '[a-z]' && echo 1 || echo 0)
    local has_upper=$(echo "$passphrase" | grep -q '[A-Z]' && echo 1 || echo 0)
    local has_digit=$(echo "$passphrase" | grep -q '[0-9]' && echo 1 || echo 0)
    local has_symbol=$(echo "$passphrase" | grep -q '[^a-zA-Z0-9]' && echo 1 || echo 0)
    
    # Calculate character space
    local charset_size=0
    [ $has_lower -eq 1 ] && charset_size=$((charset_size + 26))
    [ $has_upper -eq 1 ] && charset_size=$((charset_size + 26))
    [ $has_digit -eq 1 ] && charset_size=$((charset_size + 10))
    [ $has_symbol -eq 1 ] && charset_size=$((charset_size + 32))
    
    # Entropy = length × log2(charset_size)
    local entropy=$(echo "scale=2; $length * l($charset_size)/l(2)" | bc -l)
    
    echo "Passphrase length: $length"
    echo "Charset size: $charset_size"
    echo "Estimated entropy: $entropy bits"
    
    # Check against requirements
    if (( $(echo "$entropy >= 103" | bc -l) )); then
        echo "✅ PASS: Sufficient for GPG passphrase (≥103 bits)"
    elif (( $(echo "$entropy >= 77" | bc -l) )); then
        echo "⚠️  MARGINAL: Acceptable for master password, weak for GPG"
    else
        echo "❌ FAIL: Insufficient entropy (minimum 77 bits)"
    fi
}

# Test
calculate_entropy "correct-horse-battery-staple-mountain-river"
calculate_entropy "xK9m#Qp2$vL8@nR4wT3!zY7&"
```

+++

### 2.3 Diceware Passphrase Generation

+++

**Recommended Method: EFF Long Wordlist**

```bash
# Install diceware
uv add diceware

# Generate 6-word passphrase (master password)
diceware --num 6 --wordlist en_eff
# Example output: correct-horse-battery-staple-mountain-river

# Generate 8-word passphrase (GPG passphrase)
diceware --num 8 --wordlist en_eff
# Example output: retro-shaving-uncooked-snowman-guru-hatchet-apple-repackage

# Options:
# --no-caps    : All lowercase (easier for paper backup)
# --delimiter  : Change separator (default: -)
# --wordlist   : en_eff (7776 words), en_orig (7776), en_securedrop (7776)
```

**Manual Diceware Method** (if offline):

```bash
# 1. Download EFF wordlist
curl -O https://www.eff.org/files/2016/07/18/eff_large_wordlist.txt

# 2. Roll five 6-sided dice physically
# Example roll: 4-2-6-1-3 = 42613

# 3. Look up word in wordlist
grep "^42613" eff_large_wordlist.txt
# Output: 42613 obscure

# 4. Repeat for 6-8 words
# Final passphrase: obscure-hatchet-guru-uncooked-snowman-retro
```

**Memorization Technique**:

```
Passphrase: correct-horse-battery-staple-mountain-river

Mnemonic Story:
"The CORRECT HORSE needed a new BATTERY, so it went to the STAPLE
 store on the MOUNTAIN near the RIVER."

Practice Schedule:
- Day 1: Write passphrase 5 times
- Day 2: Type passphrase 10 times (without looking)
- Day 3: Recite from memory
- Day 7: Verify recall after 1 week
- Day 30: Verify recall after 1 month
```

+++

### 2.4 Random Password Generation

+++

**For Infrastructure Credentials** (NOT meant to be memorized):

```bash
# Method 1: OpenSSL (highest entropy)
openssl rand -base64 32
# Output: xK9m#Qp2$vL8@nR4wT3!zY7&mA5^sD1hF6

# Method 2: Password manager built-in generator
bw generate --length 32 --uppercase --lowercase --number --special
# Output: K7!pQ2$mL9@vR3&wT8#nY4^zA1*sD5

# Method 3: /dev/urandom (Linux/Unix)
tr -dc 'A-Za-z0-9!@#$%^&*()_+-=' < /dev/urandom | head -c 32
# Output: wR3&mL9@vK7!pQ2$nY4^zA1*T8#sD5
```

**Password Complexity Rules** (for compliance):

```bash
# Generate password meeting specific requirements
generate_compliant_password() {
    local length=${1:-32}
    
    # NIST SP 800-63B requirements:
    # - Minimum 8 characters (we use 32 for production)
    # - No composition rules enforced (pure entropy matters)
    # - No mandatory expiration (rotation on compromise only)
    
    openssl rand -base64 $((length * 3 / 4)) | tr -d '\n' | head -c $length
    echo
}

# Usage
generate_compliant_password 32
```

**Prohibited Patterns**:

```bash
# ❌ NEVER use these patterns:
# - Dictionary words: "password123", "admin2024"
# - Keyboard patterns: "qwerty", "asdfgh"
# - Repeated characters: "aaaa1111"
# - Sequential patterns: "abcd1234"
# - Personal information: "john1980", "company2024"
# - Common substitutions: "P@ssw0rd", "S3cur1ty"

# ✅ ALWAYS use cryptographically random generators
```

+++

## Section 3: Password Manager Workflows

+++

### 3.1 Individual Engineer Setup

+++

**Initial Configuration** (one-time, 30 minutes):

```bash
# 1. Install Bitwarden desktop app
flatpak install flathub com.bitwarden.desktop

# 2. Create account at bitwarden.com
# (or your self-hosted instance)

# 3. Generate master password
diceware --num 6 --wordlist en_eff
# Example: correct-horse-battery-staple-mountain-river

# 4. Enable Two-Factor Authentication (MANDATORY)
# Bitwarden Settings → Security → Two-step Login
# Recommended: Authenticator App (Authy, Google Authenticator)
# Alternative: YubiKey (hardware token)

# 5. Configure browser extension
# Install: Firefox/Chrome → bitwarden.com/download
# Login with master password + 2FA

# 6. Install CLI tool
npm install -g @bitwarden/cli

# 7. Login via CLI
bw login your-email@example.com
# Enter master password + 2FA code

# 8. Unlock vault (creates session key)
export BW_SESSION=$(bw unlock --raw)

# 9. Verify CLI access
bw list items --pretty
```

**Daily Workflow**:

```bash
# Unlock vault (once per terminal session)
export BW_SESSION=$(bw unlock --raw)

# Retrieve password for SSH login
bw get password "Production Server 01"
# Output: xK9m#Qp2$vL8@nR4wT3!zY7&

# Copy to clipboard (auto-clears after 30 seconds)
bw get password "Production Server 01" | xclip -selection clipboard

# Add new credential
bw create item '{
  "organizationId": null,
  "folderId": null,
  "type": 1,
  "name": "New Database Password",
  "notes": "PostgreSQL production instance",
  "fields": [
    {"name": "hostname", "value": "db.example.com", "type": 0},
    {"name": "port", "value": "5432", "type": 0}
  ],
  "login": {
    "username": "dbadmin",
    "password": "'"$(openssl rand -base64 32)"'"
  }
}'

# Sync changes
bw sync
```

+++

### 3.2 Team Sharing Workflow

+++

**Use Case**: Multiple engineers need access to production server credentials.

**Setup** (Team Admin):

```bash
# 1. Create Collection
bw create org-collection '{
  "organizationId": "your-org-id",
  "name": "Production Servers",
  "externalId": null
}'

# 2. Add credential to collection
bw create item '{
  "organizationId": "your-org-id",
  "collectionIds": ["collection-id"],
  "type": 1,
  "name": "Production Server 01 - sudo password",
  "login": {
    "username": "admin",
    "password": "'"$(openssl rand -base64 32)"'"
  }
}'

# 3. Assign engineers to collection
# Web UI: Manage → Collections → Production Servers → Manage Access
# Grant: "Can view" (read-only) or "Can edit" (read-write)
```

**Access** (Team Member):

```bash
# 1. Sync vault to get shared credentials
bw sync

# 2. List items in collection
bw list items --organizationid "your-org-id" --pretty

# 3. Retrieve shared password
bw get password "Production Server 01 - sudo password"
```

**Rotation Protocol**:

```bash
# When engineer leaves team:

# 1. Admin removes engineer from organization
# Web UI: Manage → People → [Engineer Name] → Remove

# 2. Admin rotates ALL credentials in collections that engineer had access to
bw list items --organizationid "your-org-id" | jq -r '.[].id' | while read item_id; do
  # Generate new password
  new_password=$(openssl rand -base64 32)
  
  # Update item
  bw edit item $item_id --password "$new_password"
done

# 3. Sync changes
bw sync

# 4. Apply new passwords to actual systems
# (Deploy Ansible playbook, update database users, etc.)
```

+++

### 3.3 Emergency Access

**Use Case**: Team lead is unavailable; another engineer needs urgent access to credentials.

**Setup** (Team Lead):

```bash
# Bitwarden Emergency Access Feature
# Web UI: Settings → Emergency Access → Invite Emergency Contact

# 1. Invite trusted colleague
# Email: trusted-colleague@example.com
# Access Level: "View" (read-only) or "Takeover" (full access)
# Wait Time: 24 hours (delay before access granted)

# 2. Colleague accepts invitation

# 3. Colleague can request access during emergency
# Web UI: Emergency Access → Request Access
```

**Emergency Access Workflow**:

```bash
# Scenario: Team lead on vacation, production database password needed urgently

# 1. Trusted colleague requests emergency access
# Web UI: Emergency Access → Request Access → [Team Lead Name]

# 2. System sends notification to team lead
# Email: "Emergency access requested by [Colleague]"

# 3. Team lead has 24 hours to approve/deny
# - If approved: Immediate access granted
# - If no response: Automatic approval after 24 hours

# 4. Colleague gains temporary access to vault
# Access duration: Permanent until team lead revokes

# 5. After emergency resolved:
# Team lead revokes emergency access
# Web UI: Emergency Access → [Colleague Name] → Revoke Access
```

**Alternative: Shared Emergency Vault**:

```bash
# For critical credentials (root CA keys, disaster recovery):

# 1. Create separate vault with strong master password
keepassxc-cli db-create emergency_vault.kdbx
# Master password: <8-word Diceware passphrase>

# 2. Split master password using Shamir's Secret Sharing
# Install: ssss (Shamir's Secret Sharing Scheme)
sudo apt install ssss

# Split password into 5 shares, requiring 3 to reconstruct
echo "your-8-word-diceware-passphrase" | ssss-split -t 3 -n 5
# Output:
# Share 1: 1-abc123...
# Share 2: 2-def456...
# Share 3: 3-ghi789...
# Share 4: 4-jkl012...
# Share 5: 5-mno345...

# 3. Distribute shares to 5 senior engineers
# Each engineer stores their share in personal password manager

# 4. During emergency, 3 engineers combine shares
ssss-combine -t 3
# Enter: Share 1, Share 3, Share 5
# Output: your-8-word-diceware-passphrase

# 5. Open emergency vault
keepassxc emergency_vault.kdbx
# Enter reconstructed master password
```

+++

## Section 4: Physical Backup Strategies

+++

### 4.1 Paper Backup Requirements

+++

**When Physical Backup is Mandatory**:

| **Credential Type** | **Paper Backup Required?** | **Rationale** |
|--------------------|-----------------------------|---------------|
| Password manager master password | ✅ **YES** | Single point of failure; forgot password = permanent lockout |
| GPG private key passphrase | ✅ **YES** | Cannot decrypt vault password without it |
| Root CA private key passphrase | ✅ **YES** | Infrastructure-critical; cannot reissue certificates |
| Emergency vault master password | ✅ **YES** | Disaster recovery scenario |
| Server sudo passwords | ❌ **NO** | Stored in password manager; rotatable via Ansible |
| Database passwords | ❌ **NO** | Stored in password manager; rotatable via SQL |
| API keys | ❌ **NO** | Revocable and regenerable via provider console |

+++

### 4.2 Paper Backup Template

+++

**Standard Credential Card**:

```
┌─────────────────────────────────────────────────────────────┐
│                  CREDENTIAL BACKUP CARD                      │
├─────────────────────────────────────────────────────────────┤
│ Credential Type: [ ] Master Password  [ ] GPG Passphrase   │
│                  [ ] Root CA Key      [ ] Emergency Vault   │
├─────────────────────────────────────────────────────────────┤
│ Owner: ________________________________                      │
│ Email: ________________________________                      │
│ Created: __________________                                 │
│ Expires: __________________  (if applicable)                │
├─────────────────────────────────────────────────────────────┤
│ CREDENTIAL (write in PERMANENT INK):                        │
│                                                              │
│ _____________________________________________________________│
│                                                              │
│ _____________________________________________________________│
│                                                              │
│ _____________________________________________________________│
│                                                              │
├─────────────────────────────────────────────────────────────┤
│ RECOVERY INSTRUCTIONS:                                       │
│                                                              │
│ 1. _________________________________________________________│
│                                                              │
│ 2. _________________________________________________________│
│                                                              │
│ 3. _________________________________________________________│
│                                                              │
├─────────────────────────────────────────────────────────────┤
│ STORAGE LOCATION:                                           │
│ [ ] Home Safe - Drawer: _____  Combination: _______________│
│ [ ] Bank Safe Deposit Box - Branch: ______________________│
│ [ ] Office Safe - Building: ____  Room: ____  Combo: _____│
├─────────────────────────────────────────────────────────────┤
│ AUDIT LOG:                                                  │
│ Accessed on: __________  By: __________  Reason: __________│
│ Accessed on: __________  By: __________  Reason: __________│
│ Accessed on: __________  By: __________  Reason: __________│
├─────────────────────────────────────────────────────────────┤
│ ⚠️  SECURITY WARNINGS:                                       │
│ • DO NOT PHOTOCOPY THIS CARD                                │
│ • DO NOT SCAN OR PHOTOGRAPH                                 │
│ • DO NOT EMAIL OR TRANSMIT ELECTRONICALLY                   │
│ • DESTROY SECURELY WHEN CREDENTIAL IS ROTATED              │
│ • IMMEDIATELY ROTATE CREDENTIAL IF CARD IS COMPROMISED      │
└─────────────────────────────────────────────────────────────┘
```

**Example: Completed Card**:

```
┌─────────────────────────────────────────────────────────────┐
│                  CREDENTIAL BACKUP CARD                      │
├─────────────────────────────────────────────────────────────┤
│ Credential Type: [X] Master Password  [ ] GPG Passphrase   │
│                  [ ] Root CA Key      [ ] Emergency Vault   │
├─────────────────────────────────────────────────────────────┤
│ Owner: John Smith                                           │
│ Email: john.smith@example.com                               │
│ Created: 2026-01-18                                         │
│ Expires: N/A                                                │
├─────────────────────────────────────────────────────────────┤
│ CREDENTIAL (write in PERMANENT INK):                        │
│                                                              │
│ correct-horse-battery-staple-mountain-river                 │
│                                                              │
├─────────────────────────────────────────────────────────────┤
│ RECOVERY INSTRUCTIONS:                                       │
│                                                              │
│ 1. Open Bitwarden desktop app                               │
│ 2. Enter this passphrase as master password                │
│ 3. Immediately enable 2FA if not already active             │
│                                                              │
├─────────────────────────────────────────────────────────────┤
│ STORAGE LOCATION:                                           │
│ [X] Home Safe - Drawer: Top  Combination: 15-32-7          │
│ [ ] Bank Safe Deposit Box - Branch: ______________________│
│ [ ] Office Safe - Building: ____  Room: ____  Combo: _____│
├─────────────────────────────────────────────────────────────┤
│ AUDIT LOG:                                                  │
│ Accessed on: 2026-06-15  By: J. Smith  Reason: Vault reset │
│ Accessed on: __________  By: __________  Reason: __________│
│ Accessed on: __________  By: __________  Reason: __________│
├─────────────────────────────────────────────────────────────┤
│ ⚠️  SECURITY WARNINGS:                                       │
│ • DO NOT PHOTOCOPY THIS CARD                                │
│ • DO NOT SCAN OR PHOTOGRAPH                                 │
│ • DO NOT EMAIL OR TRANSMIT ELECTRONICALLY                   │
│ • DESTROY SECURELY WHEN CREDENTIAL IS ROTATED              │
│ • IMMEDIATELY ROTATE CREDENTIAL IF CARD IS COMPROMISED      │
└─────────────────────────────────────────────────────────────┘
```

+++

### 4.3 Physical Security Requirements

+++

**Safe Specifications**:

| **Use Case** | **Minimum Safe Rating** | **Lock Type** | **Cost Range** |
|--------------|-------------------------|---------------|----------------|
| Home backup (1-2 cards) | 1-hour fire rating (UL 350°F) | Electronic keypad OR mechanical combo | $150-$500 |
| Office backup (5-10 cards) | 2-hour fire rating + burglar-resistant | Dual-lock (key + combo) | $500-$2000 |
| Data center (100+ cards) | TL-15 or better (torch/tool resistant) | Class 1 electronic lock with audit trail | $2000+ |

**Recommended Models**:

```bash
# Home Safe (Budget: $150-$300)
# - SentrySafe SFW123GDC (1.23 cu ft, 1-hour fire, waterproof)
# - Honeywell 1104 (1.06 cu ft, 1-hour fire, electronic lock)

# Office Safe (Budget: $500-$1000)
# - SentrySafe SF205CV (2.0 cu ft, 2-hour fire, combination lock)
# - FireKing KY1313-1GRFL (1.3 cu ft, 1-hour fire, UL listed)

# Data Center Safe (Budget: $2000+)
# - AMSEC BF7240 (11.4 cu ft, TL-15 rated, electronic lock)
# - Gardall Z5922-G-E (22 cu ft, fire-resistant, RSC burglary)
```

**Safe Placement**:

```
✅ CORRECT Placement:
- Bolted to floor/wall (prevents theft of entire safe)
- Climate-controlled room (prevents moisture damage)
- Not visible from windows/doors (reduces burglary risk)
- Known to 2-3 trusted individuals (emergency access)

❌ INCORRECT Placement:
- Basement (flood risk)
- Garage (extreme temperature swings)
- Shared office space (unauthorized access)
- Visible from exterior windows (burglar targeting)
```

+++

### 4.4 Paper Material Specifications

+++

**Archival Requirements**:

| **Component** | **Specification** | **Purpose** |
|--------------|------------------|-------------|
| **Paper** | Acid-free, lignin-free, 24lb bond | Prevents yellowing over 50+ years |
| **Ink** | Archival pigment ink (Sakura Pigma Micron) | UV-resistant, waterproof, permanent |
| **Lamination** | 5mil thermal lamination pouches | Water/tear protection |
| **Envelope** | Tyvek (if storing in safe) | Additional moisture barrier |

**Preparation Steps**:

```bash
# 1. Print template on archival paper
# Use laser printer (toner is more permanent than inkjet)
# Settings: Highest quality, no duplex

# 2. Fill in credential with archival pen
# Pen: Sakura Pigma Micron 01 or 05 (0.25mm-0.45mm)
# Ink: Black pigment (highest contrast)
# Technique: Print clearly, no cursive

# 3. Laminate
# Use thermal laminator (avoid cold lamination)
# Settings: 5mil pouch, medium heat
# Wait 24 hours before folding (allows adhesive to cure)

# 4. Label envelope
# Write on Tyvek envelope:
# "CONFIDENTIAL - Password Backup - Owner: [Name]"
# "DO NOT OPEN EXCEPT EMERGENCY"

# 5. Store in safe
# Place in fireproof safe, top shelf
# Record location in password manager notes
```

+++

### 4.5 Hardware Security Tokens

+++

**Use Case**: Two-factor authentication for password manager + hardware-backed passphrase storage.

**Recommended Tokens**:

| **Device** | **Protocols** | **Storage** | **Cost** | **Best For** |
|-----------|--------------|-------------|----------|--------------|
| **YubiKey 5 NFC** | FIDO2, U2F, OTP, PIV, OpenPGP | 4096-bit RSA keys | $50 | ✅ General purpose (recommended) |
| **Nitrokey Pro 2** | OpenPGP, U2F | 4096-bit RSA keys | $60 | Open-source firmware preference |
| **SoloKeys V2** | FIDO2 | No key storage (auth only) | $30 | Budget option (2FA only) |
| **OnlyKey** | FIDO2, OpenPGP, password manager | 24 password slots | $50 | Standalone password storage |

**YubiKey Setup for Password Manager 2FA**:

```bash
# 1. Insert YubiKey into USB port

# 2. Configure Bitwarden to use YubiKey
# Web UI: Settings → Security → Two-step Login → YubiKey OTP Security Key
# - Insert YubiKey
# - Touch YubiKey button when prompted
# - Save generated key

# 3. Test 2FA
bw logout
bw login your-email@example.com
# Enter master password
# Prompt: "Touch your YubiKey"
# Touch YubiKey button → Login successful

# 4. Register backup YubiKey (MANDATORY)
# Purchase second YubiKey
# Web UI: Two-step Login → Manage → Add Security Key
# Configure backup key with same process
# Store backup key in safe (separate from primary)
```

**YubiKey as GPG Key Storage** (Advanced):

```bash
# Move GPG private key to YubiKey (irreversible)
# WARNING: Key cannot be extracted from YubiKey after this

# 1. Verify YubiKey supports OpenPGP
gpg --card-status
# Expected: Card type: yubikey

# 2. Generate GPG key on YubiKey (recommended) OR import existing key
gpg --card-edit
gpg/card> admin
gpg/card> generate
# Follow prompts to create 4096-bit RSA key on device

# 3. Key is now hardware-backed
# Passphrase unlocks YubiKey, not software key

# 4. YubiKey must be inserted for all GPG operations
echo "test" | gpg --encrypt --recipient your-email@example.com
# Prompt: "Insert YubiKey and enter PIN"
# Vault password decryption now requires physical YubiKey

# 5. Backup strategy
# Purchase second YubiKey
# Import same GPG key to backup YubiKey
# Store backup YubiKey in safe
```

+++

## Section 5: Team Collaboration Workflows

+++

### 5.1 Onboarding New Engineer

+++

**Checklist** (completed by Team Lead):

```bash
# Day 1: Account Creation

# 1. Engineer installs Bitwarden
# (Engineer's responsibility)

# 2. Engineer creates Bitwarden account
# Email: new-engineer@example.com
# Master password: <6-word Diceware passphrase>

# 3. Engineer enables 2FA
# Settings → Security → Two-step Login → Authenticator App

# 4. Team Lead invites engineer to organization
bw invite-user new-engineer@example.com --organizationid "org-id"

# 5. Engineer accepts invitation
# Check email → Click "Join Organization"

# 6. Team Lead assigns collections
# Web UI: Manage → People → [New Engineer] → Collections
# Grant access:
# - "Development Servers" (Can edit)
# - "Staging Servers" (Can edit)
# - "Production Servers" (Can view) ← Read-only for first 3 months

# 7. Engineer syncs vault
bw sync

# 8. Engineer creates paper backup of master password
# (Engineer's responsibility, verify completed)

# Day 7: Security Review

# 9. Team Lead audits engineer's 2FA setup
# Web UI: Manage → People → [New Engineer] → Details
# Verify: "Two-step Login: Enabled"

# 10. Verify paper backup created
# Ask: "Have you stored your master password backup in a safe?"
# Expected: "Yes, stored in home safe"

# Day 30: Production Access Grant

# 11. Team Lead grants production write access
# Web UI: Manage → People → [New Engineer] → Collections
# Update: "Production Servers" (Can edit)

# 12. Document access grant
# Add note in password manager:
# "Production access granted to new-engineer@example.com on 2026-02-17"
```

+++

### 5.2 Offboarding Departing Engineer

+++

**Checklist** (completed within 24 hours of departure):

```bash
# Hour 0: Immediate Actions (during exit interview)

# 1. Revoke organization access
# Web UI: Manage → People → [Departing Engineer] → Remove
# Confirmation: "This will remove access to all shared credentials"

# 2. Engineer returns hardware tokens (if issued)
# Collect: YubiKey, laptop, phone with 2FA app
# Wipe: YubiKey PIN attempts (3 wrong attempts = factory reset)

# 3. Disable personal accounts that engineer had credentials for
# Example: sudo on production servers
ssh admin@production-server-01
sudo userdel departing-engineer
sudo rm -rf /home/departing-engineer

# Hour 1-4: Credential Rotation

# 4. Identify all credentials engineer had access to
bw list items --organizationid "org-id" --pretty | \
  jq -r '.[] | select(.collectionIds[] | contains("collection-id")) | .name'

# 5. Rotate shared credentials
# For each credential:
bw get item "Production Server 01 - sudo password" | \
  jq -r '.id' | \
  xargs -I {} bw edit item {} --password "$(openssl rand -base64 32)"

# 6. Apply new passwords to systems
# Run Ansible playbook to update server passwords
ansible-playbook -i inventory/production.ini rotate_passwords.yml

# 7. Rotate API keys
# For each cloud provider:
# - AWS: Deactivate IAM keys, generate new keys
# - GCP: Rotate service account keys
# - Stripe: Roll API keys via dashboard

# 8. Audit logs for engineer's activity
# Web UI: Reports → Event Logs
# Filter: User = [Departing Engineer]
# Review: Last 90 days of vault access
# Export: CSV for security audit

# Day 1-7: Post-Departure Verification

# 9. Verify engineer cannot access shared resources
# Test: Send test credential to engineer's personal email
# Expected: Email bounces (email disabled)

# 10. Review access to physical backups
# If engineer knew safe combination:
# - Change safe combination
# - Update combination in Team Lead's password manager

# 11. Document offboarding completion
# Add note in password manager:
# "Engineer [Name] offboarded on 2026-01-18. All credentials rotated."
```

+++

### 5.3 Secret Sharing Between Engineers

+++

**Use Case**: Engineer A needs to share a one-time password with Engineer B (e.g., SSL certificate private key passphrase).

**Recommended: Bitwarden Send**:

```bash
# Method 1: Web UI (easiest)

# Engineer A:
# 1. Web UI: Tools → Send → Create New Send
# 2. Type: Text
# 3. Content: <paste password>
# 4. Options:
#    - Deletion date: 7 days
#    - Expiration date: 1 day
#    - Maximum access count: 1
#    - Password protect: Yes (generate strong password)
# 5. Create Send → Copy link
# 6. Send link to Engineer B via Signal/Slack
# 7. Send password via separate channel (email)

# Engineer B:
# 1. Open link (in private browser window)
# 2. Enter password
# 3. View credential
# 4. Copy to password manager
# 5. Link auto-deletes after 1 access

# Method 2: CLI (for automation)

# Engineer A:
bw send create text '{"name":"SSL Private Key Passphrase","text":"xK9m#Qp2$vL8","password":"temp-password-123","maxAccessCount":1,"deletionDate":"2026-01-25T00:00:00.000Z"}'
# Output: https://vault.bitwarden.com/#/send/abc123.../xyz789...

# Share link + password via separate channels
```

**Alternative: One-Time Secret (Self-Hosted)**:

```bash
# Deploy onetimesecret (https://github.com/onetimesecret/onetimesecret)

# 1. Run Docker container
docker run -d -p 3000:3000 --name onetimesecret \
  -e OTS_SECRET=$(openssl rand -hex 32) \
  onetimesecret/onetimesecret:latest

# 2. Engineer A creates secret
curl -X POST http://localhost:3000/api/v1/share \
  -d "secret=xK9m#Qp2$vL8" \
  -d "passphrase=temp-password-123" \
  -d "ttl=3600"
# Output: {"secret_key":"abc123..."}

# 3. Share link + passphrase
# Link: http://localhost:3000/secret/abc123...
# Passphrase: temp-password-123 (via Signal)

# 4. Engineer B opens link once → secret deleted
```

**Prohibited Sharing Methods**:

```bash
# ❌ NEVER share passwords via:
# - Email (plaintext, searchable, logs)
# - Slack/Teams direct message (logs, backups, e-discovery)
# - SMS (plaintext, carrier logs)
# - Phone call (potential recording, shoulder surfing)
# - Shared document (Google Docs, Confluence)
# - Version control (Git commits are permanent)

# ✅ ALWAYS use:
# - Bitwarden Send (ephemeral, encrypted)
# - Signal "disappearing messages" (end-to-end encrypted, auto-delete)
# - One-Time Secret tool (self-destructing links)
# - In-person handoff (physical paper card, destroyed after use)
```

+++

### 5.4 Credential Rotation Schedule

+++

**Mandatory Rotation Events**:

| **Event** | **Action** | **Timeline** |
|-----------|-----------|-------------|
| Engineer departure | Rotate ALL shared credentials | Within 24 hours |
| Security incident | Rotate affected credentials | Immediately |
| Suspected compromise | Rotate + audit logs | Within 1 hour |
| Hardware token lost | Revoke token + rotate 2FA | Within 4 hours |
| Master password exposed | Change master + rotate vault | Immediately |

**Scheduled Rotation**:

| **Credential Type** | **Rotation Frequency** | **Automation** |
|--------------------|----------------------|----------------|
| Master password | Annually | ❌ Manual (requires memorization update) |
| GPG passphrase | Annually (key expiration) | ❌ Manual (linked to key rotation) |
| Production sudo passwords | Quarterly | ✅ Ansible playbook |
| Database passwords | Quarterly | ✅ SQL script + Ansible |
| API keys | Annually OR on provider security advisory | ⚠️ Semi-automated (provider-dependent) |
| TLS/SSL certificate private keys | On certificate renewal (13 months) | ✅ Certbot automation |

**Rotation Playbook Example**:

```yaml
# ansible/rotate_sudo_passwords.yml
---
- name: Rotate sudo passwords for all production servers
  hosts: production
  become: yes
  
  tasks:
    - name: Generate new random password
      set_fact:
        new_sudo_password: "{{ lookup('password', '/dev/null chars=ascii_letters,digits,punctuation length=32') }}"
      delegate_to: localhost
      run_once: yes
    
    - name: Update user password
      user:
        name: "{{ server_sudo_user }}"
        password: "{{ new_sudo_password | password_hash('sha512') }}"
      no_log: true
    
    - name: Store new password in Bitwarden
      command: >
        bw edit item "{{ inventory_hostname }} - sudo password"
        --password "{{ new_sudo_password }}"
      environment:
        BW_SESSION: "{{ lookup('env', 'BW_SESSION') }}"
      delegate_to: localhost
      run_once: yes
      no_log: true
    
    - name: Log rotation event
      lineinfile:
        path: /var/log/password_rotation.log
        line: "{{ ansible_date_time.iso8601 }} - sudo password rotated for {{ server_sudo_user }}"
        create: yes
```

+++

## Section 6: Compliance and Auditing

+++

### 6.1 ISO 27001 Annex A.9.4.3 Compliance

+++

**Control**: Password management systems

**Requirements**:

| **ISO Requirement** | **Implementation** | **Evidence** |
|--------------------|-------------------|--------------|
| Use password management system | Bitwarden (team organization) | Organization settings screenshot |
| Enforce strong password policy | 32-char random OR 8-word Diceware | Password generation scripts |
| Select quality passwords | OpenSSL rand (cryptographic entropy) | Entropy calculation verification |
| Separate user and privileged passwords | Collections: "User Accounts" vs "Admin Accounts" | Collection structure export |
| Change passwords when compromise suspected | Rotation playbook (Section 5.4) | Ansible playbook + execution logs |
| Store passwords securely | [AES-256](/security/password_management/aes_256_advanced_encryption_standard_with_a_256_bit.ipynb) encrypted vault + 2FA | Bitwarden security whitepaper |
| Do not share passwords | Individual credentials per engineer | User audit report |
| Temporary passwords changed at first logon | Force password change on user creation | Ansible playbook verification |

**Audit Preparation**:

```bash
# Generate compliance report

# 1. Export vault structure (without passwords)
bw list items --organizationid "org-id" | \
  jq 'map({name, type, collectionIds, organizationId, notes})' > \
  bitwarden_inventory_$(date +%Y%m%d).json

# 2. Export user access matrix
# Web UI: Reports → User Access Report
# Download CSV

# 3. Export event logs
# Web UI: Reports → Event Logs
# Filter: Last 90 days
# Download CSV

# 4. Generate password strength report
bw list items --organizationid "org-id" | \
  jq -r '.[] | select(.login.password) | .login.password' | \
  while read password; do
    length=${#password}
    echo "Length: $length"
  done | \
  awk '{sum+=$2; count++} END {print "Average password length:", sum/count}'

# 5. Compile compliance evidence package
tar -czf iso27001_compliance_$(date +%Y%m%d).tar.gz \
  bitwarden_inventory_*.json \
  user_access_report.csv \
  event_logs.csv \
  password_rotation_logs/ \
  security_policies.pdf
```

+++

### 6.2 NIST SP 800-63B Compliance

+++

**Relevant Guidance**:

| **NIST Guideline** | **Requirement** | **Our Implementation** | **Compliant?** |
|-------------------|----------------|----------------------|----------------|
| 5.1.1.1 | Minimum 8 characters (user-chosen) | 6 Diceware words = 36+ chars | ✅ |
| 5.1.1.2 | At least 64-character maximum | Password manager supports 256+ chars | ✅ |
| 5.1.1.2 | Allow all printable ASCII + Unicode | OpenSSL rand uses full printable set | ✅ |
| 5.1.1.2 | No composition rules (e.g., "must have 1 uppercase") | Entropy-based, no artificial rules | ✅ |
| 5.1.1.2 | No mandatory periodic change | Rotation on event, not schedule | ✅ |
| 5.1.1.2 | Check against breach databases | Integration with HaveIBeenPwned (optional) | ⚠️ Recommended |
| 5.1.3 | Use approved encryption (FIPS 140-2) | AES-256-GCM (FIPS approved) | ✅ |
| 5.2.2 | Require MFA for privileged accounts | 2FA mandatory for all engineers | ✅ |

**HaveIBeenPwned Integration** (Optional):

```bash
# Check if password appears in breach databases

check_password_breached() {
    local password="$1"
    
    # Hash password with SHA-1
    local hash=$(echo -n "$password" | sha1sum | awk '{print $1}' | tr '[:lower:]' '[:upper:]')
    
    # Send first 5 characters to API (k-anonymity)
    local prefix=${hash:0:5}
    local suffix=${hash:5}
    
    # Query HaveIBeenPwned API
    local response=$(curl -s "https://api.pwnedpasswords.com/range/$prefix")
    
    # Check if suffix appears in results
    if echo "$response" | grep -q "^$suffix"; then
        local count=$(echo "$response" | grep "^$suffix" | cut -d: -f2)
        echo "⚠️  WARNING: Password found in $count breaches"
        return 1
    else
        echo "✅ Password not found in breach databases"
        return 0
    fi
}

# Test
check_password_breached "password123"
# Output: ⚠️  WARNING: Password found in 123456 breaches

check_password_breached "$(openssl rand -base64 32)"
# Output: ✅ Password not found in breach databases
```

+++

### 6.3 Quarterly Security Audit

+++

**Audit Checklist** (perform every 90 days):

```bash
#!/bin/bash
# audit_password_management.sh

echo "=== PASSWORD MANAGEMENT SECURITY AUDIT ==="
echo "Date: $(date)"
echo ""

# 1. Verify all engineers have 2FA enabled
echo "1. Checking 2FA status..."
# Web UI: Reports → User Report → Export
# Manual check: Each user has "Two-step Login: Enabled"

# 2. Check for weak master passwords (if using shared emergency vault)
echo "2. Checking for weak passwords..."
# Manual: Review password lengths in audit report
# Flag any password <77 bits entropy

# 3. Verify paper backups exist
echo "3. Verifying paper backup compliance..."
# Survey team: "Have you verified your paper backup is accessible?"
# Document responses

# 4. Check safe combinations haven't been shared
echo "4. Auditing physical security..."
# Interview: "Who knows your safe combination?"
# Expected: "Only me" OR "Me + spouse"

# 5. Review event logs for anomalies
echo "5. Analyzing event logs..."
bw export --organizationid "org-id" --format json | \
  jq -r '.[] | select(.type == "User_LoggedIn") | .date' | \
  sort | uniq -c
# Flag: Logins at unusual hours (3am-5am)

# 6. Verify no credentials older than rotation policy
echo "6. Checking credential age..."
bw list items --organizationid "org-id" | \
  jq -r '.[] | {name, revisionDate}' | \
  while read item; do
    revision_date=$(echo "$item" | jq -r '.revisionDate')
    age_days=$(( ($(date +%s) - $(date -d "$revision_date" +%s)) / 86400 ))
    if [ $age_days -gt 90 ]; then
      echo "⚠️  WARNING: $(echo "$item" | jq -r '.name') not updated in $age_days days"
    fi
  done

# 7. Test disaster recovery procedure
echo "7. Testing disaster recovery..."
# Simulate: Engineer cannot access password manager
# Verify: Can retrieve master password from paper backup
# Document: Time to recover (should be <30 minutes)

echo ""
echo "=== AUDIT COMPLETE ==="
echo "Review findings and create remediation tickets"
```

+++

## Section 7: Disaster Recovery

+++

### 7.1 Scenario: Master Password Forgotten

+++

**Recovery Procedure**:

```bash
# Time estimate: 15-30 minutes

# Step 1: Locate paper backup
# Check documented location (should be in password manager notes)
# Example: "Home safe, top drawer, combination: 15-32-7"

# Step 2: Open safe
# Enter combination: 15-32-7
# Retrieve laminated credential card

# Step 3: Read master password
# Card should contain: "correct-horse-battery-staple-mountain-river"

# Step 4: Login to password manager
bw logout
bw login your-email@example.com
# Enter master password from card
# Enter 2FA code from authenticator app

# Step 5: Verify access
bw list items --pretty
# Should display all vault items

# Step 6: Optional - Change master password
# If concerned about paper backup compromise:
bw update master-password
# Enter OLD password (from card)
# Enter NEW password (generate new Diceware passphrase)

# Step 7: Update paper backup
# Create new credential card with new master password
# Destroy old card (shred + burn)
# Store new card in safe
```

**If Paper Backup is Lost**:

```bash
# CRITICAL: This is a PERMANENT LOCKOUT scenario
# Prevention is mandatory (Section 4.2)

# If backup is lost:
# 1. Immediately verify you can still login
bw login your-email@example.com
# If successful: Create new paper backup immediately

# 2. If already locked out:
# ❌ Recovery is IMPOSSIBLE (zero-knowledge encryption)
# ✅ Create NEW password manager account
# ⚠️  ALL credentials in locked vault are LOST

# 3. Recovery actions:
# - Notify team lead immediately
# - Request re-invitation to organization vault
# - Shared credentials are safe (in organization vault)
# - Personal credentials are LOST (no recovery)

# 4. Post-incident:
# - Update password recovery documentation
# - Audit all engineers' paper backup status
# - Consider implementing Shamir's Secret Sharing (Section 3.3)
```

+++

### 7.2 Scenario: Hardware Token Lost (YubiKey)

+++

**Immediate Actions**:

```bash
# Time-critical: 1-2 hours

# Step 1: Report loss
# Notify: Team lead, security team
# Document: When/where lost, who had access

# Step 2: Revoke lost token from password manager
# Web UI: Settings → Security → Two-step Login → YubiKey
# Remove: Lost YubiKey serial number
# Verify: Backup YubiKey still registered

# Step 3: Test login with backup YubiKey
bw logout
bw login your-email@example.com
# Enter master password
# Prompt: Touch YubiKey → Touch BACKUP YubiKey
# Verify: Login successful

# Step 4: If backup YubiKey also lost (EMERGENCY)
# Web UI: Settings → Security → Two-step Login → Manage
# Disable: YubiKey 2FA temporarily
# Enable: Authenticator App 2FA (emergency fallback)

# Step 5: Order replacement YubiKey
# Purchase: 2 new YubiKeys (primary + backup)
# Delivery: 3-5 business days

# Step 6: Re-register new YubiKeys
# Web UI: Settings → Security → Two-step Login → YubiKey
# Add: Primary YubiKey
# Add: Backup YubiKey
# Test: Login with each key

# Step 7: If GPG key was on lost YubiKey
# CRITICAL: GPG key cannot be extracted from YubiKey
# Action: Generate NEW GPG key on new YubiKey
# Impact: Must re-encrypt vault password for new key
# See: Ansible Vault Handbook, Section 3.2 (Engineer Offboarding)
```

+++

### 7.3 Scenario: Safe Combination Forgotten

+++

**Recovery Procedure**:

```bash
# Step 1: Verify safe model and lock type
# Check: Purchase receipt, safe exterior label
# Example: SentrySafe SFW123GDC, electronic lock

# Step 2: Manufacturer override (Electronic locks)
# SentrySafe: Customer service can provide factory override code
# Contact: 1-800-828-1438
# Required: Proof of ownership (receipt, serial number)

# Process:
# - Call customer service
# - Provide serial number (on back of safe door)
# - Verify identity (address, purchase date)
# - Receive override code (6-digit number)
# - Enter override code: Press "1" + override code + "#"
# - Safe opens, reprogram combination

# Step 3: Mechanical combination locks (if applicable)
# Option A: Hire certified safe technician
# Cost: $150-$500
# Time: 1-3 hours

# Option B: Destructive entry (last resort)
# Cost: Safe replacement ($150-$2000)
# Use: Angle grinder, pry bar
# ⚠️  ONLY if safe contains critical credentials

# Step 4: Update documentation
# Record new combination in password manager
bw create item '{
  "type": 2,
  "name": "Home Safe Combination",
  "secureNote": {
    "type": 0
  },
  "notes": "Combination: 15-32-7\nModel: SentrySafe SFW123GDC\nSerial: 12345678\nLocation: Bedroom closet, top shelf"
}'
```

+++

### 7.4 Scenario: Password Manager Company Shutdown

+++

**Example**: Bitwarden (or any provider) ceases operations.

**Preparation** (Preventive):

```bash
# Maintain encrypted local backup

# 1. Export vault monthly
bw export --organizationid "org-id" --format encrypted_json > \
  vault_backup_$(date +%Y%m%d).json

# 2. Encrypt export with GPG
gpg --encrypt --recipient your-email@example.com \
  vault_backup_$(date +%Y%m%d).json

# 3. Store encrypted backup in multiple locations
# - Local: /mnt/backups/password_vault/
# - Cloud: Nextcloud, personal NAS
# - Offline: USB drive in safe

# 4. Verify backup is restorable
bw import encrypted_json vault_backup_20260118.json
# Test: List items, verify all credentials present
```

**Recovery Actions** (if shutdown occurs):

```bash
# Day 0: Service shutdown announced

# 1. Export all data immediately
bw export --organizationid "org-id" --format encrypted_json > \
  final_export_$(date +%Y%m%d).json

# 2. Migrate to alternative password manager
# Option A: Self-host Vaultwarden
docker run -d -p 80:80 -v /vw-data/:/data/ vaultwarden/server:latest

# Option B: Migrate to KeePassXC
bw export --format json > bitwarden_export.json
# Use KeePassXC import tool: File → Import → Bitwarden JSON

# Option C: Migrate to 1Password (commercial)
# Web UI: Import → Bitwarden → Select exported JSON

# 3. Notify team of migration
# Email: "Password manager migration in progress. New system: [X]"
# Deadline: Migrate within 7 days

# 4. Verify all credentials migrated
# Compare export record count with new vault count
old_count=$(jq '. | length' bitwarden_export.json)
new_count=$(keepassxc-cli ls team_passwords.kdbx | wc -l)
echo "Old: $old_count, New: $new_count"

# 5. Update documentation
# Search for "bitwarden" in all documentation
# Replace with new password manager name
grep -r "bitwarden" docs/ | wc -l
```

+++

## Section 8: Security Incident Response

+++

### 8.1 Incident Classification

+++

| **Severity** | **Definition** | **Example** | **Response Time** |
|-------------|---------------|-------------|------------------|
| **P0 - Critical** | Active compromise of credentials | Attacker using stolen password to access production | <1 hour |
| **P1 - High** | Suspected compromise, no confirmed misuse | YubiKey lost in public place | <4 hours |
| **P2 - Medium** | Potential exposure, low likelihood of exploitation | Paper backup visible during video call | <24 hours |
| **P3 - Low** | Policy violation, no immediate risk | Engineer shared password via Slack | <1 week |

+++

### 8.2 Incident Response Playbook

**P0 - Critical Incident**:

```bash
# Example: Production database password used by unauthorized IP

# Hour 0 (Immediate)
# 1. Isolate affected system
ssh admin@production-db-01
sudo systemctl stop postgresql
# Database now offline (halts ongoing breach)

# 2. Notify security team
# Signal: "#security-incidents" channel
# Message: "P0: Production DB password compromised. DB taken offline."

# 3. Rotate compromised credential
bw get item "Production DB - postgres password" | \
  jq -r '.id' | \
  xargs -I {} bw edit item {} --password "$(openssl rand -base64 32)"

# 4. Update database with new password
ssh admin@production-db-01
sudo -u postgres psql
ALTER USER postgres WITH PASSWORD 'NEW_PASSWORD_HERE';
\q

# 5. Restart service with new credential
sudo systemctl start postgresql

# Hour 1-2 (Investigation)
# 6. Review audit logs
# PostgreSQL: /var/log/postgresql/postgresql-*.log
# Check: Unauthorized queries, data exfiltration

# 7. Identify breach vector
# Review: SSH access logs, application logs, password manager event logs
# Determine: How did attacker obtain password?

# Hour 2-4 (Containment)
# 8. Rotate ALL credentials attacker may have accessed
# If breach vector = compromised password manager:
for item_id in $(bw list items --organizationid "org-id" | jq -r '.[].id'); do
  bw edit item $item_id --password "$(openssl rand -base64 32)"
done

# 9. Force re-authentication of all team members
# Web UI: Organization → Policies → Require Master Password on Restart
# All engineers must re-login (flushes cached sessions)

# Hour 4-8 (Recovery)
# 10. Restore database from backup (if data corrupted)
# 11. Document incident timeline
# 12. Schedule post-mortem meeting (within 48 hours)
```

**Post-Incident Report Template**:

```markdown
# Security Incident Report: [Incident ID]

## Incident Summary
- **Date**: 2026-01-18
- **Severity**: P0 - Critical
- **Affected System**: Production PostgreSQL Database
- **Impact**: 2 hours downtime, no data loss

## Timeline
- **14:23 UTC**: Unauthorized access detected (IP: 203.0.113.42)
- **14:25 UTC**: Database taken offline
- **14:30 UTC**: Password rotated
- **14:45 UTC**: Service restored
- **15:00 UTC**: Investigation began
- **16:30 UTC**: Root cause identified

## Root Cause
Engineer's laptop stolen from car. Laptop was unlocked, password manager
session active. No full-disk encryption enabled.

## Actions Taken
1. Rotated production database password
2. Reviewed audit logs (no data exfiltration detected)
3. Rotated all credentials on stolen laptop's password manager session
4. Remotely wiped laptop via MDM
5. Disabled engineer's password manager session

## Preventive Measures
1. **Implemented**: Mandatory full-disk encryption policy (FDE)
2. **Implemented**: Password manager auto-lock after 5 minutes idle
3. **Planned**: Hardware token (YubiKey) for 2FA (removes software-only risk)
4. **Planned**: Quarterly security training (physical security module)

## Lessons Learned
- FDE is critical for mobile devices
- Auto-lock timeout was too long (was 30 minutes, now 5 minutes)
- Incident response was effective (2-hour containment)

**Incident closed**: 2026-01-18 18:00 UTC
```

+++

## Section 9: Training and Best Practices

+++

### 9.1 Engineer Onboarding Training

+++

**Day 1 Training Module** (2 hours):

```markdown
# Password Management Training

+++

## Learning Objectives

+++

By the end of this training, you will be able to:
- Generate cryptographically secure passwords
- Store credentials in Bitwarden organization vault
- Create and secure physical backup of master password
- Identify prohibited password sharing methods
- Respond to password-related security incidents

+++

## Hands-On Exercises

+++

### Exercise 1: Generate Strong Passphrase (15 minutes)

+++

1. Install diceware: `uv add diceware`
2. Generate 6-word passphrase: `diceware --num 6 --wordlist en_eff`
3. Calculate entropy: Use script from Section 2.2
4. Verify entropy ≥77 bits

+++

### Exercise 2: Create Bitwarden Account (20 minutes)

+++

1. Install Bitwarden desktop app
2. Create account with generated passphrase
3. Enable 2FA (Authenticator App)
4. Accept organization invitation
5. Sync vault and verify access to "Development Servers" collection

+++

### Exercise 3: Create Paper Backup (30 minutes)

+++

1. Print credential card template (Section 4.2)
2. Fill in master password with archival pen
3. Laminate card
4. Document safe location in password manager notes

+++

### Exercise 4: Retrieve Shared Credential (15 minutes)

+++

1. Sync vault: `bw sync`
2. List organization items: `bw list items --organizationid "org-id"`
3. Retrieve password: `bw get password "Development Server 01"`
4. Use credential to SSH to server

+++

### Exercise 5: Incident Response Drill (30 minutes)

+++

Scenario: You suspect your laptop was accessed by unauthorized person.

**Your actions** (write down step-by-step):
1. ___________________________________________________________
2. ___________________________________________________________
3. ___________________________________________________________

**Correct Answer** (reveal after attempt):
1. Immediately logout of password manager on all devices
2. Change master password from trusted device
3. Notify team lead via Signal
4. Review event logs for unauthorized access
5. Rotate any credentials you accessed in past 24 hours

+++

## Quiz (must score 100%)

+++

1. What is the minimum entropy for a GPG passphrase?
   - [ ] 77 bits
   - [x] 103 bits
   - [ ] 128 bits

2. Where should you NEVER store passwords?
   - [ ] Password manager
   - [ ] Laminated paper in safe
   - [x] Slack direct message
   - [ ] Hardware token

3. How often must production sudo passwords be rotated?
   - [ ] Monthly
   - [x] Quarterly
   - [ ] Annually
   - [ ] Never (only on compromise)

4. What should you do if you forget your master password?
   - [ ] Contact Bitwarden support for reset
   - [x] Retrieve from paper backup in safe
   - [ ] Ask team lead to share their password
   - [ ] Create new account

5. What is the response time for P0 security incidents?
   - [x] <1 hour
   - [ ] <4 hours
   - [ ] <24 hours
   - [ ] <1 week
```

+++

### 9.2 Best Practices Summary

+++

**DO**:
- ✅ Use password manager for ALL credentials (no exceptions)
- ✅ Enable 2FA on password manager
- ✅ Create paper backup of master password within 24 hours
- ✅ Use cryptographic random generators (`openssl rand`)
- ✅ Rotate credentials on engineer departure (within 24 hours)
- ✅ Store paper backup in fireproof safe
- ✅ Use Bitwarden Send for one-time secret sharing
- ✅ Report suspected compromise within 1 hour
- ✅ Audit password manager quarterly
- ✅ Use hardware token (YubiKey) for high-security accounts

**DON'T**:
- ❌ Share passwords via email, Slack, SMS, phone
- ❌ Use memorable passwords for infrastructure credentials
- ❌ Store passwords in plaintext files (even encrypted)
- ❌ Reuse passwords across systems
- ❌ Disable 2FA (even temporarily)
- ❌ Photocopy or scan paper backups
- ❌ Store paper backup in desk drawer (use safe)
- ❌ Share master password with anyone (including team lead)
- ❌ Use browser password managers for work credentials
- ❌ Delay incident reporting ("I'll tell them tomorrow")

+++

## Appendix A: Quick Reference

+++

### Common Commands

+++

```bash
# Bitwarden CLI

# Login
bw login email@example.com

# Unlock vault
export BW_SESSION=$(bw unlock --raw)

# List items
bw list items --pretty

# Get password
bw get password "Server Name"

# Add item
bw create item '{"type":1,"name":"New Item","login":{"username":"user","password":"pass"}}'

# Edit item
bw edit item <item-id> --password "new-password"

# Sync
bw sync

# Logout
bw logout

# KeePassXC CLI

# Open database
keepassxc-cli open database.kdbx

# Show entry
keepassxc-cli show database.kdbx "Entry Title"

# Add entry
keepassxc-cli add database.kdbx "New Entry"

# Edit entry
keepassxc-cli edit database.kdbx "Entry Title"

# Password generation

# Random password (32 chars)
openssl rand -base64 32

# Diceware passphrase (6 words)
diceware --num 6 --wordlist en_eff

# Diceware passphrase (8 words)
diceware --num 8 --wordlist en_eff
```

+++

## Appendix B: Compliance Mapping

+++

| **Standard** | **Control** | **Implementation** | **Section** |
|-------------|------------|-------------------|-------------|
| ISO 27001 | A.9.4.3 Password management | Bitwarden + 2FA | 1.3 |
| ISO 27001 | A.18.1.3 Protection of records | Encrypted vault + backups | 4.1 |
| NIST 800-63B | 5.1.1.1 Memorized secrets | Diceware passphrase ≥77 bits | 2.2 |
| NIST 800-63B | 5.1.1.2 No composition rules | Entropy-based requirements | 2.1 |
| NIST 800-63B | 5.2.2 Multi-factor authentication | YubiKey + TOTP | 4.5 |
| CIS Controls v8 | 6.5 Centralize account management | Bitwarden organization | 3.1 |
| CIS Controls v8 | 6.2 Establish access revoking | Offboarding procedure | 5.2 |
| SOC2 | CC6.1 Logical access controls | Role-based collections | 3.2 |
| SOC2 | CC7.2 System monitoring | Event log auditing | 6.3 |

+++

## Appendix C: Glossary

+++

- **Master Password**: The single password that unlocks your password manager vault
- **Passphrase**: A password composed of multiple words (e.g., Diceware)
- **Entropy**: Measure of password randomness/unpredictability (in bits)
- **2FA/MFA**: Two-Factor/Multi-Factor Authentication
- **Zero-Knowledge**: Encryption where service provider cannot decrypt your data
- **Diceware**: Method of generating passphrases using physical dice and wordlist
- **Hardware Token**: Physical device for authentication (e.g., YubiKey)
- **Vault**: Encrypted database containing all your passwords
- **Collection**: Group of credentials in Bitwarden organization
- **Emergency Access**: Delegated access to vault during emergencies
- **Paper Backup**: Physical written copy of critical password (stored in safe)
- **Archival Paper**: Acid-free paper designed for long-term storage
- **Lamination**: Plastic coating to protect paper from water/damage
- **Fireproof Safe**: Container rated to protect contents from fire
- **SOC2 Type II**: Security audit certification for service providers

+++

## Document Changelog

+++

| **Version** | **Date** | **Author** | **Changes** |
|------------|----------|-----------|------------|
| 1.0.0 | 2026-01-18 | Vadim Rudakov | Initial production handbook |

+++

---

**END OF DOCUMENT**
