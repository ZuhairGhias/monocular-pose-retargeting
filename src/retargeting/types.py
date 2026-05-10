from dataclasses import dataclass
from typing import Protocol

from src.source_skeleton import SourceBone
from src.source_skeleton import SourceSkeletonFrame

Vector3 = tuple[float, float, float]


@dataclass(frozen=True)
class RetargetInput:
    source_skeleton: SourceSkeletonFrame


@dataclass(frozen=True)
class BoneMap:
    label: str
    source: SourceBone
    targets: tuple[str, ...]
    weights: tuple[float, ...]


@dataclass(frozen=True)
class TargetBoneDirection:
    target_bone: str
    source_bone: str
    direction: Vector3
    confidence: float
    weight: float

    def to_payload(self) -> dict:
        return {
            "source_bone": self.source_bone,
            "direction": list(self.direction),
            "confidence": self.confidence,
            "weight": self.weight,
        }


@dataclass(frozen=True)
class RootOrientation:
    right: Vector3
    up: Vector3
    forward: Vector3
    confidence: float

    def to_payload(self) -> dict:
        return {
            "right": list(self.right),
            "up": list(self.up),
            "forward": list(self.forward),
            "confidence": self.confidence,
        }


@dataclass(frozen=True)
class RetargetFrame:
    method: str
    bones: dict[str, TargetBoneDirection]
    skipped: tuple[str, ...]
    root_orientation: RootOrientation | None = None

    def to_payload(self) -> dict:
        return {
            "method": self.method,
            "bones": {
                bone_name: direction.to_payload()
                for bone_name, direction in self.bones.items()
            },
            "skipped": list(self.skipped),
            "root_orientation": (
                self.root_orientation.to_payload()
                if self.root_orientation is not None
                else None
            ),
        }


class Retargeter(Protocol):
    name: str

    def retarget(self, frame: RetargetInput) -> RetargetFrame: ...
