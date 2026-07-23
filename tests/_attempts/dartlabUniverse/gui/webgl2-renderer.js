// @ts-nocheck
import { screenPoint } from './math.js';

function shader(gl, type, source) {
	const value = gl.createShader(type);
	if (!value) throw new Error('WebGL shader 생성 실패');
	gl.shaderSource(value, source);
	gl.compileShader(value);
	if (!gl.getShaderParameter(value, gl.COMPILE_STATUS)) {
		const message = gl.getShaderInfoLog(value) || 'WebGL shader compile 실패';
		gl.deleteShader(value);
		throw new Error(message);
	}
	return value;
}

function program(gl, vertexSource, fragmentSource) {
	const value = gl.createProgram();
	if (!value) throw new Error('WebGL program 생성 실패');
	const vertex = shader(gl, gl.VERTEX_SHADER, vertexSource);
	const fragment = shader(gl, gl.FRAGMENT_SHADER, fragmentSource);
	gl.attachShader(value, vertex);
	gl.attachShader(value, fragment);
	gl.linkProgram(value);
	gl.deleteShader(vertex);
	gl.deleteShader(fragment);
	if (!gl.getProgramParameter(value, gl.LINK_STATUS)) throw new Error(gl.getProgramInfoLog(value) || 'WebGL link 실패');
	return value;
}

function rgba(value) {
	const normalized = value.trim();
	if (/^#[0-9a-f]{6}$/i.test(normalized)) {
		return [
			parseInt(normalized.slice(1, 3), 16) / 255,
			parseInt(normalized.slice(3, 5), 16) / 255,
			parseInt(normalized.slice(5, 7), 16) / 255,
			1
		];
	}
	const match = normalized.match(/[\d.]+/g)?.map(Number);
	if (match && match.length >= 3) return [match[0] / 255, match[1] / 255, match[2] / 255, 1];
	return [0.48, 0.72, 1, 1];
}

function palette(element) {
	const styles = getComputedStyle(element);
	return Array.from({ length: 6 }, (_, index) => rgba(styles.getPropertyValue(`--series-${index + 1}`)));
}

const NODE_VERTEX = `#version 300 es
precision highp float;
layout(location=0) in vec3 aPosition;
layout(location=1) in float aSize;
layout(location=2) in vec4 aColor;
layout(location=3) in float aSelected;
uniform mat4 uViewProjection;
out vec4 vColor;
out float vSelected;
void main() {
	vec4 clip = uViewProjection * vec4(aPosition, 1.0);
	gl_Position = clip;
	float perspectiveScale = clamp(2.2 / max(0.25, clip.w), 0.72, 2.8);
	gl_PointSize = min(72.0, aSize * perspectiveScale + aSelected * 8.0);
	vColor = aColor;
	vSelected = aSelected;
}`;

const NODE_FRAGMENT = `#version 300 es
precision highp float;
in vec4 vColor;
in float vSelected;
out vec4 outColor;
void main() {
	vec2 point = gl_PointCoord * 2.0 - 1.0;
	float distanceFromCenter = length(point);
	if (distanceFromCenter > 1.0) discard;
	float core = smoothstep(1.0, 0.38, distanceFromCenter);
	float halo = smoothstep(1.0, 0.05, distanceFromCenter) * 0.34;
	float ring = vSelected * smoothstep(0.95, 0.78, distanceFromCenter) * smoothstep(0.55, 0.78, distanceFromCenter);
	vec3 color = mix(vColor.rgb, vec3(1.0), core * 0.48 + ring * 0.5);
	outColor = vec4(color, max(core, halo) * (0.78 + ring * 0.22));
}`;

const EDGE_VERTEX = `#version 300 es
precision highp float;
layout(location=0) in vec3 aPosition;
layout(location=1) in vec4 aColor;
uniform mat4 uViewProjection;
out vec4 vColor;
void main() {
	gl_Position = uViewProjection * vec4(aPosition, 1.0);
	vColor = aColor;
}`;

const EDGE_FRAGMENT = `#version 300 es
precision highp float;
in vec4 vColor;
out vec4 outColor;
void main() { outColor = vColor; }`;

export class WebGlUniverseRenderer {
	constructor(canvas, onContextLost) {
		const gl = canvas.getContext('webgl2', {
			alpha: true,
			antialias: true,
			depth: true,
			powerPreference: 'high-performance',
			premultipliedAlpha: true
		});
		if (!gl) throw new Error('WebGL2를 사용할 수 없음');
		this.canvas = canvas;
		this.gl = gl;
		this.backendName = 'WebGL2';
		this.nodeProgram = program(gl, NODE_VERTEX, NODE_FRAGMENT);
		this.edgeProgram = program(gl, EDGE_VERTEX, EDGE_FRAGMENT);
		this.nodeBuffer = gl.createBuffer();
		this.edgeBuffer = gl.createBuffer();
		this.nodes = [];
		this.edges = [];
		this.selectedPickId = 0;
		this.nodeCount = 0;
		this.edgeVertexCount = 0;
		canvas.addEventListener('webglcontextlost', (event) => {
			event.preventDefault();
			onContextLost?.();
		});
	}

	setScene(scene) {
		this.nodes = scene.nodes;
		this.edges = scene.edges;
		this._uploadNodes();
		this._uploadEdges();
	}

	setSelected(pickId) {
		if (this.selectedPickId === pickId) return;
		this.selectedPickId = pickId || 0;
		this._uploadNodes();
	}

	_uploadNodes() {
		const gl = this.gl;
		const colors = palette(this.canvas);
		const values = new Float32Array(this.nodes.length * 9);
		this.nodes.forEach((node, index) => {
			const offset = index * 9;
			const color = colors[node.styleIndex % colors.length];
			values.set(node.position, offset);
			values[offset + 3] = node.size;
			values.set(color, offset + 4);
			values[offset + 8] = node.pickId === this.selectedPickId ? 1 : 0;
		});
		gl.bindBuffer(gl.ARRAY_BUFFER, this.nodeBuffer);
		gl.bufferData(gl.ARRAY_BUFFER, values, gl.DYNAMIC_DRAW);
		this.nodeCount = this.nodes.length;
	}

	_uploadEdges() {
		const gl = this.gl;
		const colors = palette(this.canvas);
		const values = new Float32Array(this.edges.length * 14);
		this.edges.forEach((edge, index) => {
			const color = [...colors[edge.styleIndex % colors.length].slice(0, 3), Math.min(0.34, 0.08 + edge.weight * 0.025)];
			const offset = index * 14;
			values.set(edge.from, offset);
			values.set(color, offset + 3);
			values.set(edge.to, offset + 7);
			values.set(color, offset + 10);
		});
		gl.bindBuffer(gl.ARRAY_BUFFER, this.edgeBuffer);
		gl.bufferData(gl.ARRAY_BUFFER, values, gl.STATIC_DRAW);
		this.edgeVertexCount = this.edges.length * 2;
	}

	resize() {
		const ratio = Math.min(2, window.devicePixelRatio || 1);
		const width = Math.max(1, Math.round(this.canvas.clientWidth * ratio));
		const height = Math.max(1, Math.round(this.canvas.clientHeight * ratio));
		if (this.canvas.width !== width || this.canvas.height !== height) {
			this.canvas.width = width;
			this.canvas.height = height;
		}
		this.gl.viewport(0, 0, width, height);
		return { width: this.canvas.clientWidth, height: this.canvas.clientHeight, ratio };
	}

	render(camera, options = {}) {
		const gl = this.gl;
		this.resize();
		gl.clearColor(0, 0, 0, 0);
		gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);
		gl.enable(gl.BLEND);
		gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA);
		gl.enable(gl.DEPTH_TEST);
		gl.depthMask(false);

		if (options.edges !== false && this.edgeVertexCount) {
			gl.useProgram(this.edgeProgram);
			gl.uniformMatrix4fv(gl.getUniformLocation(this.edgeProgram, 'uViewProjection'), false, camera.matrix);
			gl.bindBuffer(gl.ARRAY_BUFFER, this.edgeBuffer);
			gl.enableVertexAttribArray(0);
			gl.vertexAttribPointer(0, 3, gl.FLOAT, false, 28, 0);
			gl.enableVertexAttribArray(1);
			gl.vertexAttribPointer(1, 4, gl.FLOAT, false, 28, 12);
			gl.drawArrays(gl.LINES, 0, this.edgeVertexCount);
		}

		gl.blendFunc(gl.SRC_ALPHA, gl.ONE);
		gl.useProgram(this.nodeProgram);
		gl.uniformMatrix4fv(gl.getUniformLocation(this.nodeProgram, 'uViewProjection'), false, camera.matrix);
		gl.bindBuffer(gl.ARRAY_BUFFER, this.nodeBuffer);
		gl.enableVertexAttribArray(0);
		gl.vertexAttribPointer(0, 3, gl.FLOAT, false, 36, 0);
		gl.enableVertexAttribArray(1);
		gl.vertexAttribPointer(1, 1, gl.FLOAT, false, 36, 12);
		gl.enableVertexAttribArray(2);
		gl.vertexAttribPointer(2, 4, gl.FLOAT, false, 36, 16);
		gl.enableVertexAttribArray(3);
		gl.vertexAttribPointer(3, 1, gl.FLOAT, false, 36, 32);
		gl.drawArrays(gl.POINTS, 0, this.nodeCount);
		gl.depthMask(true);
	}

	project(position, camera) {
		return screenPoint(camera.matrix, position, this.canvas.clientWidth, this.canvas.clientHeight);
	}

	dispose() {
		const gl = this.gl;
		gl.deleteBuffer(this.nodeBuffer);
		gl.deleteBuffer(this.edgeBuffer);
		gl.deleteProgram(this.nodeProgram);
		gl.deleteProgram(this.edgeProgram);
	}
}
