import sqlite3
import json
import time
import os
from enum import Enum

DB_PATH = "/root/AgentLink/core/mission.db"
STICKY_NOTE_PATH = "/root/AgentLink/ACTIVE_CONTEXT.md"

class Status(Enum):
    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    DRIFT_DETECTED = "DRIFT_DETECTED"

class MissionControl:
    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH)
        self.cursor = self.conn.cursor()
        self.init_db()

    def init_db(self):
        # 1. The Plan (Intent)
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                description TEXT,
                status TEXT,
                parent_id INTEGER, -- For sub-plans
                created_at REAL
            )
        ''')
        # 2. The To-Do List (Atomic Steps)
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plan_id INTEGER,
                description TEXT,
                status TEXT,
                sequence INTEGER,
                FOREIGN KEY(plan_id) REFERENCES plans(id)
            )
        ''')
        # 3. The Progress (Reality/Memory)
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plan_id INTEGER,
                task_id INTEGER,
                entry_type TEXT, -- 'LOG', 'ERROR', 'ARTIFACT', 'THOUGHT'
                content TEXT,
                timestamp REAL
            )
        ''')
        self.conn.commit()

    # --- Plan Management ---
    def create_plan(self, title, description, steps=[], parent_id=None):
        self.cursor.execute(
            "INSERT INTO plans (title, description, status, parent_id, created_at) VALUES (?, ?, ?, ?, ?)",
            (title, description, Status.PENDING.value, parent_id, time.time())
        )
        plan_id = self.cursor.lastrowid
        
        for idx, step in enumerate(steps):
            self.add_task(plan_id, step, idx)
            
        self.conn.commit()
        return plan_id

    def add_task(self, plan_id, description, sequence):
        self.cursor.execute(
            "INSERT INTO tasks (plan_id, description, status, sequence) VALUES (?, ?, ?, ?)",
            (plan_id, description, Status.PENDING.value, sequence)
        )

    def cancel_plan(self, plan_id):
        self.cursor.execute("UPDATE plans SET status = ? WHERE id = ?", (Status.CANCELLED.value, plan_id))
        self.conn.commit()
        self.update_sticky_note(plan_id)

    # --- Execution & Progress ---
    def start_plan(self, plan_id):
        self.cursor.execute("UPDATE plans SET status = ? WHERE id = ?", (Status.ACTIVE.value, plan_id))
        self.conn.commit()
        self.update_sticky_note(plan_id)

    def complete_task(self, task_id, success=True):
        status = Status.COMPLETED.value if success else Status.FAILED.value
        self.cursor.execute("UPDATE tasks SET status = ? WHERE id = ?", (status, task_id))
        self.conn.commit()
        # Auto-update sticky note for next task
        task = self.get_task(task_id)
        if task: self.update_sticky_note(task['plan_id'])

    def log_progress(self, plan_id, task_id, content, entry_type="LOG"):
        self.cursor.execute(
            "INSERT INTO progress (plan_id, task_id, entry_type, content, timestamp) VALUES (?, ?, ?, ?, ?)",
            (plan_id, task_id, entry_type, content, time.time())
        )
        self.conn.commit()

    # --- The "Sticky Note" (Context Anchor) ---
    def update_sticky_note(self, plan_id):
        """Generates the ACTIVE_CONTEXT.md file for agents to see."""
        plan = self.get_plan(plan_id)
        current_task = self.get_next_pending_task(plan_id)
        
        if not plan: return

        content = f"""
# 📌 AGENT CONTEXT ANCHOR
**DO NOT IGNORE.** You are executing a long-running plan.

##  CURRENT MISSION: {plan['title']}
- **Status:** {plan['status']}
- **Goal:** {plan['description']}

## 👉 IMMEDIATE TASK (FOCUS HERE)
**[ ] {current_task['description'] if current_task else "ALL TASKS COMPLETED"}**

## 📝 RECENT PROGRESS
"""
        # Get last 3 logs
        self.cursor.execute("SELECT content FROM progress WHERE plan_id = ? ORDER BY id DESC LIMIT 3", (plan_id,))
        logs = self.cursor.fetchall()
        for log in logs:
            content += f"- {log[0]}\n"

        with open(STICKY_NOTE_PATH, "w") as f:
            f.write(content)

    # --- Helpers ---
    def get_plan(self, plan_id):
        self.cursor.execute("SELECT * FROM plans WHERE id = ?", (plan_id,))
        r = self.cursor.fetchone()
        return {'id': r[0], 'title': r[1], 'description': r[2], 'status': r[3]} if r else None

    def get_task(self, task_id):
        self.cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        r = self.cursor.fetchone()
        return {'id': r[0], 'plan_id': r[1]} if r else None

    def get_next_pending_task(self, plan_id):
        self.cursor.execute("SELECT * FROM tasks WHERE plan_id = ? AND status = ? ORDER BY sequence ASC LIMIT 1", (plan_id, Status.PENDING.value))
        r = self.cursor.fetchone()
        return {'id': r[0], 'description': r[2], 'sequence': r[4]} if r else None