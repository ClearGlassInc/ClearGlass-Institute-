export interface CommandContext {
  sessionId: string
  profileId: string
  input: string
}

export interface SlashCommand {
  name: string
  description: string
  execute(context: CommandContext): Promise<void>
}

export const slashCommands: SlashCommand[] = [
  { name: '/new', description: 'Create new session', async execute() {} },
  { name: '/clear', description: 'Clear conversation', async execute() {} },
  { name: '/fast', description: 'Fast inference mode', async execute() {} },
  { name: '/web', description: 'Enable web tools', async execute() {} },
  { name: '/image', description: 'Image generation', async execute() {} },
  { name: '/browse', description: 'Browser tools', async execute() {} },
  { name: '/code', description: 'Code execution', async execute() {} },
  { name: '/shell', description: 'Shell execution', async execute() {} },
  { name: '/usage', description: 'Token usage', async execute() {} },
  { name: '/help', description: 'Help menu', async execute() {} },
  { name: '/tools', description: 'Tool registry', async execute() {} },
  { name: '/skills', description: 'Skill system', async execute() {} },
  { name: '/model', description: 'Model selection', async execute() {} },
  { name: '/memory', description: 'Memory manager', async execute() {} },
  { name: '/persona', description: 'Persona editor', async execute() {} },
  { name: '/version', description: 'Runtime version', async execute() {} },
  { name: '/compact', description: 'Compact context', async execute() {} },
  { name: '/compress', description: 'Compression', async execute() {} },
  { name: '/undo', description: 'Undo action', async execute() {} },
  { name: '/retry', description: 'Retry request', async execute() {} },
  { name: '/debug', description: 'Debug runtime', async execute() {} },
  { name: '/status', description: 'System status', async execute() {} }
]
