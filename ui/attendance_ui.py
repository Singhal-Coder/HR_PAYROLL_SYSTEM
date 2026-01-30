import tkinter as tk
from tkinter import messagebox
import cv2
from PIL import Image, ImageTk
import logging
import time
import threading
from datetime import datetime

from ui.styles import *
from models.attendance_model import AttendanceModel
from services.face_service import process_face_recognition
from services.attendance_service import mark_attendance as attendance_mark

logger = logging.getLogger(__name__)

class AttendanceFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=BACKGROUND_MAIN)
        self.controller = controller
        self.model = AttendanceModel()

        # --- System State ---
        self.cap = None
        self.is_running = False
        
        # UI State
        self.unknown_counter = 0
        self.last_results = [] # Stores latest face boxes [(top, right, bottom, left), name, color]
        
        # Threading State
        self.thread_lock = threading.Lock()
        self.current_frame_to_process = None
        self.is_processing = False
        self.stop_event = threading.Event()

        # Debouncing
        self.last_shown_at = {} 
        self.COOLDOWN_SECONDS = 5.0

        # RAM Cache
        self.known_face_encodings = []
        self.known_face_ids = []
        self.marked_today = set()

        self._init_ui()
        logger.info("Attendance UI Initialized (Threaded)")

        self.after(100, self.start_system)

    def _init_ui(self):
        # 1. Main Container
        self.grid_columnconfigure(0, weight=3) 
        self.grid_columnconfigure(1, weight=1) 
        self.grid_rowconfigure(0, weight=1)

        # Left: Camera
        self.left_panel = tk.Frame(self, bg="black", padx=10, pady=10)
        self.left_panel.grid(row=0, column=0, sticky="nsew")
        
        tk.Label(self.left_panel, text="Live Camera Feed", font=("Segoe UI", 12), bg="black", fg="#bdc3c7").pack(anchor="nw")
        
        self.canvas = tk.Canvas(self.left_panel, bg="#1a1a1a", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        self.status_frame = tk.Frame(self.left_panel, bg="black")
        self.status_frame.pack(fill="x", pady=10)
        self.lbl_status = tk.Label(self.status_frame, text="System Ready", font=("Segoe UI", 14), bg="black", fg="white")
        self.lbl_status.pack(side="left")

        self.btn_manual = tk.Button(self.status_frame, text="Problems? Manual Check-In", 
                                  command=self.open_manual_checkin,
                                  bg="#e74c3c", fg="white", font=("Segoe UI", 10, "bold"), 
                                  bd=0, padx=15, pady=5)
        self.btn_manual.pack_forget()

        # Right: Activity Feed
        self.right_panel = tk.Frame(self, bg="white", bd=1, relief="solid")
        self.right_panel.grid(row=0, column=1, sticky="nsew")
        self.right_panel.pack_propagate(False)

        feed_header = tk.Frame(self.right_panel, bg=SIDEBAR_BG, height=50)
        feed_header.pack(fill="x")
        tk.Label(feed_header, text="Recent Activity", font=("Segoe UI", 14, "bold"), bg=SIDEBAR_BG, fg="white").pack(pady=10)

        self.feed_container = tk.Frame(self.right_panel, bg="#f4f6f9")
        self.feed_container.pack(fill="both", expand=True, padx=5, pady=5)

    def open_manual_checkin(self):
        top = tk.Toplevel(self)
        top.title("Manual Check-In")
        top.geometry("300x250")
        top.configure(bg="white")
        
        tk.Label(top, text="Manual Entry", font=("Segoe UI", 12, "bold"), bg="white").pack(pady=10)
        tk.Label(top, text="Enter Employee Code:", bg="white").pack()
        
        e_code = tk.Entry(top, font=("Segoe UI", 12), bd=2, relief="solid")
        e_code.pack(pady=5, padx=20, fill="x")
        
        def submit():
            code = e_code.get().strip()
            if code:
                success, msg = attendance_mark(code, method="MANUAL")
                if success:
                    self.marked_today.add(code)
                    messagebox.showinfo("Success", msg)
                    top.destroy()
                else:
                    messagebox.showerror("Failed", msg)
        
        tk.Button(top, text="Verify & Mark", command=submit, 
                  bg=ACCENT_COLOR, fg="white", font=("Segoe UI", 11)).pack(pady=15)

    def start_system(self):
        if self.is_running: return

        self.lbl_status.config(text="Loading Data...", fg="#f39c12")
        self.update_idletasks()

        try:
            self.known_face_encodings, self.known_face_ids = self.model.get_all_encodings()
            self.marked_today = self.model.get_todays_attendance()
        except Exception as e:
            logger.error(f"DB Error: {e}")
            return

        try:
            self.cap = cv2.VideoCapture(0)
            if not self.cap.isOpened(): self.cap = cv2.VideoCapture(1)
            if not self.cap.isOpened(): raise Exception("No Camera Found")

            self.is_running = True
            self.stop_event.clear()
            
            # Start Background Thread for Recognition
            self.process_thread = threading.Thread(target=self.recognition_worker, daemon=True)
            self.process_thread.start()

            self.update_frame_loop() # Start UI Loop
            self.lbl_status.config(text="Scanning Active", fg=SUCCESS_COLOR)

        except Exception as e:
            logger.error(f"Start Error: {e}")
            self.lbl_status.config(text="Camera Error", fg=ERROR_COLOR)

    def recognition_worker(self):
        """Background Thread: Sirf Recognition karega"""
        while not self.stop_event.is_set():
            frame_copy = None
            
            with self.thread_lock:
                if self.current_frame_to_process is not None:
                    frame_copy = self.current_frame_to_process.copy()
                    self.current_frame_to_process = None # Clear buffer
            
            if frame_copy is None:
                time.sleep(0.05)
                continue

            try:
                # 2. Heavy Processing
                small_frame = cv2.resize(frame_copy, (0, 0), fx=0.25, fy=0.25)
                rgb_small = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

                results = process_face_recognition(
                    rgb_small, self.known_face_encodings, self.known_face_ids
                )

                # 3. Process Results
                processed_results = []
                found_unknown = False
                
                for (top, right, bottom, left), emp_code in results:
                    # Scale coordinates back
                    coords = (top*4, right*4, bottom*4, left*4)
                    
                    if emp_code is None:
                        processed_results.append((coords, "Unknown", ERROR_COLOR))
                        found_unknown = True
                    else:
                        color = ACCENT_COLOR if emp_code in self.marked_today else SUCCESS_COLOR
                        processed_results.append((coords, emp_code, color))
                        
                        # Trigger UI update in Main Thread
                        self.after(0, lambda code=emp_code: self.handle_recognition(code))


                if found_unknown:
                    self.unknown_counter += 1
                else:
                    self.unknown_counter = 0

                # 4. Update Shared State for Drawing
                self.last_results = processed_results

            except Exception as e:
                logger.error(f"Worker Error: {e}")

    def update_frame_loop(self):
        """Main Thread: Sirf Video dikhayega"""
        if not self.is_running: return

        ret, frame = self.cap.read()
        if ret:
            frame = cv2.flip(frame, 1)
            
            # Pass frame to worker thread (if free)
            with self.thread_lock:
                self.current_frame_to_process = frame

            # Draw Boxes (From last known results)
            for (top, right, bottom, left), name, color in self.last_results:
                c = tuple(int(color.lstrip("#")[i:i+2], 16) for i in (4, 2, 0))
                cv2.rectangle(frame, (left, top), (right, bottom), c, 2)

            if self.unknown_counter > 10:
                self.btn_manual.pack(side="right", padx=10)
            else:
                self.btn_manual.pack_forget()

            # Render
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Resize logic
            cw = self.canvas.winfo_width()
            ch = self.canvas.winfo_height()
            if cw > 10 and ch > 10:
                img_pil = Image.fromarray(rgb_frame)
                
                # Aspect Ratio Resize
                w, h = img_pil.size
                scale = min(cw/w, ch/h)
                new_w, new_h = int(w*scale), int(h*scale)
                img_pil = img_pil.resize((new_w, new_h), Image.Resampling.LANCZOS)
                
                imgtk = ImageTk.PhotoImage(image=img_pil)
                self.canvas.create_image(cw//2, ch//2, anchor="center", image=imgtk)
                self.canvas.imgtk = imgtk

        self.after(30, self.update_frame_loop) # Keep running smoothly

    def handle_recognition(self, emp_code):
        """UI updates (Called via self.after from worker)"""
        last_time = self.last_shown_at.get(emp_code, 0)
        if time.time() - last_time < self.COOLDOWN_SECONDS:
            return

        current_time_str = datetime.now().strftime("%H:%M:%S")
        
        if emp_code in self.marked_today:
            self.create_activity_card(f"Employee {emp_code}", current_time_str, "Already Marked", False)
        else:
            success, msg = attendance_mark(emp_code)
            if success:
                clean_name = msg.replace("Welcome, ", "")
                self.marked_today.add(emp_code)
                self.create_activity_card(clean_name, current_time_str, "Marked Present", True)
            
        self.last_shown_at[emp_code] = time.time()

    def create_activity_card(self, name, time_str, status, is_success):
        border_color = SUCCESS_COLOR if is_success else ACCENT_COLOR
        
        card = tk.Frame(self.feed_container, bg="white", bd=0, highlightbackground=border_color, highlightthickness=2)
        card.pack(side="top", fill="x", pady=5, padx=2)
        
        inner = tk.Frame(card, bg="white", padx=10, pady=10)
        inner.pack(fill="both")
        
        tk.Label(inner, text=name, font=("Segoe UI", 12, "bold"), bg="white", fg=TEXT_DARK).pack(anchor="w")
        
        row = tk.Frame(inner, bg="white")
        row.pack(fill="x", pady=(5,0))
        tk.Label(row, text=time_str, font=("Segoe UI", 10), bg="white", fg="#7f8c8d").pack(side="left")
        tk.Label(row, text=status, font=("Segoe UI", 10, "bold"), bg="white", fg=border_color).pack(side="right")
        
        if len(self.feed_container.winfo_children()) > 6:
            self.feed_container.winfo_children()[0].destroy()

    def stop_system(self):
        self.is_running = False
        self.stop_event.set() # Stop worker
        if self.cap: self.cap.release()

    def destroy(self):
        self.stop_system()
        super().destroy()