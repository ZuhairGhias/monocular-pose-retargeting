import math

import numpy as np
from scipy.optimize import minimize

from src.retargeting.rig_mapping import MIXAMO_BODY_MAPPING
from src.retargeting.root_orientation import estimate_root_orientation
from src.retargeting.types import RetargetFrame
from src.retargeting.types import RetargetInput
from src.retargeting.types import RootOrientation
from src.retargeting.types import TargetBoneDirection
from src.retargeting.types import Vector3

UNIT_LENGTH_WEIGHT = 8.0
MAX_OPTIMIZER_ITERATIONS = 20


def to_vector3(values) -> Vector3:
    return (float(values[0]), float(values[1]), float(values[2]))


def normalize(vector: Vector3) -> Vector3 | None:
    length = math.sqrt(sum(value * value for value in vector))
    if length < 1e-6:
        return None

    return (vector[0] / length, vector[1] / length, vector[2] / length)


def confidence_weights(confidence: float) -> tuple[float, float]:
    clamped_confidence = max(0.0, min(1.0, confidence))
    tracking_weight = 0.5 + 4.0 * clamped_confidence
    temporal_weight = 0.25 + 2.0 * (1.0 - clamped_confidence)
    return tracking_weight, temporal_weight


def cross_vector(a: Vector3, b: Vector3) -> Vector3:
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


class OptimizedTemporalDirectionRetargeter:
    name = "retarget_optimized_temporal_directions"

    def __init__(self) -> None:
        self._previous_directions: dict[str, Vector3] = {}

    def retarget(self, frame: RetargetInput) -> RetargetFrame:
        # This method keeps the same payload contract as the direct methods,
        # but solves each output direction with a small per-bone cost function.
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
                optimized_direction = self._optimize_direction(
                    target_bone,
                    source_direction,
                    confidence,
                )
                target_bones[target_bone] = TargetBoneDirection(
                    target_bone=target_bone,
                    source_bone=source_bone,
                    direction=optimized_direction,
                    confidence=confidence,
                    weight=weight,
                )

        return RetargetFrame(
            method=self.name,
            bones=target_bones,
            skipped=tuple(skipped),
            root_orientation=self._optimize_root_orientation(
                estimate_root_orientation(source_skeleton)
            ),
        )

    def _optimize_direction(
        self,
        target_bone: str,
        source_direction: Vector3,
        confidence: float,
    ) -> Vector3:
        previous_direction = self._previous_directions.get(target_bone)
        if previous_direction is None:
            self._previous_directions[target_bone] = source_direction
            return source_direction

        tracking_weight, temporal_weight = confidence_weights(confidence)
        source = np.array(source_direction, dtype=np.float64)
        previous = np.array(previous_direction, dtype=np.float64)

        def cost(candidate: np.ndarray) -> float:
            tracking_error = np.sum((candidate - source) ** 2)
            temporal_error = np.sum((candidate - previous) ** 2)
            unit_error = (np.linalg.norm(candidate) - 1.0) ** 2
            return float(
                tracking_weight * tracking_error
                + temporal_weight * temporal_error
                + UNIT_LENGTH_WEIGHT * unit_error
            )

        result = minimize(
            cost,
            previous,
            method="L-BFGS-B",
            bounds=((-1.0, 1.0), (-1.0, 1.0), (-1.0, 1.0)),
            options={"maxiter": MAX_OPTIMIZER_ITERATIONS},
        )
        optimized_direction = normalize(to_vector3(result.x))
        if optimized_direction is None:
            optimized_direction = source_direction

        self._previous_directions[target_bone] = optimized_direction
        return optimized_direction

    def _optimize_root_orientation(
        self,
        root_orientation: RootOrientation | None,
    ) -> RootOrientation | None:
        if root_orientation is None:
            return None

        right = self._optimize_direction(
            "root.right",
            root_orientation.right,
            root_orientation.confidence,
        )
        up = self._optimize_direction(
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
