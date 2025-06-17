import pyodbc # Change from psycopg2
import os
from dotenv import load_dotenv
import logging
from backend.app.config import settings
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

def initialize_database():
    conn = None
    try:
        conn_str = (
            f"DRIVER={settings.db_driver};"
            f"SERVER={settings.db_server};"
            f"DATABASE={settings.db_name};"
            f"Trusted_Connection=yes;" # <<< THIS IS THE KEY CHANGE FOR WINDOWS AUTH
            f"{'PORT=' + str(settings.db_port) + ';' if settings.db_port else ''}"
        )
        conn = pyodbc.connect(conn_str, autocommit=True)
        cursor = conn.cursor()

        # SQL Server specific syntax for CREATE TABLE IF NOT EXISTS, IDENTITY, NVARCHAR(MAX), GETDATE()
        cursor.execute("""
            IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'chat_history')
            BEGIN
                CREATE TABLE chat_history (
                    id INT IDENTITY(1,1) PRIMARY KEY,
                    conversation_id NVARCHAR(255),
                    user_id NVARCHAR(255) NOT NULL,
                    question NVARCHAR(MAX) NOT NULL,
                    response NVARCHAR(MAX) NOT NULL,
                    sources NVARCHAR(MAX),
                    timestamp DATETIME DEFAULT GETDATE(),
                    feedback INT
                )
            END;
        """)

        cursor.execute("""
            IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'conversations')
            BEGIN
                CREATE TABLE conversations (
                    conversation_id NVARCHAR(255) PRIMARY KEY,
                    user_id NVARCHAR(255) NOT NULL,
                    context NVARCHAR(MAX),
                    created_at DATETIME DEFAULT GETDATE(),
                    updated_at DATETIME DEFAULT GETDATE()
                )
            END;
        """)

        # Create indexes
        cursor.execute("""
            IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_chat_history_user_id' AND object_id = OBJECT_ID('chat_history'))
            CREATE INDEX IX_chat_history_user_id ON chat_history(user_id);
        """)
        cursor.execute("""
            IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_chat_history_timestamp' AND object_id = OBJECT_ID('chat_history'))
            CREATE INDEX IX_chat_history_timestamp ON chat_history(timestamp);
        """)

        logger.info("✅ SQL Server Database initialized successfully")

    except Exception as e:
        logger.error(f"❌ SQL Server Database initialization failed: {e}")
        raise
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    initialize_database()