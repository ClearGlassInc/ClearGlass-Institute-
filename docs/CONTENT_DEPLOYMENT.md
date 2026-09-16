# ClearGlass Content Deployment System

Opal-Koboi includes a human-gated institutional content deployment workflow for the ClearGlass Trust Infrastructure program.

## Purpose

The system converts a structured campaign manifest into deterministic local artifacts:

- platform-ready Markdown drafts
- a Notion-importable content calendar CSV
- a machine-readable deployment manifest
- an appendable audit record
- a print-ready HTML whitepaper that can be saved as PDF

It does **not** auto-post, mass-engage, call social-platform APIs, call Notion, or bypass platform controls.

## Source campaign

The included example is `examples/trust-infrastructure-campaign.json`. It captures the ClearGlass verified-trust frame, identity integrity, civic cyber readiness, citizen literacy, AI governance, and the 90-day / 12-month / 36-month implementation logic.

## Generate a draft bundle

```bash
npm run content:deploy
```

Equivalent direct command:

```bash
node bin/opal-koboi.js deploy-content \
  examples/trust-infrastructure-campaign.json \
  output/trust-infrastructure
```

The default state is `draft-awaiting-human-approval`.

## Mark a bundle approved for manual publication

```bash
node bin/opal-koboi.js --approve deploy-content \
  examples/trust-infrastructure-campaign.json \
  output/trust-infrastructure-approved
```

`--approve` changes only the local audit/manifest state. It still performs no external publishing.

## Generated structure

```text
output/trust-infrastructure/
├── README.md
├── deployment-manifest.json
├── audit/
│   └── deployment-audit.json
├── drafts/
│   └── *.md
├── notion/
│   ├── README.md
│   └── content-calendar.csv
└── pdf/
    ├── README.md
    └── whitepaper.html
```

## PDF workflow

Open `pdf/whitepaper.html` in a modern browser and use **Print → Save as PDF**. The generated stylesheet is Letter-sized and uses a restrained institutional layout.

## Approval gate

Before publication, a human reviewer must confirm factual support, institutional tone, legal/compliance posture, privacy, platform policy, and final wording. The generated manifest records whether the package is still a draft or has been manually approved.
