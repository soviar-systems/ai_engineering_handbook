---
jupytext:
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.19.0
kernelspec:
  name: bash
  display_name: Bash
  language: bash
---

# Ansible Vault: Production Secret Management Handbook

+++

---

Owner: Vadim Rudakov, rudakow.wadim@gmail.com  
Version: 0.2.1  
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

This handbook establishes the **mandatory** secret management protocol for production Ansible deployments. All procedures are designed to meet:

- **ISO 27001 Annex A.9.4.3**: Password management systems
- **CIS Controls v8**: Control 6 - Access Control Management
- **NIST SP 800-57**: Key Management

:::{warning} Non-Negotiable Principle
Vault passwords **SHALL NEVER** exist in plaintext on any filesystem, including temporary files, backup systems, or log files.
:::

+++

## **Architecture Overview**

+++

The production secret management system uses a three-layer security model:

```
┌─────────────────────────────────────────────────────────────┐
│ Layer 1: GPG Private Key (Hardware-backed, passphrase-protected)       │
│         Protected by: OS keyring + gpg-agent caching                   │
└────────────────────┬────────────────────────────────────────┘
                         │ decrypts
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ Layer 2: Encrypted Vault Password (.vault_pass.gpg)                    │
│         Location: Git repository (version-controlled)                  │
└────────────────────┬────────────────────────────────────────┘
                         │ unlocks
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ Layer 3: Encrypted Secrets (vault.yml files)                           │
│         Contains: Passwords, API keys, certificates                    │
└─────────────────────────────────────────────────────────────┘
```

**Key Properties**:
- **Individual Accountability**: Each engineer has a unique GPG key
- **Revocability**: Departing engineers can be removed without re-encrypting vault files
- **Auditability**: GPG signature logs track who accessed vault password
- **Zero Plaintext**: Vault password exists only in encrypted form or in-memory

+++

## **Prerequisites**

+++

Before proceeding, verify your environment meets these requirements:

+++

### 1. Verify GnuPG installation (required version: 2.2+)

+++

Expected: `gpg (GnuPG) 2.4.0` or higher

```{code-cell}
gpg --version | head -n1
```

### 2. Verify Ansible installation (required version: 2.20+)

+++

Expected: `ansible [core 2.20.1]` or higher

```{code-cell}
env -u VIRTUAL_ENV uv run ansible --version | head -n1
```

### 3. Verify gpg-agent is running

+++

Expected: `<PID> /usr/bin/gpg-agent --supervised`

```{code-cell}
pgrep -a gpg-agent 
```

```{code-cell}
systemctl --user status gpg-agent.service | head -n5
```

```{code-cell}
systemctl --user start gpg-agent.service
```

```{code-cell}
pgrep -a gpg-agent 
```

### 4. Verify Git is configured

+++

```bash
git config user.email
```

Expected: `your-email@example.com (must match GPG key email)`

+++

:::{warning} If any check fails
Install the required component before continuing.
:::

+++

## **Section 1: Initial Setup (Control Machine)**

+++

This section is performed **once per engineer** on their primary control machine.

+++

### 1.1 Generate GPG Key Pair

+++

**Critical Requirements**:
- Key type: RSA 4096-bit (minimum)
- Expiration: 1 year (forces annual key rotation)
- Real name and email MUST match Git configuration

```bash
# Generate key interactively
gpg --full-generate-key

# ┌─────────────────────────────────────────────────────────┐
# │ Prompts and Required Answers:                           │
# ├─────────────────────────────────────────────────────────┤
# │ Please select what kind of key you want:                │
# │ Your selection? 1 (RSA and RSA)                         │
# │                                                           │
# │ What keysize do you want? 4096                          │
# │                                                           │
# │ Key is valid for? 1y (force annual rotation)            │
# │                                                           │
# │ Real name: Your Full Name                               │
# │ Email address: your-git-email@example.com               │
# │ Comment: Ansible Vault Decryption                       │
# │                                                           │
# │ Enter passphrase: <Use password manager to generate>    │
# │ (Minimum 20 characters, mix of upper/lower/numbers/symbols) │
# └─────────────────────────────────────────────────────────┘
```

**Verify key creation**:

```bash
gpg --list-secret-keys --keyid-format LONG

# Expected output:
# sec   rsa4096/AABBCCDD11223344 2026-01-18 [SC] [expires: 2027-01-18]
#       AABBCCDD11223344AABBCCDD11223344AABBCCDD
# uid                 [ultimate] Your Full Name (Ansible Vault Decryption) <your-git-email@example.com>
# ssb   rsa4096/55667788AABBCCDD 2026-01-18 [E]
```

**Record your key ID**: The 16-character string after `rsa4096/` (e.g., `AABBCCDD11223344`)

+++

### 1.2 Configure GPG Agent Caching

Prevent excessive passphrase prompts during active development:

```bash
# Create/edit GPG agent configuration
mkdir -p ~/.gnupg
chmod 700 ~/.gnupg

cat >> ~/.gnupg/gpg-agent.conf <<EOF
# Cache passphrase for 8 hours (28800 seconds)
default-cache-ttl 28800
max-cache-ttl 28800

# Use pinentry for secure passphrase entry
pinentry-program /usr/bin/pinentry-curses
EOF

# Reload agent
gpg-connect-agent reloadagent /bye
```

+++

### 1.3 Generate Vault Password

**CRITICAL**: The vault password MUST be cryptographically random. Do NOT use memorable passwords.

```bash
# Generate 256-bit random password
openssl rand -base64 32 > /tmp/vault_password.txt

# Verify strength (should output: ~44 characters)
wc -c /tmp/vault_password.txt
```

+++

### 1.4 Encrypt Vault Password with GPG

```bash
# Navigate to Ansible project root
cd /path/to/ansible/project

# Encrypt vault password
cat /tmp/vault_password.txt | gpg --encrypt \
  --recipient your-git-email@example.com \
  --output .vault_pass.gpg

# Verify encryption
file .vault_pass.gpg
# Expected: .vault_pass.gpg: GPG encrypted data

# MANDATORY: Secure delete plaintext password
shred -u /tmp/vault_password.txt

# Verify deletion
ls /tmp/vault_password.txt 2>&1
# Expected: ls: cannot access '/tmp/vault_password.txt': No such file or directory
```

+++

### 1.5 Create Vault Decryption Script

This script allows Ansible to decrypt the vault password automatically:

```bash
cat > .vault_pass_decrypt.sh <<'EOF'
#!/bin/bash
# Ansible Vault Password Decryption Script
# This script decrypts .vault_pass.gpg using the engineer's GPG private key

set -euo pipefail

# Verify .vault_pass.gpg exists
if [[ ! -f .vault_pass.gpg ]]; then
    echo "ERROR: .vault_pass.gpg not found" >&2
    exit 1
fi

# Decrypt and output to stdout (Ansible reads from stdout)
gpg --decrypt --quiet .vault_pass.gpg 2>/dev/null

# Exit codes:
# 0 = success
# 1 = file not found
# 2 = GPG decryption failed (wrong key, no access, etc.)
EOF

chmod +x .vault_pass_decrypt.sh
```

+++

### 1.6 Configure Ansible

```bash
# Create/edit ansible.cfg in project root
cat >> ansible.cfg <<EOF

[defaults]
# Use GPG-decrypted vault password
vault_password_file = ./.vault_pass_decrypt.sh

# Prevent accidental logging of vault variables
no_log = True
EOF
```

+++

### 1.7 Update .gitignore

Ensure the decryption script is NOT committed (it's environment-specific):

```bash
cat >> .gitignore <<EOF

# Ansible Vault - Local Decryption Script
.vault_pass_decrypt.sh

# Ansible Vault - NEVER commit plaintext passwords
*.vault_pass
.ansible_vault_pass
vault_password.txt
EOF
```

+++

### 1.8 Commit GPG-Encrypted Vault Password

```bash
# Add encrypted vault password to Git
git add .vault_pass.gpg ansible.cfg .gitignore

# Commit
git commit -m "Add GPG-encrypted vault password management"

# Verify .vault_pass.gpg is tracked
git ls-files | grep vault_pass.gpg
# Expected: .vault_pass.gpg
```

+++

## Section 2: Creating and Managing Vault Files

+++

### 2.1 Variable Organization Strategy

Use the **Variable Mapping Pattern** to separate public and secret data:

```
group_vars/
├── all/
│   └── vars.yml          # Public variables (committed)
├── production/
│   ├── vars.yml          # Environment-specific public vars
│   └── vault.yml         # ENCRYPTED secrets
└── clients/
    ├── vars.yml
    └── vault.yml         # ENCRYPTED secrets
```

**Public File** (`group_vars/production/vars.yml`):
```yaml
---
# Public variables that reference vault variables
server_sudo_user: "{{ vault_server_sudo_user }}"
server_ssh_port: "{{ vault_server_ssh_port }}"
database_password: "{{ vault_database_password }}"
```

**Secret File** (`group_vars/production/vault.yml`) - **ENCRYPTED**:
```yaml
---
# Actual secret values
vault_server_sudo_user: admin
vault_server_ssh_port: 2222
vault_database_password: "xK9m#Qp2$vL8@nR4"
```

+++

### 2.2 Creating New Vault File

```bash
# Create and encrypt in one command
ansible-vault create group_vars/production/vault.yml

# This will:
# 1. Decrypt .vault_pass.gpg using your GPG key
# 2. Use the vault password to create an encrypted file
# 3. Open your default editor (vim/nano) in decrypted mode
# 4. Automatically re-encrypt when you save and exit
```

**In the editor, add your secrets**:
```yaml
---
vault_server_sudo_user: admin
vault_sudo_password: "GeneratedStrongPassword123!"
vault_server_podman_user: containers
vault_podman_password: "AnotherStrongPassword456!"
vault_ssh_public_key: "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQC..."
vault_server_ssh_port: 2222
```

**Save and exit** (`:wq` in vim, `Ctrl+X` then `Y` in nano)

+++

### 2.3 Viewing Encrypted Vault Files

```bash
# View without editing
ansible-vault view group_vars/production/vault.yml

# Output is decrypted content printed to terminal
# File remains encrypted on disk
```

+++

### 2.4 Editing Existing Vault Files

```bash
# Edit encrypted file
ansible-vault edit group_vars/production/vault.yml

# This will:
# 1. Decrypt the file temporarily
# 2. Open in your editor
# 3. Re-encrypt automatically when you save
```

**NEVER do this**:
```bash
# ❌ WRONG - Decrypts file permanently
ansible-vault decrypt group_vars/production/vault.yml

# ❌ DANGER - Leaves secrets in plaintext
vim group_vars/production/vault.yml
```

+++

### 2.5 Encrypting Existing Files

If you have a plaintext file with secrets:

```bash
# Encrypt existing file in-place
ansible-vault encrypt group_vars/production/vault.yml

# Verify encryption
head -n1 group_vars/production/vault.yml
# Expected: $ANSIBLE_VAULT;1.1;AES256
```

+++

### 2.6 Encrypting Individual Strings

For secrets embedded in non-vault YAML files:

```bash
# Encrypt a single string
ansible-vault encrypt_string 'my_secret_value' --name 'vault_api_key'

# Output (copy this into your YAML):
# vault_api_key: !vault |
#           $ANSIBLE_VAULT;1.1;AES256
#           66386439653765326662616436633266...
```

**Usage in playbook**:
```yaml
# roles/api_service/defaults/main.yml
api_key: !vault |
          $ANSIBLE_VAULT;1.1;AES256
          66386439653765326662616436633266...
```

+++

## Section 3: Team Collaboration

+++

### 3.1 Adding New Team Members

**Step 1: New engineer generates their GPG key** (Section 1.1)

**Step 2: New engineer exports public key**:
```bash
# On new engineer's machine
gpg --export --armor your-email@example.com > your_name_public_key.asc

# Send this file to project maintainer via secure channel
# (e.g., encrypted email, secure file share)
```

**Step 3: Project maintainer imports and trusts key**:
```bash
# On maintainer's machine
gpg --import new_engineer_public_key.asc

# Verify import
gpg --list-keys new-engineer@example.com

# Set trust level (required for encryption)
gpg --edit-key new-engineer@example.com
# In GPG prompt:
gpg> trust
# Select: 5 (I trust ultimately)
gpg> quit
```

**Step 4: Maintainer re-encrypts vault password for multiple recipients**:
```bash
# Decrypt current vault password to temporary file
gpg --decrypt .vault_pass.gpg > /tmp/vault_pass_temp.txt

# Re-encrypt for both maintainer AND new engineer
cat /tmp/vault_pass_temp.txt | gpg --encrypt \
  --recipient maintainer@example.com \
  --recipient new-engineer@example.com \
  --output .vault_pass.gpg

# Secure delete temporary file
shred -u /tmp/vault_pass_temp.txt

# Commit updated .vault_pass.gpg
git add .vault_pass.gpg
git commit -m "Grant vault access to new-engineer@example.com"
git push
```

**Step 5: New engineer pulls and configures**:
```bash
# On new engineer's machine
git pull

# Create decryption script (Section 1.5)
cat > .vault_pass_decrypt.sh <<'EOF'
#!/bin/bash
gpg --decrypt --quiet .vault_pass.gpg 2>/dev/null
EOF
chmod +x .vault_pass_decrypt.sh

# Test access
ansible-vault view group_vars/production/vault.yml
# Should display decrypted content without password prompt
```

+++

### 3.2 Removing Team Members (Offboarding)

**CRITICAL**: This process MUST be completed within 24 hours of engineer departure.

**Step 1: Revoke GPG access to vault password**:
```bash
# On maintainer's machine
# Decrypt vault password
gpg --decrypt .vault_pass.gpg > /tmp/vault_pass_temp.txt

# Re-encrypt WITHOUT departed engineer's key
cat /tmp/vault_pass_temp.txt | gpg --encrypt \
  --recipient remaining-engineer-1@example.com \
  --recipient remaining-engineer-2@example.com \
  --output .vault_pass.gpg

# Secure delete
shred -u /tmp/vault_pass_temp.txt

# Commit revocation
git add .vault_pass.gpg
git commit -m "Revoke vault access for departed-engineer@example.com"
git push
```

**Step 2: Rotate all secrets** (MANDATORY):

Even though the departed engineer can no longer decrypt `.vault_pass.gpg`, they may have cached the vault password. Therefore:

```bash
# 1. Generate NEW vault password
openssl rand -base64 32 > /tmp/new_vault_password.txt

# 2. Rekey all vault files with new password
export OLD_VAULT_PASS=$(gpg --decrypt .vault_pass.gpg)
export NEW_VAULT_PASS=$(cat /tmp/new_vault_password.txt)

# For each vault file:
ansible-vault rekey \
  --vault-id old@<(echo "$OLD_VAULT_PASS") \
  --vault-id new@<(echo "$NEW_VAULT_PASS") \
  group_vars/production/vault.yml

# Repeat for group_vars/clients/vault.yml, etc.

# 3. Encrypt new vault password with GPG
cat /tmp/new_vault_password.txt | gpg --encrypt \
  --recipient remaining-engineer-1@example.com \
  --recipient remaining-engineer-2@example.com \
  --output .vault_pass.gpg

# 4. Secure delete
shred -u /tmp/new_vault_password.txt
unset OLD_VAULT_PASS NEW_VAULT_PASS

# 5. Commit changes
git add .vault_pass.gpg group_vars/*/vault.yml
git commit -m "Rotate vault password and secrets after engineer departure"
git push
```

**Step 3: Rotate actual secrets inside vault files**:

```bash
# Edit each vault file and change:
# - vault_sudo_password (generate new password)
# - vault_podman_password (generate new password)
# - vault_ssh_public_key (if departed engineer had server access)
# - Any API keys/tokens the departed engineer could have copied

ansible-vault edit group_vars/production/vault.yml
# Change all values, save, commit
```

+++

### 3.3 Multi-Environment Access Control

If engineers should have different access levels (e.g., all engineers access `dev`, only senior engineers access `prod`):

**Strategy**: Use separate vault passwords for each environment.

```bash
# Create separate GPG-encrypted vault passwords
cat /tmp/dev_vault_password.txt | gpg --encrypt \
  --recipient junior-dev@example.com \
  --recipient senior-dev@example.com \
  --output .vault_pass_dev.gpg

cat /tmp/prod_vault_password.txt | gpg --encrypt \
  --recipient senior-dev@example.com \
  --output .vault_pass_prod.gpg

# Create environment-specific decryption scripts
cat > .vault_pass_dev_decrypt.sh <<'EOF'
#!/bin/bash
gpg --decrypt --quiet .vault_pass_dev.gpg 2>/dev/null
EOF

cat > .vault_pass_prod_decrypt.sh <<'EOF'
#!/bin/bash
gpg --decrypt --quiet .vault_pass_prod.gpg 2>/dev/null
EOF

chmod +x .vault_pass_*_decrypt.sh

# Update ansible.cfg to use vault IDs
cat >> ansible.cfg <<EOF
[defaults]
vault_identity_list = dev@./.vault_pass_dev_decrypt.sh, prod@./.vault_pass_prod_decrypt.sh
EOF

# Encrypt vault files with specific IDs
ansible-vault encrypt group_vars/dev/vault.yml --vault-id dev
ansible-vault encrypt group_vars/prod/vault.yml --vault-id prod
```

**Result**: Junior engineers can decrypt `dev` vaults but get "decryption failed" error for `prod` vaults.

+++

## Section 4: CI/CD Integration

+++

### 4.1 GitLab CI/CD Setup

**Step 1: Export GPG private key**:

```bash
# On your machine (use a dedicated CI/CD GPG key, not your personal key)
gpg --export-secret-keys --armor CI_KEY_ID > ci_gpg_private_key.asc
```

**Step 2: Add to GitLab CI/CD Variables**:

1. Navigate to **Settings → CI/CD → Variables**
2. Click **Add Variable**
3. Configure:
   - **Key**: `GPG_PRIVATE_KEY`
   - **Value**: (paste contents of `ci_gpg_private_key.asc`)
   - **Type**: File
   - **Protected**: ✅ (only accessible on protected branches)
   - **Masked**: ❌ (too long for masking, but protected by branch restrictions)

**Step 3: Create `.gitlab-ci.yml`**:

```yaml
variables:
  ANSIBLE_VAULT_PASSWORD_FILE: ./.vault_pass_decrypt.sh

stages:
  - validate
  - deploy

before_script:
  # Import GPG private key from CI/CD variable
  - gpg --import --batch --yes "$GPG_PRIVATE_KEY"
  
  # Verify key imported successfully
  - gpg --list-secret-keys
  
  # Create decryption script
  - |
    cat > .vault_pass_decrypt.sh <<'EOF'
    #!/bin/bash
    gpg --decrypt --quiet .vault_pass.gpg 2>/dev/null
    EOF
  - chmod +x .vault_pass_decrypt.sh

syntax-check:
  stage: validate
  script:
    - ansible-playbook -i inventory/production.ini site.yml --syntax-check
  only:
    - merge_requests
    - main

deploy-production:
  stage: deploy
  script:
    - ansible-playbook -i inventory/production.ini site.yml
  only:
    - main
  when: manual
  environment:
    name: production
```

+++

### 4.2 GitHub Actions Setup

**Step 1: Add GPG private key as secret**:

1. Navigate to **Settings → Secrets and variables → Actions**
2. Click **New repository secret**
3. Configure:
   - **Name**: `GPG_PRIVATE_KEY`
   - **Value**: (paste contents of `ci_gpg_private_key.asc`)

**Step 2: Create `.github/workflows/deploy.yml`**:

```yaml
name: Ansible Deploy

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install Ansible
        run: pip install ansible
      
      - name: Import GPG key
        run: |
          echo "${{ secrets.GPG_PRIVATE_KEY }}" | gpg --import --batch --yes
          gpg --list-secret-keys
      
      - name: Create vault decryption script
        run: |
          cat > .vault_pass_decrypt.sh <<'EOF'
          #!/bin/bash
          gpg --decrypt --quiet .vault_pass.gpg 2>/dev/null
          EOF
          chmod +x .vault_pass_decrypt.sh
      
      - name: Syntax check
        run: ansible-playbook -i inventory/production.ini site.yml --syntax-check
      
      - name: Deploy (manual approval required)
        if: github.event_name == 'push' && github.ref == 'refs/heads/main'
        run: ansible-playbook -i inventory/production.ini site.yml
        environment: production
```

+++

## Section 5: Security Hardening

+++

### 5.1 Pre-Commit Hooks for Secret Detection

Prevent accidental secret leakage in commits:

```bash
# Install pre-commit framework
uv add pre-commit

# Create .pre-commit-config.yaml
cat > .pre-commit-config.yaml <<EOF
repos:
  # Detect hardcoded secrets
  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.4.0
    hooks:
      - id: detect-secrets
        args: ['--baseline', '.secrets.baseline']
        exclude: ^\.vault_pass\.gpg$

  # Custom hooks
  - repo: local
    hooks:
      # Verify all vault.yml files are encrypted
      - id: vault-encryption-check
        name: Verify vault files are encrypted
        entry: bash -c 'for f in \$(find . -name "vault.yml" -o -name "vault.yaml"); do head -n1 "\$f" | grep -q "^\\\$ANSIBLE_VAULT" || { echo "ERROR: \$f is not encrypted"; exit 1; }; done'
        language: system
        pass_filenames: false
      
      # Block commits with plaintext passwords
      - id: no-plaintext-passwords
        name: Detect plaintext passwords in diff
        entry: bash -c 'git diff --cached | grep -iE "(password|secret|api[_-]?key).*[:=].*['\''\"]\\w{8,}" && { echo "ERROR: Plaintext password detected"; exit 1; } || exit 0'
        language: system
        pass_filenames: false
      
      # Prevent committing GPG private keys
      - id: no-gpg-private-keys
        name: Block GPG private key commits
        entry: bash -c 'git diff --cached | grep -q "BEGIN PGP PRIVATE KEY BLOCK" && { echo "ERROR: GPG private key detected"; exit 1; } || exit 0'
        language: system
        pass_filenames: false
EOF

# Initialize detect-secrets baseline
detect-secrets scan > .secrets.baseline

# Install hooks
pre-commit install

# Test
pre-commit run --all-files
```

+++

### 5.2 Prevent Vault Variable Logging

Add `no_log: true` to tasks using vault variables:

```yaml
# ❌ INSECURE - Logs password in -vvv mode
- name: Set user password
  ansible.builtin.user:
    name: admin
    password: "{{ vault_sudo_password | password_hash('sha512') }}"

# ✅ SECURE - Prevents logging
- name: Set user password
  ansible.builtin.user:
    name: admin
    password: "{{ vault_sudo_password | password_hash('sha512') }}"
  no_log: true
```

**Global Configuration** (ansible.cfg):
```ini
[defaults]
no_log = True
```

+++

### 5.3 GPG Key Backup and Recovery

**Backup Procedure** (perform immediately after key generation):

```bash
# Export GPG private key
gpg --export-secret-keys --armor YOUR_KEY_ID > gpg_backup_$(date +%Y%m%d).asc

# Encrypt backup with strong passphrase
gpg --symmetric --cipher-algo AES256 gpg_backup_$(date +%Y%m%d).asc

# Result: gpg_backup_20260118.asc.gpg
# Store this file on:
# 1. Encrypted USB drive in physical safe
# 2. Company-managed secure storage (e.g., 1Password vault)
# 3. Offline backup system

# Secure delete plaintext backup
shred -u gpg_backup_$(date +%Y%m%d).asc
```

**Recovery Procedure** (if control machine is lost):

```bash
# On new machine
# 1. Retrieve encrypted backup from secure storage

# 2. Decrypt GPG backup
gpg --decrypt gpg_backup_20260118.asc.gpg > gpg_backup.asc

# 3. Import private key
gpg --import gpg_backup.asc

# 4. Verify import
gpg --list-secret-keys

# 5. Secure delete plaintext key
shred -u gpg_backup.asc

# 6. Clone project and test
git clone <project-url>
cd <project>
ansible-vault view group_vars/production/vault.yml
# Should decrypt successfully
```

+++

### 5.4 Annual GPG Key Rotation

**30 days before key expiration**:

```bash
# Check key expiration
gpg --list-keys YOUR_KEY_ID

# Extend expiration by 1 year
gpg --edit-key YOUR_KEY_ID
# In GPG prompt:
gpg> expire
# Select: 1y
gpg> save

# Update public key on keyserver (if using)
gpg --send-keys YOUR_KEY_ID

# Notify team of key update
git commit --allow-empty -m "GPG key extended to $(date -d '+1 year' +%Y-%m-%d)"
```

**If key is compromised or lost**:

```bash
# 1. Generate new GPG key (Section 1.1)

# 2. Re-encrypt vault password with new key
gpg --decrypt .vault_pass.gpg > /tmp/vault_pass_temp.txt
cat /tmp/vault_pass_temp.txt | gpg --encrypt \
  --recipient new-email@example.com \
  --output .vault_pass.gpg
shred -u /tmp/vault_pass_temp.txt

# 3. Rotate vault password (Section 3.2, Step 2)

# 4. Revoke old GPG key
gpg --gen-revoke OLD_KEY_ID > revocation_certificate.asc
gpg --import revocation_certificate.asc
gpg --send-keys OLD_KEY_ID  # Publish revocation to keyserver
```

+++

## Section 6: Troubleshooting

+++

### 6.1 Common Issues and Solutions

#### Issue: "gpg: decryption failed: No secret key"

**Cause**: `.vault_pass.gpg` is encrypted with a different GPG key than the one on your machine.

**Solution**:
```bash
# List keys that can decrypt the file
gpg --list-only .vault_pass.gpg

# If your key is not listed, request re-encryption from project maintainer
# Send your public key to maintainer (Section 3.1)
```

#### Issue: "ERROR! Decryption failed"

**Cause**: Vault file is corrupted or encrypted with different password.

**Solution**:
```bash
# Verify vault file starts with $ANSIBLE_VAULT
head -n1 group_vars/production/vault.yml

# If corrupted, restore from Git history
git log --all --full-history -- group_vars/production/vault.yml
git show COMMIT_HASH:group_vars/production/vault.yml > vault_restored.yml
ansible-vault view vault_restored.yml  # Test decryption
```

#### Issue: "gpg: public key decryption failed: Inappropriate ioctl for device"

**Cause**: GPG agent cannot prompt for passphrase.

**Solution**:
```bash
# Set GPG_TTY environment variable
export GPG_TTY=$(tty)

# Add to ~/.bashrc or ~/.zshrc
echo 'export GPG_TTY=$(tty)' >> ~/.bashrc
```

#### Issue: Pre-commit hook fails with "vault file not encrypted"

**Cause**: A `vault.yml` file was committed in plaintext.

**Solution**:
```bash
# Identify unencrypted vault files
find . -name "vault.yml" -exec sh -c 'head -n1 "$1" | grep -q "^\$ANSIBLE_VAULT" || echo "Unencrypted: $1"' _ {} \;

# Encrypt the file
ansible-vault encrypt path/to/unencrypted/vault.yml

# Commit fix
git add path/to/unencrypted/vault.yml
git commit -m "Fix: Encrypt vault file"
```

+++

### 6.2 Emergency Access (Break-Glass Procedure)

If all GPG keys are lost and vault password is unrecoverable:

**Prevention**: This should NEVER happen if backup procedures (Section 5.3) are followed.

**Recovery (requires vault password from external source)**:

```bash
# 1. Obtain vault password from secure backup
#    (e.g., password manager, printed backup in safe)

# 2. Temporarily use plaintext password file
echo "recovered_vault_password" > /tmp/temp_vault_pass
chmod 600 /tmp/temp_vault_pass

# 3. Configure Ansible to use it
ansible-vault view \
  --vault-password-file=/tmp/temp_vault_pass \
  group_vars/production/vault.yml

# 4. Immediately rotate to new GPG-based system
#    - Generate new GPG key (Section 1.1)
#    - Create new vault password (Section 1.3)
#    - Rekey all vault files
ansible-vault rekey \
  --vault-password-file=/tmp/temp_vault_pass \
  group_vars/production/vault.yml

# 5. Secure delete temporary password file
shred -u /tmp/temp_vault_pass
```

+++

## Section 7: Compliance and Auditing

+++

### 7.1 Security Audit Checklist

Perform this audit quarterly:

- [ ] All `vault.yml` files start with `$ANSIBLE_VAULT` (encrypted)
- [ ] No files named `.ansible_vault_pass` or `vault_password.txt` exist
- [ ] `.vault_pass.gpg` is tracked in Git
- [ ] `.vault_pass_decrypt.sh` is in `.gitignore`
- [ ] GPG keys expire within 1 year
- [ ] All team members have backed up their GPG keys (Section 5.3)
- [ ] Pre-commit hooks are installed and passing
- [ ] CI/CD pipelines use protected GPG private key variable
- [ ] `no_log: true` is present on all tasks using vault variables
- [ ] Departed engineers' GPG access has been revoked (Section 3.2)

**Audit Command**:
```bash
# Run automated security checks
bash <<'EOF'
echo "=== Vault File Encryption Check ==="
find . -name "vault.yml" -o -name "vault.yaml" | while read f; do
  if head -n1 "$f" | grep -q "^\$ANSIBLE_VAULT"; then
    echo "✓ $f is encrypted"
  else
    echo "✗ $f is NOT encrypted"
  fi
done

echo ""
echo "=== Plaintext Password Check ==="
if find . -name ".ansible_vault_pass" -o -name "vault_password.txt" | grep -q .; then
  echo "✗ Plaintext password files found"
  find . -name ".ansible_vault_pass" -o -name "vault_password.txt"
else
  echo "✓ No plaintext password files"
fi

echo ""
echo "=== GPG Encrypted Vault Password Check ==="
if [[ -f .vault_pass.gpg ]]; then
  echo "✓ .vault_pass.gpg exists"
else
  echo "✗ .vault_pass.gpg missing"
fi

echo ""
echo "=== Pre-commit Hooks Check ==="
if [[ -f .git/hooks/pre-commit ]]; then
  echo "✓ Pre-commit hooks installed"
else
  echo "✗ Pre-commit hooks NOT installed"
fi
EOF
```

+++

### 7.2 Incident Response

If a vault password or secret is compromised:

**Step 1: Immediate Actions (within 1 hour)**:
```bash
# 1. Rotate vault password
openssl rand -base64 32 > /tmp/new_vault_pass.txt

# 2. Rekey all vault files
for vault_file in $(find . -name "vault.yml" -o -name "vault.yaml"); do
  ansible-vault rekey "$vault_file"
done

# 3. Re-encrypt vault password with GPG
cat /tmp/new_vault_pass.txt | gpg --encrypt \
  --recipient team-member-1@example.com \
  --recipient team-member-2@example.com \
  --output .vault_pass.gpg

shred -u /tmp/new_vault_pass.txt
```

**Step 2: Secret Rotation (within 24 hours)**:
```bash
# Edit each vault file and change:
# - All passwords
# - All API keys
# - All SSH keys
# - All certificates

ansible-vault edit group_vars/production/vault.yml
ansible-vault edit group_vars/clients/vault.yml

# Deploy new secrets to all servers
ansible-playbook -i inventory/production.ini site.yml
```

**Step 3: Post-Incident Review (within 1 week)**:
- Document how the compromise occurred
- Update security procedures to prevent recurrence
- Review GPG key management practices
- Audit all access logs

+++

## Section 8: Reference Commands

+++

### Quick Reference Table

| **Task** | **Command** |
|----------|-------------|
| **Generate GPG key** | `gpg --full-generate-key` |
| **List GPG keys** | `gpg --list-secret-keys --keyid-format LONG` |
| **Encrypt vault password** | `cat password.txt \| gpg --encrypt --recipient email@example.com > .vault_pass.gpg` |
| **Create encrypted vault file** | `ansible-vault create group_vars/production/vault.yml` |
| **View encrypted vault file** | `ansible-vault view group_vars/production/vault.yml` |
| **Edit encrypted vault file** | `ansible-vault edit group_vars/production/vault.yml` |
| **Encrypt existing file** | `ansible-vault encrypt file.yml` |
| **Rekey vault file** | `ansible-vault rekey file.yml` |
| **Encrypt single string** | `ansible-vault encrypt_string 'value' --name 'var_name'` |
| **Backup GPG key** | `gpg --export-secret-keys --armor KEY_ID > backup.asc` |
| **Import GPG key** | `gpg --import backup.asc` |
| **Test vault decryption** | `ansible-playbook site.yml --syntax-check` |

+++

## Appendix A: Security Standards Compliance

This handbook implements the following security controls:

**ISO 27001:2022**:
- A.9.4.3: Password management systems
- A.8.24: Use of cryptography
- A.5.13: Labelling of information

**CIS Controls v8**:
- Control 6.2: Establish an access revoking process
- Control 6.3: Require MFA for externally-exposed applications
- Control 10.4: Enforce automatic device lockout

**NIST SP 800-57**:
- Section 6.2.2: Key establishment and transport
- Section 8.1.5.1.2: Individual keys vs. shared keys

**NIST SP 800-63B**:
- Section 5.1.1.2: Memorized secrets (passphrases)

+++

## Appendix B: Glossary

- **Vault Password**: The symmetric encryption key used by Ansible Vault to encrypt/decrypt vault files
- **GPG (GNU Privacy Guard)**: Asymmetric encryption tool used to protect the vault password
- **Vault File**: YAML file encrypted by Ansible Vault (contains secrets)
- **Variable Mapping**: Pattern where public YAML files reference encrypted vault variables
- **gpg-agent**: Background daemon that caches GPG passphrase
- **Vault ID**: Named vault password for multi-environment setups
- **Rekey**: Process of changing the vault password for an encrypted file
- **Symmetric Encryption**: Encryption using same key for encryption and decryption (Ansible Vault uses AES256)
- **Asymmetric Encryption**: Encryption using public/private key pairs (GPG uses RSA)

+++

## Document Changelog

| **Version** | **Date** | **Author** | **Changes** |
|------------|----------|-----------|------------|
| 1.0.0 | 2026-01-18 | Vadim Rudakov | Initial production handbook; removed all non-production patterns; added GPG-based workflow |

+++

---

**END OF DOCUMENT**

For questions or security incidents, contact: lefthand67@gmail.com
