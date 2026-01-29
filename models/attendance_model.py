import sqlite3
import pickle
import logging
from datetime import datetime
from database.db_connection import Database

logger = logging.getLogger(__name__)


class AttendanceModel:
    def __init__(self):
        self.db = Database()

    def get_all_encodings(self) -> tuple[list, list]:
        """
        Load all employees' face encodings on startup.
        Returns:
            known_face_encodings (List): [encoding1, encoding2...]
            known_face_ids (List): ['E001', 'E002'...]
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()

        try:
            query = """
                SELECT f.encoding, e.emp_code
                FROM face_encodings f
                JOIN employees e ON f.emp_code = e.emp_code
                WHERE e.is_active = 1
            """
            cursor.execute(query)
            rows = cursor.fetchall()

            known_encodings = []
            known_ids = []

            for blob, emp_code in rows:
                encoding = pickle.loads(blob)
                known_encodings.append(encoding)
                known_ids.append(emp_code)

            logger.info(f"Loaded {len(known_encodings)} face samples from DB.")
            return known_encodings, known_ids

        except Exception as e:
            logger.error(f"Encoding Load Error: {e}")
            return [], []
        finally:
            conn.close()

    def get_employee_shift_info(self, emp_code: str) -> tuple[str | None, str | None]:
        """
        Returns (full_name, shift_start_str) from employees JOIN roles.
        Returns (None, None) if employee not found.
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT e.full_name, r.start_time
                FROM employees e
                JOIN roles r ON e.role_id = r.role_id
                WHERE e.emp_code = ?
                """,
                (emp_code,),
            )
            result = cursor.fetchone()
            if not result:
                return (None, None)
            full_name, shift_start_str = result
            return (full_name, shift_start_str)
        finally:
            conn.close()

    def insert_attendance(
        self,
        emp_code: str,
        date_str: str,
        time_str: str,
        status: str,
        method: str,
    ) -> tuple[bool, str]:
        """
        Pure INSERT into attendance_logs. No business logic.
        Returns (success, message). On success message is full_name for welcome text.
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                INSERT INTO attendance_logs (emp_code, date, in_time, status, method)
                VALUES (?, ?, ?, ?, ?)
                """,
                (emp_code, date_str, time_str, status, method),
            )
            conn.commit()

            cursor.execute("SELECT full_name FROM employees WHERE emp_code=?", (emp_code,))
            row = cursor.fetchone()
            full_name = row[0] if row else emp_code

            logger.info(f"Attendance inserted: {emp_code} ({method})")
            return (True, full_name)

        except sqlite3.IntegrityError:
            return (False, "Already Marked Today")

        except Exception as e:
            logger.error(f"Attendance Insert Error: {e}")
            return (False, str(e))
        finally:
            conn.close()

    def get_todays_attendance(self) -> set:
        """Get today's attendance (set of emp_code)."""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        date_str = datetime.now().strftime("%Y-%m-%d")

        cursor.execute("SELECT emp_code FROM attendance_logs WHERE date=?", (date_str,))
        marked_ids = [row[0] for row in cursor.fetchall()]

        conn.close()
        return set(marked_ids)
