from typing import List
from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas, security

router = APIRouter(prefix="/api/banking", tags=["Banking"])

@router.get("/accounts", response_model=List[schemas.AccountOut])
def get_user_accounts(
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(get_db)
):
    accounts = db.query(models.Account).filter(models.Account.user_id == current_user.id).all()
    results = []
    for acc in accounts:
        results.append({
            "id": acc.id,
            "account_number": security.decrypt_sensitive_data(acc.account_number_encrypted),
            "balance": acc.balance
        })
    return results

@router.post("/transfer", response_model=schemas.TransactionOut)
async def transfer_funds(
    transfer_data: schemas.TransferRequest,
    x_signature: str = Header(..., alias="X-Signature", description="HMAC-SHA256 request payload signature"),
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(get_db)
):
    # Retrieve accounts
    sender = db.query(models.Account).filter(models.Account.id == transfer_data.sender_account_id).first()
    receiver = db.query(models.Account).filter(models.Account.id == transfer_data.receiver_account_id).first()

    if not sender or sender.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sender account not found or access denied")
    if not receiver:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Receiver account not found")
    if sender.balance < transfer_data.amount:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient funds")

    #start the atomic ledger balance transfer
    sender.balance -= transfer_data.amount
    receiver.balance += transfer_data.amount

    # process database row integrity with HMAC
    raw_payload = f"{sender.id}:{receiver.id}:{transfer_data.amount}".encode()
    row_signature = security.generate_hmac_signature(raw_payload)

    #saving  the transaction record
    transaction = models.Transaction(
        sender_account_id=sender.id,
        receiver_account_id=receiver.id,
        amount=transfer_data.amount,
        hmac_signature=row_signature
    )
    db.add(transaction)
    db.commit()
    db.refresh(transaction)

    return transaction