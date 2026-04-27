
(async () => {
	const THREE = await import("/static/three.js")
	const {FBXLoader, OrbitControls} = THREE


	// setup
	const scene = new THREE.Scene();
	const camera = new THREE.PerspectiveCamera( 75, window.innerWidth / window.innerHeight, 0.1, 1000 );

	const canvas = document.getElementById("canvas")
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

	// const geometry = new THREE.BoxGeometry( 1, 1, 1 );
	// const material = new THREE.MeshBasicMaterial( { color: 0x00ff00 } );
	// const cube = new THREE.Mesh( geometry, material );
	// scene.add( cube );

	// load object
	const loader = new FBXLoader()
	const object = await loader.loadAsync("/rigs/Exo Gray.fbx")
	scene.add(object)

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

	let skeleton = null
	object.traverse(c => {
		if (c.isSkinnedMesh) {
			if (!skeleton) {
				skeleton = c.skeleton
			} else {
				console.warn("Detected multiple skeletons", skeleton, c.skeleton)
			}
		}
	});

	const boneMap = {}
	skeleton.bones.forEach(b => boneMap[b.name] = b);
	function updateBones(value) {
		console.log("Got bones value", value)

		// TODO: actually process this value here
		// for now just wave arm
		boneMap["mixamorigRightArm"].rotation.set(-0.6, 5 + 2 * ((Date.now() % 1000) / 1000), -2.9)
		console.log(-0.6, 5 + 2 * ((Date.now() % 1000) / 1000), -2.9)
	}

	watch(["value"], () => {
		if (!props.value || !skeleton) return;
		updateBones(props.value)
	})

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
})();
