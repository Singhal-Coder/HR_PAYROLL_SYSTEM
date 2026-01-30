import os
import calendar
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
import logging

from models.payroll_model import PayrollModel

logger = logging.getLogger(__name__)

class PayrollService:
    def __init__(self):
        self.model = PayrollModel()

    def calculate_salary(self, emp_code, month, year):
        """
        Pure Business Logic Layer.
        Fetches data from Model -> Applies Math -> Returns Result.
        """
        month_str = f"{year}-{month:02d}"          # For Exact Match
        wildcard_str = f"{year}-{month:02d}%"      # For LIKE query
        
        # --- DATA FETCHING ---
        data = self.model.get_salary_components(emp_code, month_str, wildcard_str)
        if not data:
            return None
            
        (name, base, pf_pct, tax_ded, bonus, dept, role), present_days, leave_days = data

        # --- BUSINESS LOGIC ---
        payable_days = present_days + leave_days
        
        # 1. Earned Basic
        earned_basic = (base / 30) * payable_days
        
        # 2. Earnings
        gross_earnings = earned_basic + (bonus * present_days)
        
        # 3. Deductions
        pf_amt = earned_basic * pf_pct
        
        # Edge Case: No Tax if 0 earnings
        final_tax = tax_ded if gross_earnings > 0 else 0
        
        # 4. Net Pay
        net_salary = gross_earnings - pf_amt - final_tax
        if net_salary < 0: net_salary = 0

        return {
            "emp_code": emp_code,
            "name": name,
            "dept": dept,
            "role": role,
            "month_year": f"{datetime.now().strftime('%B')} {year}",
            "base_salary": base,
            "present_days": present_days,
            "leaves": leave_days,
            "pf": round(pf_amt, 2),
            "tax": final_tax,
            "bonus": round(bonus * present_days, 2),
            "net_salary": round(net_salary, 2),
            "status": "Generated"
        }

    def mark_as_paid(self, emp_code, month, year, net_salary):
        """Delegates update to Model"""
        month_year_txt = f"{month}-{year}"
        
        # Calculate Last Day of Month for Ledger
        last_day = calendar.monthrange(year, month)[1]
        cleared_date = f"{year}-{month:02d}-{last_day}"
        
        return self.model.record_payment(emp_code, month_year_txt, net_salary, cleared_date)

    def add_leave(self, emp_code, leave_date, leave_type="Casual"):
        """Delegates insert to Model"""
        return self.model.add_leave_record(emp_code, leave_date, leave_type)

    def generate_payslip_pdf(self, salary_data):
        """Generates a PDF payslip and returns the filepath."""
        if not os.path.exists("payslips"):
            os.makedirs("payslips")

        filename = f"payslips/Payslip_{salary_data['emp_code']}_{salary_data['month_year'].replace(' ', '_')}.pdf"
        c = canvas.Canvas(filename, pagesize=letter)
        width, height = letter

        # Header
        c.setFont("Helvetica-Bold", 20)
        c.drawString(50, height - 50, "SMART HRMS - MONTHLY PAYSLIP")
        
        c.setFont("Helvetica", 12)
        c.drawString(50, height - 80, f"Employee: {salary_data['name']} ({salary_data['emp_code']})")
        c.drawString(50, height - 100, f"Department: {salary_data['dept']} | Role: {salary_data['role']}")
        c.drawString(400, height - 80, f"Period: {salary_data['month_year']}")

        # Line
        c.line(50, height - 120, 550, height - 120)

        # Earnings Table
        y = height - 150
        c.drawString(50, y, "EARNINGS")
        c.drawString(300, y, "DEDUCTIONS")
        y -= 20
        
        c.setFont("Helvetica", 10)
        # Left Side (Earnings)
        c.drawString(50, y, f"Base Salary: {salary_data['base_salary']}")
        c.drawString(50, y-20, f"Payable Days: {salary_data['present_days'] + salary_data['leaves']}")
        c.drawString(50, y-40, f"Performance Bonus: {salary_data['bonus']}")
        
        # Right Side (Deductions)
        c.drawString(300, y, f"Provident Fund (PF): {salary_data['pf']}")
        c.drawString(300, y-20, f"Professional Tax: {salary_data['tax']}")

        # Total
        c.setFont("Helvetica-Bold", 14)
        c.setFillColor(colors.darkblue)
        c.drawString(50, y-80, f"NET PAYABLE SALARY: INR {salary_data['net_salary']}")

        c.save()
        logger.info(f"Payslip generated: {filename}")
        return filename

        """Simple method to add a leave record manually."""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO employee_leaves (emp_code, leave_date, leave_type, status)
                VALUES (?, ?, ?, 'Approved')
            """, (emp_code, leave_date, leave_type))
            conn.commit()
            return True, "Leave Added Successfully"
        except sqlite3.IntegrityError:
            return False, "Leave already exists for this date"
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()