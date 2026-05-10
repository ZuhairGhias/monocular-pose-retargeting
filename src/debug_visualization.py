import cv2
import numpy as np

from src.source_skeleton import SOURCE_BONES
from src.source_skeleton import SourceBone
from src.source_skeleton import SourceSkeletonFrame


def confidence_to_rgb(confidence: float) -> tuple[int, int, int]:
    confidence = max(0.0, min(1.0, confidence))
    red = int(255 * (1.0 - confidence))
    green = int(255 * confidence)
    return red, green, 0


def joint_pixel(frame: np.ndarray, position: np.ndarray) -> tuple[int, int]:
    height, width = frame.shape[:2]
    return int(position[0] * width), int(position[1] * height)


def bone_confidence(source_skeleton: SourceSkeletonFrame, bone: SourceBone) -> float:
    parent_confidence = source_skeleton.joint_confidences.get(bone.parent, 0.0)
    child_confidence = source_skeleton.joint_confidences.get(bone.child, 0.0)
    return min(parent_confidence, child_confidence)


def draw_source_skeleton_vectors(
    frame: np.ndarray,
    source_skeleton: SourceSkeletonFrame,
) -> np.ndarray:
    annotated_frame = np.copy(frame)

    for bone in SOURCE_BONES:
        if bone.parent not in source_skeleton.joints or bone.child not in source_skeleton.joints:
            continue

        start = joint_pixel(annotated_frame, source_skeleton.joints[bone.parent])
        end = joint_pixel(annotated_frame, source_skeleton.joints[bone.child])
        color = confidence_to_rgb(bone_confidence(source_skeleton, bone))

        cv2.arrowedLine(
            annotated_frame,
            start,
            end,
            color,
            thickness=2,
            tipLength=0.2,
        )

    return annotated_frame
