import numpy as np

from src.retargeting.types import RootOrientation
from src.retargeting.types import Vector3
from src.source_skeleton import SourceJoint
from src.source_skeleton import SourceSkeletonFrame


def to_vector3(values: np.ndarray) -> Vector3:
    return (float(values[0]), float(values[1]), float(values[2]))


def normalize(vector: np.ndarray) -> np.ndarray | None:
    length = np.linalg.norm(vector)
    if length < 1e-6:
        return None

    return vector / length


def estimate_root_orientation(
    source_skeleton: SourceSkeletonFrame,
) -> RootOrientation | None:
    joints = source_skeleton.joints
    required_joints = (
        SourceJoint.LEFT_HIP,
        SourceJoint.RIGHT_HIP,
        SourceJoint.PELVIS,
        SourceJoint.SPINE,
    )
    if any(joint not in joints for joint in required_joints):
        return None

    right = normalize(joints[SourceJoint.RIGHT_HIP] - joints[SourceJoint.LEFT_HIP])
    up = normalize(joints[SourceJoint.SPINE] - joints[SourceJoint.PELVIS])
    if right is None or up is None:
        return None

    forward = normalize(np.cross(right, up))
    if forward is None:
        return None

    confidence = min(
        source_skeleton.joint_confidences.get(SourceJoint.LEFT_HIP, 0.0),
        source_skeleton.joint_confidences.get(SourceJoint.RIGHT_HIP, 0.0),
    )

    return RootOrientation(
        right=to_vector3(right),
        up=to_vector3(up),
        forward=to_vector3(forward),
        confidence=confidence,
    )
