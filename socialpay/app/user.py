from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
import sqlite3
import secrets

from app.database import get_db
from app.auth import get_current_user, hash_password, verify_password
from app.models import *
from app.config import config

router = APIRouter()

@router.get("/profile", response_model=UserProfile)
async def get_profile(current_user: dict = Depends(get_current_user), db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (current_user['user_id'],))
    user = cursor.fetchone()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return UserProfile(
        user_id=user['user_id'],
        name=user['name'],
        email=user['email'],
        phone=user['phone'],
        role=user['role'],
        is_verified=bool(user['is_verified']),
        referrer_id=user['referrer_id'],
        joined_at=user['joined_at']
    )

@router.get("/wallet", response_model=WalletBalance)
async def get_wallet(current_user: dict = Depends(get_current_user), db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("SELECT * FROM wallets WHERE user_id = ?", (current_user['user_id'],))
    wallet = cursor.fetchone()
    
    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet not found")
    
    return WalletBalance(
        naira=wallet['naira'],
        dollar=wallet['dollar'],
        completed_tasks=wallet['completed_tasks'],
        pending_tasks=wallet['pending_tasks'],
        referral_count=wallet['referral_count'],
        referral_naira=wallet['referral_naira'],
        referral_dollar=wallet['referral_dollar']
    )

@router.post("/payment-details")
async def set_payment_details(details: PaymentDetailsInput, current_user: dict = Depends(get_current_user), db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    
    cursor.execute("SELECT * FROM payment_details WHERE user_id = ?", (current_user['user_id'],))
    existing = cursor.fetchone()
    
    if existing:
        cursor.execute("""
            UPDATE payment_details 
            SET payment_type = ?, details = ?, updated_at = ?
            WHERE user_id = ?
        """, (details.payment_type, details.details, datetime.now().isoformat(), current_user['user_id']))
    else:
        cursor.execute("""
            INSERT INTO payment_details (user_id, payment_type, details, updated_at)
            VALUES (?, ?, ?, ?)
        """, (current_user['user_id'], details.payment_type, details.details, datetime.now().isoformat()))
    
    db.commit()
    
    return {"message": "Payment details saved successfully"}

@router.post("/pin/create")
async def create_pin(pin_data: PINCreate, current_user: dict = Depends(get_current_user), db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    
    cursor.execute("SELECT * FROM user_pins WHERE user_id = ?", (current_user['user_id'],))
    if cursor.fetchone():
        raise HTTPException(status_code=400, detail="PIN already exists")
    
    pin_hash = hash_password(pin_data.pin)
    
    cursor.execute("""
        INSERT INTO user_pins (user_id, pin_hash, created_at)
        VALUES (?, ?, ?)
    """, (current_user['user_id'], pin_hash, datetime.now().isoformat()))
    
    db.commit()
    
    return {"message": "PIN created successfully"}

@router.post("/transfer", response_model=TransferResponse)
async def transfer_money(transfer: TransferRequest, current_user: dict = Depends(get_current_user), db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    
    cursor.execute("SELECT * FROM user_pins WHERE user_id = ?", (current_user['user_id'],))
    pin_record = cursor.fetchone()
    
    if not pin_record:
        raise HTTPException(status_code=400, detail="PIN not set")
    
    if not verify_password(transfer.pin, pin_record['pin_hash']):
        raise HTTPException(status_code=401, detail="Invalid PIN")
    
    today = datetime.now().date().isoformat()
    cursor.execute("SELECT * FROM transfer_limits WHERE user_id = ? AND date = ?", 
                   (current_user['user_id'], today))
    limit = cursor.fetchone()
    
    if limit and limit['count'] >= config.MAX_TRANSFERS_PER_DAY:
        raise HTTPException(status_code=400, detail="Daily transfer limit reached")
    
    if transfer.amount > config.MAX_TRANSFER_AMOUNT:
        raise HTTPException(status_code=400, detail="Amount exceeds maximum")
    
    cursor.execute("SELECT * FROM wallets WHERE user_id = ?", (current_user['user_id'],))
    sender_wallet = cursor.fetchone()
    
    cursor.execute("SELECT * FROM wallets WHERE user_id = ?", (transfer.receiver_id,))
    receiver_wallet = cursor.fetchone()
    
    if not receiver_wallet:
        raise HTTPException(status_code=404, detail="Receiver not found")
    
    if sender_wallet['naira'] < transfer.amount:
        raise HTTPException(status_code=400, detail="Insufficient balance")
    
    cursor.execute("UPDATE wallets SET naira = naira - ? WHERE user_id = ?", 
                   (transfer.amount, current_user['user_id']))
    cursor.execute("UPDATE wallets SET naira = naira + ? WHERE user_id = ?", 
                   (transfer.amount, transfer.receiver_id))
    
    if limit:
        cursor.execute("UPDATE transfer_limits SET count = count + 1 WHERE user_id = ? AND date = ?", 
                       (current_user['user_id'], today))
    else:
        cursor.execute("INSERT INTO transfer_limits (user_id, date, count) VALUES (?, ?, 1)", 
                       (current_user['user_id'], today))
    
    log_id = f"log_{int(datetime.now().timestamp())}_{secrets.token_hex(4)}"
    cursor.execute("""
        INSERT INTO transfer_audit (log_id, type, from_user, to_user, amount, status, created_at)
        VALUES (?, 'p2p_transfer', ?, ?, ?, 'success', ?)
    """, (log_id, current_user['user_id'], transfer.receiver_id, transfer.amount, datetime.now().isoformat()))
    
    db.commit()
    
    return TransferResponse(
        transfer_id=log_id,
        from_user=current_user['user_id'],
        to_user=transfer.receiver_id,
        amount=transfer.amount,
        status="success",
        created_at=datetime.now().isoformat()
    )