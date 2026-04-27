from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import gradio as gr
import numpy as np
import uvicorn
from src.fbx import FBXViewer
from src.pose_detection import process_frame

STREAM_EVERY_SECONDS = 0.2


def passthrough(frame: np.ndarray) -> np.ndarray:
    """Accept an RGB image as a NumPy array with shape (H, W, 3) and return the same shape."""
    _, annotated_frame = process_frame(frame)
    # TODO: figure out fbx passthrough
    fbx_passthrough_value = annotated_frame
    return annotated_frame, fbx_passthrough_value


def build_app() -> gr.Blocks:
    with gr.Blocks(title="Monocular Pose Retargeting") as demo:
        gr.Markdown("# Monocular Pose Retargeting")
        with gr.Row():
            with gr.Column():
                with gr.Tab("Input"):
                    input_img = gr.Image(label="Input", sources="webcam")
            with gr.Column():
                with gr.Tab("Landmarks"):
                    output_img = gr.Image(label="Output")
                with gr.Tab("Model"):
                    output_fbx = FBXViewer(label="Output Model")

        input_img.stream(
            passthrough,
            inputs=input_img,
            outputs=[output_img, output_fbx],
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
    uvicorn.run(app, log_level="warning")
