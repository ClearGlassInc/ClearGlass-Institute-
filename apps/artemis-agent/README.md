# Artemis Agent

Electron + Vite desktop agent environment integrated into the Opal-Koboi repository.

## Features

- Guided first-run installation with dependency resolution
- Multi-provider routing
- Streaming SSE chat UI
- Tool orchestration runtime
- Session search with SQLite FTS5
- Memory provider abstraction
- Persona editor using SOUL.md
- Cron scheduler and gateway delivery
- Auto-updater using electron-updater
- Vitest test coverage

## Providers

- OpenRouter
- Anthropic
- OpenAI
- Google Gemini
- xAI Grok
- Nous Portal
- Qwen
- MiniMax
- Hugging Face
- Groq
- Ollama
- LM Studio
- llama.cpp
- vLLM

## Local Backend

Default local runtime:

http://127.0.0.1:8642

## Commands

- /new
- /clear
- /fast
- /web
- /image
- /browse
- /code
- /shell
- /usage
- /help
- /tools
- /skills
- /model
- /memory
- /persona
- /version
- /compact
- /compress
- /undo
- /retry
- /debug
- /status

## Architecture

apps/artemis-agent/
  src/main
  src/preload
  src/renderer
  src/providers
  src/tools
  src/memory
  src/gateways
  src/session
  src/persona
  src/install
  src/updater
  src/tests
