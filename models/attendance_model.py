import sqlite3
import pickle
import logging
from datetime import datetime, time
from database.db_connection import Database

logger = logging.getLogger(__name__)

class AttendanceModel:
    def __init__(self):
        self.db = Database()

    def get_all_encodings(self):
        """
        Load all employees' face encodings on startup.
        Returns: 
            known_face_encodings (List): [encoding1, encoding2...]
            known_face_names (List): ['E001', 'E002'...]
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            # Join to get Name for "Welcome Rahul" message
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
                encoding = pickle.loads(blob) # Blob -> Numpy Array (Face Encoding)
                known_encodings.append(encoding)
                known_ids.append(emp_code)
                
            logger.info(f"Loaded {len(known_encodings)} face samples from DB.")
            return known_encodings, known_ids
            
        except Exception as e:
            logger.error(f"Encoding Load Error: {e}")
            return [], []
        finally:
            conn.close()

    def mark_attendance(self, emp_code, method="FACE"):
        """
        Insert attendance into database.
        Returns: (Success: Bool, Message: Str)
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        now = datetime.now()
        date_str = now.strftime('%Y-%m-%d')
        time_str = now.strftime('%H:%M:%S')
        
        try:
            query = """
                SELECT e.full_name, r.start_time 
                FROM employees e
                JOIN roles r ON e.role_id = r.role_id
                WHERE e.emp_code = ?
            """
            cursor.execute(query, (emp_code,))
            result = cursor.fetchone()
            if not result:
                return False, "Employee Not Found"
                
            full_name, shift_start_str = result
            status = "Present"
            if shift_start_str:
                try:
                    shift_start = datetime.strptime(shift_start_str, "%H:%M:%S").time()
                    current_time = now.time()
                    
                    if current_time > shift_start:
                        status = "Late"
                except ValueError:
                    logger.warning(f"Time format error for {emp_code}, defaulting to Present")
            cursor.execute("""
                INSERT INTO attendance_logs (emp_code, date, in_time, status, method)
                VALUES (?, ?, ?, ?, ?)
            """, (emp_code, date_str, time_str, status, method))
            
            conn.commit()
            
            # Fetch Employee Name for Welcome Message
            cursor.execute("SELECT full_name FROM employees WHERE emp_code=?", (emp_code,))
            name = cursor.fetchone()[0]
            
            logger.info(f"Attendance Marked: {emp_code} ({method})")
            return True, f"Welcome, {name}"
            
        except sqlite3.IntegrityError:
            # UNIQUE constraint failed -> Attendance already marked today
            return False, "Already Marked Today"
            
        except Exception as e:
            logger.error(f"Attendance Error: {e}")
            return False, str(e)
        finally:
            conn.close()

    def get_todays_attendance(self):
        """Get today's attendance (RAM Cache Update)"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        date_str = datetime.now().strftime('%Y-%m-%d')
        
        cursor.execute("SELECT emp_code FROM attendance_logs WHERE date=?", (date_str,))
        marked_ids = [row[0] for row in cursor.fetchall()]
        
        conn.close()
        return set(marked_ids)