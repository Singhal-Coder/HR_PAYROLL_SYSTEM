import sqlite3
import os
import logging
from config.settings import DB_PATH, ADMIN_DEFAULT_USER, ADMIN_DEFAULT_PASS
from utils.security import hash_password
from utils.logger import setup_logging

# Logger setup
setup_logging()
logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self.db_path = DB_PATH
        self.initialize_db()

    def get_connection(self):
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute("PRAGMA foreign_keys = ON")
            return conn
        except sqlite3.Error as e:
            logger.critical(f"Database Connection Failed: {e}")
            raise e

    def initialize_db(self):
        """Creates tables and ensures default admin exists."""
        if not os.path.exists("database"):
            os.makedirs("database")
            logger.info("Created 'database' directory.")
            
        conn = self.get_connection()
        cursor = conn.cursor()
        
        schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
        try:
            with open(schema_path, "r") as f:
                schema_script = f.read()
            
            cursor.executescript(schema_script)
            logger.info("Schema Checked/Tables Verified.")
            
            # Bootstrapping: Admin is mandatory for system to work
            self._ensure_super_admin(cursor)
            
            conn.commit()
            logger.info("Core System Initialization Complete.")
        except FileNotFoundError:
            logger.error(f"Schema file not found at {schema_path}")
            raise
        except sqlite3.Error as e:
            logger.error(f"SQL Execution Error: {e}")
            raise
        finally:
            conn.close()

    def _ensure_super_admin(self, cursor):
        """Creates a default admin if none exists (System Bootstrapping)."""
        cursor.execute("SELECT COUNT(*) FROM admins")
        if cursor.fetchone()[0] == 0:
            hashed_pw = hash_password(ADMIN_DEFAULT_PASS)
            cursor.execute(
                "INSERT INTO admins (username, password_hash) VALUES (?, ?)", 
                (ADMIN_DEFAULT_USER, hashed_pw)
            )
            logger.warning(f"Bootstrapping: SuperAdmin created (User: {ADMIN_DEFAULT_USER})")

# ---------------------------------------------------------
# MOCK DATA SEEDER (Only runs when executed directly)
# ---------------------------------------------------------
def run_mock_seeding():
    """Inserts sample data for Testing/Development purposes."""
    db = Database()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    logger.info("🚀 Starting Mock Data Seeding...")

    # 1. Mock Departments
    departments = [
        ('Engineering',), ('Human Resources',), ('Sales',), ('Finance',)
    ]
    cursor.executemany("INSERT OR IGNORE INTO departments (dept_name) VALUES (?)", departments)
    
    # 2. Mock Roles (Designation, PF, Tax, Bonus, Start, End)
    roles = [
        ('Intern', 0.0, 0, 0, '10:00:00', '18:00:00'),
        ('SDE-1', 0.12, 1500, 500, '09:30:00', '18:30:00'),
        ('Manager', 0.12, 5000, 1500, '10:00:00', '19:00:00')
    ]
    cursor.executemany("""
        INSERT OR IGNORE INTO roles 
        (designation, base_pf_percent, tax_deduction, daily_bonus, start_time, end_time) 
        VALUES (?, ?, ?, ?, ?, ?)
    """, roles)
    
    conn.commit()
    conn.close()
    logger.info("✅ Mock Data Seeding Finished Successfully.")

if __name__ == "__main__":
    try:
        run_mock_seeding()
    except Exception as e:
        logger.error(f"Seeding Failed: {e}")