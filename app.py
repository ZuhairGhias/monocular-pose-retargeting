import json
import os

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import gradio as gr
import numpy as np
import uvicorn
from src.fbx import FBXViewer
from src.debug_visualization import draw_source_skeleton_vectors
from src.pose_detection import process_frame
from src.retargeting import DirectSourceDirectionRetargeter
from src.retargeting import OptimizedTemporalDirectionRetargeter
from src.retargeting import RetargetInput
from src.retargeting import SmoothedSourceDirectionRetargeter
from src.ui.debug_panel import format_debug_info

STREAM_EVERY_SECONDS = 0.2
DEFAULT_RETARGETER = "Smoothed source directions"
RETARGETERS = {
    "Direct source directions": DirectSourceDirectionRetargeter(),
    "Smoothed source directions": SmoothedSourceDirectionRetargeter(),
    "Optimized temporal directions": OptimizedTemporalDirectionRetargeter(),
}


def selected_retargeter(name: str):
    return RETARGETERS.get(name, RETARGETERS[DEFAULT_RETARGETER])


def format_fbx_payload(result, retargeter_name: str) -> str:
    skeleton = result.source_skeleton
    retarget_frame = selected_retargeter(retargeter_name).retarget(
        RetargetInput(source_skeleton=skeleton)
    )
    return json.dumps(
        {
            "joints": {
                joint.value: position.tolist()
                for joint, position in skeleton.joints.items()
            },
            "joint_confidences": {
                joint.value: confidence
                for joint, confidence in skeleton.joint_confidences.items()
            },
            "bone_directions": {
                f"{bone.parent.value}->{bone.child.value}": direction.tolist()
                for bone, direction in skeleton.bone_directions.items()
            },
            "retargeting": retarget_frame.to_payload(),
        }
    )


def passthrough(
    frame: np.ndarray, retargeter_name: str
) -> tuple[np.ndarray, np.ndarray, str, str]:
    """Accept an RGB image as a NumPy array with shape (H, W, 3) and return the same shape."""
    result = process_frame(frame)
    source_skeleton_frame = draw_source_skeleton_vectors(
        result.processed_frame,
        result.source_skeleton,
    )
    retargeter = selected_retargeter(retargeter_name)
    try:
        fbx_passthrough_value = format_fbx_payload(result, retargeter_name)
        fbx_debug = f"fbx payload bytes: {len(fbx_passthrough_value)}"
    except Exception as exc:
        fbx_passthrough_value = "{}"
        fbx_debug = f"fbx payload error: {exc}"

    debug_info = "\n".join(
        [
            format_debug_info(result),
            fbx_debug,
            f"retargeter: {retargeter.name}",
        ]
    )
    return (
        result.annotated_frame,
        source_skeleton_frame,
        debug_info,
        fbx_passthrough_value,
    )


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
                        pose_landmarks_img = gr.Image(
                            label="Pose Landmarks", height=320
                        )
                        source_skeleton_img = gr.Image(
                            label="Source Skeleton Vectors", height=320
                        )
                    debug_text = gr.Textbox(label="Debug", lines=8)
                with gr.Tab("Model"):
                    retargeter_dropdown = gr.Dropdown(
                        choices=list(RETARGETERS.keys()),
                        value=DEFAULT_RETARGETER,
                        label="Retargeter",
                    )
                    output_fbx = FBXViewer(label="Output Model")

        input_img.stream(
            passthrough,
            inputs=[input_img, retargeter_dropdown],
            outputs=[pose_landmarks_img, source_skeleton_img, debug_text, output_fbx],
            time_limit=15,
            stream_every=STREAM_EVERY_SECONDS,
            concurrency_limit=30,
            show_progress = "hidden"
        )

    return demo


if __name__ == "__main__":
    app = FastAPI()
    app.mount("/static", StaticFiles(directory="static"), name="static")
    app.mount("/rigs", StaticFiles(directory="rigs"), name="rigs")
    gr.mount_gradio_app(app, build_app(), path="/")

    host = "0.0.0.0"
    port = int(os.environ.get("PORT", "7860"))
    print(f"Starting server on http://{host}:{port}...")
    print(f"Open local demo at http://127.0.0.1:{port}")
    uvicorn.run(app, host=host, port=port, log_level="warning")
