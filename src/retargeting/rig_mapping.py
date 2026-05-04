from src.source_skeleton import SourceBone
from src.source_skeleton import SourceJoint
from src.retargeting.types import BoneMap

MIXAMO_BODY_MAPPING: tuple[BoneMap, ...] = (
    BoneMap(
        label="spine_lower",
        source=SourceBone(SourceJoint.PELVIS, SourceJoint.SPINE),
        targets=("mixamorigSpine",),
        weights=(1.0,),
    ),
    BoneMap(
        label="spine_upper",
        source=SourceBone(SourceJoint.SPINE, SourceJoint.NECK),
        targets=("mixamorigSpine1", "mixamorigSpine2"),
        weights=(0.5, 0.5),
    ),
    BoneMap(
        label="neck",
        source=SourceBone(SourceJoint.NECK, SourceJoint.HEAD),
        targets=("mixamorigNeck",),
        weights=(1.0,),
    ),
    BoneMap(
        label="left_shoulder",
        source=SourceBone(SourceJoint.NECK, SourceJoint.LEFT_SHOULDER),
        targets=("mixamorigLeftShoulder",),
        weights=(1.0,),
    ),
    BoneMap(
        label="left_upper_arm",
        source=SourceBone(SourceJoint.LEFT_SHOULDER, SourceJoint.LEFT_ELBOW),
        targets=("mixamorigLeftArm",),
        weights=(1.0,),
    ),
    BoneMap(
        label="left_forearm",
        source=SourceBone(SourceJoint.LEFT_ELBOW, SourceJoint.LEFT_WRIST),
        targets=("mixamorigLeftForeArm",),
        weights=(1.0,),
    ),
    BoneMap(
        label="left_hand",
        source=SourceBone(SourceJoint.LEFT_ELBOW, SourceJoint.LEFT_WRIST),
        targets=("mixamorigLeftHand",),
        weights=(0.35,),
    ),
    BoneMap(
        label="right_shoulder",
        source=SourceBone(SourceJoint.NECK, SourceJoint.RIGHT_SHOULDER),
        targets=("mixamorigRightShoulder",),
        weights=(1.0,),
    ),
    BoneMap(
        label="right_upper_arm",
        source=SourceBone(SourceJoint.RIGHT_SHOULDER, SourceJoint.RIGHT_ELBOW),
        targets=("mixamorigRightArm",),
        weights=(1.0,),
    ),
    BoneMap(
        label="right_forearm",
        source=SourceBone(SourceJoint.RIGHT_ELBOW, SourceJoint.RIGHT_WRIST),
        targets=("mixamorigRightForeArm",),
        weights=(1.0,),
    ),
    BoneMap(
        label="right_hand",
        source=SourceBone(SourceJoint.RIGHT_ELBOW, SourceJoint.RIGHT_WRIST),
        targets=("mixamorigRightHand",),
        weights=(0.35,),
    ),
    BoneMap(
        label="left_upper_leg",
        source=SourceBone(SourceJoint.LEFT_HIP, SourceJoint.LEFT_KNEE),
        targets=("mixamorigLeftUpLeg",),
        weights=(1.0,),
    ),
    BoneMap(
        label="left_lower_leg",
        source=SourceBone(SourceJoint.LEFT_KNEE, SourceJoint.LEFT_ANKLE),
        targets=("mixamorigLeftLeg",),
        weights=(1.0,),
    ),
    BoneMap(
        label="right_upper_leg",
        source=SourceBone(SourceJoint.RIGHT_HIP, SourceJoint.RIGHT_KNEE),
        targets=("mixamorigRightUpLeg",),
        weights=(1.0,),
    ),
    BoneMap(
        label="right_lower_leg",
        source=SourceBone(SourceJoint.RIGHT_KNEE, SourceJoint.RIGHT_ANKLE),
        targets=("mixamorigRightLeg",),
        weights=(1.0,),
    ),
)
