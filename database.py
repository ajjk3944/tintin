import sqlite3
from datetime import datetime

DB_PATH = "tensortitan.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS gpu_metrics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        node_id INTEGER,
        temperature REAL,
        utilization REAL,
        memory_used REAL,
        power_draw REAL
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS predictions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        node_id INTEGER,
        risk_score REAL,
        risk_level TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        job_name TEXT,
        assigned_node INTEGER,
        reason TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS idle_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        node_id INTEGER,
        idle_minutes REAL
    )''')
    conn.commit()
    conn.close()

def insert_metrics(metrics_list):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    ts = datetime.now().isoformat()
    for m in metrics_list:
        c.execute("INSERT INTO gpu_metrics VALUES (NULL,?,?,?,?,?,?)",
                  (ts, m['node_id'], m['temperature'], m['utilization'],
                   m['memory_used'], m['power_draw']))
    conn.commit()
    conn.close()

def insert_prediction(node_id, risk_score, risk_level):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO predictions VALUES (NULL,?,?,?,?)",
              (datetime.now().isoformat(), node_id, risk_score, risk_level))
    conn.commit()
    conn.close()

def log_job(job_name, assigned_node, reason):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO jobs VALUES (NULL,?,?,?,?)",
              (datetime.now().isoformat(), job_name, assigned_node, reason))
    conn.commit()
    conn.close()

def log_idle(node_id, idle_minutes):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO idle_log VALUES (NULL,?,?,?)",
              (datetime.now().isoformat(), node_id, idle_minutes))
    conn.commit()
    conn.close()

def get_recent_metrics(limit=50):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM gpu_metrics ORDER BY id DESC LIMIT ?", (limit,))
    rows = c.fetchall()
    conn.close()
    return rows

def get_recent_predictions(limit=20):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM predictions ORDER BY id DESC LIMIT ?", (limit,))
    rows = c.fetchall()
    conn.close()
    return rows

def get_recent_jobs(limit=20):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM jobs ORDER BY id DESC LIMIT ?", (limit,))
    rows = c.fetchall()
    conn.close()
    return rows
