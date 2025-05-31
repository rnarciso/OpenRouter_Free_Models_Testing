import sqlite3
from datetime import datetime

def init_db():
    conn = sqlite3.connect('results.db')
    c = conn.cursor()
    
    # Create results table
    c.execute('''CREATE TABLE IF NOT EXISTS results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        model_id TEXT NOT NULL,
        model_name TEXT NOT NULL,
        prompt TEXT NOT NULL,
        response_text TEXT NOT NULL,
        is_correct BOOLEAN NOT NULL,
        answer_found TEXT,
        response_time REAL NOT NULL,
        prompt_tokens INTEGER NOT NULL,
        completion_tokens INTEGER NOT NULL,
        total_tokens INTEGER NOT NULL,
        score INTEGER NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')
    
    conn.commit()
    conn.close()

def save_result(result):
    conn = sqlite3.connect('results.db')
    c = conn.cursor()
    
    c.execute('''INSERT INTO results (
        model_id, model_name, prompt, response_text, 
        is_correct, answer_found, response_time, 
        prompt_tokens, completion_tokens, total_tokens, score
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', (
        result['model_id'],
        result['model_name'],
        result['prompt'],
        result['response_text'],
        result['is_correct'],
        result['answer_found'],
        result['response_time'],
        result['prompt_tokens'],
        result['completion_tokens'],
        result['total_tokens'],
        result['score']
    ))
    
    conn.commit()
    conn.close()