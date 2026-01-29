"""
Face recognition and head pose detection service.
Handles all image processing and face recognition logic; UI stays decoupled from heavy libraries.
"""
import logging
from typing import Literal

import cv2
import face_recognition
import numpy as np

logger = logging.getLogger(__name__)


def detect_head_pose(landmarks: dict) -> Literal["FRONT", "LEFT", "RIGHT"]:
    """
    Uses facial landmarks to estimate head pose.
    Returns: 'FRONT', 'LEFT', 'RIGHT'
    """
    left_eye = np.mean(landmarks["left_eye"], axis=0)
    right_eye = np.mean(landmarks["right_eye"], axis=0)
    nose_tip = np.mean(landmarks["nose_tip"], axis=0)

    dist_left_screen = float(nose_tip[0] - left_eye[0])
    dist_right_screen = float(right_eye[0] - nose_tip[0])

    ratio = dist_left_screen / (dist_right_screen + 1e-6)

    if 0.6 < ratio < 1.4:
        return "FRONT"
    elif ratio <= 0.6:
        return "LEFT"
    else:
        return "RIGHT"


def get_face_landmarks(rgb_frame: np.ndarray) -> list:
    """Return face landmarks from RGB frame (for pose detection)."""
    return face_recognition.face_landmarks(rgb_frame)


def get_face_encodings(rgb_frame: np.ndarray) -> list:
    """Return face encodings from RGB frame (for registration capture)."""
    return face_recognition.face_encodings(rgb_frame)


def process_face_recognition(
    frame: np.ndarray,
    known_encodings: list,
    known_ids: list,
    scale: float = 1.0,
    tolerance: float = 0.5,
) -> list[tuple[tuple[int, int, int, int], str | None]]:
    """
    Run face detection and recognition on a frame.
    Frame should be RGB; pass scale < 1.0 to resize for speed (e.g. 0.25).
    Returns list of (face_location, emp_code_or_None) in same scale as input.
    face_location is (top, right, bottom, left).
    """
    if frame is None or frame.size == 0:
        return []

    # Ensure RGB; resize for speed if requested
    if len(frame.shape) == 2:
        rgb_small = cv2.cvtColor(frame, cv2.COLOR_GRAY2RGB)
    else:
        rgb_small = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB) if frame.shape[2] == 3 else frame.copy()

    if scale != 1.0 and scale > 0:
        rgb_small = cv2.resize(rgb_small, (0, 0), fx=scale, fy=scale)

    face_locations = face_recognition.face_locations(rgb_small)
    if not face_locations:
        return []

    face_encodings_list = face_recognition.face_encodings(rgb_small, face_locations)
    results: list[tuple[tuple[int, int, int, int], str | None]] = []

    for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings_list):
        matches = face_recognition.compare_faces(known_encodings, face_encoding, tolerance=tolerance)
        emp_code: str | None = None
        if True in matches:
            first_match_index = matches.index(True)
            emp_code = known_ids[first_match_index]

        results.append(((top, right, bottom, left), emp_code))

    if results:
        logger.debug("Recognized %d face(s)", len(results))
    return results
