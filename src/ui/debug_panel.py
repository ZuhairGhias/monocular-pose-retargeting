from src.pose_detection import PoseFrameResult


def format_debug_info(result: PoseFrameResult) -> str:
    skeleton = result.source_skeleton

    return "\n".join(
        [
            f"pose detected: {bool(result.landmarks.pose_landmarks)}",
            f"source joints: {len(skeleton.joints)}",
            f"joint confidences: {len(skeleton.joint_confidences)}",
            f"bone vectors: {len(skeleton.bone_directions)}",
            f"frame shape: {result.annotated_frame.shape}",
        ]
    )
