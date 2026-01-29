import tkinter as tk
from tkinter import messagebox
import cv2
import face_recognition
import numpy as np
from PIL import Image, ImageTk
import logging

from ui.styles import *
from models.attendance_model import AttendanceModel

logger = logging.getLogger(__name__)

class AttendanceFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=BACKGROUND_MAIN)
        self.controller = controller
        self.model = AttendanceModel()
        
        # --- System State ---
        self.cap = None
        self.is_running = False
        self.process_this_frame = True
        self.unknown_counter = 0 
        
        # RAM Cache
        self.known_face_encodings = []
        self.known_face_ids = []
        self.marked_today = set()

        # UI Layout
        self._init_ui()
        logger.info("Attendance UI Initialized")
        
        self.after(100, self.start_system) 

    def _init_ui(self):
        # Header
        header = tk.Frame(self, bg=SIDEBAR_BG, height=60)
        header.pack(fill="x")
        tk.Label(header, text="  Live Attendance System", font=FONT_HEADER, bg=SIDEBAR_BG, fg="white").pack(side="left", pady=10)
        
        # Main Content (Video Feed)
        self.video_frame = tk.Frame(self, bg="black", bd=2, relief="sunken")
        self.video_frame.pack(expand=True, fill="both", padx=20, pady=20)
        
        # Canvas
        self.canvas = tk.Canvas(self.video_frame, bg="black", width=640, height=480)
        self.canvas.pack()
        
        # Status Bar
        self.lbl_status = tk.Label(self, text="System Ready", font=("Segoe UI", 16), bg=BACKGROUND_MAIN, fg=TEXT_DARK)
        self.lbl_status.pack(pady=10)
        
        # Manual Check-in Button
        self.btn_manual = tk.Button(self, text="Manual Check-In", command=self.open_manual_checkin,
                                    bg="#e74c3c", fg="white", font=FONT_BOLD, state="disabled")

    def start_system(self):
        # 1. Stop existing camera if any
        if self.is_running:
            self.stop_system()

        logger.info("Starting Attendance System...")
        
        # 2. Load Data
        self.lbl_status.config(text="Loading Biometric Data...", fg="#e67e22")
        self.update_idletasks()
        
        try:
            self.known_face_encodings, self.known_face_ids = self.model.get_all_encodings()
            self.marked_today = self.model.get_todays_attendance()
            logger.info(f"Loaded {len(self.known_face_encodings)} faces from DB.")
        except Exception as e:
            logger.error(f"Data Load Error: {e}")
            messagebox.showerror("Error", "Failed to load database")
            return

        # 3. Start Camera
        try:
            self.cap = cv2.VideoCapture(0)
            
            if not self.cap.isOpened():
                logger.critical("Camera failed to open! trying Index 1...")
                self.cap = cv2.VideoCapture(1) # Try alternative index
                if not self.cap.isOpened():
                    raise Exception("Could not open video device (Index 0 or 1)")

            self.is_running = True
            self.process_this_frame = True
            
            # Loop Start
            self.update_frame()
            self.lbl_status.config(text="Scanning...", fg=ACCENT_COLOR)
            logger.info("Camera Started Successfully.")
            
        except Exception as e:
            logger.error(f"Camera Start Error: {e}")
            self.lbl_status.config(text="Camera Error", fg=ERROR_COLOR)
            messagebox.showerror("Camera Error", f"Cannot access webcam.\nDetails: {e}")

    def stop_system(self):
        self.is_running = False
        if self.cap:
            self.cap.release()
            self.cap = None
        self.canvas.delete("all")
        self.btn_manual.pack_forget()

    def update_frame(self):
        if not self.is_running or not self.cap:
            return

        try:
            ret, frame = self.cap.read()
            if not ret:
                self.after(10, self.update_frame)
                return

            # Mirror Effect (Better UX)
            frame = cv2.flip(frame, 1)

            # --- LOGIC START ---
            small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
            rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

            face_locations = []
            face_names = []
            face_colors = []

            if self.process_this_frame:
                face_locations = face_recognition.face_locations(rgb_small_frame)
                
                if face_locations:
                    face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

                    for face_encoding in face_encodings:
                        matches = face_recognition.compare_faces(self.known_face_encodings, face_encoding, tolerance=0.5)
                        name = "Unknown"
                        color = "#e74c3c" # Red

                        if True in matches:
                            first_match_index = matches.index(True)
                            emp_code = self.known_face_ids[first_match_index]
                            
                            if emp_code in self.marked_today:
                                name = f"{emp_code}"
                                color = "#3498db" # Blue
                                self.unknown_counter = 0
                            else:
                                success, msg = self.model.mark_attendance(emp_code)
                                if success:
                                    self.marked_today.add(emp_code)
                                    name = msg
                                    color = "#2ecc71" # Green
                                    self.unknown_counter = 0
                        else:
                            self.unknown_counter += 1

                        face_names.append(name)
                        face_colors.append(color)
                else:
                    self.unknown_counter = 0

            self.process_this_frame = not self.process_this_frame

            # --- DRAWING ---
            for (top, right, bottom, left), name, color in zip(face_locations, face_names, face_colors):
                top *= 4
                right *= 4
                bottom *= 4
                left *= 4

                cv_color = tuple(int(color.lstrip('#')[i:i+2], 16) for i in (4, 2, 0))
                cv2.rectangle(frame, (left, top), (right, bottom), cv_color, 2)
                cv2.rectangle(frame, (left, bottom - 35), (right, bottom), cv_color, cv2.FILLED)
                cv2.putText(frame, name, (left + 6, bottom - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

            # Manual Button Logic
            if self.unknown_counter > 30:
                self.btn_manual.pack(pady=5)
                self.lbl_status.config(text="Not Recognized? Use Manual Check-in", fg=ERROR_COLOR)
            else:
                self.btn_manual.pack_forget()
                if not face_locations:
                    self.lbl_status.config(text="Scanning...", fg=TEXT_DARK)

            # Render
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(rgb_frame)
            imgtk = ImageTk.PhotoImage(image=img)
            self.canvas.create_image(0, 0, anchor="nw", image=imgtk)
            self.canvas.imgtk = imgtk

            self.after(30, self.update_frame)

        except Exception as e:
            logger.error(f"Update Loop Crashed: {e}")
            self.stop_system()

    def open_manual_checkin(self):
        top = tk.Toplevel(self)
        top.title("Manual Check-In")
        top.geometry("300x200")
        top.configure(bg="white")
        
        tk.Label(top, text="Enter Employee Code", bg="white", font=FONT_NORMAL).pack(pady=10)
        e_code = tk.Entry(top, font=FONT_NORMAL, bd=2)
        e_code.pack(pady=5)
        
        def submit():
            code = e_code.get().strip()
            if not code: return
            
            success, msg = self.model.mark_attendance(code, method="MANUAL")
            if success:
                messagebox.showinfo("Success", msg)
                self.marked_today.add(code)
                top.destroy()
            else:
                messagebox.showerror("Failed", msg)
                
        tk.Button(top, text="Mark Present", command=submit, bg=ACCENT_COLOR, fg="white").pack(pady=20)

    def destroy(self):
        """Cleanup jab user dusre tab par jaye"""
        logger.info("Cleaning up Attendance Frame...")
        self.stop_system()
        super().destroy()