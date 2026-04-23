import gradio as gr
import numpy as np
from src.pose_detection import process_frame

STREAM_EVERY_SECONDS = 0.2


def passthrough(frame: np.ndarray) -> np.ndarray:
    """Accept an RGB image as a NumPy array with shape (H, W, 3) and return the same shape."""
    result = process_frame(frame)
    return result.annotated_frame


def build_app() -> gr.Blocks:
    with gr.Blocks(title="Monocular Pose Retargeting") as demo:
        gr.Markdown("# Monocular Pose Retargeting")
        with gr.Row():
            input_img = gr.Image(label="Input", sources="webcam")
            output_img = gr.Image(label="Output")

        input_img.stream(
            passthrough,
            inputs=input_img,
            outputs=output_img,
            time_limit=15,
            stream_every=STREAM_EVERY_SECONDS,
            concurrency_limit=30,
        )

    return demo


if __name__ == "__main__":
    build_app().launch()
