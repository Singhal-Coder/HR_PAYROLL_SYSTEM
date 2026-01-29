import tkinter as tk
from ui.login_ui import LoginFrame
from ui.dashboard_ui import DashboardFrame

class MainWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        
        self.title("Smart HRMS - Enterprise Edition")
        
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        self.geometry(f"{int(screen_width*0.8)}x{int(screen_height*0.8)}")
        
        # --- Cross-Platform Maximize Logic ---
        try:
            # For Windows
            self.state('zoomed')
        except tk.TclError:
            try:
                # For Linux
                self.attributes('-zoomed', True)
            except tk.TclError:
                # Fallback: If both fail, set geometry to screen size
                self.geometry(f"{screen_width}x{screen_height}")
        # -------------------------------------

        # Container to hold all frames (main content area)
        self.container = tk.Frame(self)
        self.container.pack(side="top", fill="both", expand=True)
        
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)
        
        # Dictionary to store frames (all pages)
        self.frames = {}
        
        # Initialize Frames
        for F in (LoginFrame, DashboardFrame): 
            page_name = F.__name__
            frame = F(parent=self.container, controller=self)
            self.frames[page_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")
            
        self.show_frame("LoginFrame")

    def show_frame(self, page_name):
        """Show the given page name at the top."""
        frame = self.frames[page_name]
        frame.tkraise()
        
    def get_user_session(self):
        """Global User Session storage"""
        return getattr(self, 'current_user', None)

if __name__ == "__main__":
    app = MainWindow()
    app.mainloop()