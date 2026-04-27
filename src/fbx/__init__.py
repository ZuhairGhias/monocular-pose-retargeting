from pathlib import Path

import gradio as gr

class FBXViewer(gr.HTML):
    def __init__(self, label, **kwargs):
        super().__init__(
            value="",
            label=label,
            html_template=(Path(__file__).parent / "fbx.html").read_text(),
            js_on_load=(Path(__file__).parent / "fbx.js").read_text(),
            min_height=540,
            **kwargs,
        )
