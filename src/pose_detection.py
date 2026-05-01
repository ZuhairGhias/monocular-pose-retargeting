import time

import cv2
import mediapipe as mp
import numpy as np
from mediapipe.tasks.python import vision
from mediapipe.tasks.python.vision import drawing_styles, PoseLandmarkerResult
from mediapipe.tasks.python.vision import drawing_utils

from src.source_skeleton import SourceSkeletonFrame
from src.source_skeleton import estimate_source_skeleton

from typing import NamedTuple
class PoseFrameResult(NamedTuple):
    landmarks: PoseLandmarkerResult
    source_skeleton: SourceSkeletonFrame
    processed_frame: np.ndarray
    annotated_frame: np.ndarray

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


def process_frame(frame: np.ndarray) -> PoseFrameResult:
    resized_frame = resize_frame(frame)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=resized_frame)
    pose_landmarker_result = _landmarker.detect_for_video(
        mp_image,
        timestamp_ms=time.time_ns() // 1_000_000,
    )
    source_skeleton = estimate_source_skeleton(pose_landmarker_result)
    annotated_frame = draw_pose_landmarks(resized_frame, pose_landmarker_result)
    return PoseFrameResult(
        landmarks=pose_landmarker_result,
        source_skeleton=source_skeleton,
        processed_frame=resized_frame,
        annotated_frame=annotated_frame,
    )
