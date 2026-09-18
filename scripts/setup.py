import sys
import os
import subprocess

# run: python scripts/setup.py


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


def run_command(command):
    print(f"[*] Running: {command}")
    result = subprocess.run(command, shell=True)
    if result.returncode != 0:
        print(f"[!] Error executing {command}")
        sys.exit(1)


def setup_environment():
    print("=== B207 Environment & Database Setup ===")

    # installing packages / dependencies
    run_command(f'"{sys.executable}" -m pip install -r requirements.txt')

    # importing base and module from database
    from app.database import engine, Base, SessionLocal
    import app.models as models  # ensures the attachment of models
    from app import security
    import pyotp

    print("[*] Initializing SQLite database tables...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    # print detected tables to verify registration
    print(f"[*] Tables registered in metadata: {list(Base.metadata.tables.keys())}")

    # here are the preset user credentials with preset bank balances for the sake of testing.
    print("[*] Seeding initial test data...")
    db = SessionLocal()

    try:
        mfa_secret_1 = pyotp.random_base32()
        user1 = models.User(
            username="alice",
            hashed_password=security.hash_password("Password123!"),
            mfa_secret_encrypted=security.encrypt_sensitive_data(mfa_secret_1)
        )
        db.add(user1)
        db.commit()
        db.refresh(user1)

        acc1 = models.Account(
            user_id=user1.id,
            account_number_encrypted=security.encrypt_sensitive_data("ACC-000001"),
            balance=5000.00
        )
        db.add(acc1)

        mfa_secret_2 = pyotp.random_base32()
        user2 = models.User(
            username="bob",
            hashed_password=security.hash_password("SecurePass456!"),
            mfa_secret_encrypted=security.encrypt_sensitive_data(mfa_secret_2)
        )
        db.add(user2)
        db.commit()
        db.refresh(user2)

        acc2 = models.Account(
            user_id=user2.id,
            account_number_encrypted=security.encrypt_sensitive_data("ACC-000002"),
            balance=1200.00
        )
        db.add(acc2)

        db.commit()
        print("\n[✔] Setup Completed Successfully!")
        print(f"Demo User 'alice' MFA Secret: {mfa_secret_1}")
        print(f"Demo User 'bob' MFA Secret: {mfa_secret_2}")
        print("\nRun application using: uvicorn app.main:app --reload")

    except Exception as e:
        db.rollback()
        print(f"\n[!] Error during database seeding: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    setup_environment()