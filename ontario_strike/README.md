# ClearGlass Ontario strike scripts

Public, local-only tools. They do not authenticate to a third-party production account unless the operator exports data or passes a path.

| Script | Bottleneck class | Intended company class |
|---|---|---|
| terraform_plan_guard.py | Slow / unsafe Terraform + Terrateam plans | AWS IaC platform teams |
| gha_queue_doctor.py | GitHub Actions queue time, flaky jobs, missing concurrency | Product orgs shipping on GHA |
| azure_slo_burn.py | Azure SRE without a burn-rate gate | Healthcare / enterprise Azure |
| cloud_idle_finops.py | Cloud waste and missing FinOps guardrails | SaaS cloud platform orgs |
| k8s_rollout_brake.py | Deployments that roll forward on error | Kubernetes SaaS platforms |

Run:

    python3 terraform_plan_guard.py --plan sample_plan.json
    python3 gha_queue_doctor.py --log sample_gha.json
    python3 azure_slo_burn.py --window 1h --slo 99.9 --burn 2.0 --errors 12 --requests 10000
    python3 cloud_idle_finops.py --inventory sample_inventory.json
    python3 k8s_rollout_brake.py --status sample_rollout.json
