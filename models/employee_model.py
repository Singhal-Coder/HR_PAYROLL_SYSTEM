import sqlite3
import pickle
import logging
from database.db_connection import Database

logger = logging.getLogger(__name__)

class EmployeeModel:
    def __init__(self):
        self.db = Database()

    def get_departments(self):
        """Fetch departments for dropdown"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT dept_id, dept_name FROM departments")
        data = cursor.fetchall()
        conn.close()
        return data

    def get_roles(self):
        """Fetch roles for dropdown"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT role_id, designation FROM roles")
        data = cursor.fetchall()
        conn.close()
        return data

    def add_employee(self, emp_data, face_encodings):
        """
        Save employee and their face samples (Atomic Transaction).
        emp_data: Dictionary {emp_code, name, salary, etc.}
        face_encodings: List of numpy arrays
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            # 1. Insert Employee Basic Details
            cursor.execute("""
                INSERT INTO employees (emp_code, full_name, joining_date, base_salary, dept_id, role_id)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                emp_data['code'], 
                emp_data['name'], 
                emp_data['joining_date'], 
                emp_data['salary'], 
                emp_data['dept_id'], 
                emp_data['role_id']
            ))
            
            # 2. Insert Face Encodings (Multiple samples)
            for encoding in face_encodings:
                # Convert numpy array to binary (BLOB)
                encoding_blob = pickle.dumps(encoding)
                
                cursor.execute("""
                    INSERT INTO face_encodings (emp_code, encoding)
                    VALUES (?, ?)
                """, (emp_data['code'], encoding_blob))
            
            conn.commit()
            logger.info(f"Employee {emp_data['code']} added with {len(face_encodings)} face samples.")
            return True, "Employee Added Successfully"
            
        except sqlite3.IntegrityError as e:
            conn.rollback()
            if "UNIQUE constraint failed: employees.emp_code" in str(e):
                return False, "Employee Code already exists!"
            logger.error(f"DB Integrity Error: {e}")
            return False, f"Database Error: {e}"
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Add Employee Error: {e}")
            return False, str(e)
            
        finally:
            conn.close()