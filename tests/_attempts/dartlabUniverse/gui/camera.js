import { lookAt, multiply4, perspective } from './math.js';

export class OrbitCamera {
	constructor() {
		this.target = [0, 0, 0];
		this.yaw = -0.62;
		this.pitch = 0.28;
		this.distance = 3.35;
		this.aspect = 1;
		this.matrix = new Float32Array(16);
		this.eye = [0, 0, 3.35];
		this.update();
	}

	update() {
		const cosPitch = Math.cos(this.pitch);
		this.eye = [
			this.target[0] + this.distance * cosPitch * Math.sin(this.yaw),
			this.target[1] + this.distance * Math.sin(this.pitch),
			this.target[2] + this.distance * cosPitch * Math.cos(this.yaw)
		];
		const view = lookAt(this.eye, this.target, [0, 1, 0]);
		const projection = perspective(Math.PI * 0.3, Math.max(0.1, this.aspect), 0.01, 40);
		this.matrix = multiply4(projection, view);
		return this.matrix;
	}

	reset() {
		this.target = [0, 0, 0];
		this.yaw = -0.62;
		this.pitch = 0.28;
		this.distance = 3.35;
		this.update();
	}

	focus(point, distance = 1.25) {
		this.target = [...point];
		this.distance = Math.max(0.3, Math.min(6, distance));
		this.update();
	}

	frame(points) {
		if (!points.length) {
			this.reset();
			return;
		}
		const minimum = [...points[0]];
		const maximum = [...points[0]];
		for (const point of points) {
			for (let axis = 0; axis < 3; axis += 1) {
				minimum[axis] = Math.min(minimum[axis], point[axis]);
				maximum[axis] = Math.max(maximum[axis], point[axis]);
			}
		}
		this.target = minimum.map((value, axis) => (value + maximum[axis]) * 0.5);
		const radius = Math.max(...points.map((point) => Math.hypot(
			point[0] - this.target[0],
			point[1] - this.target[1],
			point[2] - this.target[2]
		)));
		const narrowViewportScale = this.aspect < 1 ? 1 / Math.max(0.38, this.aspect) : 1;
		this.distance = Math.max(0.24, Math.min(8, radius * 1.92 * narrowViewportScale));
		this.yaw = -0.62;
		this.pitch = 0.28;
		this.update();
	}

	orbit(deltaX, deltaY) {
		this.yaw -= deltaX * 0.006;
		this.pitch = Math.max(-1.42, Math.min(1.42, this.pitch - deltaY * 0.006));
		this.update();
	}

	zoom(delta) {
		this.distance = Math.max(0.18, Math.min(8, this.distance * Math.exp(delta * 0.001)));
		this.update();
	}

	pan(horizontal, vertical) {
		const scale = this.distance * 0.018;
		this.target[0] += horizontal * scale;
		this.target[1] += vertical * scale;
		this.update();
	}
}

export function bindCameraControls(canvas, camera, onChange, onClick) {
	let activePointer = null;
	let lastX = 0;
	let lastY = 0;
	let travel = 0;

	canvas.addEventListener('pointerdown', (event) => {
		activePointer = event.pointerId;
		lastX = event.clientX;
		lastY = event.clientY;
		travel = 0;
		canvas.setPointerCapture(event.pointerId);
	});

	canvas.addEventListener('pointermove', (event) => {
		if (event.pointerId !== activePointer) return;
		const dx = event.clientX - lastX;
		const dy = event.clientY - lastY;
		lastX = event.clientX;
		lastY = event.clientY;
		travel += Math.hypot(dx, dy);
		camera.orbit(dx, dy);
		onChange();
	});

	canvas.addEventListener('pointerup', (event) => {
		if (event.pointerId !== activePointer) return;
		activePointer = null;
		if (travel < 5) onClick(event.clientX, event.clientY);
	});

	canvas.addEventListener('wheel', (event) => {
		event.preventDefault();
		camera.zoom(event.deltaY);
		onChange();
	}, { passive: false });

	window.addEventListener('keydown', (event) => {
		if (event.target instanceof HTMLInputElement || event.target instanceof HTMLTextAreaElement) return;
		const movement = {
			ArrowLeft: [-1, 0],
			ArrowRight: [1, 0],
			ArrowUp: [0, 1],
			ArrowDown: [0, -1]
		}[event.key];
		if (movement) {
			event.preventDefault();
			camera.pan(movement[0], movement[1]);
			onChange();
		} else if (event.key === '+' || event.key === '=') {
			camera.zoom(-120);
			onChange();
		} else if (event.key === '-') {
			camera.zoom(120);
			onChange();
		}
	});
}
