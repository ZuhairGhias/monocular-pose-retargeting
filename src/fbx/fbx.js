
(async () => {
	const THREE = await import("/static/three.js")
	const {FBXLoader, OrbitControls} = THREE
	const MIN_CONFIDENCE = 0.2
	// MediaPipe source directions are camera-relative. Keep the camera-to-model
	// handedness and depth scaling in one mapping so retargeting code does not
	// contain unexplained per-bone sign flips.
	const SOURCE_TO_MODEL_AXES = {
		x: {sourceIndex: 0, scale: 1},
		y: {sourceIndex: 1, scale: -1},
		z: {sourceIndex: 2, scale: -0.25},
	}
	const ROOT_NEUTRAL_RIGHT = new THREE.Vector3(-1, 0, 0)
	const TARGET_LOCAL_AXES = {
		mixamorigSpine: [0, 1, 0],
		mixamorigSpine1: [0, 1, 0],
		mixamorigSpine2: [0, 1, 0],
		mixamorigNeck: [0, 1, 0],
		mixamorigLeftShoulder: [1, 0, 0],
		mixamorigLeftArm: [1, 0, 0],
		mixamorigLeftForeArm: [1, 0, 0],
		mixamorigRightShoulder: [-1, 0, 0],
		mixamorigRightArm: [-1, 0, 0],
		mixamorigRightForeArm: [-1, 0, 0],
		mixamorigLeftUpLeg: [0, -1, 0],
		mixamorigLeftLeg: [0, -1, 0],
		mixamorigRightUpLeg: [0, -1, 0],
		mixamorigRightLeg: [0, -1, 0],
	}


	// setup
	const scene = new THREE.Scene();
	const camera = new THREE.PerspectiveCamera( 75, window.innerWidth / window.innerHeight, 0.1, 1000 );

	const canvas = document.getElementById("canvas")
	const boneDebug = document.getElementById("bone-debug")
	const renderer = new THREE.WebGLRenderer({ canvas });


	const resize = () => {
		const aspect = 16/9
		renderer.setSize(canvas.parentElement.clientWidth, canvas.parentElement.clientWidth / aspect, false);
		camera.aspect = aspect;
		camera.updateProjectionMatrix();
	};
	new ResizeObserver(resize).observe(canvas.parentElement);
	resize();

	const controls = new OrbitControls( camera, renderer.domElement );

	const setBoneDebug = (text) => {
		if (boneDebug) boneDebug.textContent = text
	}

	const formatVector = (vector) => {
		if (!vector) return "leaf"
		if (Array.isArray(vector)) {
			return vector.map(value => Number(value).toFixed(3)).join(", ")
		}
		return `${vector.x.toFixed(3)}, ${vector.y.toFixed(3)}, ${vector.z.toFixed(3)}`
	}

	const parsePayload = (value) => {
		if (!value) return {}
		if (typeof value !== "string") return value
		try {
			return JSON.parse(value)
		} catch (error) {
			console.warn("Could not parse FBX payload", error)
			return {error: String(error)}
		}
	}

	const findChildBone = (bone) => {
		return childBoneMap[bone.name] || bone.children.find(child => child.isBone) || null
	}

	const boneDirection = (bone) => {
		const childBone = findChildBone(bone)
		if (!childBone) return null

		const start = new THREE.Vector3()
		const end = new THREE.Vector3()
		bone.getWorldPosition(start)
		childBone.getWorldPosition(end)
		const worldDirection = end.sub(start)
		if (worldDirection.lengthSq() > 1e-8) return worldDirection.normalize()

		const boneIndex = skeleton.bones.indexOf(bone)
		const childIndex = skeleton.bones.indexOf(childBone)
		if (boneIndex >= 0 && childIndex >= 0) {
			const bindStart = new THREE.Vector3()
			const bindEnd = new THREE.Vector3()
			bindStart.setFromMatrixPosition(skeleton.boneInverses[boneIndex].clone().invert())
			bindEnd.setFromMatrixPosition(skeleton.boneInverses[childIndex].clone().invert())
			const bindDirection = bindEnd.sub(bindStart)
			if (bindDirection.lengthSq() > 1e-8) return bindDirection.normalize()
		}

		const localDirection = childBone.position.clone()
		if (localDirection.lengthSq() > 1e-8) return localDirection.normalize()
		return null
	}

	let object = null
	let skeleton = null
	let boneMap = {}
	let childBoneMap = {}
	let latestPayload = {}
	let restQuaternions = {}
	let latestApplyStats = {applied: 0, skipped: [], rootYaw: null}

	const sourceComponent = (direction, axis) => {
		const mapping = SOURCE_TO_MODEL_AXES[axis]
		return direction[mapping.sourceIndex] * mapping.scale
	}

	const sourceDirectionToModel = (direction) => {
		if (!direction || direction.length < 3) return null
		const vector = new THREE.Vector3(
			sourceComponent(direction, "x"),
			sourceComponent(direction, "y"),
			sourceComponent(direction, "z"),
		)
		if (vector.lengthSq() < 1e-8) return null
		return vector.normalize()
	}

	const signedYawBetween = (from, to) => {
		const cross = new THREE.Vector3().crossVectors(from, to)
		const dot = Math.max(-1, Math.min(1, from.dot(to)))
		return Math.atan2(cross.y, dot)
	}

	const targetLocalAxis = (targetBone) => {
		const childBone = childBoneMap[targetBone]
		if (childBone && childBone.position.lengthSq() > 1e-8) {
			return childBone.position.clone().normalize()
		}

		const axis = TARGET_LOCAL_AXES[targetBone] || [0, 1, 0]
		return new THREE.Vector3(axis[0], axis[1], axis[2]).normalize()
	}

	const resetMappedBones = (retargetedBones) => {
		for (const targetBone of Object.keys(retargetedBones)) {
			const bone = boneMap[targetBone]
			const restQuaternion = restQuaternions[targetBone]
			if (bone && restQuaternion) bone.quaternion.copy(restQuaternion)
		}
		object.updateMatrixWorld(true)
	}

	const applyRootOrientation = () => {
		const hips = boneMap["mixamorigHips"]
		const restQuaternion = restQuaternions["mixamorigHips"]
		const rootOrientation = latestPayload.retargeting?.root_orientation
		if (!hips || !restQuaternion) return null

		hips.quaternion.copy(restQuaternion)
		if (!rootOrientation) {
			return null
		}

		const desiredRight = sourceDirectionToModel(rootOrientation.right)
		if (!desiredRight) return null

		desiredRight.y = 0
		if (desiredRight.lengthSq() < 1e-8) return null
		desiredRight.normalize()

		const yaw = signedYawBetween(ROOT_NEUTRAL_RIGHT, desiredRight)
		const yawQuaternion = new THREE.Quaternion().setFromAxisAngle(
			new THREE.Vector3(0, 1, 0),
			yaw,
		)
		hips.quaternion.copy(yawQuaternion.multiply(restQuaternion))
		object.updateMatrixWorld(true)
		return yaw
	}

	const applyDirectionInstruction = (targetBone, instruction) => {
		const bone = boneMap[targetBone]
		const restQuaternion = restQuaternions[targetBone]
		if (!bone || !restQuaternion) return "missing target bone"

		const confidence = Number(instruction.confidence || 0)
		if (confidence < MIN_CONFIDENCE) return "low confidence"

		const desiredWorldDirection = sourceDirectionToModel(instruction.direction)
		if (!desiredWorldDirection) return "missing source direction"

		const parentWorldQuaternion = new THREE.Quaternion()
		if (bone.parent) bone.parent.getWorldQuaternion(parentWorldQuaternion)
		const desiredParentDirection = desiredWorldDirection.clone()
			.applyQuaternion(parentWorldQuaternion.invert())
			.normalize()

		const restAxis = targetLocalAxis(targetBone).applyQuaternion(restQuaternion).normalize()
		const delta = new THREE.Quaternion().setFromUnitVectors(restAxis, desiredParentDirection)
		const targetQuaternion = delta.multiply(restQuaternion)
		const weight = Math.max(0, Math.min(1, Number(instruction.weight || 1)))

		bone.quaternion.copy(restQuaternion).slerp(targetQuaternion, weight)
		return null
	}

	const applyRetargeting = () => {
		const retargetedBones = latestPayload.retargeting?.bones || {}
		resetMappedBones(retargetedBones)
		const rootYaw = applyRootOrientation()

		const skipped = []
		let applied = 0
		for (const [targetBone, instruction] of Object.entries(retargetedBones)) {
			const skipReason = applyDirectionInstruction(targetBone, instruction)
			if (skipReason) {
				skipped.push(`${targetBone}: ${skipReason}`)
			} else {
				applied += 1
			}
			object.updateMatrixWorld(true)
		}
		latestApplyStats = {applied, skipped, rootYaw}
	}

	const updateBoneDebug = () => {
		if (!skeleton) {
			setBoneDebug("No model skeleton loaded.")
			return
		}

		object.updateMatrixWorld(true)
		const retargeting = latestPayload.retargeting || {}
		const payloadInfo = latestPayload.error
			? `payload error: ${latestPayload.error}`
			: [
				`source joints: ${Object.keys(latestPayload.joints || {}).length}`,
				`source bone directions: ${Object.keys(latestPayload.bone_directions || {}).length}`,
				`retargeting method: ${retargeting.method || "none"}`,
				`retargeted bones: ${Object.keys(retargeting.bones || {}).length}`,
				`retarget skipped: ${(retargeting.skipped || []).length}`,
				`applied bones: ${latestApplyStats.applied}`,
				`apply skipped: ${latestApplyStats.skipped.length}`,
				`root yaw: ${latestApplyStats.rootYaw === null ? "none" : latestApplyStats.rootYaw.toFixed(3)}`,
				`root confidence: ${Number(retargeting.root_orientation?.confidence || 0).toFixed(3)}`,
				`source axes: x=${SOURCE_TO_MODEL_AXES.x.scale}*source[${SOURCE_TO_MODEL_AXES.x.sourceIndex}], y=${SOURCE_TO_MODEL_AXES.y.scale}*source[${SOURCE_TO_MODEL_AXES.y.sourceIndex}], z=${SOURCE_TO_MODEL_AXES.z.scale}*source[${SOURCE_TO_MODEL_AXES.z.sourceIndex}]`,
			].join("\n")
		const retargetedBones = retargeting.bones || {}
		const boneLines = Object.entries(retargetedBones).map(([targetBone, instruction]) => {
			const modelBone = boneMap[targetBone]
			const modelDirection = modelBone ? formatVector(boneDirection(modelBone)) : "missing"
			return [
				targetBone,
				`  source: ${instruction.source_bone}`,
				`  source direction: ${formatVector(instruction.direction)}`,
				`  model direction: ${modelDirection}`,
				`  confidence: ${Number(instruction.confidence || 0).toFixed(3)} weight: ${Number(instruction.weight || 0).toFixed(3)}`,
			].join("\n")
		})

		setBoneDebug([
			`model bones: ${skeleton.bones.length}`,
			payloadInfo,
			"",
			...latestApplyStats.skipped,
			latestApplyStats.skipped.length ? "" : null,
			"mapped target bones:",
			...boneLines,
		].filter(line => line !== null).join("\n"))
	}

	// load object
	const loader = new FBXLoader()
	try {
		object = await loader.loadAsync("/rigs/Exo Gray.fbx")
		scene.add(object)
	} catch (error) {
		console.error("Could not load FBX model", error)
		setBoneDebug(`Could not load FBX model: ${error}`)
		return
	}

	let box = new THREE.Box3().setFromObject(object);
	let center = box.getCenter(new THREE.Vector3());
	let size = box.getSize(new THREE.Vector3());
	object.scale.setScalar(2 / size.y)

	box = new THREE.Box3().setFromObject(object);
	center = box.getCenter(new THREE.Vector3());
	size = box.getSize(new THREE.Vector3());

	object.position.sub(center);

	camera.position.set(0, size.y / 2, size.z * 4);
	camera.lookAt(0, 0, 0);
	controls.update()

	// bones
	const helper = new THREE.SkeletonHelper(object);
	scene.add(helper);

	object.traverse(c => {
		if (c.isSkinnedMesh) {
			if (!skeleton) {
				skeleton = c.skeleton
			} else {
				console.warn("Detected multiple skeletons", skeleton, c.skeleton)
			}
		}
	});

	if (!skeleton) {
		setBoneDebug("FBX loaded, but no skinned mesh skeleton was found.")
		return
	}

	skeleton.bones.forEach(bone => {
		boneMap[bone.name] = bone
		restQuaternions[bone.name] = bone.quaternion.clone()
		if (bone.parent?.isBone && !childBoneMap[bone.parent.name]) {
			childBoneMap[bone.parent.name] = bone
		}
	});
	function updateBones(value) {
		latestPayload = parsePayload(value)
		applyRetargeting()
		updateBoneDebug()
	}

	watch(["value"], () => {
		if (!props.value || !skeleton) return;
		updateBones(props.value)
	})
	updateBones(props.value)

	// light
	scene.add(new THREE.AmbientLight(0xffffff, 1));
	const dirLight = new THREE.DirectionalLight(0xffffff, 1);
	dirLight.position.set(0, 200, 100);
	scene.add(dirLight);

	// animate
	function animate( time ) {
		controls.update();
		renderer.render( scene, camera );
	}
	renderer.setAnimationLoop( animate );
})().catch(error => {
	console.error("FBX viewer failed", error)
	const boneDebug = document.getElementById("bone-debug")
	if (boneDebug) boneDebug.textContent = `FBX viewer failed: ${error}`
});
