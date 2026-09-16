const DEFAULT_WEIGHTS = Object.freeze({
  impact: 0.35,
  urgency: 0.25,
  confidence: 0.25,
  effort: 0.15
});

const DEFAULT_TASKS = Object.freeze([
  {
    id: 'site-link',
    title: 'Keep the ClearGlass web surface connected to Opal-Koboi',
    impact: 92,
    urgency: 78,
    confidence: 88,
    effort: 25,
    owner: 'ClearGlass Inc.'
  },
  {
    id: 'ci-health',
    title: 'Maintain clean CI, package validation, and release readiness',
    impact: 84,
    urgency: 82,
    confidence: 90,
    effort: 30,
    owner: 'ClearGlass Inc.'
  },
  {
    id: 'automation-core',
    title: 'Expand the automation runtime with real operational adapters',
    impact: 96,
    urgency: 70,
    confidence: 72,
    effort: 58,
    owner: 'ClearGlass Inc.'
  }
]);

export function clampScore(value) {
  const number = Number(value);
  if (!Number.isFinite(number)) return 0;
  return Math.max(0, Math.min(100, Math.round(number)));
}

export function scoreTask(task, weights = DEFAULT_WEIGHTS) {
  const impact = clampScore(task.impact);
  const urgency = clampScore(task.urgency);
  const confidence = clampScore(task.confidence ?? 70);
  const effort = clampScore(task.effort ?? 50);
  const score = impact * weights.impact + urgency * weights.urgency + confidence * weights.confidence + (100 - effort) * weights.effort;
  return clampScore(score);
}

export function classifyPriority(score) {
  const normalized = clampScore(score);
  if (normalized >= 80) return 'critical';
  if (normalized >= 65) return 'high';
  if (normalized >= 45) return 'medium';
  return 'low';
}

export function normalizeTask(task, index = 0) {
  if (!task || typeof task !== 'object') throw new TypeError(`Task at index ${index} must be an object.`);
  const title = String(task.title ?? task.name ?? '').trim();
  if (!title) throw new Error(`Task at index ${index} is missing a title.`);
  const id = String(
    task.id ?? (title.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '') || `task-${index + 1}`)
  );
  const score = scoreTask(task);
  return {
    id,
    title,
    owner: String(task.owner ?? 'Unassigned'),
    impact: clampScore(task.impact),
    urgency: clampScore(task.urgency),
    confidence: clampScore(task.confidence ?? 70),
    effort: clampScore(task.effort ?? 50),
    status: String(task.status ?? 'ready'),
    score,
    priority: classifyPriority(score)
  };
}

export function createOperationPlan(input = {}) {
  const mission = String(input.mission ?? 'Opal-Koboi Mission Command').trim();
  const tasks = Array.isArray(input.tasks) && input.tasks.length > 0 ? input.tasks : DEFAULT_TASKS;
  const normalizedTasks = tasks.map(normalizeTask).sort((a, b) => b.score - a.score || b.urgency - a.urgency);
  const critical = normalizedTasks.filter((task) => task.priority === 'critical').length;
  const high = normalizedTasks.filter((task) => task.priority === 'high').length;
  const averageScore = normalizedTasks.length ? clampScore(normalizedTasks.reduce((sum, task) => sum + task.score, 0) / normalizedTasks.length) : 0;
  const nextAction = normalizedTasks[0] ?? null;
  return {
    mission,
    generatedAt: new Date().toISOString(),
    summary: {
      totalTasks: normalizedTasks.length,
      averageScore,
      critical,
      high,
      posture: averageScore >= 75 ? 'aggressive' : averageScore >= 55 ? 'stable' : 'needs-focus'
    },
    nextAction,
    tasks: normalizedTasks
  };
}

export function formatPlan(plan) {
  const lines = [];
  lines.push(`Opal-Koboi Mission: ${plan.mission}`);
  lines.push(`Posture: ${plan.summary.posture}`);
  lines.push(`Average Score: ${plan.summary.averageScore}`);
  lines.push(`Tasks: ${plan.summary.totalTasks} | Critical: ${plan.summary.critical} | High: ${plan.summary.high}`);
  if (plan.nextAction) {
    lines.push('');
    lines.push(`Next Action: [${plan.nextAction.priority.toUpperCase()}] ${plan.nextAction.title}`);
    lines.push(`Owner: ${plan.nextAction.owner} | Score: ${plan.nextAction.score}`);
  }
  lines.push('');
  lines.push('Ranked Tasks:');
  for (const [index, task] of plan.tasks.entries()) lines.push(`${index + 1}. ${task.title} — ${task.priority} (${task.score})`);
  return lines.join('\n');
}

export function runOperation(input = {}) {
  const plan = createOperationPlan(input);
  return {
    ok: true,
    program: 'opal-koboi',
    version: '2.1.0',
    plan,
    message: plan.nextAction ? `Execute next: ${plan.nextAction.title}` : 'No tasks available.'
  };
}

export const defaultMission = Object.freeze({
  mission: 'Opal-Koboi Advanced Automation',
  tasks: DEFAULT_TASKS
});

export { AuditLedger, PolicyEngine, WorkflowEngine, EnterpriseAutomationPlatform } from './platform.js';
export { buildDeploymentBundle, normalizeCampaign, slugify } from './content-deployment.js';
