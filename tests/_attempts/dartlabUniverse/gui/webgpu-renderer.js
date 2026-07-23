// @ts-nocheck
import { screenPoint } from './math.js';

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

function palette() {
	const styles = getComputedStyle(document.documentElement);
	return Array.from({ length: 6 }, (_, index) => rgba(styles.getPropertyValue(`--series-${index + 1}`)));
}

const NODE_SHADER = `
struct Camera {
	viewProjection: mat4x4<f32>,
	viewport: vec2<f32>,
	padding: vec2<f32>,
};
@group(0) @binding(0) var<uniform> camera: Camera;

struct VertexInput {
	@location(0) position: vec3<f32>,
	@location(1) size: f32,
	@location(2) color: vec4<f32>,
	@location(3) selected: f32,
	@builtin(vertex_index) vertexIndex: u32,
};

struct VertexOutput {
	@builtin(position) position: vec4<f32>,
	@location(0) local: vec2<f32>,
	@location(1) color: vec4<f32>,
	@location(2) selected: f32,
};

@vertex fn vertexMain(input: VertexInput) -> VertexOutput {
	var corners = array<vec2<f32>, 6>(
		vec2<f32>(-1.0, -1.0), vec2<f32>(1.0, -1.0), vec2<f32>(-1.0, 1.0),
		vec2<f32>(-1.0, 1.0), vec2<f32>(1.0, -1.0), vec2<f32>(1.0, 1.0)
	);
	let corner = corners[input.vertexIndex];
	var clip = camera.viewProjection * vec4<f32>(input.position, 1.0);
	clip.z = (clip.z + clip.w) * 0.5;
	let perspectiveScale = clamp(2.2 / max(0.25, clip.w), 0.72, 2.8);
	let pixelSize = min(72.0, input.size * perspectiveScale + input.selected * 8.0);
	let offset = corner * pixelSize * vec2<f32>(1.0 / camera.viewport.x, 1.0 / camera.viewport.y) * clip.w;
	clip.x = clip.x + offset.x;
	clip.y = clip.y + offset.y;
	var output: VertexOutput;
	output.position = clip;
	output.local = corner;
	output.color = input.color;
	output.selected = input.selected;
	return output;
}

@fragment fn fragmentMain(input: VertexOutput) -> @location(0) vec4<f32> {
	let distanceFromCenter = length(input.local);
	if (distanceFromCenter > 1.0) { discard; }
	let core = smoothstep(1.0, 0.38, distanceFromCenter);
	let halo = smoothstep(1.0, 0.05, distanceFromCenter) * 0.34;
	let ring = input.selected * smoothstep(0.95, 0.78, distanceFromCenter) * smoothstep(0.55, 0.78, distanceFromCenter);
	let color = mix(input.color.rgb, vec3<f32>(1.0), core * 0.48 + ring * 0.5);
	return vec4<f32>(color, max(core, halo) * (0.78 + ring * 0.22));
}`;

const EDGE_SHADER = `
struct Camera {
	viewProjection: mat4x4<f32>,
	viewport: vec2<f32>,
	padding: vec2<f32>,
};
@group(0) @binding(0) var<uniform> camera: Camera;
struct VertexInput { @location(0) position: vec3<f32>, @location(1) color: vec4<f32> };
struct VertexOutput { @builtin(position) position: vec4<f32>, @location(0) color: vec4<f32> };
@vertex fn vertexMain(input: VertexInput) -> VertexOutput {
	var output: VertexOutput;
	var clip = camera.viewProjection * vec4<f32>(input.position, 1.0);
	clip.z = (clip.z + clip.w) * 0.5;
	output.position = clip;
	output.color = input.color;
	return output;
}
@fragment fn fragmentMain(input: VertexOutput) -> @location(0) vec4<f32> { return input.color; }
`;

function createBuffer(device, values, usage) {
	const byteLength = Math.max(4, values.byteLength);
	const buffer = device.createBuffer({ size: byteLength, usage, mappedAtCreation: values.byteLength > 0 });
	if (values.byteLength) {
		new Float32Array(buffer.getMappedRange()).set(values);
		buffer.unmap();
	}
	return buffer;
}

export class WebGpuUniverseRenderer {
	static async create(canvas, onContextLost) {
		if (!navigator.gpu) throw new Error('WebGPU를 사용할 수 없음');
		const adapter = await navigator.gpu.requestAdapter({ powerPreference: 'high-performance' });
		if (!adapter) throw new Error('WebGPU adapter를 찾을 수 없음');
		const device = await adapter.requestDevice();
		device.pushErrorScope('validation');
		let renderer;
		try {
			renderer = new WebGpuUniverseRenderer(canvas, device, onContextLost);
		} catch (error) {
			await device.popErrorScope();
			throw error;
		}
		const validationError = await device.popErrorScope();
		if (validationError) {
			renderer.dispose();
			throw new Error(`WebGPU pipeline validation 실패: ${validationError.message}`);
		}
		return renderer;
	}

	constructor(canvas, device, onContextLost) {
		this.canvas = canvas;
		this.device = device;
		this.backendName = 'WebGPU';
		this.context = canvas.getContext('webgpu');
		if (!this.context) throw new Error('WebGPU canvas context를 만들 수 없음');
		this.format = navigator.gpu.getPreferredCanvasFormat();
		this.context.configure({
			device,
			format: this.format,
			alphaMode: 'premultiplied',
			usage: GPUTextureUsage.RENDER_ATTACHMENT | GPUTextureUsage.COPY_SRC
		});
		this.uniformBuffer = device.createBuffer({ size: 80, usage: GPUBufferUsage.UNIFORM | GPUBufferUsage.COPY_DST });
		this.nodes = [];
		this.edges = [];
		this.selectedPickId = 0;
		this.nodeBuffer = createBuffer(device, new Float32Array(), GPUBufferUsage.VERTEX | GPUBufferUsage.COPY_DST);
		this.edgeBuffer = createBuffer(device, new Float32Array(), GPUBufferUsage.VERTEX | GPUBufferUsage.COPY_DST);
		this.depthTexture = null;
		this.width = 0;
		this.height = 0;

		const blend = {
			color: { srcFactor: 'src-alpha', dstFactor: 'one-minus-src-alpha', operation: 'add' },
			alpha: { srcFactor: 'one', dstFactor: 'one-minus-src-alpha', operation: 'add' }
		};
		this.nodePipeline = device.createRenderPipeline({
			layout: 'auto',
			vertex: {
				module: device.createShaderModule({ code: NODE_SHADER }),
				entryPoint: 'vertexMain',
				buffers: [{
					arrayStride: 36,
					stepMode: 'instance',
					attributes: [
						{ shaderLocation: 0, offset: 0, format: 'float32x3' },
						{ shaderLocation: 1, offset: 12, format: 'float32' },
						{ shaderLocation: 2, offset: 16, format: 'float32x4' },
						{ shaderLocation: 3, offset: 32, format: 'float32' }
					]
				}]
			},
			fragment: { module: device.createShaderModule({ code: NODE_SHADER }), entryPoint: 'fragmentMain', targets: [{ format: this.format, blend }] },
			primitive: { topology: 'triangle-list' },
			depthStencil: { format: 'depth24plus', depthWriteEnabled: false, depthCompare: 'less' }
		});
		this.edgePipeline = device.createRenderPipeline({
			layout: 'auto',
			vertex: {
				module: device.createShaderModule({ code: EDGE_SHADER }),
				entryPoint: 'vertexMain',
				buffers: [{
					arrayStride: 28,
					attributes: [
						{ shaderLocation: 0, offset: 0, format: 'float32x3' },
						{ shaderLocation: 1, offset: 12, format: 'float32x4' }
					]
				}]
			},
			fragment: { module: device.createShaderModule({ code: EDGE_SHADER }), entryPoint: 'fragmentMain', targets: [{ format: this.format, blend }] },
			primitive: { topology: 'line-list' },
			depthStencil: { format: 'depth24plus', depthWriteEnabled: false, depthCompare: 'less' }
		});
		this.nodeBindGroup = device.createBindGroup({
			layout: this.nodePipeline.getBindGroupLayout(0),
			entries: [{ binding: 0, resource: { buffer: this.uniformBuffer } }]
		});
		this.edgeBindGroup = device.createBindGroup({
			layout: this.edgePipeline.getBindGroupLayout(0),
			entries: [{ binding: 0, resource: { buffer: this.uniformBuffer } }]
		});
		device.lost.then(() => onContextLost?.());
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
		const colors = palette();
		const values = new Float32Array(this.nodes.length * 9);
		this.nodes.forEach((node, index) => {
			const offset = index * 9;
			values.set(node.position, offset);
			values[offset + 3] = node.size;
			values.set(colors[node.styleIndex % colors.length], offset + 4);
			values[offset + 8] = node.pickId === this.selectedPickId ? 1 : 0;
		});
		this.nodeBuffer.destroy();
		this.nodeBuffer = createBuffer(this.device, values, GPUBufferUsage.VERTEX | GPUBufferUsage.COPY_DST);
	}

	_uploadEdges() {
		const colors = palette();
		const values = new Float32Array(this.edges.length * 14);
		this.edges.forEach((edge, index) => {
			const color = [...colors[edge.styleIndex % colors.length].slice(0, 3), Math.min(0.34, 0.08 + edge.weight * 0.025)];
			const offset = index * 14;
			values.set(edge.from, offset);
			values.set(color, offset + 3);
			values.set(edge.to, offset + 7);
			values.set(color, offset + 10);
		});
		this.edgeBuffer.destroy();
		this.edgeBuffer = createBuffer(this.device, values, GPUBufferUsage.VERTEX | GPUBufferUsage.COPY_DST);
	}

	resize() {
		const ratio = Math.min(2, window.devicePixelRatio || 1);
		const width = Math.max(1, Math.round(this.canvas.clientWidth * ratio));
		const height = Math.max(1, Math.round(this.canvas.clientHeight * ratio));
		if (width !== this.width || height !== this.height) {
			this.width = width;
			this.height = height;
			this.canvas.width = width;
			this.canvas.height = height;
			this.depthTexture?.destroy();
			this.depthTexture = this.device.createTexture({
				size: [width, height],
				format: 'depth24plus',
				usage: GPUTextureUsage.RENDER_ATTACHMENT
			});
		}
		return { width: this.canvas.clientWidth, height: this.canvas.clientHeight, ratio };
	}

	_renderFrame(camera, options = {}, readback = false) {
		this.resize();
		const uniform = new Float32Array(20);
		uniform.set(camera.matrix, 0);
		uniform[16] = this.width;
		uniform[17] = this.height;
		this.device.queue.writeBuffer(this.uniformBuffer, 0, uniform);
		const encoder = this.device.createCommandEncoder();
		const currentTexture = this.context.getCurrentTexture();
		const pass = encoder.beginRenderPass({
			colorAttachments: [{
				view: currentTexture.createView(),
				clearValue: { r: 0, g: 0, b: 0, a: 0 },
				loadOp: 'clear',
				storeOp: 'store'
			}],
			depthStencilAttachment: {
				view: this.depthTexture.createView(),
				depthClearValue: 1,
				depthLoadOp: 'clear',
				depthStoreOp: 'discard'
			}
		});
		if (options.edges !== false && this.edges.length) {
			pass.setPipeline(this.edgePipeline);
			pass.setBindGroup(0, this.edgeBindGroup);
			pass.setVertexBuffer(0, this.edgeBuffer);
			pass.draw(this.edges.length * 2);
		}
		if (this.nodes.length) {
			pass.setPipeline(this.nodePipeline);
			pass.setBindGroup(0, this.nodeBindGroup);
			pass.setVertexBuffer(0, this.nodeBuffer);
			pass.draw(6, this.nodes.length);
		}
		pass.end();
		let probe = null;
		if (readback) {
			const bytesPerRow = Math.ceil(this.width * 4 / 256) * 256;
			const buffer = this.device.createBuffer({
				size: bytesPerRow * this.height,
				usage: GPUBufferUsage.COPY_DST | GPUBufferUsage.MAP_READ
			});
			encoder.copyTextureToBuffer(
				{ texture: currentTexture },
				{ buffer, bytesPerRow, rowsPerImage: this.height },
				{ width: this.width, height: this.height, depthOrArrayLayers: 1 }
			);
			probe = { buffer, bytesPerRow };
		}
		this.device.queue.submit([encoder.finish()]);
		return probe;
	}

	render(camera, options = {}) {
		this._renderFrame(camera, options, false);
	}

	async probeFrame(camera, options = {}) {
		const probe = this._renderFrame(camera, options, true);
		if (!probe) return false;
		await probe.buffer.mapAsync(GPUMapMode.READ);
		const bytes = new Uint8Array(probe.buffer.getMappedRange());
		let coloredPixels = 0;
		for (let row = 0; row < this.height; row += 1) {
			const rowOffset = row * probe.bytesPerRow;
			for (let column = 0; column < this.width; column += 1) {
				if (bytes[rowOffset + column * 4 + 3] > 8) coloredPixels += 1;
			}
		}
		probe.buffer.unmap();
		probe.buffer.destroy();
		return coloredPixels >= Math.min(64, this.nodes.length);
	}

	project(position, camera) {
		return screenPoint(camera.matrix, position, this.canvas.clientWidth, this.canvas.clientHeight);
	}

	dispose() {
		this.nodeBuffer.destroy();
		this.edgeBuffer.destroy();
		this.uniformBuffer.destroy();
		this.depthTexture?.destroy();
	}
}
