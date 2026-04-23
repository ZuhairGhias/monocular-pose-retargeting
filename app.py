import gradio as gr
import numpy as np
from src.debug_visualization import draw_source_skeleton_vectors
from src.pose_detection import process_frame
from src.ui.debug_panel import format_debug_info

STREAM_EVERY_SECONDS = 0.2


def passthrough(frame: np.ndarray) -> tuple[np.ndarray, np.ndarray, str]:
    """Accept an RGB image as a NumPy array with shape (H, W, 3) and return the same shape."""
    result = process_frame(frame)
    source_skeleton_frame = draw_source_skeleton_vectors(
        result.processed_frame,
        result.source_skeleton,
    )
    return result.annotated_frame, source_skeleton_frame, format_debug_info(result)


def build_app() -> gr.Blocks:
    with gr.Blocks(title="Monocular Pose Retargeting") as demo:
        gr.Markdown("# Monocular Pose Retargeting")
        input_img = gr.Image(label="Input", sources="webcam", height=420)
        with gr.Row(equal_height=True):
            pose_landmarks_img = gr.Image(label="Pose Landmarks", height=320)
            source_skeleton_img = gr.Image(label="Source Skeleton Vectors", height=320)
        debug_text = gr.Textbox(label="Debug", lines=8)

        input_img.stream(
            passthrough,
            inputs=input_img,
            outputs=[pose_landmarks_img, source_skeleton_img, debug_text],
            time_limit=15,
            stream_every=STREAM_EVERY_SECONDS,
            concurrency_limit=30,
        )

    return demo


if __name__ == "__main__":
    build_app().launch()
