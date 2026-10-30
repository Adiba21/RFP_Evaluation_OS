import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Any

DB_FILE = "rfp_evaluation.db"

def get_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS evaluation_criteria (
        criterion_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT NOT NULL,
        weight REAL NOT NULL,
        max_score REAL NOT NULL,
        is_active INTEGER DEFAULT 1
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS rfp_runs (
        rfp_run_id TEXT PRIMARY KEY,
        created_at TEXT NOT NULL,
        status TEXT NOT NULL
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS supplier_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        rfp_run_id TEXT NOT NULL,
        supplier_name TEXT NOT NULL,
        submission_date TEXT NOT NULL,
        experience_rating REAL NOT NULL,
        absolute_score REAL NOT NULL,
        ppi REAL NOT NULL,
        final_rank INTEGER NOT NULL,
        result_json TEXT NOT NULL,
        FOREIGN KEY (rfp_run_id) REFERENCES rfp_runs (rfp_run_id)
    );
    """)

    cursor.execute("SELECT COUNT(*) FROM evaluation_criteria")
    if cursor.fetchone()[0] == 0:
        default_criteria = [
            ("Technical Capability", "Architecture, integrations, scalability, technical fit", 0.30, 10.0, 1),
            ("Implementation Plan", "Timeline, milestones, staffing, risk plan", 0.20, 10.0, 1),
            ("Commercial Value", "Pricing clarity, total cost, assumptions", 0.20, 10.0, 1),
            ("Security & Compliance", "Controls, certifications, privacy, auditability", 0.20, 10.0, 1),
            ("Support & Experience", "Support model, similar projects, references", 0.10, 10.0, 1)
        ]
        cursor.executemany("""
            INSERT INTO evaluation_criteria (name, description, weight, max_score, is_active)
            VALUES (?, ?, ?, ?, ?)
        """, default_criteria)

    conn.commit()
    conn.close()

def get_active_criteria() -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM evaluation_criteria WHERE is_active = 1")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def save_rfp_run(rfp_run_id: str, status: str, ranked_suppliers: List[Dict[str, Any]]):
    conn = get_connection()
    cursor = conn.cursor()
    now_str = datetime.utcnow().isoformat()
    cursor.execute("INSERT INTO rfp_runs (rfp_run_id, created_at, status) VALUES (?, ?, ?)",
                   (rfp_run_id, now_str, status))

    for item in ranked_suppliers:
        cursor.execute("""
            INSERT INTO supplier_results (
                rfp_run_id, supplier_name, submission_date, experience_rating,
                absolute_score, ppi, final_rank, result_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            rfp_run_id,
            item["supplier_name"],
            item["submission_date"],
            item["experience_rating"],
            item["absolute_score"],
            item["ppi"],
            item["final_rank"],
            json.dumps(item)
        ))
    conn.commit()
    conn.close()
