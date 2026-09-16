import assert from 'node:assert/strict';
import {
  AuditLedger,
  EnterpriseAutomationPlatform,
  PolicyEngine,
  WorkflowEngine,
  buildDeploymentBundle,
  classifyPriority,
  createOperationPlan,
  normalizeCampaign,
  runOperation,
  scoreTask,
  slugify
} from '../src/index.js';

const task = {
  title: 'Deploy ClearGlass automation layer',
  impact: 90,
  urgency: 80,
  confidence: 85,
  effort: 20,
  owner: 'ClearGlass Inc.'
};

assert.equal(classifyPriority(85), 'critical');
assert.equal(classifyPriority(70), 'high');
assert.equal(classifyPriority(50), 'medium');
assert.equal(classifyPriority(20), 'low');
assert.equal(scoreTask(task) >= 80, true);

const plan = createOperationPlan({ mission: 'Test mission', tasks: [task] });
assert.equal(plan.mission, 'Test mission');
assert.equal(plan.summary.totalTasks, 1);
assert.equal(plan.nextAction.title, task.title);
assert.equal(plan.tasks[0].priority, 'critical');

const result = runOperation({ mission: 'Runtime mission', tasks: [task] });
assert.equal(result.ok, true);
assert.equal(result.program, 'opal-koboi');
assert.equal(result.message.includes('Deploy ClearGlass automation layer'), true);

const audit = new AuditLedger();
audit.add('test.event', { ok: true });
assert.equal(audit.all().length, 1);

const policy = new PolicyEngine();
const policyResult = policy.evaluatePlan(plan);
assert.equal(policyResult.allowed, true);

const workflow = new WorkflowEngine({ audit, policy });
const workflowResult = workflow.run({
  name: 'Test Workflow',
  steps: [
    { type: 'note', name: 'intake', message: 'ready' },
    { type: 'plan', name: 'planning', input: { mission: 'Workflow mission', tasks: [task] } },
    { type: 'metric', name: 'readiness', value: 90, minimum: 75 },
    { type: 'gate', name: 'approval', allow: true }
  ]
});
assert.equal(workflowResult.ok, true);
assert.equal(workflowResult.results.length, 4);

const platform = new EnterpriseAutomationPlatform();
const dashboard = platform.dashboard({ mission: 'Dashboard mission', tasks: [task] });
assert.equal(dashboard.platform, 'Opal-Koboi');
assert.equal(dashboard.health, 'green');

const campaignInput = {
  title: 'Verified Trust Test',
  brand: 'ClearGlass Inc.',
  posts: [
    {
      title: 'Trust Is Infrastructure',
      body: 'Verification replaces assumption.',
      channels: ['linkedin', 'x']
    }
  ],
  whitepaper: {
    title: 'Public Trust Architecture',
    sections: [
      {
        heading: 'Executive Summary',
        body: 'Truth must be verifiable and governance must be auditable.'
      }
    ]
  }
};

const normalizedCampaign = normalizeCampaign(campaignInput);
assert.equal(normalizedCampaign.id, 'verified-trust-test');
assert.equal(slugify('Identity = Sovereignty'), 'identity-sovereignty');

const deployment = buildDeploymentBundle(campaignInput, {
  approved: false,
  generatedAt: '2026-08-13T17:11:00.000Z'
});
assert.equal(deployment.summary.status, 'draft-awaiting-human-approval');
assert.equal(deployment.summary.fileCount, 8);
assert.equal(deployment.summary.postCount, 1);
assert.equal(deployment.files['deployment-manifest.json'].includes('draft-awaiting-human-approval'), true);
assert.equal(deployment.files['notion/content-calendar.csv'].includes('Trust Is Infrastructure'), true);
assert.equal(deployment.files['pdf/whitepaper.html'].includes('Public Trust Architecture'), true);
assert.equal(deployment.files['audit/deployment-audit.json'].includes('"automaticPublishing": false'), true);

console.log('Opal-Koboi enterprise platform tests passed.');
