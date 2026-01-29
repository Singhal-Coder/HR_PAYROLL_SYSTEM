import tkinter as tk
from tkinter import messagebox
from models.admin_model import AdminModel

class LoginFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.auth_model = AdminModel()
        
        # Layout Config
        self.configure(bg="#f0f2f5")
        
        # Center Box
        login_box = tk.Frame(self, bg="white", padx=40, pady=40, relief=tk.RIDGE, bd=1)
        login_box.place(relx=0.5, rely=0.5, anchor="center")
        
        # UI Elements
        tk.Label(login_box, text="HRMS Login", font=("Helvetica", 24, "bold"), bg="white", fg="#333").pack(pady=(0, 20))
        
        tk.Label(login_box, text="Username", bg="white", fg="#666").pack(anchor="w")
        self.user_entry = tk.Entry(login_box, width=30, font=("Arial", 12))
        self.user_entry.pack(pady=(0, 15))
        
        tk.Label(login_box, text="Password", bg="white", fg="#666").pack(anchor="w")
        self.pass_entry = tk.Entry(login_box, width=30, font=("Arial", 12), show="*")
        self.pass_entry.pack(pady=(0, 20))
        
        btn = tk.Button(login_box, text="Login", command=self.handle_login, 
                        bg="#1877f2", fg="white", font=("Arial", 12, "bold"), 
                        width=28, height=2, cursor="hand2", relief="flat")
        btn.pack()

    def handle_login(self):
        username = self.user_entry.get()
        password = self.pass_entry.get()
        
        if not username or not password:
            messagebox.showerror("Error", "Please fill all fields")
            return
            
        admin_id = self.auth_model.login(username, password)
        
        if admin_id:
            # Session Store (Memory mein)
            self.controller.current_user = {'id': admin_id, 'username': username}
            # Switch to Dashboard
            self.controller.show_frame("DashboardFrame")
            self.clear_fields()
        else:
            messagebox.showerror("Failed", "Invalid Username or Password")
            
    def clear_fields(self):
        self.user_entry.delete(0, tk.END)
        self.pass_entry.delete(0, tk.END)