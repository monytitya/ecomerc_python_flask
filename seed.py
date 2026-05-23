import pymysql
from sqlalchemy import create_engine, text
from app.db.session import SQLALCHEMY_DATABASE_URL
import os

def run_sql_file(filename):

    url_parts = SQLALCHEMY_DATABASE_URL.rsplit('/', 1)
    base_url = url_parts[0]
    db_name = url_parts[1]
    
    try:
        temp_engine = create_engine(base_url)
        with temp_engine.connect() as conn:
            conn.execution_options(isolation_level="AUTOCOMMIT").execute(text(f"CREATE DATABASE IF NOT EXISTS {db_name}"))
            print(f"Database '{db_name}' checked/created.")
        temp_engine.dispose()
    except Exception as e:
        print(f"Failed to connect to MySQL server: {e}")
        return False

    try:
        engine = create_engine(SQLALCHEMY_DATABASE_URL)
        with engine.connect() as conn:
            with open(filename, 'r', encoding='utf-8') as f:
                
                sql_content = f.read()
                
                commands = []
                current_command = []
                for line in sql_content.split('\n'):
                    if line.strip().startswith('--') or line.strip().startswith('/*'):
                        continue
                    if not line.strip():
                        continue
                    current_command.append(line)
                    if line.strip().endswith(';'):
                        commands.append(' '.join(current_command))
                        current_command = []
                
                print(f"Executing {len(commands)} commands from {filename}...")
                for cmd in commands:
                    try:
                        conn.execution_options(isolation_level="AUTOCOMMIT").execute(text(cmd))
                    except Exception as ex:
                        if "already exists" not in str(ex).lower():
                            print(f"Warning on command: {str(ex)[:100]}...")
            
            print("SQL file executed successfully!")
        engine.dispose()
        return True
    except Exception as e:
        print(f"Error executing SQL file: {e}")
        return False

if __name__ == "__main__":
    sql_file = "ecom_store.sql"
    if os.path.exists(sql_file):
        run_sql_file(sql_file)
    else:
        print(f"Error: {sql_file} not found.")
