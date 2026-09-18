import pyotp
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas, security

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(user_data: schemas.UserCreate, db: Session = Depends(get_db)):
    # check if the user exists
    existing_user = db.query(models.User).filter(models.User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered")

    # Generate the MFA token secret and then directly encrypt at rest
    raw_mfa_secret = pyotp.random_base32()
    encrypted_mfa = security.encrypt_sensitive_data(raw_mfa_secret)

    new_user = models.User(
        username=user_data.username,
        hashed_password=security.hash_password(user_data.password),
        mfa_secret_encrypted=encrypted_mfa
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # default bank account information
    enc_acc_num = security.encrypt_sensitive_data(f"ACC-{new_user.id:06d}")
    new_account = models.Account(
        user_id=new_user.id,
        account_number_encrypted=enc_acc_num,
        balance=1000.0  # signup bonus
    )
    db.add(new_account)
    db.commit()

    totp_uri = pyotp.totp.TOTP(raw_mfa_secret).provisioning_uri(
        name=new_user.username,
        issuer_name="Secure Bank"
    )
    return {
        "message": "User registered successfully",
        "mfa_secret": raw_mfa_secret,
        "totp_uri": totp_uri
    }


@router.post("/login", response_model=schemas.Token)
def login(credentials: schemas.UserLogin, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == credentials.username).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    if user.is_locked:
        raise HTTPException(status_code=403, detail="Account has been locked due to multiple failed attempts")

    if not security.verify_password(credentials.password, user.hashed_password):
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= 5:
            user.is_locked = 1
        db.commit()
        raise HTTPException(status_code=401, detail="Invalid username or password")

    # Validate MFA Token
    raw_mfa_secret = security.decrypt_sensitive_data(user.mfa_secret_encrypted)
    totp = pyotp.TOTP(raw_mfa_secret)
    if not credentials.mfa_code or not totp.verify(credentials.mfa_code):
        user.failed_login_attempts += 1
        db.commit()
        raise HTTPException(status_code=401, detail="Invalid or missing MFA code")

    # Reset failure counter on success
    user.failed_login_attempts = 0
    db.commit()

    access_token = security.create_access_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}