from dataclasses import dataclass
from enum import StrEnum

import numpy as np
from mediapipe.tasks.python.components.containers.landmark import NormalizedLandmark
from mediapipe.tasks.python.vision.pose_landmarker import PoseLandmarkerResult


class SourceJoint(StrEnum):
    PELVIS = "pelvis"
    SPINE = "spine"
    NECK = "neck"
    HEAD = "head"
    LEFT_SHOULDER = "left_shoulder"
    LEFT_ELBOW = "left_elbow"
    LEFT_WRIST = "left_wrist"
    RIGHT_SHOULDER = "right_shoulder"
    RIGHT_ELBOW = "right_elbow"
    RIGHT_WRIST = "right_wrist"
    LEFT_HIP = "left_hip"
    LEFT_KNEE = "left_knee"
    LEFT_ANKLE = "left_ankle"
    RIGHT_HIP = "right_hip"
    RIGHT_KNEE = "right_knee"
    RIGHT_ANKLE = "right_ankle"


@dataclass(frozen=True)
class SourceBone:
    parent: SourceJoint
    child: SourceJoint


@dataclass(frozen=True)
class SourceSkeletonFrame:
    joints: dict[SourceJoint, np.ndarray]
    joint_confidences: dict[SourceJoint, float]
    bone_directions: dict[SourceBone, np.ndarray]


SOURCE_BONES = (
    SourceBone(SourceJoint.PELVIS, SourceJoint.SPINE),
    SourceBone(SourceJoint.SPINE, SourceJoint.NECK),
    SourceBone(SourceJoint.NECK, SourceJoint.HEAD),
    SourceBone(SourceJoint.NECK, SourceJoint.LEFT_SHOULDER),
    SourceBone(SourceJoint.LEFT_SHOULDER, SourceJoint.LEFT_ELBOW),
    SourceBone(SourceJoint.LEFT_ELBOW, SourceJoint.LEFT_WRIST),
    SourceBone(SourceJoint.NECK, SourceJoint.RIGHT_SHOULDER),
    SourceBone(SourceJoint.RIGHT_SHOULDER, SourceJoint.RIGHT_ELBOW),
    SourceBone(SourceJoint.RIGHT_ELBOW, SourceJoint.RIGHT_WRIST),
    SourceBone(SourceJoint.PELVIS, SourceJoint.LEFT_HIP),
    SourceBone(SourceJoint.LEFT_HIP, SourceJoint.LEFT_KNEE),
    SourceBone(SourceJoint.LEFT_KNEE, SourceJoint.LEFT_ANKLE),
    SourceBone(SourceJoint.PELVIS, SourceJoint.RIGHT_HIP),
    SourceBone(SourceJoint.RIGHT_HIP, SourceJoint.RIGHT_KNEE),
    SourceBone(SourceJoint.RIGHT_KNEE, SourceJoint.RIGHT_ANKLE),
)


def landmark_to_position(landmark: NormalizedLandmark) -> np.ndarray:
    return np.array([landmark.x, landmark.y, landmark.z], dtype=np.float32)


def landmark_confidence(landmark: NormalizedLandmark) -> float:
    visibility = landmark.visibility if landmark.visibility is not None else 1.0
    presence = landmark.presence if landmark.presence is not None else 1.0
    return float(min(visibility, presence))


def midpoint(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    return (a + b) * 0.5


def normalize(vector: np.ndarray) -> np.ndarray | None:
    length = np.linalg.norm(vector)
    if length < 1e-6:
        return None

    return vector / length


def estimate_source_joints(pose_result: PoseLandmarkerResult) -> dict[SourceJoint, np.ndarray]:
    if not pose_result.pose_landmarks:
        return {}

    landmarks = pose_result.pose_landmarks[0]

    left_shoulder = landmark_to_position(landmarks[11])
    right_shoulder = landmark_to_position(landmarks[12])
    left_hip = landmark_to_position(landmarks[23])
    right_hip = landmark_to_position(landmarks[24])

    pelvis = midpoint(left_hip, right_hip)
    neck = midpoint(left_shoulder, right_shoulder)
    spine = midpoint(pelvis, neck)

    return {
        SourceJoint.PELVIS: pelvis,
        SourceJoint.SPINE: spine,
        SourceJoint.NECK: neck,
        SourceJoint.HEAD: landmark_to_position(landmarks[0]),
        SourceJoint.LEFT_SHOULDER: left_shoulder,
        SourceJoint.LEFT_ELBOW: landmark_to_position(landmarks[13]),
        SourceJoint.LEFT_WRIST: landmark_to_position(landmarks[15]),
        SourceJoint.RIGHT_SHOULDER: right_shoulder,
        SourceJoint.RIGHT_ELBOW: landmark_to_position(landmarks[14]),
        SourceJoint.RIGHT_WRIST: landmark_to_position(landmarks[16]),
        SourceJoint.LEFT_HIP: left_hip,
        SourceJoint.LEFT_KNEE: landmark_to_position(landmarks[25]),
        SourceJoint.LEFT_ANKLE: landmark_to_position(landmarks[27]),
        SourceJoint.RIGHT_HIP: right_hip,
        SourceJoint.RIGHT_KNEE: landmark_to_position(landmarks[26]),
        SourceJoint.RIGHT_ANKLE: landmark_to_position(landmarks[28]),
    }


def estimate_bone_directions(joints: dict[SourceJoint, np.ndarray]) -> dict[SourceBone, np.ndarray]:
    directions = {}

    for bone in SOURCE_BONES:
        if bone.parent not in joints or bone.child not in joints:
            continue

        direction = normalize(joints[bone.child] - joints[bone.parent])
        if direction is None:
            continue

        directions[bone] = direction

    return directions


def estimate_joint_confidences(pose_result: PoseLandmarkerResult) -> dict[SourceJoint, float]:
    if not pose_result.pose_landmarks:
        return {}

    landmarks = pose_result.pose_landmarks[0]

    left_shoulder = landmark_confidence(landmarks[11])
    right_shoulder = landmark_confidence(landmarks[12])
    left_hip = landmark_confidence(landmarks[23])
    right_hip = landmark_confidence(landmarks[24])

    pelvis = min(left_hip, right_hip)
    neck = min(left_shoulder, right_shoulder)
    spine = min(pelvis, neck)

    return {
        SourceJoint.PELVIS: pelvis,
        SourceJoint.SPINE: spine,
        SourceJoint.NECK: neck,
        SourceJoint.HEAD: landmark_confidence(landmarks[0]),
        SourceJoint.LEFT_SHOULDER: left_shoulder,
        SourceJoint.LEFT_ELBOW: landmark_confidence(landmarks[13]),
        SourceJoint.LEFT_WRIST: landmark_confidence(landmarks[15]),
        SourceJoint.RIGHT_SHOULDER: right_shoulder,
        SourceJoint.RIGHT_ELBOW: landmark_confidence(landmarks[14]),
        SourceJoint.RIGHT_WRIST: landmark_confidence(landmarks[16]),
        SourceJoint.LEFT_HIP: left_hip,
        SourceJoint.LEFT_KNEE: landmark_confidence(landmarks[25]),
        SourceJoint.LEFT_ANKLE: landmark_confidence(landmarks[27]),
        SourceJoint.RIGHT_HIP: right_hip,
        SourceJoint.RIGHT_KNEE: landmark_confidence(landmarks[26]),
        SourceJoint.RIGHT_ANKLE: landmark_confidence(landmarks[28]),
    }


def estimate_source_skeleton(pose_result: PoseLandmarkerResult) -> SourceSkeletonFrame:
    joints = estimate_source_joints(pose_result)
    joint_confidences = estimate_joint_confidences(pose_result)
    bone_directions = estimate_bone_directions(joints)

    return SourceSkeletonFrame(
        joints=joints,
        joint_confidences=joint_confidences,
        bone_directions=bone_directions,
    )
