export function multiply4(a, b) {
	const out = new Float32Array(16);
	for (let column = 0; column < 4; column += 1) {
		for (let row = 0; row < 4; row += 1) {
			out[column * 4 + row] =
				a[row] * b[column * 4] +
				a[4 + row] * b[column * 4 + 1] +
				a[8 + row] * b[column * 4 + 2] +
				a[12 + row] * b[column * 4 + 3];
		}
	}
	return out;
}

export function perspective(fovRadians, aspect, near, far) {
	const f = 1 / Math.tan(fovRadians / 2);
	const range = 1 / (near - far);
	return new Float32Array([
		f / aspect, 0, 0, 0,
		0, f, 0, 0,
		0, 0, (far + near) * range, -1,
		0, 0, 2 * far * near * range, 0
	]);
}

function normalize(v) {
	const length = Math.hypot(v[0], v[1], v[2]) || 1;
	return [v[0] / length, v[1] / length, v[2] / length];
}

function cross(a, b) {
	return [
		a[1] * b[2] - a[2] * b[1],
		a[2] * b[0] - a[0] * b[2],
		a[0] * b[1] - a[1] * b[0]
	];
}

function dot(a, b) {
	return a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
}

export function lookAt(eye, center, up) {
	const z = normalize([eye[0] - center[0], eye[1] - center[1], eye[2] - center[2]]);
	const x = normalize(cross(up, z));
	const y = cross(z, x);
	return new Float32Array([
		x[0], y[0], z[0], 0,
		x[1], y[1], z[1], 0,
		x[2], y[2], z[2], 0,
		-dot(x, eye), -dot(y, eye), -dot(z, eye), 1
	]);
}

export function transformPoint(matrix, point) {
	const x = point[0];
	const y = point[1];
	const z = point[2];
	return [
		matrix[0] * x + matrix[4] * y + matrix[8] * z + matrix[12],
		matrix[1] * x + matrix[5] * y + matrix[9] * z + matrix[13],
		matrix[2] * x + matrix[6] * y + matrix[10] * z + matrix[14],
		matrix[3] * x + matrix[7] * y + matrix[11] * z + matrix[15]
	];
}

export function screenPoint(matrix, point, width, height) {
	const clip = transformPoint(matrix, point);
	if (clip[3] <= 0) return null;
	const x = clip[0] / clip[3];
	const y = clip[1] / clip[3];
	const z = clip[2] / clip[3];
	if (z < -1 || z > 1) return null;
	return {
		x: (x * 0.5 + 0.5) * width,
		y: (1 - (y * 0.5 + 0.5)) * height,
		depth: z,
		clipW: clip[3]
	};
}
