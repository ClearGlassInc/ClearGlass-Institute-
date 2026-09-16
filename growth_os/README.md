# Growth OS

Growth OS is a compliant social growth analytics and drafting assistant for account-level optimization.

It does **not** auto-post, mass-engage, bypass platform controls, or automate spam behavior.

## What it does

- Ingests post history and comment history from CSV or JSON
- Scores topics, hooks, structures, CTAs, and tones
- Recommends posting windows using your own account performance
- Flags high-value comments to reply to quickly
- Converts strong comments into follow-up reply drafts and new post drafts
- Generates 3–5 post variants per topic
- Suggests simple A/B tests for hooks, length, CTA, and tone

## Files

- `growth_os.py` — main CLI
- `Run-GrowthOS.ps1` — PowerShell wrapper
- `config.example.json` — identity and voice settings
- `examples/posts_template.csv` — starter posts schema
- `examples/comments_template.csv` — starter comments schema

## Quick start

```bash
python growth_os.py \
  --posts examples/posts_template.csv \
  --comments examples/comments_template.csv \
  --identity config.example.json \
  --topics "AI,cybersecurity,policy,finance,Ontario" \
  --outdir output
```

PowerShell:

```powershell
.\Run-GrowthOS.ps1 `
  -Posts .\examples\posts_template.csv `
  -Comments .\examples\comments_template.csv `
  -Identity .\config.example.json `
  -Topics "AI,cybersecurity,policy,finance,Ontario" `
  -OutDir .\output
```

## Posts schema

Required columns:

- `post_id`
- `created_at`
- `text`
- `topic`
- `hook_style`
- `structure`
- `cta`
- `tone`
- `impressions`
- `likes`
- `replies`
- `reposts`
- `profile_visits`
- `follows_gained`

## Comments schema

Recommended columns:

- `comment_id`
- `post_id`
- `created_at`
- `author`
- `body`
- `author_followers`
- `likes`
- `replies_count`

## Output

Growth OS writes:

- `growth_os_report.json`
- `growth_os_report.md`

## Notes

This is an analytics and drafting system. It is intentionally designed without auto-posting or platform manipulation features.
