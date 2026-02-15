from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
import sqlite3

from app.database import get_db
from app.auth import get_admin_user
from app.models import *
from app.config import config

router = APIRouter()

@router.post("/tasks/create")
async def create_task(task: TaskCreate, admin: dict = Depends(get_admin_user), db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    
    task_id = f"task_{int(datetime.now().timestamp())}"
    price_naira = task.price if task.currency == "naira" else 0
    price_dollar = task.price if task.currency == "dollar" else 0
    
    cursor.execute("""
        INSERT INTO tasks (task_id, platform, task_type, link, currency, price_naira, price_dollar, max_users, created_at, created_by)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (task_id, task.platform, task.task_type, task.link, task.currency, price_naira, price_dollar, 
          task.max_users, datetime.now().isoformat(), admin['user_id']))
    
    db.commit()
    
    return {"message": "Task created successfully", "task_id": task_id}

@router.delete("/tasks/{task_id}")
async def delete_task(task_id: str, admin: dict = Depends(get_admin_user), db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("DELETE FROM tasks WHERE task_id = ?", (task_id,))
    
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="Task not found")
    
    db.commit()
    return {"message": "Task deleted successfully"}

@router.get("/submissions/pending")
async def get_pending_submissions(admin: dict = Depends(get_admin_user), db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    
    cursor.execute("""
        SELECT s.*, u.name as user_name, t.platform, t.task_type, t.currency, t.price_naira, t.price_dollar
        FROM submissions s
        JOIN users u ON s.user_id = u.user_id
        JOIN tasks t ON s.task_id = t.task_id
        WHERE s.status = 'pending'
        ORDER BY s.submitted_at ASC
    """)
    
    submissions = cursor.fetchall()
    
    result = []
    for sub in submissions:
        result.append({
            "submission_id": sub['submission_id'],
            "user_id": sub['user_id'],
            "user_name": sub['user_name'],
            "task_id": sub['task_id'],
            "platform": sub['platform'],
            "task_type": sub['task_type'],
            "photo_url": sub['photo_url'],
            "price": sub['price_naira'] if sub['currency'] == 'naira' else sub['price_dollar'],
            "currency": sub['currency'],
            "submitted_at": sub['submitted_at']
        })
    
    return {"submissions": result}

@router.post("/submissions/approve")
async def approve_submission(approval: TaskApproval, admin: dict = Depends(get_admin_user), db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    
    cursor.execute("SELECT * FROM submissions WHERE submission_id = ?", (approval.submission_id,))
    submission = cursor.fetchone()
    
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    
    cursor.execute("SELECT * FROM tasks WHERE task_id = ?", (submission['task_id'],))
    task = cursor.fetchone()
    
    if approval.approved:
        price = task['price_naira'] if task['currency'] == 'naira' else task['price_dollar']
        
        cursor.execute("UPDATE submissions SET status = 'approved', processed_at = ? WHERE submission_id = ?", 
                       (datetime.now().isoformat(), approval.submission_id))
        
        if task['currency'] == 'naira':
            cursor.execute("UPDATE wallets SET naira = naira + ?, completed_tasks = completed_tasks + 1, pending_tasks = pending_tasks - 1 WHERE user_id = ?", 
                           (price, submission['user_id']))
        else:
            cursor.execute("UPDATE wallets SET dollar = dollar + ?, completed_tasks = completed_tasks + 1, pending_tasks = pending_tasks - 1 WHERE user_id = ?", 
                           (price, submission['user_id']))
        
        cursor.execute("INSERT INTO task_completions (task_id, user_id, completed_at) VALUES (?, ?, ?)", 
                       (submission['task_id'], submission['user_id'], datetime.now().isoformat()))
        
        cursor.execute("SELECT * FROM referrals WHERE referred_user_id = ? AND reward_paid = 0", (submission['user_id'],))
        referral = cursor.fetchone()
        
        if referral:
            cursor.execute("UPDATE referrals SET tasks_completed = tasks_completed + 1 WHERE id = ?", (referral['id'],))
            
            if referral['tasks_completed'] + 1 >= config.REFERRAL_TASKS_REQUIRED:
                cursor.execute("UPDATE referrals SET reward_paid = 1 WHERE id = ?", (referral['id'],))
                cursor.execute("UPDATE wallets SET naira = naira + ?, referral_naira = referral_naira + ?, referral_count = referral_count + 1 WHERE user_id = ?", 
                               (config.REFERRAL_REWARD_NAIRA, config.REFERRAL_REWARD_NAIRA, referral['referrer_id']))
        
        cursor.execute("SELECT COUNT(*) as count FROM task_completions WHERE task_id = ?", (task['task_id'],))
        count = cursor.fetchone()['count']
        
        if count >= task['max_users']:
            cursor.execute("DELETE FROM tasks WHERE task_id = ?", (task['task_id'],))
    else:
        cursor.execute("UPDATE submissions SET status = 'rejected', processed_at = ? WHERE submission_id = ?", 
                       (datetime.now().isoformat(), approval.submission_id))
        cursor.execute("UPDATE wallets SET pending_tasks = pending_tasks - 1 WHERE user_id = ?", (submission['user_id'],))
    
    db.commit()
    
    return {"message": f"Submission {'approved' if approval.approved else 'rejected'} successfully"}

@router.get("/withdrawals/pending")
async def get_pending_withdrawals(admin: dict = Depends(get_admin_user), db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    
    cursor.execute("""
        SELECT w.*, u.name as user_name, p.payment_type, p.details as payment_details
        FROM withdrawals w
        JOIN users u ON w.user_id = u.user_id
        LEFT JOIN payment_details p ON w.user_id = p.user_id
        WHERE w.status = 'pending'
        ORDER BY w.requested_at ASC
    """)
    
    withdrawals = cursor.fetchall()
    
    result = []
    for w in withdrawals:
        result.append({
            "withdrawal_id": w['withdrawal_id'],
            "user_id": w['user_id'],
            "user_name": w['user_name'],
            "currency": w['currency'],
            "amount": w['amount'],
            "fee": w['fee'],
            "total": w['total'],
            "payment_type": w['payment_type'],
            "payment_details": w['payment_details'],
            "requested_at": w['requested_at']
        })
    
    return {"withdrawals": result}

@router.post("/withdrawals/approve")
async def approve_withdrawal(approval: WithdrawalApproval, admin: dict = Depends(get_admin_user), db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    
    cursor.execute("SELECT * FROM withdrawals WHERE withdrawal_id = ?", (approval.withdrawal_id,))
    withdrawal = cursor.fetchone()
    
    if not withdrawal:
        raise HTTPException(status_code=404, detail="Withdrawal not found")
    
    if approval.approved:
        cursor.execute("UPDATE withdrawals SET status = 'approved', approved_at = ? WHERE withdrawal_id = ?", 
                       (datetime.now().isoformat(), approval.withdrawal_id))
    else:
        cursor.execute("UPDATE withdrawals SET status = 'cancelled', cancelled_at = ? WHERE withdrawal_id = ?", 
                       (datetime.now().isoformat(), approval.withdrawal_id))
        
        if withdrawal['currency'] == 'naira':
            cursor.execute("UPDATE wallets SET naira = naira + ? WHERE user_id = ?", 
                           (withdrawal['total'], withdrawal['user_id']))
        else:
            cursor.execute("UPDATE wallets SET dollar = dollar + ? WHERE user_id = ?", 
                           (withdrawal['total'], withdrawal['user_id']))
    
    db.commit()
    
    return {"message": f"Withdrawal {'approved' if approval.approved else 'cancelled'} successfully"}

@router.get("/statistics")
async def get_statistics(admin: dict = Depends(get_admin_user), db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    
    cursor.execute("SELECT COUNT(*) as count FROM users")
    total_users = cursor.fetchone()['count']
    
    cursor.execute("SELECT COUNT(*) as count FROM tasks WHERE status = 'active'")
    total_tasks = cursor.fetchone()['count']
    
    cursor.execute("SELECT SUM(completed_tasks) as count FROM wallets")
    completed_tasks = cursor.fetchone()['count'] or 0
    
    cursor.execute("SELECT COUNT(*) as count FROM submissions WHERE status = 'pending'")
    pending_submissions = cursor.fetchone()['count']
    
    cursor.execute("SELECT COUNT(*) as count FROM withdrawals WHERE status = 'pending'")
    pending_withdrawals = cursor.fetchone()['count']
    
    cursor.execute("SELECT SUM(naira) as total FROM wallets")
    total_naira = cursor.fetchone()['total'] or 0
    
    cursor.execute("SELECT SUM(dollar) as total FROM wallets")
    total_dollar = cursor.fetchone()['total'] or 0
    
    return {
        "total_users": total_users,
        "total_tasks": total_tasks,
        "completed_tasks": completed_tasks,
        "pending_submissions": pending_submissions,
        "pending_withdrawals": pending_withdrawals,
        "total_naira": total_naira,
        "total_dollar": total_dollar
    }