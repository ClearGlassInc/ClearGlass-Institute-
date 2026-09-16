#! /usr/bin/env node
import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import {
  buildDeploymentBundle,
  createOperationPlan,
  defaultMission,
  formatPlan,
  runOperation,
  EnterpriseAutomationPlatform
} from '../src/index.js';

const args = process.argv.slice(2);
const outputJson = args.includes('--json');
const approved = args.includes('--approve');
const cleanArgs = args.filter((item) => item !== '--json' && item !== '--approve');
const command = cleanArgs[0] || 'help';
const inputPath = cleanArgs[1];
const platform = new EnterpriseAutomationPlatform();

function helpText() {
  return [
    'Opal-Koboi Enterprise Automation Platform',
    '',
    'Commands:',
    '  status                               Show runtime status',
    '  dashboard [file.json]                Show enterprise dashboard summary',
    '  plan [file.json]                     Build an operation plan',
    '  run [file.json]                      Build and execute the next-action simulation',
    '  orchestrate [file.json]              Run a workflow file through the platform engine',
    '  deploy-content file.json [outdir]    Build local drafts, Notion CSV, audit files, and print-ready HTML',
    '  --approve deploy-content ...         Mark generated bundle approved for manual publication',
    '  --json dashboard                     Print machine-readable JSON',
    '',
    'Examples:',
    '  node bin/opal-koboi.js dashboard examples/mission.json',
    '  node bin/opal-koboi.js orchestrate examples/workflow.json',
    '  node bin/opal-koboi.js deploy-content examples/trust-infrastructure-campaign.json output/trust'
  ].join('\n');
}

function loadJson(path, fallback) {
  if (!path) return fallback;
  const absolute = resolve(process.cwd(), path);
  if (!existsSync(absolute)) throw new Error('Input file not found: ' + absolute);
  return JSON.parse(readFileSync(absolute, 'utf8'));
}

function print(value, fallbackText) {
  console.log(outputJson ? JSON.stringify(value, null, 2) : fallbackText);
}

function writeDeployment(bundle, outdir) {
  const root = resolve(process.cwd(), outdir);
  for (const [relativePath, content] of Object.entries(bundle.files)) {
    const target = resolve(root, relativePath);
    mkdirSync(dirname(target), { recursive: true });
    writeFileSync(target, content, 'utf8');
  }
  return root;
}

try {
  if (command === 'help' || command === '--help' || command === '-h') {
    console.log(helpText());
  } else if (command === 'version' || command === '--version' || command === '-v') {
    console.log('2.1.0');
  } else if (command === 'status') {
    const plan = createOperationPlan(loadJson(inputPath, defaultMission));
    const status = {
      ok: true,
      program: 'opal-koboi',
      version: '2.1.0',
      posture: plan.summary.posture,
      tasks: plan.summary.totalTasks,
      nextAction: plan.nextAction ? plan.nextAction.title : null
    };
    print(status, 'Opal-Koboi online. Posture: ' + status.posture + '. Tasks: ' + status.tasks + '.');
  } else if (command === 'dashboard') {
    const dashboard = platform.dashboard(loadJson(inputPath, defaultMission));
    print(dashboard, 'Opal-Koboi dashboard: health=' + dashboard.health + ', posture=' + dashboard.plan.posture + ', tasks=' + dashboard.plan.totalTasks + '.');
  } else if (command === 'plan') {
    const plan = createOperationPlan(loadJson(inputPath, defaultMission));
    print(plan, formatPlan(plan));
  } else if (command === 'run') {
    const result = runOperation(loadJson(inputPath, defaultMission));
    print(result, formatPlan(result.plan) + '\n\n' + result.message);
  } else if (command === 'orchestrate') {
    const workflow = loadJson(inputPath, { name: 'Default Workflow', steps: [{ type: 'plan', name: 'Default Plan', input: defaultMission }] });
    const result = platform.run(workflow);
    print(result, 'Workflow ' + result.name + ' completed. ok=' + result.ok + ', steps=' + result.results.length + '.');
  } else if (command === 'deploy-content') {
    if (!inputPath) throw new Error('deploy-content requires a campaign JSON file.');
    const outdir = cleanArgs[2] || 'output/content-deployment';
    const bundle = buildDeploymentBundle(loadJson(inputPath), { approved });
    const writtenTo = writeDeployment(bundle, outdir);
    const result = {
      ok: true,
      program: 'opal-koboi',
      command: 'deploy-content',
      writtenTo,
      ...bundle.summary,
      externalSideEffects: false,
      automaticPublishing: false
    };
    print(result, `Content deployment bundle written to ${writtenTo}. Status: ${bundle.summary.status}. Files: ${bundle.summary.fileCount}.`);
  } else {
    throw new Error('Unknown command: ' + command);
  }
} catch (error) {
  console.error('Opal-Koboi error: ' + error.message);
  process.exitCode = 1;
}
