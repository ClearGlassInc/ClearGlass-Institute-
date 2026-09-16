# Opal-Koboi Platform Runbook

Use the current CI workflow on main as the source of truth.

## Local verification

```bash
npm ci
npm test
npm run build
npm run dashboard
npm run orchestrate
npm run demo
```

## Platform commands

```bash
npm run status
npm run dashboard
npm run plan
npm run run
npm run orchestrate
npm run demo
npm run ci
```

## Expected result

The platform validates package metadata, runs tests, builds artifacts, renders the dashboard command, and runs the orchestration example.

## Azure note

Azure deployment is manual-only until real Azure Functions project files and credentials are configured. Opal-Koboi currently operates as a Node/npm enterprise automation platform.
