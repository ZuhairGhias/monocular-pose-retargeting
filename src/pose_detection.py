import time

import cv2
import mediapipe as mp
import numpy as np
from mediapipe.tasks.python import vision
from mediapipe.tasks.python.vision import drawing_styles
from mediapipe.tasks.python.vision import drawing_utils

MODEL_PATH = "./models/pose_landmarker_lite.task"
DOWNSAMPLE_SCALE = 0.25

BaseOptions = mp.tasks.BaseOptions
PoseLandmarker = mp.tasks.vision.PoseLandmarker
PoseLandmarkerOptions = mp.tasks.vision.PoseLandmarkerOptions
VisionRunningMode = mp.tasks.vision.RunningMode

_options = PoseLandmarkerOptions(
    base_options=BaseOptions(model_asset_path=MODEL_PATH),
    running_mode=VisionRunningMode.VIDEO,
)
_landmarker = PoseLandmarker.create_from_options(_options)


def resize_frame(frame: np.ndarray) -> np.ndarray:
    return cv2.resize(frame, None, fx=DOWNSAMPLE_SCALE, fy=DOWNSAMPLE_SCALE, interpolation=cv2.INTER_AREA)


def draw_pose_landmarks(frame: np.ndarray, pose_landmarker_result) -> np.ndarray:
    annotated_frame = np.copy(frame)
    pose_landmark_style = drawing_styles.get_default_pose_landmarks_style()
    pose_connection_style = drawing_utils.DrawingSpec(color=(0, 255, 0), thickness=2)

    for pose_landmarks in pose_landmarker_result.pose_landmarks:
        drawing_utils.draw_landmarks(
            image=annotated_frame,
            landmark_list=pose_landmarks,
            connections=vision.PoseLandmarksConnections.POSE_LANDMARKS,
            landmark_drawing_spec=pose_landmark_style,
            connection_drawing_spec=pose_connection_style,
        )

    return annotated_frame


def draw_debug_text(frame: np.ndarray, text: str) -> np.ndarray:
    cv2.putText(frame, text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2, cv2.LINE_AA)
    return frame


def process_frame(frame: np.ndarray):
    resized_frame = resize_frame(frame)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=resized_frame)
    pose_landmarker_result = _landmarker.detect_for_video(mp_image, timestamp_ms=time.time_ns() // 1000)
    annotated_frame = draw_pose_landmarks(resized_frame, pose_landmarker_result)
    annotated_frame = draw_debug_text(annotated_frame, f"shape={resized_frame.shape}")
    return pose_landmarker_result, annotated_frame
