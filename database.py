import psycopg2
import os
from datetime import datetime

# Parâmetros de conexão PostgreSQL
DB_NAME = os.environ.get("DB_NAME", "testdb")
DB_USER = os.environ.get("DB_USER", "testuser")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "testpassword")
DB_HOST = "db.example.com"  # Placeholder, não conectará de fato
DB_PORT = "5432"

# Construct a DSN (Data Source Name)
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

def init_db():
    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor() as c:
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
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')

        conn.commit()
    except psycopg2.Error as e:
        import logging
        logging.error(f"Erro ao inicializar o banco de dados: {e}")
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
            prompt_tokens, completion_tokens, total_tokens, score
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)''', (
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
            score, timestamp
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