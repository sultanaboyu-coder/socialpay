from fastapi import APIRouter, Depends
import sqlite3
import secrets
from datetime import datetime

from app.database import get_db
from app.auth import get_current_user, get_admin_user
from app.models import *
from app.config import config

router = APIRouter()

@router.post("/message")
async def send_support_message(message: SupportMessage, current_user: dict = Depends(get_current_user), db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    
    message_id = f"msg_{current_user['user_id']}_{int(datetime.now().timestamp())}"
    
    cursor.execute("""
        INSERT INTO support_messages (message_id, user_id, message, created_at)
        VALUES (?, ?, ?, ?)
    """, (message_id, current_user['user_id'], message.message, datetime.now().isoformat()))
    
    db.commit()
    
    return {"message": "Support message sent successfully", "message_id": message_id}

@router.get("/my-messages")
async def get_my_messages(current_user: dict = Depends(get_current_user), db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    
    cursor.execute("""
        SELECT * FROM support_messages 
        WHERE user_id = ?
        ORDER BY created_at DESC
    """, (current_user['user_id'],))
    
    messages = cursor.fetchall()
    
    result = []
    for msg in messages:
        result.append({
            "message_id": msg['message_id'],
            "message": msg['message'],
            "reply": msg['reply'],
            "status": msg['status'],
            "created_at": msg['created_at'],
            "replied_at": msg['replied_at']
        })
    
    return {"messages": result}

@router.get("/info")
async def get_support_info():
    return {
        "telegram": config.SUPPORT_TELEGRAM,
        "group": config.SUPPORT_GROUP,
        "channel": config.SUPPORT_CHANNEL
    }