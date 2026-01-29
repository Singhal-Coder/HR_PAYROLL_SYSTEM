import sqlite3
import logging
from database.db_connection import Database
from utils.security import verify_password

logger = logging.getLogger(__name__)

class AdminModel:
    def __init__(self):
        self.db = Database()

    def login(self, username, password):
        """
        Returns Admin ID if login success, else None.
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT admin_id, password_hash FROM admins WHERE username=?", (username,))
            row = cursor.fetchone()
            
            if row:
                admin_id, stored_hash = row
                if verify_password(password, stored_hash):
                    logger.info(f"Admin Login Success: {username}")
                    return admin_id
                else:
                    logger.warning(f"Login Failed (Bad Password): {username}")
            else:
                logger.warning(f"Login Failed (User Not Found): {username}")
                
            return None
        except Exception as e:
            logger.error(f"Login Error: {e}")
            return None
        finally:
            conn.close()