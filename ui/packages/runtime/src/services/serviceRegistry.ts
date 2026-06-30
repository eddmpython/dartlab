// service command registry · TerminalSurface 는 descriptor/command 만 렌더하고 구현은 여기 등록 (02 §7).
import type {
	ServiceCommand,
	ServiceCommandInput,
	ServiceCommandResult,
	ServiceContext,
	ServiceDescriptor,
	ServiceStatusEvent,
	ServicesPort
} from '@dartlab/ui-contracts';

export interface ServiceRegistration {
	descriptor: ServiceDescriptor;
	commands: ServiceCommand[];
	execute: (input: ServiceCommandInput) => Promise<ServiceCommandResult>;
}

export function createServiceRegistry(registrations: ServiceRegistration[]): ServicesPort {
	const listeners = new Set<(status: ServiceStatusEvent) => void>();
	const byCommand = new Map<string, ServiceRegistration>();
	for (const reg of registrations) {
		for (const cmd of reg.commands) byCommand.set(cmd.id, reg);
	}

	return {
		async listServices(_context: ServiceContext): Promise<ServiceDescriptor[]> {
			return registrations.map((r) => r.descriptor);
		},
		async listCommands(context: ServiceContext): Promise<ServiceCommand[]> {
			return registrations
				.flatMap((r) => r.commands)
				.filter((c) => c.mode === 'both' || c.mode === context.mode);
		},
		async executeCommand(input: ServiceCommandInput): Promise<ServiceCommandResult> {
			const reg = byCommand.get(input.commandId);
			if (!reg) {
				return { kind: 'status', ok: false, message: `unknown command: ${input.commandId}` };
			}
			if (reg.descriptor.availability === 'localOnly' || reg.descriptor.availability === 'disabled') {
				// 실행 불가를 정직하게 · upgradeHint 는 surface 가 descriptor 에서 렌더.
				return { kind: 'status', ok: false, message: reg.descriptor.reason ?? reg.descriptor.availability };
			}
			return reg.execute(input);
		},
		subscribeStatus(cb: (status: ServiceStatusEvent) => void): () => void {
			listeners.add(cb);
			return () => listeners.delete(cb);
		}
	};
}
