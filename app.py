from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import gradio as gr
import numpy as np
import uvicorn
from src.fbx import FBXViewer
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
    # TODO: figure out fbx passthrough
    fbx_passthrough_value = result
    return result.annotated_frame, source_skeleton_frame, format_debug_info(result), fbx_passthrough_value


def build_app() -> gr.Blocks:
    with gr.Blocks(title="Monocular Pose Retargeting") as demo:
        gr.Markdown("# Monocular Pose Retargeting")
        with gr.Row():
            with gr.Column():
                with gr.Tab("Input"):
                    input_img = gr.Image(label="Input", sources="webcam")
            with gr.Column():
                with gr.Tab("Landmarks"):
                    with gr.Row(equal_height=True):
                        pose_landmarks_img = gr.Image(label="Pose Landmarks", height=320)
                        source_skeleton_img = gr.Image(label="Source Skeleton Vectors", height=320)
                    debug_text = gr.Textbox(label="Debug", lines=8)
                with gr.Tab("Model"):
                    output_fbx = FBXViewer(label="Output Model")

        input_img.stream(
            passthrough,
            inputs=input_img,
            outputs=[pose_landmarks_img, source_skeleton_img, debug_text, output_fbx],
            time_limit=15,
            stream_every=STREAM_EVERY_SECONDS,
            concurrency_limit=30,
        )

    return demo

if __name__ == "__main__":
    app = FastAPI()
    app.mount("/static", StaticFiles(directory="static"), name="static")
    app.mount("/rigs", StaticFiles(directory="rigs"), name="rigs")
    gr.mount_gradio_app(app, build_app(), path="/")
    result = uvicorn.run(app, log_level="warning")
