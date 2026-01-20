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

# Bootstrap Secret Management: The "Digital Safe" (Shamir’s Secret Sharing)

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

This document addresses the **Bootstrap Secret** problem—the "First Password" required to unlock infrastructure automation.

+++

## **The Bootstrap Paradox**

+++

If you store the password for your `vault.yml` inside the `vault.yml`, you have a circular logic failure. If you store it in a plaintext file on the server, you have a security failure. The "Digital Safe" methodology solves this by moving the password into the **human collective**.

:::{seealso}
> ["Ansible Vault: Production Secret Management Handbook"](/security/password_management/03_ansible_vault_setup_step_by_step_instruction.ipynb)
:::

In a high-integrity SVA (Smallest Viable Architecture), we accept that the **Root of Trust** cannot be automated—it must be a human-driven "unsealing" event. Once unsealed, the rest of the pipeline is fully automated.

+++

## **1. The Failure of Physical-Only Storage**

+++

Traditional reliance on a physical notebook or a single safe creates a **Single Point of Failure (SPOF)**. Per **ISO 29148 (Correctness)**, a system is considered "bricked" if access depends on a single physical asset that can be lost, destroyed, or becomes inaccessible during an outage.

| Failure Mode | Impact | Technical Debt/Penalty |
| --- | --- | --- |
| **Zero Traceability** | No audit trail for access. | Compliance violation. |
| **No Redundancy** | Paper degradation or forgotten codes. | Irrecoverable data loss. |
| **Low Velocity** | Physical access requirements. | Increased MTTR (Mean Time to Recovery). |

+++

## **2. Methodology: M-of-N Threshold Cryptography**

+++

We utilize **Shamir’s Secret Sharing (SSS)**. This ensures a secret is split into $N$ fragments, requiring a quorum of $M$ fragments to reconstruct. A single fragment provides zero information about the secret.

+++

### Example Scenario: The "Shielded Vault" Workflow

+++

#### Step 1: The Generation (Admin Workstation)

+++

Imagine your team decides the "First Password" for your production server's Ansible Vault is `SuperSecret2026!`.

1. **Encrypt the Data**: You run `ansible-vault encrypt vault.yml` using that password.
2. **Split the Key**: Instead of writing `SuperSecret2026!` in a notebook, you run `ssss-split -t 3 -n 5`.
3. **Distribute Fragments**: You give one hex-fragment to five different team members (or "buckets").
4. **Create Integrity Hash**: You run `echo -n "SuperSecret2026!" | sha256sum > vault.sha256` and commit this hash to Git.

+++

#### Step 2: The Infrastructure Deployment (The "Ceremony")

+++

You are at a new Fedora workstation and need to run Ansible to configure the central server.

1. **Git Clone**: You pull the repository containing the encrypted `vault.yml` and the `vault.sha256` hash.
2. **Gather Quorum**: You ask three colleagues for their fragments.
3. **Reconstruct**: You run the [`unseal_secret.sh` script](#unseal_secret_script). It creates a RAM disk, combines the 3 fragments back into `SuperSecret2026!`, and checks it against `vault.sha256`.
4. **Deploy**: Now that you have the password in your shell's temporary memory, you run:
    ```bash
    ansible-playbook site.yml --vault-id @prompt
    ```
    and paste the verified password.

+++

### Why this works for Small Teams

+++

| Feature | Small Team Benefit | Traceability ID |
| --- | --- | --- |
| **No Server Required** | You don't need to maintain a "Vault Server" just to store the "Vault Password." | [ISO 29148: Feasibility] |
| **Resignation Safety** | If 1 person leaves, the other 4 still have enough fragments (3) to unlock and re-key. | [SWEBOK: Maintenance-3.2] |
| **Tamper Evidence** | Because you committed a SHA-256 hash, no one can "sneakily" change the master password without the Git history showing it. | [SWEBOK: Security-4.3] |

+++

## **3. Implementation Guide (Fedora/Debian)**

+++

### Phase 1: Tooling Installation

+++

Install the `ssss` (Shamir's Secret Sharing Scheme) utility on your local administrative workstation.

```bash
# Debian/Ubuntu
sudo apt-get install ssss

# Fedora
sudo dnf install ssss
```

+++

### Phase 2: Generating Fragments (3-of-5 Scheme)

+++

#### Split the Password

+++

We will split the **Ansible Master Password** into 5 fragments. Any 3 are required for recovery.

```bash
ssss-split -t 3 -n 5
```

+++

Where:
- `-t`: threshold (3 required)
- `-n`: total shares (5 generated)

+++

:::{attention} Action
Enter your high-entropy password when prompted. The utility will output 5 unique hex-encoded fragments.
:::

+++

#### Integrity Hashing [ISO 29148: Correctness]

+++

To ensure the reconstructed secret is correct before use, generate a SHA-256 hash. Store this hash in your public repository.

```bash
#!/bin/bash
# seal_vault.sh - MUST be used for all re-keying events.
read -s -p "Enter New Master Password: " NEW_PASS
echo ""

# Update Vault and Generate Hash simultaneously
ansible-vault rekey vault.yml --vault-password-file <(echo "$NEW_PASS")
echo -n "$NEW_PASS" | sha256sum | awk '{print $1}' > vault.sha256

echo "DONE: Commit both vault.yml and vault.sha256 now."
```

Generate hash of the master password (no trailing newline):

```bash
 echo -n "YOUR_MASTER_PASSWORD" | sha256sum > bootstrap.hash
```

* **Action**: Commit `bootstrap.sha256` to your Git repository. It contains no secret data, only a fingerprint of the correct password.
* **Validation**: During recovery, after `ssss-combine` provides an output, the team must run `echo -n "RECONSTRUCTED_OUTPUT" | sha256sum` and compare it to the committed hash.

:::{note} During recovery, if ssss-combine produces a string that does not match this hash, a fragment was likely entered incorrectly.
:::

+++

### Phase 3: Strategic Distribution [SWEBOK: Security-4.3]

+++

To ensure fault tolerance and collusion resistance, distribute fragments across disparate "buckets":

1. **Fragment A (Physical):** Printed and stored in the primary office safe.
2. **Fragment B (Digital/Lead):** Encrypted via GPG for the Lead Architect.
3. **Fragment C (Digital/Sec):** Encrypted via GPG for the Security Officer.
4. **Fragment D (Manager):** Stored in a corporate password manager (e.g., Bitwarden).
5. **Fragment E (Emergency):** Stored with the CTO or at an offsite disaster recovery location.

+++

## **4. Recovery Protocol (The "Unseal" Process)**

+++

To reconstruct the master password during a system-wide recovery or initial deployment:

1. Gather at least **3** fragment holders.
2. Execute the combination command:
    ```bash
     ssss-combine -t 3
    ```
    
    :::{tip}
    Use a leading space in Bash to avoid history logging if `HISTCONTROL=ignorespace` is set).
    :::
3. Input the fragments as prompted. The original secret will be rendered.

+++

## **5. The Reconstruction Ceremony**

+++

To mitigate the risk of keyloggers and memory scraping, follow these constraints:
1. **Isolated Environment**: Use a Live-USB or air-gapped Fedora/Debian instance.
2. **Volatile Storage**: Perform all operations in `/dev/shm` (RAM disk).
3. **Multi-Person Input**: Each fragment holder must personally type their fragment into the terminal to ensure no single person sees the full quorum.

**Fragment Health Audit**

Perform a "Partial Ceremony" every 90-180 days. Fragment holders must verify they can access and decrypt their individual fragments (via GPG or Bitwarden) without performing a full reconstruction.

* **The Environment**: Reconstruction should occur on a "Clean Room" machine (e.g., a Fedora Live USB or a tmpfs) to ensure no keyloggers or swap-file leaks persist.
* **The Input**: Each fragment holder should physically type their own fragment. No one should ever email or Slack a fragment to a single "operator".
* **The Trade-off**: [Security / Overhead]. This consumes 15 minutes of team time twice a year but prevents "Secret Decay" where a fragment holder realizes they lost their GPG passphrase only during a real emergency.

* **The Strategy**: Use a RAM-backed filesystem for the operation.
```bash
# Create a temporary RAM disk (Fedora/Debian)
sudo mount -t tmpfs -o size=10M tmpfs /mnt/secure_work
cd /mnt/secure_work
# Perform ssss-combine here...
cd ~
sudo umount /mnt/secure_work
```

**The Benefit**: This ensures that even if the OS is not rebooted, the secret fragments never touch the physical disk platter or SSD cells.

+++

## **6. Pitfalls & Technical Debt**

+++

:::{important} Fragment Rotation
SSS fragments do not expire. If a fragment holder leaves the organization, the secret must be reconstructed and a **new split** performed to revoke the validity of the old fragment set.
:::

* **Entropy Warning:** SSS does not strengthen a weak password; it only distributes it. Ensure the base secret is  characters.
* **History Leaks:** Always verify shell history is disabled or cleaned after a reconstruction event to prevent fragments from persisting in plaintext on the local disk.

+++

(unseal_secret_script)=
## **Appendix A:** High-Integrity Reconstruction Script (SVA-Compliant)

+++

:::{error} Not tested!
:::

This script automates the creation of a volatile workspace in RAM, performs the reconstruction, and validates the output against your integrity hash. This minimizes **Technical Debt** by ensuring the secret never touches the physical disk and prevents "garbage" output from being used.

+++

### The Pattern

+++

#### 'unseal_secret.sh'

+++

```bash
#!/bin/bash
# Description: Securely reconstructs the Bootstrap Secret in RAM.
# Requirements: ssss, coreutils, sudo (for tmpfs)
# [ISO 29148: Verifiability]

set -eu

SECURE_DIR="/mnt/secure_unseal"
HASH_FILE="bootstrap.sha256" # Path to your committed hash

# 1. Setup RAM-backed filesystem (tmpfs)
echo "Creating volatile memory workspace..."
sudo mkdir -p $SECURE_DIR
sudo mount -t tmpfs -o size=1M,mode=700 tmpfs $SECURE_DIR

trap 'sudo umount $SECURE_DIR && sudo rm -rf $SECURE_DIR && echo "Cleanup complete."' EXIT

# 2. Perform Reconstruction
echo "Enter 3 fragments for reconstruction:"
# Leading space prevents history logging if HISTCONTROL=ignorespace is set
export HISTCONTROL=ignorespace
 RECONSTRUCTED_SECRET=$(ssss-combine -t 3 2>/dev/null)

# 3. Integrity Check [SWEBOK: Security-4.3]
if [ -f "$HASH_FILE" ]; then
    EXPECTED_HASH=$(cat "$HASH_FILE" | awk '{print $1}')
    ACTUAL_HASH=$(echo -n "$RECONSTRUCTED_SECRET" | sha256sum | awk '{print $1}')

    if [ "$EXPECTED_HASH" == "$ACTUAL_HASH" ]; then
        echo -e "\033[0;32m[SUCCESS]\033[0m Secret integrity verified."
        echo "The reconstructed password is: $RECONSTRUCTED_SECRET"
    else
        echo -e "\033[0;31m[FAILURE]\033[0m Hash mismatch! Fragments are corrupted or incorrect."
        exit 1
    fi
else
    echo "Warning: No $HASH_FILE found. Proceeding without verification."
    echo "Reconstructed: $RECONSTRUCTED_SECRET"
fi
```

+++

#### The "Unsealing" Wrapper (Enforces the Quorum)

+++

```bash
#!/bin/bash
# unseal_and_run.sh - Prevents execution if protocol was bypassed.
set -e

# Reconstruct into variable (RAM only)
SECRET=$(ssss-combine -t 3 2>/dev/null)

# Detect Manual Bypass/Silent Re-key [SWEBOK: Security-4.3]
ACTUAL_HASH=$(echo -n "$SECRET" | sha256sum | awk '{print $1}')
EXPECTED_HASH=$(cat vault.sha256 | awk '{print $1}')

if [ "$ACTUAL_HASH" != "$EXPECTED_HASH" ]; then
    echo "INTEGRITY ERROR: vault.sha256 does not match. Protocol bypassed!"
    exit 1
fi

ansible-playbook "$@" --vault-password-file <(echo "$SECRET")
```

+++

If a user runs a raw `rekey` and forgets to update the hash, the *next* person trying to run the deployment will be blocked. This is the intended behavior: **Stop on Integrity Failure**.

+++

### The Trade-off: [Security / Persistence]

+++

By using `tmpfs` and an `EXIT` trap, the secret is wiped from the machine as soon as the script finishes. The consequence for your local stack is that you must have `sudo` privileges to mount the RAM disk, and you cannot "copy-paste" this password into a permanent file without violating the security protocol.

| Action Item | Technical Traceability |
| --- | --- |
| **Verify Hash** | Ensures the quorum reached a valid mathematical result. |
| **RAM Mounting** | Prevents secret leakage to swap space or unallocated disk sectors. |
| **Trap Execution** | Guarantees cleanup even if the script is interrupted (Ctrl+C). |

+++

### Security Implications

+++

* **Shoulder Surfing**: The script prints the password to the terminal. In a "Ceremony" setting, ensure only authorized personnel are present.
* **Clipboard Poisoning**: Avoid copying the output to a clipboard manager that saves history.
