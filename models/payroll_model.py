import sqlite3
import logging
from database.db_connection import Database

logger = logging.getLogger(__name__)

class PayrollModel:
    def __init__(self):
        self.db = Database()

    def get_salary_components(self, emp_code, month_str, year_month_wildcard):
        """
        Fetches all raw data required for salary calculation.
        Returns: Tuple (emp_data, present_days, leave_days) or None
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        try:
            # 1. Employee & Role Details
            cursor.execute("""
                SELECT e.full_name, e.base_salary, r.base_pf_percent, 
                       r.tax_deduction, r.daily_bonus, d.dept_name, r.designation
                FROM employees e
                JOIN roles r ON e.role_id = r.role_id
                JOIN departments d ON e.dept_id = d.dept_id
                WHERE e.emp_code = ?
            """, (emp_code,))
            emp_data = cursor.fetchone()
            
            if not emp_data: return None

            # 2. Present Days
            cursor.execute("""
                SELECT COUNT(*) FROM attendance_logs 
                WHERE emp_code = ? AND date LIKE ?
            """, (emp_code, year_month_wildcard))
            present_days = cursor.fetchone()[0]

            # 3. Approved Leaves
            cursor.execute("""
                SELECT COUNT(*) FROM employee_leaves 
                WHERE emp_code = ? AND strftime('%Y-%m', leave_date) = ? AND status = 'Approved'
            """, (emp_code, month_str))
            leave_days = cursor.fetchone()[0]

            return emp_data, present_days, leave_days

        except Exception as e:
            logger.error(f"Payroll Model Fetch Error: {e}")
            return None
        finally:
            conn.close()

    def record_payment(self, emp_code, month_year, net_salary, cleared_upto_date):
        """Transactional update for Slip + Ledger"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        try:
            # 1. Insert Slip
            cursor.execute("""
                INSERT INTO salary_slips (emp_code, month_year, net_salary, payment_status, payment_date)
                VALUES (?, ?, ?, 'Paid', DATE('now'))
            """, (emp_code, month_year, net_salary))
            
            # 2. Update Ledger
            cursor.execute("""
                UPDATE employees 
                SET last_dues_cleared_upto = ? 
                WHERE emp_code = ?
            """, (cleared_upto_date, emp_code))
            
            conn.commit()
            return True, "Success"
        except Exception as e:
            conn.rollback()
            logger.error(f"Payment Record Error: {e}")
            return False, str(e)
        finally:
            conn.close()

    def add_leave_record(self, emp_code, leave_date, leave_type):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO employee_leaves (emp_code, leave_date, leave_type, status)
                VALUES (?, ?, ?, 'Approved')
            """, (emp_code, leave_date, leave_type))
            conn.commit()
            return True, "Leave Added"
        except sqlite3.IntegrityError:
            return False, "Leave already exists"
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()