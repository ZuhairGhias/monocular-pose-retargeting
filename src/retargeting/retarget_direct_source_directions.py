from src.retargeting.rig_mapping import MIXAMO_BODY_MAPPING
from src.retargeting.root_orientation import estimate_root_orientation
from src.retargeting.types import RetargetFrame
from src.retargeting.types import RetargetInput
from src.retargeting.types import TargetBoneDirection
from src.retargeting.types import Vector3


def to_vector3(values) -> Vector3:
    return (float(values[0]), float(values[1]), float(values[2]))


class DirectSourceDirectionRetargeter:
    name = "retarget_direct_source_directions"

    def retarget(self, frame: RetargetInput) -> RetargetFrame:
        # This baseline does not solve rotations in Python. It forwards source
        # bone directions to mapped target bones so the viewer can apply them.
        source_skeleton = frame.source_skeleton
        target_bones = {}
        skipped = []

        for bone_map in MIXAMO_BODY_MAPPING:
            direction = source_skeleton.bone_directions.get(bone_map.source)
            if direction is None:
                # Missing directions usually mean the pose was not detected or
                # a parent/child landmark was unavailable for this frame.
                skipped.append(bone_map.label)
                continue

            # A bone is only as reliable as its least reliable endpoint.
            confidence = min(
                source_skeleton.joint_confidences.get(bone_map.source.parent, 0.0),
                source_skeleton.joint_confidences.get(bone_map.source.child, 0.0),
            )
            source_bone = (
                f"{bone_map.source.parent.value}->{bone_map.source.child.value}"
            )

            # Some source bones drive multiple target bones, such as upper
            # spine motion split across Mixamo Spine1 and Spine2.
            for target_bone, weight in zip(
                bone_map.targets, bone_map.weights, strict=True
            ):
                target_bones[target_bone] = TargetBoneDirection(
                    target_bone=target_bone,
                    source_bone=source_bone,
                    direction=to_vector3(direction),
                    confidence=confidence,
                    weight=weight,
                )

        return RetargetFrame(
            method=self.name,
            bones=target_bones,
            skipped=tuple(skipped),
            root_orientation=estimate_root_orientation(source_skeleton),
        )
