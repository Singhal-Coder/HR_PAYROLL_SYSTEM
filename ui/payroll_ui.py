import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
from datetime import datetime
import os
import subprocess
import platform

from ui.styles import *
from services.payroll_service import PayrollService
from models.employee_model import EmployeeModel # To get list of employees

class PayrollFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=BACKGROUND_MAIN)
        self.controller = controller
        self.service = PayrollService()
        self.emp_model = EmployeeModel() # Reusing to fetch employee list
        
        self._init_ui()

    def _init_ui(self):
        # Header
        header = tk.Frame(self, bg="white", padx=20, pady=15)
        header.pack(fill="x")
        tk.Label(header, text="Payroll Management", font=FONT_HEADER, bg="white", fg=TEXT_DARK).pack(side="left")

        # Controls (Month Selection)
        controls = tk.Frame(self, bg=BACKGROUND_MAIN, pady=10)
        controls.pack(fill="x", padx=20)
        
        tk.Label(controls, text="Select Month:", font=FONT_NORMAL, bg=BACKGROUND_MAIN).pack(side="left")
        
        self.month_var = tk.StringVar(value=str(datetime.now().month))
        self.year_var = tk.StringVar(value=str(datetime.now().year))
        
        month_cb = ttk.Combobox(controls, textvariable=self.month_var, values=[str(i) for i in range(1, 13)], width=5)
        month_cb.pack(side="left", padx=5)
        
        year_cb = ttk.Combobox(controls, textvariable=self.year_var, values=["2025", "2026"], width=6)
        year_cb.pack(side="left", padx=5)
        
        btn_process = tk.Button(controls, text="Calculate Payroll", command=self.load_data, 
                              bg=ACCENT_COLOR, fg="white", font=FONT_BOLD)
        btn_process.pack(side="left", padx=20)

        # Table
        columns = ("code", "name", "present", "leaves", "net_salary", "status")
        self.tree = ttk.Treeview(self, columns=columns, show="headings", height=15)
        
        self.tree.heading("code", text="Emp Code")
        self.tree.heading("name", text="Name")
        self.tree.heading("present", text="Present Days")
        self.tree.heading("leaves", text="Approved Leaves")
        self.tree.heading("net_salary", text="Net Salary (₹)")
        self.tree.heading("status", text="Action")
        
        self.tree.column("code", width=80)
        self.tree.column("name", width=150)
        self.tree.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Action Buttons
        btn_frame = tk.Frame(self, bg=BACKGROUND_MAIN)
        btn_frame.pack(fill="x", padx=20, pady=10)
        
        # Left Side: Leave Management
        tk.Button(btn_frame, text="+ Add Leave", command=self.open_add_leave_dialog,
                 bg="#e67e22", fg="white", font=FONT_BOLD, padx=15).pack(side="left")

        # Right Side: Payroll Actions
        tk.Button(btn_frame, text="Generate PDF", command=self.generate_pdf, 
                 bg="#34495e", fg="white", font=FONT_BOLD, padx=15).pack(side="right", padx=5)
                 
        tk.Button(btn_frame, text="✓ Mark as Paid", command=self.mark_paid, 
                 bg="#27ae60", fg="white", font=FONT_BOLD, padx=15).pack(side="right", padx=5)

    def load_data(self):
        # Clear Table
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        # Get all employees
        # Note: Ideally EmployeeModel should have get_all_employees(), assume direct DB fetch here for speed
        conn = self.emp_model.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT emp_code FROM employees WHERE is_active=1")
        emps = cursor.fetchall()
        conn.close()
        
        self.current_payroll_data = []
        
        for (code,) in emps:
            data = self.service.calculate_salary(code, int(self.month_var.get()), int(self.year_var.get()))
            if data:
                self.current_payroll_data.append(data)
                self.tree.insert("", "end", values=(
                    data['emp_code'], data['name'], data['present_days'], 
                    data['leaves'], data['net_salary'], "Ready"
                ))

    def generate_pdf(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Select Employee", "Please select an employee row to generate payslip.")
            return
            
        item = self.tree.item(selected_item)
        code = item['values'][0]
        
        # Find data
        data = next((x for x in self.current_payroll_data if x['emp_code'] == code), None)
        if data:
            path = self.service.generate_payslip_pdf(data)
            messagebox.showinfo("Success", f"Payslip saved at:\n{path}")
            
            # Open PDF automatically (Platform dependent)
            if platform.system() == 'Windows':
                os.startfile(path)
            elif platform.system() == 'Linux':
                subprocess.call(['xdg-open', path])

    def mark_paid(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Select Employee", "Select an employee to mark as paid.")
            return
            
        item = self.tree.item(selected_item)
        code = item['values'][0]
        net_salary = float(item['values'][4]) # Fetch from tree column
        
        confirm = messagebox.askyesno("Confirm Payment", f"Mark ₹{net_salary} as PAID for {code}?")
        if confirm:
            month = int(self.month_var.get())
            year = int(self.year_var.get())
            
            success, msg = self.service.mark_as_paid(code, month, year, net_salary)
            if success:
                messagebox.showinfo("Success", msg)
                self.load_data() # Refresh list
            else:
                messagebox.showerror("Error", msg)

    def open_add_leave_dialog(self):
        top = tk.Toplevel(self)
        top.title("Add Leave Record")
        top.geometry("300x250")
        top.configure(bg="white")
        
        tk.Label(top, text="Employee Code:", bg="white").pack(pady=5)
        # Dropdown for employees ideally, but Text Entry for speed
        e_code = tk.Entry(top) 
        e_code.pack(pady=5)
        
        tk.Label(top, text="Date:", bg="white").pack(pady=5)
        e_date = DateEntry(top, date_pattern='yyyy-mm-dd')
        e_date.pack(pady=5)
        
        def submit():
            code = e_code.get().strip()
            date = e_date.get_date().strftime('%Y-%m-%d')
            
            if not code: return
            
            success, msg = self.service.add_leave(code, date)
            if success:
                messagebox.showinfo("Done", msg)
                top.destroy()
                self.load_data() # Refresh if needed
            else:
                messagebox.showerror("Error", msg)
                
        tk.Button(top, text="Save Leave", command=submit, bg=ACCENT_COLOR, fg="white").pack(pady=20)