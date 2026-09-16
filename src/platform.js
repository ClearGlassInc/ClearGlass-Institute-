import { createOperationPlan, formatPlan } from './index.js';

export class AuditLedger {
  constructor() {
    this.records = [];
  }

  add(event, details = {}) {
    const record = {
      id: `audit-${String(this.records.length + 1).padStart(6, '0')}`,
      event,
      details,
      timestamp: new Date().toISOString()
    };

    this.records.push(Object.freeze(record));
    return record;
  }

  all() {
    return [...this.records];
  }
}

export class PolicyEngine {
  constructor(rules = []) {
    this.rules = rules.length > 0 ? rules : [
      { id: 'require-owner', field: 'owner', mode: 'required', severity: 'high' },
      { id: 'block-low-confidence-critical', field: 'confidence', mode: 'minimum', value: 55, severity: 'critical' },
      { id: 'control-extreme-effort', field: 'effort', mode: 'maximum', value: 95, severity: 'medium' }
    ];
  }

  evaluateTask(task) {
    const findings = [];

    for (const rule of this.rules) {
      const value = task[rule.field];
      if (rule.mode === 'required' && (value === undefined || value === null || String(value).trim() === '')) {
        findings.push({ ruleId: rule.id, severity: rule.severity, message: `${rule.field} is required` });
      }
      if (rule.mode === 'minimum' && Number(value) < Number(rule.value)) {
        findings.push({ ruleId: rule.id, severity: rule.severity, message: `${rule.field} must be at least ${rule.value}` });
      }
      if (rule.mode === 'maximum' && Number(value) > Number(rule.value)) {
        findings.push({ ruleId: rule.id, severity: rule.severity, message: `${rule.field} must be no more than ${rule.value}` });
      }
    }

    return {
      taskId: task.id,
      allowed: !findings.some((finding) => finding.severity === 'critical'),
      findings
    };
  }

  evaluatePlan(plan) {
    const taskResults = plan.tasks.map((task) => this.evaluateTask(task));
    return {
      allowed: taskResults.every((result) => result.allowed),
      taskResults,
      findingCount: taskResults.reduce((sum, result) => sum + result.findings.length, 0)
    };
  }
}

export class WorkflowEngine {
  constructor({ audit = new AuditLedger(), policy = new PolicyEngine() } = {}) {
    this.audit = audit;
    this.policy = policy;
  }

  run(workflow = {}) {
    const name = String(workflow.name ?? 'Opal-Koboi Enterprise Workflow');
    const steps = Array.isArray(workflow.steps) ? workflow.steps : [];
    const startedAt = new Date().toISOString();
    const results = [];

    this.audit.add('workflow.started', { name, steps: steps.length });

    for (const [index, step] of steps.entries()) {
      const result = this.runStep(step, index);
      results.push(result);
      if (!result.ok) break;
    }

    const ok = results.every((result) => result.ok);
    const completedAt = new Date().toISOString();
    this.audit.add('workflow.completed', { name, ok, completedSteps: results.length });

    return { ok, name, startedAt, completedAt, results, audit: this.audit.all() };
  }

  runStep(step = {}, index = 0) {
    const type = String(step.type ?? 'note');
    const name = String(step.name ?? `step-${index + 1}`);
    this.audit.add('workflow.step', { index, name, type });

    if (type === 'note') {
      return { ok: true, index, name, type, output: String(step.message ?? 'Recorded note.') };
    }

    if (type === 'plan') {
      const plan = createOperationPlan(step.input ?? {});
      const policy = this.policy.evaluatePlan(plan);
      return { ok: policy.allowed, index, name, type, output: formatPlan(plan), plan, policy };
    }

    if (type === 'gate') {
      const condition = Boolean(step.allow ?? true);
      return { ok: condition, index, name, type, output: condition ? 'Gate passed.' : 'Gate blocked.' };
    }

    if (type === 'metric') {
      const value = Number(step.value ?? 0);
      const minimum = Number(step.minimum ?? 0);
      return { ok: value >= minimum, index, name, type, output: `${value} >= ${minimum}`, value, minimum };
    }

    return { ok: false, index, name, type, output: `Unsupported step type: ${type}` };
  }
}

export class EnterpriseAutomationPlatform {
  constructor(config = {}) {
    this.config = {
      organization: 'ClearGlass Inc.',
      environment: 'production-ready',
      ...config
    };
    this.audit = new AuditLedger();
    this.policy = new PolicyEngine(config.rules);
    this.workflow = new WorkflowEngine({ audit: this.audit, policy: this.policy });
  }

  dashboard(input = {}) {
    const plan = createOperationPlan(input);
    const policy = this.policy.evaluatePlan(plan);
    return {
      platform: 'Opal-Koboi',
      organization: this.config.organization,
      environment: this.config.environment,
      generatedAt: new Date().toISOString(),
      plan: plan.summary,
      nextAction: plan.nextAction,
      policy,
      health: policy.allowed ? 'green' : 'red'
    };
  }

  plan(input = {}) {
    const plan = createOperationPlan(input);
    const policy = this.policy.evaluatePlan(plan);
    this.audit.add('platform.plan.created', { mission: plan.mission, tasks: plan.summary.totalTasks, allowed: policy.allowed });
    return { plan, policy, audit: this.audit.all() };
  }

  run(workflow = {}) {
    return this.workflow.run(workflow);
  }
}
