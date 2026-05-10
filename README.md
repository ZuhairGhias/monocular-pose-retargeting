---
title: Monocular Pose Retargeting
sdk: docker
app_port: 7860
---

# monocular-pose-retargeting
Pose detection and retargeting.

## Usage

The attached Dockerfile can be used to deploy directly, or the instructions below also work for manual deployment.

To run, you must first install the latest versions of node & python.

First, build a three.js bundle:
```
npm install
npm run build
```

Install the python dependencies:
```
pip install -r requirements.txt
```

The port the app will run on can be set with the env variable `PORT`.

Finally, you should be able to launch the app:
```
python app.py
```

You should see a log output when the server launches:
```
Starting on http://0.0.0.0:7860...
```
## Hugging Face Demo

Use this link: https://huggingface.co/spaces/zghias/monocular-pose-retargeting to use the hugging face demo.

Press record to start recording movements, and you will see pose landmarks, source skeleton vectors, and debug output update in real time.

Switch to model view to see the avatar. You can use the retargeter dropdown to change retargeter methods.

## Organization

- `app.py` is the entrypoint into the gradio app
- `rigs` contains the FBX rigs used for rendering
- `models` contains the landmark models
- `src/fbx` contains the fbx rendering component, using three.js
- `src/retargeting` contains retargeting logic
- `src/ui` contains debug panel ui
- `src/*` the rest of src contains pose detection logic
- 

## Useful Docs
* https://www.gradio.app/guides/
* https://ai.google.dev/edge/mediapipe/solutions/vision/pose_landmarker/python
