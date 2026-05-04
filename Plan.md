# Motion Retargeting Project Plan

## Goal

Build a Python-first, server-driven Gradio app that takes monocular camera pose landmarks, converts them into a stable intermediate skeleton, and retargets that motion onto a rigged Mixamo avatar.

## Scope

The project does not attempt full source-mesh reconstruction or STaR-style learned retargeting. The baseline focuses on:

- pose landmark detection
- canonical source skeleton fitting
- skeleton-to-skeleton retargeting
- driving a Mixamo rig
- temporal stabilization and basic contact constraints

## Current App Direction

The first usable application should:

- launch locally with `python app.py`
- open a Gradio web page
- accept webcam input
- process frames on the Python backend
- run MediaPipe Pose Landmarker
- return an annotated frame with pose landmarks and limb connections
- keep the UI simple and server-driven

Gradio remains the main UI shell. Do not build a custom frontend unless the project scope changes.

## Pipeline

### 1. Landmark Capture

- Capture frames from webcam or uploaded video
- Run pose landmark detection
- Store per-frame landmark positions and confidence values
- Render raw landmarks for debugging

### 2. Canonical Source Skeleton

- Define a fixed source skeleton hierarchy:
  - pelvis
  - spine
  - neck
  - head
  - shoulders
  - elbows
  - wrists
  - hips
  - knees
  - ankles
- Estimate a stable root transform from hips and torso
- Use fixed bone lengths rather than frame-by-frame landmark distances

### 3. Joint Rotation Estimation

- Compute bone direction vectors from landmarks for each frame
- Convert direction vectors into joint rotations relative to rest pose
- Apply confidence checks and clamp invalid rotations
- Smooth rotations over time to reduce jitter

### 4. Mixamo Retargeting

- Import one Mixamo character and inspect its joint hierarchy
- Create a mapping from source skeleton joints to Mixamo joints
- Drive the Mixamo rig using source joint rotations
- Keep target skeleton bone lengths fixed

### 5. IK and Constraints

- Add IK or simple constraints for arms, legs, head orientation, and pelvis/root motion
- Enforce joint angle limits
- Add basic foot planting and anti-sliding heuristics

### 6. Debugging and Visualization

- Visualize raw landmarks
- Visualize the canonical source skeleton
- Visualize the retargeted target skeleton
- Visualize final Mixamo avatar output
- Add side-by-side debugging views for each pipeline stage

## Current Status

- Webcam pose detection and landmark visualization are working.
- A canonical source skeleton is produced with source joints, confidences, and bone directions.
- The Mixamo FBX model renders in the Gradio app.
- A first `src/retargeting/` scaffold exists with shared types, a Mixamo body mapping, `retarget_direct_source_directions`, `retarget_smoothed_source_directions`, and `retarget_optimized_temporal_directions`.
- The FBX viewer receives a JSON-safe retargeting payload and applies a naive FK direction match to mapped body bones.
- Retargeting payloads include a root orientation frame estimated from the source hip axis and pelvis-to-spine direction.
- The model debug panel shows mapped target bones, source directions, model directions, confidence, weights, and application skips.

Known limitations:

- MediaPipe `z` depth is not calibrated to image-space `x/y`; current depth scaling is a temporary tuning constant.
- The naive FK method has no rest-pose calibration, joint limits, IK, root alignment, or temporal smoothing.
- Full-body retargeting is only barely working and should be treated as a baseline for comparison.
- Model bone direction/debug extraction is useful for mapped bones, but should be hardened as rig introspection improves.

Next steps:

- Tune one limb at a time, starting with right arm axis, sign, and depth behavior.
- Move source-to-model coordinate conversion into an explicit retargeting adapter so naive and refined methods can differ.
- Improve pelvis/root orientation so hip yaw/turning is calibrated against the target rig rest pose and camera/model alignment.
- Add rest-pose calibration from actual target rig bind/rest directions instead of relying on fallback local axes.
- Continue refining the smoothed and optimized retargeting methods with rest-pose calibration, joint limits, and later IK.
- Explore an optimization-based refinement pass that minimizes tracking error, joint-limit violations, temporal jitter, contact errors, and simple proxy-shape interpenetration.
- Add focused tests for mapping coverage and JSON payload shape before expanding the retargeting contract.

## Milestones

### Milestone 1: Pose Input

- Webcam/video input works
- Pose landmarks are detected and rendered consistently
- Basic performance is acceptable after downsampling or other simple optimizations

### Milestone 2: Source Skeleton

- Canonical source skeleton is defined
- Stable root and bone directions are computed from landmarks
- Missing or low-confidence landmarks are handled explicitly

### Milestone 3: Retargeting

- Source skeleton motion is mapped onto a Mixamo rig
- Avatar roughly follows user motion
- Target skeleton bone lengths remain fixed

### Milestone 4: Stabilization

- Temporal smoothing reduces jitter
- Joint limits and simple IK improve plausibility
- Basic foot planting reduces visible sliding

### Milestone 5: Demo

- End-to-end real-time demo works
- Example success cases and failure cases are recorded
- Limitations and next steps are documented

## Repository Direction

Keep the project modular without over-engineering. A likely structure is:

```text
monocular-pose-retargeting/
├── app.py
├── requirements.txt
├── models/
├── src/
│   ├── pose_detection.py
│   ├── source_skeleton.py
│   ├── retargeting.py
│   ├── smoothing.py
│   └── types.py
├── tests/
└── scripts/
```

Near-term code can remain simpler than this. Add modules only when the responsibility is clear.

## Quality Requirements

- Keep modules small and readable
- Use type hints for public functions
- Avoid putting all logic in `app.py`
- Prefer clear interfaces over premature abstractions
- Keep changes incremental and reviewable
- Keep pose-specific configuration close to the pose code it affects

## Deliverables

- Working code for the full retargeting pipeline
- One real-time avatar demo using a Mixamo character
- Visualization and debugging tools
- Short write-up describing:
  - approach
  - design choices
  - limitations
  - future improvements

## Possible Extensions

- Better 3D pose lifting
- Contact-aware constraints
- Hand tracking
- Improved temporal filtering
- Learned motion refinement after baseline retargeting works
