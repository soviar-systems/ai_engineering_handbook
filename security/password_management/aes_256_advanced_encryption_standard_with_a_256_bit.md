---
jupytext:
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.18.1
kernelspec:
  name: python3
  display_name: Python 3 (ipykernel)
  language: python
---

# AES-256: Advanced Encryption Standard with a 256-bit key

+++

---

Owner: Vadim Rudakov, lefthand67@gmail.com  
Version: 0.1.0  
Birth: 2026-01-19  
Last Modified: 2026-01-19

---

+++

**AES-256** (Advanced Encryption Standard with a 256-bit key) is the gold standard of data encryption used worldwide to secure everything from top-secret government files to your VPN keys.

At its core, it is a **symmetric block cipher**. This means it uses the same secret key to both lock (encrypt) and unlock (decrypt) data, and it processes that data in fixed-size chunks called "blocks."

+++

## **How It Works: The "14 Rounds" of Scrambling**

+++

AES-256 doesn't just scramble data once; it puts every 128-bit block of data through a rigorous 14-round "washing machine" of mathematical transformations.

Each of the **14 rounds** consists of four specific steps:

1. **SubBytes:** Every byte of data is replaced by another according to a complex look-up table (S-box), like a sophisticated substitution cipher.
2. **ShiftRows:** The rows of data are shifted horizontally by different offsets to mix up the positions.
3. **MixColumns:** A mathematical formula is applied to each column to further blur the relationship between the original data and the result.
4. **AddRoundKey:** A unique "sub-key" (derived from your master 256-bit key) is combined with the data.

+++

## **Why Is It Considered "Unbreakable"?**

+++

The "256" refers to the length of the encryption key in bits. This creates an astronomical number of possible combinations:

* **Total Combinations:** $2^{256}$
* **The Number:** Approximately $1.1 \times 10^{77}$ (a 78-digit number).

:::{note}
To put this in perspective: even if you used every supercomputer on Earth simultaneously, it would take **billions of years** to try every possible key. This is why it is often called "military-grade" encryption.
:::

+++

## **Key Comparisons: AES-128 vs. AES-256**

+++

While AES-128 is also secure, AES-256 is the preferred choice for long-term security.

| Feature | AES-128 | AES-256 |
| --- | --- | --- |
| **Key Size** | 128 bits | 256 bits |
| **Rounds** | 10 rounds | 14 rounds |
| **Speed** | Faster (requires less CPU) | Slightly slower (~40% more resources) |
| **Quantum Resistance** | Potentially vulnerable | **Quantum-resistant** (remains secure) |

+++

## **Real-World Use Cases**

+++

You likely use AES-256 dozens of times a day without knowing it:

* **VPNs:** To create a secure tunnel for your internet traffic.
* **Password Managers:** Like Bitwarden or LastPass, to store your vault.
* **Messaging:** WhatsApp and Signal use it for end-to-end encryption.

+++

## **Is it future-proof?**

+++

Yes. Unlike many older algorithms (like RSA), AES-256 is considered **quantum-resistant**. Even with the eventual arrival of powerful quantum computers using Grover's Algorithm, the security of AES-256 would only be "halved" to 128-bit security—which is still effectively impossible to crack.
