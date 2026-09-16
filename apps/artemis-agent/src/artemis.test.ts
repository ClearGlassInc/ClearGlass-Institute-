import { describe, it, expect } from 'vitest'
import { providerRegistry } from './providers/provider-registry.js'
import { slashCommands } from './commands/registry.js'
import { toolRegistry } from './tools/runtime.js'
import { gatewayRegistry } from './gateways/registry.js'
import { installStages, createProgress, ARTEMIS_LOCAL_BACKEND_URL } from './install/progress.js'

describe('provider registry', () => {
  it('has at least one provider', () => {
    expect(providerRegistry.length).toBeGreaterThan(0)
  })

  it('every provider has id and name', () => {
    for (const p of providerRegistry) {
      expect(typeof p.id).toBe('string')
      expect(typeof p.name).toBe('string')
      expect(p.id.length).toBeGreaterThan(0)
    }
  })

  it('anthropic and openai providers are registered', () => {
    const ids = providerRegistry.map(p => p.id)
    expect(ids).toContain('anthropic')
    expect(ids).toContain('openai')
  })

  it('models() returns an array', async () => {
    const result = await providerRegistry[0].models()
    expect(Array.isArray(result)).toBe(true)
  })
})

describe('slash commands', () => {
  it('has standard commands', () => {
    const names = slashCommands.map(c => c.name)
    expect(names).toContain('/help')
    expect(names).toContain('/new')
    expect(names).toContain('/status')
  })

  it('every command has name and description', () => {
    for (const cmd of slashCommands) {
      expect(typeof cmd.name).toBe('string')
      expect(typeof cmd.description).toBe('string')
      expect(cmd.name.startsWith('/')).toBe(true)
    }
  })

  it('execute() is callable without throwing', async () => {
    const ctx = { sessionId: 's1', profileId: 'p1', input: '' }
    for (const cmd of slashCommands) {
      await expect(cmd.execute(ctx)).resolves.toBeUndefined()
    }
  })
})

describe('tool registry', () => {
  it('has core tools', () => {
    const ids = toolRegistry.map(t => t.id)
    expect(ids).toContain('web')
    expect(ids).toContain('terminal')
    expect(ids).toContain('code')
  })

  it('all tools are sandboxed', () => {
    for (const t of toolRegistry) {
      expect(t.sandboxed).toBe(true)
    }
  })
})

describe('gateway registry', () => {
  it('includes common platforms', () => {
    expect(gatewayRegistry).toContain('telegram')
    expect(gatewayRegistry).toContain('slack')
    expect(gatewayRegistry).toContain('discord')
  })

  it('all entries are non-empty strings', () => {
    for (const g of gatewayRegistry) {
      expect(typeof g).toBe('string')
      expect(g.length).toBeGreaterThan(0)
    }
  })
})

describe('install progress', () => {
  it('has six stages ending in complete', () => {
    expect(installStages[installStages.length - 1]).toBe('complete')
    expect(installStages.length).toBe(6)
  })

  it('createProgress returns correct shape', () => {
    const p = createProgress('check_env', 0, 'Checking environment')
    expect(p.stage).toBe('check_env')
    expect(p.percent).toBeGreaterThan(0)
    expect(p.detail).toBe('Checking environment')
    expect(p.complete).toBe(false)
  })

  it('final stage marks complete', () => {
    const p = createProgress('complete', installStages.length - 1, 'Done')
    expect(p.complete).toBe(true)
    expect(p.percent).toBe(100)
  })

  it('backend URL is a valid localhost URL', () => {
    expect(ARTEMIS_LOCAL_BACKEND_URL).toMatch(/^http:\/\/127\.0\.0\.1:\d+$/)
  })
})
