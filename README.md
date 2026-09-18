# The Banking Portal

A secure FastAPI banking backend featuring multi-factor authentication (TOTP), Argon2 password hashing, Fernet encryption at rest, and HMAC-SHA256 request payload integrity verification.

---

## How to Run

### 1. Prerequisites
Ensure you have **Python 3.10+** installed on your system.

### 2. One-Click Setup
Run the automated setup script to install dependencies, drop/rebuild the SQLite database, and seed initial test accounts:

```bash
python setup.py
