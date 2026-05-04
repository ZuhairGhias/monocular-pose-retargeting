import math

from src.retargeting.rig_mapping import MIXAMO_BODY_MAPPING
from src.retargeting.root_orientation import estimate_root_orientation
from src.retargeting.types import RetargetFrame
from src.retargeting.types import RetargetInput
from src.retargeting.types import RootOrientation
from src.retargeting.types import TargetBoneDirection
from src.retargeting.types import Vector3

MIN_BLEND = 0.15
MAX_BLEND = 0.75


def to_vector3(values) -> Vector3:
    return (float(values[0]), float(values[1]), float(values[2]))


def normalize(vector: Vector3) -> Vector3 | None:
    length = math.sqrt(sum(value * value for value in vector))
    if length < 1e-6:
        return None

    return (vector[0] / length, vector[1] / length, vector[2] / length)


def lerp_vector(a: Vector3, b: Vector3, weight: float) -> Vector3:
    return (
        a[0] + (b[0] - a[0]) * weight,
        a[1] + (b[1] - a[1]) * weight,
        a[2] + (b[2] - a[2]) * weight,
    )


def blend_for_confidence(confidence: float) -> float:
    clamped_confidence = max(0.0, min(1.0, confidence))
    return MIN_BLEND + (MAX_BLEND - MIN_BLEND) * clamped_confidence


def cross_vector(a: Vector3, b: Vector3) -> Vector3:
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


class SmoothedSourceDirectionRetargeter:
    name = "retarget_smoothed_source_directions"

    def __init__(self) -> None:
        self._previous_directions: dict[str, Vector3] = {}

    def retarget(self, frame: RetargetInput) -> RetargetFrame:
        # This method keeps the naive direction payload shape, but adds a small
        # temporal model so noisy frame-to-frame landmark changes are damped.
        source_skeleton = frame.source_skeleton
        target_bones = {}
        skipped = []

        for bone_map in MIXAMO_BODY_MAPPING:
            direction = source_skeleton.bone_directions.get(bone_map.source)
            if direction is None:
                skipped.append(bone_map.label)
                continue

            confidence = min(
                source_skeleton.joint_confidences.get(bone_map.source.parent, 0.0),
                source_skeleton.joint_confidences.get(bone_map.source.child, 0.0),
            )
            source_direction = to_vector3(direction)
            source_bone = (
                f"{bone_map.source.parent.value}->{bone_map.source.child.value}"
            )

            for target_bone, weight in zip(
                bone_map.targets, bone_map.weights, strict=True
            ):
                smoothed_direction = self._smooth_direction(
                    target_bone,
                    source_direction,
                    confidence,
                )
                target_bones[target_bone] = TargetBoneDirection(
                    target_bone=target_bone,
                    source_bone=source_bone,
                    direction=smoothed_direction,
                    confidence=confidence,
                    weight=weight,
                )

        return RetargetFrame(
            method=self.name,
            bones=target_bones,
            skipped=tuple(skipped),
            root_orientation=self._smooth_root_orientation(
                estimate_root_orientation(source_skeleton)
            ),
        )

    def _smooth_direction(
        self,
        target_bone: str,
        direction: Vector3,
        confidence: float,
    ) -> Vector3:
        previous_direction = self._previous_directions.get(target_bone)
        if previous_direction is None:
            self._previous_directions[target_bone] = direction
            return direction

        blended_direction = normalize(
            lerp_vector(
                previous_direction,
                direction,
                blend_for_confidence(confidence),
            )
        )
        if blended_direction is None:
            blended_direction = direction

        self._previous_directions[target_bone] = blended_direction
        return blended_direction

    def _smooth_root_orientation(
        self,
        root_orientation: RootOrientation | None,
    ) -> RootOrientation | None:
        if root_orientation is None:
            return None

        right = self._smooth_direction(
            "root.right",
            root_orientation.right,
            root_orientation.confidence,
        )
        up = self._smooth_direction(
            "root.up",
            root_orientation.up,
            root_orientation.confidence,
        )
        forward = normalize(cross_vector(right, up)) or root_orientation.forward

        return RootOrientation(
            right=right,
            up=up,
            forward=forward,
            confidence=root_orientation.confidence,
        )
