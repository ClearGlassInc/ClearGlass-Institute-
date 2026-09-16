export type ArtemisTool = {
  id: string
  description: string
  sandboxed: boolean
}

export const toolRegistry: ArtemisTool[] = [
  { id: 'web', description: 'Web search and retrieval', sandboxed: true },
  { id: 'browser', description: 'Browser automation', sandboxed: true },
  { id: 'terminal', description: 'Terminal execution', sandboxed: true },
  { id: 'file', description: 'File management', sandboxed: true },
  { id: 'code', description: 'Code execution', sandboxed: true },
  { id: 'vision', description: 'Vision processing', sandboxed: true },
  { id: 'image', description: 'Image generation', sandboxed: true },
  { id: 'tts', description: 'Text to speech', sandboxed: true },
  { id: 'skills', description: 'Skill runtime', sandboxed: true },
  { id: 'memory', description: 'Memory system', sandboxed: true },
  { id: 'session-search', description: 'Conversation search', sandboxed: true },
  { id: 'clarify', description: 'Clarification engine', sandboxed: true },
  { id: 'delegation', description: 'Delegation runtime', sandboxed: true },
  { id: 'moa', description: 'Mixture of agents', sandboxed: true },
  { id: 'planning', description: 'Task planning', sandboxed: true }
]
