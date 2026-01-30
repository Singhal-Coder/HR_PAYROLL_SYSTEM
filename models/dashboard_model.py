import sqlite3
import logging
from datetime import datetime
from database.db_connection import Database

logger = logging.getLogger(__name__)

class DashboardModel:
    def __init__(self):
        self.db = Database()

    def get_dashboard_stats(self):
        """
        Fetches all KPI counters in a single connection.
        Returns: dict {'total_emp': int, 'present_today': int, 'pending': int}
        """
        stats = {
            'total_emp': 0,
            'present_today': 0,
            'pending': 0
        }
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            # 1. Total Active Employees
            cursor.execute("SELECT COUNT(*) FROM employees WHERE is_active=1")
            stats['total_emp'] = cursor.fetchone()[0]
            
            # 2. Present Today
            today_str = datetime.now().strftime("%Y-%m-%d")
            cursor.execute("SELECT COUNT(DISTINCT emp_code) FROM attendance_logs WHERE date=?", (today_str,))
            stats['present_today'] = cursor.fetchone()[0]
            
                      
            return stats

        except Exception as e:
            logger.error(f"Dashboard Stats Error: {e}")
            return stats # Return 0s on error logic
        finally:
            conn.close()