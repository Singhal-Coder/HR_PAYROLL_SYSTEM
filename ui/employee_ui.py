import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
import cv2
from PIL import Image, ImageTk
import logging

from ui.styles import *
from models.employee_model import EmployeeModel
from services.face_service import detect_head_pose, get_face_landmarks, get_face_encodings

logger = logging.getLogger(__name__)

class EmployeeFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=BACKGROUND_MAIN)
        self.controller = controller
        self.model = EmployeeModel()
        
        # --- State Variables ---
        self.cap = None
        self.is_camera_on = False
        self.captured_encodings = [] # To store 5 frames (3 Front, 1 Left, 1 Right)
        
        # State Machine: 'IDLE', 'FRONT', 'LEFT', 'RIGHT', 'DONE'
        self.capture_state = 'IDLE' 
        self.frame_stability_counter = 0 # To ensure pose is stable before capturing
        
        # UI Layout
        self.grid_columnconfigure(0, weight=1) # Form
        self.grid_columnconfigure(1, weight=1) # Camera
        self.grid_rowconfigure(0, weight=1)

        self._init_ui()
        
    def _init_ui(self):
        # === LEFT SIDE: FORM (Compact 2-Col Grid) ===
        form_frame = tk.Frame(self, bg="white", padx=20, pady=20)
        form_frame.grid(row=0, column=0, sticky="nsew", padx=15, pady=15)
        
        tk.Label(form_frame, text="New Employee Registration", font=FONT_SUBHEADER, 
                 bg="white", fg=TEXT_DARK).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 20))
        
        # Helper to create inputs
        def add_field(label, var_name, r, c):
            tk.Label(form_frame, text=label, bg="white", font=FONT_NORMAL, fg="#7f8c8d").grid(row=r, column=c, sticky="w", pady=(5, 0), padx=5)
            entry = tk.Entry(form_frame, font=FONT_NORMAL, bg="#f8f9fa", relief="flat", bd=1)
            entry.grid(row=r+1, column=c, sticky="ew", pady=(0, 10), padx=5)
            setattr(self, var_name, entry)

        # Row 1
        add_field("Employee Code", "code_entry", 1, 0)
        add_field("Full Name", "name_entry", 1, 1)
        
        # Row 2
        # add_field("Joining Date (YYYY-MM-DD)", "date_entry", 3, 0)
        tk.Label(form_frame, text="Joining Date", bg="white", font=FONT_NORMAL, fg="#7f8c8d").grid(row=3, column=0, sticky="w", pady=(5, 0), padx=5)
        self.date_entry = DateEntry(form_frame, font=FONT_NORMAL, bg="#f8f9fa", date_pattern='yyyy-mm-dd')
        self.date_entry.grid(row=4, column=0, sticky="ew", pady=(0, 10), padx=5)

        add_field("Base Salary (₹)", "salary_entry", 3, 1)

        
        
        # Row 3 (Dropdowns)
        tk.Label(form_frame, text="Department", bg="white", font=FONT_NORMAL, fg="#7f8c8d").grid(row=5, column=0, sticky="w", padx=5)
        self.dept_combo = ttk.Combobox(form_frame, state="readonly", font=FONT_NORMAL)
        self.dept_combo.grid(row=6, column=0, sticky="ew", padx=5, pady=(0, 10))
        
        tk.Label(form_frame, text="Role", bg="white", font=FONT_NORMAL, fg="#7f8c8d").grid(row=5, column=1, sticky="w", padx=5)
        self.role_combo = ttk.Combobox(form_frame, state="readonly", font=FONT_NORMAL)
        self.role_combo.grid(row=6, column=1, sticky="ew", padx=5, pady=(0, 10))

        # Save Button (Initially Disabled)
        self.btn_save = tk.Button(form_frame, text="Save Employee (Capture First)", command=self.save_employee,
                                  bg="#95a5a6", fg="white", font=FONT_BOLD, relief="flat", pady=12, state="disabled")
        self.btn_save.grid(row=7, column=0, columnspan=2, sticky="ew", pady=20)
        
        self._load_dropdowns()

        # === RIGHT SIDE: SMART CAMERA ===
        cam_frame = tk.Frame(self, bg=SIDEBAR_BG, padx=10, pady=10)
        cam_frame.grid(row=0, column=1, sticky="nsew", padx=(0, 15), pady=15)
        
        tk.Label(cam_frame, text="Biometric Auto-Capture", font=FONT_SUBHEADER, 
                 bg=SIDEBAR_BG, fg="white").pack(pady=(0, 10))
        
        # Instruction Banner
        self.lbl_instruction = tk.Label(cam_frame, text="Click 'Start Camera' to Begin", 
                                      font=("Segoe UI", 14, "bold"), bg="#e67e22", fg="white", width=30)
        self.lbl_instruction.pack(pady=5)
        
        # Video Canvas
        self.cam_canvas = tk.Canvas(cam_frame, bg="black", width=440, height=330)
        self.cam_canvas.pack(pady=10)
        
        # Controls
        self.btn_start = tk.Button(cam_frame, text="Start Camera", command=self.toggle_camera, 
                                 bg=ACCENT_COLOR, fg="white", font=FONT_BOLD, width=20, pady=5)
        self.btn_start.pack(pady=10)
        
        # Progress Bar
        self.progress = ttk.Progressbar(cam_frame, orient="horizontal", length=400, mode="determinate")
        self.progress.pack(pady=10)

    def _load_dropdowns(self):
        try:
            depts = self.model.get_departments()
            self.dept_map = {name: id for id, name in depts}
            self.dept_combo['values'] = list(self.dept_map.keys())
            
            roles = self.model.get_roles()
            self.role_map = {name: id for id, name in roles}
            self.role_combo['values'] = list(self.role_map.keys())
        except Exception:
            pass

    # --- CAMERA & AUTO-CAPTURE LOGIC ---
    def toggle_camera(self):
        if not self.is_camera_on:
            try:
                self.cap = cv2.VideoCapture(0)
                if not self.cap.isOpened():
                    raise Exception("Camera Access Denied")
                
                self.is_camera_on = True
                self.btn_start.config(text="Stop Camera", bg=ERROR_COLOR)
                self.captured_encodings = []
                self.capture_state = 'FRONT' # Start State
                self.progress['value'] = 0
                self.update_frame()
            except Exception as e:
                messagebox.showerror("Camera Error", str(e))
                logger.error(f"Camera Start Error: {e}")
        else:
            self.stop_camera()

    def stop_camera(self):
        self.is_camera_on = False
        if self.cap:
            self.cap.release()
        self.btn_start.config(text="Start Camera", bg=ACCENT_COLOR)
        self.cam_canvas.delete("all")
        self.lbl_instruction.config(text="Camera Stopped", bg=SIDEBAR_BG)

    def update_frame(self):
        if not self.is_camera_on: return

        try:
            ret, frame = self.cap.read()
            if not ret:
                logger.error("Failed to read frame")
                return

            # Mirror Effect (Better UX)
            frame = cv2.flip(frame, 1)
            
            # Processing Logic (Pose & Auto Capture)
            frame_processed = self.process_auto_capture(frame)
            
            # Render to UI
            rgb_frame = cv2.cvtColor(frame_processed, cv2.COLOR_BGR2RGB)
            rgb_frame = cv2.resize(rgb_frame, (440, 330))
            img = Image.fromarray(rgb_frame)
            imgtk = ImageTk.PhotoImage(image=img)
            self.cam_canvas.create_image(0, 0, anchor="nw", image=imgtk)
            self.cam_canvas.imgtk = imgtk

            if self.capture_state != 'DONE':
                self.after(30, self.update_frame) # Keep loop running
            else:
                self.finalize_capture(rgb_frame)

        except Exception as e:
            logger.error(f"Frame Update Error: {e}")
            self.stop_camera()

    def process_auto_capture(self, frame):
        """State Machine for capturing 3 Front, 1 Left, 1 Right"""
        
        # --- STATE MACHINE ---
        target_pose = 'FRONT'
        if self.capture_state == 'FRONT':
            target_pose = 'FRONT'
            self.update_instruction("Look Straight 😐", "#3498db")
            
        elif self.capture_state == 'LEFT':
            target_pose = 'LEFT'
            self.update_instruction("Turn Head Left ⬅️", "#e67e22")
            
        elif self.capture_state == 'RIGHT':
            target_pose = 'RIGHT'
            self.update_instruction("Turn Head Right ➡️", "#e67e22")
        
        # Resize for speed
        small_frame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
        rgb_small = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
        
        # Detect Landmarks
        landmarks_list = get_face_landmarks(rgb_small)
        
        if not landmarks_list:
            self.update_instruction("No Face Detected", "#e74c3c")
            return frame
        
        # Assuming single face
        landmarks = landmarks_list[0]
        
        pose = detect_head_pose(landmarks)

        # Capture Logic
        if pose == target_pose:
            self.frame_stability_counter += 1
            # Draw Green Box to indicate "Good"
            h, w, _ = frame.shape
            cv2.rectangle(frame, (20, 20), (w-20, h-20), (0, 255, 0), 4)
            
            # Require 10 consecutive stable frames (~0.3s)
            if self.frame_stability_counter > 8:
                self._capture_snap(rgb_small)
                self.frame_stability_counter = 0 # Reset
        else:
            self.frame_stability_counter = 0 # Reset if user moves

        return frame

    def _capture_snap(self, rgb_frame):
        """Encodings generate karta hai aur state change karta hai"""
        encodings = get_face_encodings(rgb_frame)
        if not encodings:
            return
        
        self.captured_encodings.append(encodings[0])
        count = len(self.captured_encodings)
        self.progress['value'] = (count / 5) * 100
        
        # State Transitions
        if count < 3:
            self.capture_state = 'FRONT' # Keep taking Front
        elif count == 3:
            self.capture_state = 'LEFT' # Next state is LEFT
        elif count == 4:
            self.capture_state = 'RIGHT' # Next
        elif count == 5:
            self.capture_state = 'DONE' # Finished

    def update_instruction(self, text, color):
        self.lbl_instruction.config(text=text, bg=color)

    def finalize_capture(self, last_frame):
        """Freeze frame and Show Success"""
        self.stop_camera()
        
        # Overlay Success
        img_pil = Image.fromarray(last_frame)
        imgtk = ImageTk.PhotoImage(image=img_pil)
        self.cam_canvas.create_image(0, 0, anchor="nw", image=imgtk)
        self.cam_canvas.imgtk = imgtk
        
        self.cam_canvas.create_text(220, 165, text="✔", font=("Arial", 60), fill="#2ecc71")
        self.lbl_instruction.config(text="Capture Complete!", bg=SUCCESS_COLOR)
        
        # Enable Save
        self.btn_save.config(state="normal", bg=SUCCESS_COLOR, text="Save Employee Now")

    def save_employee(self):
        # Basic Validation and Save call to Model (Same as before)
        if not self.code_entry.get() or not self.name_entry.get():
             messagebox.showerror("Error", "Please fill required fields")
             return
             
        try:
            data = {
                'code': self.code_entry.get(),
                'name': self.name_entry.get(),
                'joining_date': self.date_entry.get_date().strftime('%Y-%m-%d'),
                # 'joining_date': self.date_entry.get(),
                'salary': float(self.salary_entry.get() or 0),
                'dept_id': self.dept_map.get(self.dept_combo.get()),
                'role_id': self.role_map.get(self.role_combo.get())
            }
            success, msg = self.model.add_employee(data, self.captured_encodings)
            if success:
                messagebox.showinfo("Success", "Employee Registered!")
                dashboard = self.controller.frames["DashboardFrame"]
                dashboard.show_home()
            else:
                messagebox.showerror("Error", msg)
        except Exception as e:
            messagebox.showerror("Error", f"Error: {e}")
            return
        