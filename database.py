import psycopg2
import os
from datetime import datetime

# PostgreSQL connection parameters fetched from environment variables
# Defaults are provided for local development or if variables are not set.
DB_HOST = os.environ.get("DB_HOST", "db.example.com")
DB_PORT = os.environ.get("DB_PORT", "5432")
DB_NAME = os.environ.get("DB_NAME", "testdb")
DB_USER = os.environ.get("DB_USER", "testuser")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "testpassword")

# Construct a DSN (Data Source Name) using the fetched parameters
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

def init_db():
    conn = None  # Initialize conn to None
    c = None # Initialize cursor to None
    try:
        conn = psycopg2.connect(DATABASE_URL)
        c = conn.cursor()

        # Create results table
        c.execute('''CREATE TABLE IF NOT EXISTS results (
            id SERIAL PRIMARY KEY,
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
    except psycopg2.Error as e:
        print(f"Error initializing database: {e}")
    finally:
        if c:
            c.close()
        if conn:
            conn.close()

def save_result(result):
    conn = None  # Initialize conn to None
    c = None # Initialize cursor to None
    try:
        conn = psycopg2.connect(DATABASE_URL)
        c = conn.cursor()

        c.execute('''INSERT INTO results (
            model_id, model_name, prompt, response_text,
            is_correct, answer_found, response_time,
            prompt_tokens, completion_tokens, total_tokens, score, expected_answer
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)''', (
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
    except psycopg2.Error as e:
        print(f"Error saving result: {e}")
    finally:
        if c:
            c.close()
        if conn:
            conn.close()

def get_all_results():
    conn = None  # Initialize conn to None
    c = None # Initialize cursor to None
    results_list = []
    try:
        conn = psycopg2.connect(DATABASE_URL)
        c = conn.cursor()

        c.execute('''SELECT
            id, model_id, model_name, prompt, response_text,
            is_correct, answer_found, response_time,
            prompt_tokens, completion_tokens, total_tokens,
            score, expected_answer, timestamp
            FROM results ORDER BY timestamp DESC;''')

        rows = c.fetchall()
        columns = [desc[0] for desc in c.description]
        for row in rows:
            results_list.append(dict(zip(columns, row)))

    except psycopg2.Error as e:
        print(f"Error fetching results: {e}")
    finally:
        if c:
            c.close()
        if conn:
            conn.close()
    return results_list

def save_global_problem(problem_text, correct_answer):
    conn = None
    c = None
    try:
        conn = psycopg2.connect(DATABASE_URL)
        c = conn.cursor()

        upsert_sql = """
        INSERT INTO global_problem (id, problem_text, correct_answer, last_updated)
        VALUES (1, %s, %s, CURRENT_TIMESTAMP)
        ON CONFLICT (id) DO UPDATE
        SET problem_text = EXCLUDED.problem_text,
            correct_answer = EXCLUDED.correct_answer,
            last_updated = EXCLUDED.last_updated;
        """
        c.execute(upsert_sql, (problem_text, correct_answer))
        conn.commit()
        print(f"Global problem saved: {problem_text[:50]}... Answer: {correct_answer}")
    except psycopg2.Error as e:
        print(f"Error saving global problem: {e}")
    finally:
        if c:
            c.close()
        if conn:
            conn.close()

def get_global_problem():
    conn = None
    c = None
    problem_data = None
    try:
        conn = psycopg2.connect(DATABASE_URL)
        c = conn.cursor()

        c.execute("SELECT problem_text, correct_answer FROM global_problem WHERE id = 1;")
        row = c.fetchone()

        if row:
            problem_data = {
                "problem_text": row[0],
                "correct_answer": row[1]
            }
            print(f"Global problem retrieved: {problem_data['problem_text'][:50]}...")
    except psycopg2.Error as e:
        print(f"Error fetching global problem: {e}")
    finally:
        if c:
            c.close()
        if conn:
            conn.close()
    return problem_data