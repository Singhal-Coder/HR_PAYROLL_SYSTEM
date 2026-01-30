"""
Attendance business logic: late/present rules, manual check-in validation.
Delegates DB access to AttendanceModel.
"""
import logging
from datetime import datetime

from models.attendance_model import AttendanceModel
from utils.network import is_connected_to_office_network

logger = logging.getLogger(__name__)

# Time format used by roles.start_time in DB
SHIFT_TIME_FMT = "%H:%M:%S"


def compute_attendance_status(shift_start_str: str | None) -> tuple[str, str, str]:
    """
    Determine Present vs Late from current time and shift start.
    Returns (status, date_str, time_str) for the current moment.
    """
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime(SHIFT_TIME_FMT)

    if not shift_start_str or not shift_start_str.strip():
        return ("Present", date_str, time_str)

    try:
        shift_start = datetime.strptime(shift_start_str.strip(), SHIFT_TIME_FMT).time()
        current_time = now.time()
        status = "Late" if current_time > shift_start else "Present"
        return (status, date_str, time_str)
    except ValueError:
        logger.warning("Time format error for shift_start %r, defaulting to Present", shift_start_str)
        return ("Present", date_str, time_str)


def mark_attendance(emp_code: str, method: str = "FACE") -> tuple[bool, str]:
    """
    Load shift info, compute status, insert via model. Returns (success, message).
    """


    if method == "MANUAL":
        if not is_connected_to_office_network():
            return (False, "Security Alert: Not connected to Office Wi-Fi.")

    model = AttendanceModel()
    full_name, shift_start_str = model.get_employee_shift_info(emp_code)

    if full_name is None:
        return (False, "Employee Not Found")

    status, date_str, time_str = compute_attendance_status(shift_start_str)
    success, msg = model.insert_attendance(emp_code, date_str, time_str, status, method)

    if success:
        return (True, f"Welcome, {msg}")  # msg is full_name from model
    return (False, msg)
