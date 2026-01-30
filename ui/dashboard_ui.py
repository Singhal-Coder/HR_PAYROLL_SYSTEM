import tkinter as tk
from datetime import datetime

from models.dashboard_model import DashboardModel
from ui.styles import *

from ui.employee_ui import EmployeeFrame 
from ui.attendance_ui import AttendanceFrame
from ui.payroll_ui import PayrollFrame

class DashboardFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        # 1. Main Layout (Grid: 2 Columns)
        # Col 0: Sidebar (Fixed width), Col 1: Content (Expandable)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # --- Sidebar (Left) ---
        self.sidebar = tk.Frame(self, bg=SIDEBAR_BG, width=250)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False) # Width fix rakho
        
        # App Title in Sidebar
        tk.Label(self.sidebar, text="Smart HRMS", font=FONT_HEADER, 
                 bg=SIDEBAR_BG, fg=TEXT_WHITE).pack(pady=(30, 50))
        
        # Navigation Buttons
        self.nav_buttons = {}
        self.create_nav_button("Dashboard", self.show_home)
        self.create_nav_button("Employees", self.show_employees)
        self.create_nav_button("Attendance", self.show_attendance)
        self.create_nav_button("Payroll", self.show_payroll)
        
        # Logout at bottom
        btn_logout = tk.Button(self.sidebar, text="Logout", 
                             command=lambda: controller.show_frame("LoginFrame"),
                             **BTN_STYLE_SIDEBAR)
        btn_logout.pack(side="bottom", fill="x", pady=20)
        
        # --- Content Area (Right) ---
        self.content_area = tk.Frame(self, bg=BACKGROUND_MAIN)
        self.content_area.grid(row=0, column=1, sticky="nsew")
        
        # Default View
        self.current_frame = None
        self.show_home()

    def create_nav_button(self, text, command):
        """Helper to create consistent sidebar buttons"""
        btn = tk.Button(self.sidebar, text=f"  {text}", command=command, **BTN_STYLE_SIDEBAR)
        btn.pack(fill="x", pady=2)
        self.nav_buttons[text] = btn

    def switch_content(self, frame_class):
        """Right side area mein frame replace karta hai"""
        if self.current_frame:
            self.current_frame.destroy()
            
        self.current_frame = frame_class(self.content_area, self.controller)
        self.current_frame.pack(fill="both", expand=True, padx=20, pady=20)

    # --- Navigation Handlers ---
    def show_home(self):
        self.switch_content(HomeView)
        
    def show_employees(self):
        self.switch_content(EmployeeFrame)
        
    def show_attendance(self):
        self.switch_content(AttendanceFrame)
        
    def show_payroll(self):
        self.switch_content(PayrollFrame)

class HomeView(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=BACKGROUND_MAIN)
        self.model = DashboardModel()
        
        tk.Label(self, text="Dashboard Overview", font=FONT_HEADER, 
                 bg=BACKGROUND_MAIN, fg=TEXT_DARK).pack(anchor="w")
        
        # KPI Cards Placeholder
        stats_frame = tk.Frame(self, bg=BACKGROUND_MAIN)
        stats_frame.pack(fill="x", pady=20)
        
        # Cards create karke Labels ko store kar rahe hain taaki update kar sakein
        self.lbl_total = self.create_card(stats_frame, "Total Employees", "Loading...", 0)
        self.lbl_present = self.create_card(stats_frame, "Present Today", "0", 1)
        self.lbl_pending = self.create_card(stats_frame, "Pending Issues", "0", 2) # Placeholder logic

        # Data Load Trigger
        self.refresh_data()

    def create_card(self, parent, title, value, col):
        card = tk.Frame(parent, bg="white", padx=20, pady=20, relief="flat")
        card.grid(row=0, column=col, padx=10, sticky="ew")
        parent.grid_columnconfigure(col, weight=1)
        
        tk.Label(card, text=title, font=FONT_NORMAL, bg="white", fg="#7f8c8d").pack(anchor="w")
        
        # Value Label return kar rahe hain
        lbl = tk.Label(card, text=value, font=("Segoe UI", 24, "bold"), bg="white", fg=ACCENT_COLOR)
        lbl.pack(anchor="w")
        return lbl

    def refresh_data(self):
        stats = self.model.get_dashboard_stats()
        
        self.lbl_total.config(text=str(stats['total_emp']))
        self.lbl_present.config(text=str(stats['present_today']))
        self.lbl_pending.config(text=str(stats['pending']))