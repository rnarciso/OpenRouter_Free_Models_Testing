import sqlite3
import os
from datetime import datetime

# SQLite database file
DB_FILE = 'results.db'

def init_db():
    conn = None
    try:
        conn = sqlite3.connect(DB_FILE)
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
            expected_answer TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')

        # Create global_problem table
        c.execute('''CREATE TABLE IF NOT EXISTS global_problem (
            id INTEGER PRIMARY KEY DEFAULT 1 CHECK (id = 1),
            problem_text TEXT NOT NULL,
            correct_answer TEXT NOT NULL,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')

        conn.commit()
    except sqlite3.Error as e:
        print(f"Error initializing database: {e}")
    finally:
        if conn:
            conn.close()

def save_result(result):
    conn = None
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()

        c.execute('''INSERT INTO results (
            model_id, model_name, prompt, response_text,
            is_correct, answer_found, response_time,
            prompt_tokens, completion_tokens, total_tokens, score, expected_answer
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', (
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
            result['score'],
            result['expected_answer']
        ))

        conn.commit()
    except sqlite3.Error as e:
        print(f"Error saving result: {e}")
    finally:
        if conn:
            conn.close()

def get_all_results():
    conn = None
    results_list = []
    try:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()

        c.execute('''SELECT
            id, model_id, model_name, prompt, response_text,
            is_correct, answer_found, response_time,
            prompt_tokens, completion_tokens, total_tokens,
            score, expected_answer, timestamp
            FROM results ORDER BY timestamp DESC;''')

        rows = c.fetchall()
        for row in rows:
            results_list.append(dict(row))

    except sqlite3.Error as e:
        print(f"Error fetching results: {e}")
    finally:
        if conn:
            conn.close()
    return results_list

def save_global_problem(problem_text, correct_answer):
    conn = None
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()

        upsert_sql = """
        INSERT INTO global_problem (id, problem_text, correct_answer, last_updated)
        VALUES (1, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT (id) DO UPDATE
        SET problem_text = excluded.problem_text,
            correct_answer = excluded.correct_answer,
            last_updated = excluded.last_updated;
        """
        c.execute(upsert_sql, (problem_text, correct_answer))
        conn.commit()
        print(f"Global problem saved: {problem_text[:50]}... Answer: {correct_answer}")
    except sqlite3.Error as e:
        print(f"Error saving global problem: {e}")
    finally:
        if conn:
            conn.close()

def get_global_problem():
    conn = None
    problem_data = None
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()

        c.execute("SELECT problem_text, correct_answer FROM global_problem WHERE id = 1;")
        row = c.fetchone()

        if row:
            problem_data = {
                "problem_text": row[0],
                "correct_answer": row[1]
            }
            print(f"Global problem retrieved: {problem_data['problem_text'][:50]}...")
    except sqlite3.Error as e:
        print(f"Error fetching global problem: {e}")
    finally:
        if conn:
            conn.close()
    return problem_data