import gradio as gr


def passthrough(frame):
    return frame


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
            stream_every=0.1,
            concurrency_limit=30,
        )

    return demo


if __name__ == "__main__":
    build_app().launch()
