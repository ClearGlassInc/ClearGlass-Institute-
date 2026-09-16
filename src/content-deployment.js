const DEFAULT_CHANNELS = Object.freeze(['linkedin', 'x']);

export function slugify(value) {
  return String(value ?? '')
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '') || 'untitled';
}

function escapeCsv(value) {
  const text = String(value ?? '');
  return /[",\n]/.test(text) ? `"${text.replaceAll('"', '""')}"` : text;
}

function escapeHtml(value) {
  return String(value ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;');
}

function requireText(value, label) {
  const text = String(value ?? '').trim();
  if (!text) throw new Error(`${label} is required.`);
  return text;
}

function normalizePost(post, index) {
  if (!post || typeof post !== 'object') throw new TypeError(`Post at index ${index} must be an object.`);
  const body = requireText(post.body, `Post ${index + 1} body`);
  const title = String(post.title ?? `Signal ${index + 1}`).trim();
  const channels = Array.isArray(post.channels) && post.channels.length
    ? post.channels.map((channel) => String(channel).trim().toLowerCase()).filter(Boolean)
    : [...DEFAULT_CHANNELS];
  return {
    id: String(post.id ?? slugify(title)),
    title,
    body,
    pillar: String(post.pillar ?? 'verified-trust'),
    cta: String(post.cta ?? '').trim(),
    channels,
    status: String(post.status ?? 'draft')
  };
}

function normalizeWhitepaper(whitepaper = {}) {
  const title = requireText(whitepaper.title, 'Whitepaper title');
  const sections = Array.isArray(whitepaper.sections) ? whitepaper.sections : [];
  if (!sections.length) throw new Error('Whitepaper requires at least one section.');
  return {
    title,
    subtitle: String(whitepaper.subtitle ?? '').trim(),
    sections: sections.map((section, index) => ({
      heading: requireText(section?.heading, `Whitepaper section ${index + 1} heading`),
      body: requireText(section?.body, `Whitepaper section ${index + 1} body`)
    }))
  };
}

export function normalizeCampaign(input = {}) {
  if (!input || typeof input !== 'object') throw new TypeError('Campaign input must be an object.');
  const title = requireText(input.title, 'Campaign title');
  const brand = requireText(input.brand, 'Campaign brand');
  const posts = Array.isArray(input.posts) ? input.posts.map(normalizePost) : [];
  if (!posts.length) throw new Error('Campaign requires at least one post draft.');

  return {
    id: String(input.id ?? slugify(title)),
    title,
    brand,
    tone: String(input.tone ?? 'institutional, measured'),
    coreFrame: Array.isArray(input.coreFrame) ? input.coreFrame.map(String) : [],
    pillars: Array.isArray(input.pillars) ? input.pillars.map(String) : [],
    posts,
    whitepaper: normalizeWhitepaper(input.whitepaper),
    notion: {
      database: String(input.notion?.database ?? 'ClearGlass Deployment Queue'),
      owner: String(input.notion?.owner ?? brand)
    },
    visual: {
      background: String(input.visual?.background ?? 'solid black or white'),
      accent: String(input.visual?.accent ?? '1px silver'),
      titleFont: String(input.visual?.titleFont ?? 'serif'),
      bodyFont: String(input.visual?.bodyFont ?? 'sans-serif'),
      codeFont: String(input.visual?.codeFont ?? 'monospace')
    }
  };
}

function renderNotionCsv(campaign) {
  const rows = [['Name', 'Status', 'Pillar', 'Channels', 'CTA', 'Body']];
  for (const post of campaign.posts) {
    rows.push([
      post.title,
      post.status,
      post.pillar,
      post.channels.join(' | '),
      post.cta,
      post.body
    ]);
  }
  return `${rows.map((row) => row.map(escapeCsv).join(',')).join('\n')}\n`;
}

function renderDraft(post) {
  const channels = post.channels.map((channel) => `- ${channel}`).join('\n');
  return `# ${post.title}\n\n**Status:** ${post.status}\n\n**Pillar:** ${post.pillar}\n\n**Channels:**\n${channels}\n\n## Draft\n\n${post.body}${post.cta ? `\n\n${post.cta}` : ''}\n`;
}

function renderWhitepaperHtml(campaign) {
  const { whitepaper, visual } = campaign;
  const sections = whitepaper.sections
    .map((section) => `<section><h2>${escapeHtml(section.heading)}</h2><p>${escapeHtml(section.body)}</p></section>`)
    .join('\n');
  const subtitle = whitepaper.subtitle ? `<p class="subtitle">${escapeHtml(whitepaper.subtitle)}</p>` : '';
  return `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>${escapeHtml(whitepaper.title)}</title>
<style>
@page { size: Letter; margin: 0.7in; }
:root { color-scheme: light; }
* { box-sizing: border-box; }
body { margin: 0 auto; max-width: 8.5in; color: #111; background: #fff; font-family: ${escapeHtml(visual.bodyFont)}; line-height: 1.55; }
header { border-bottom: 1px solid #888; padding-bottom: 24px; margin-bottom: 32px; }
h1, h2 { font-family: ${escapeHtml(visual.titleFont)}; font-weight: 600; }
h1 { font-size: 34px; margin: 0 0 8px; }
h2 { font-size: 21px; margin-top: 28px; }
.subtitle { color: #444; max-width: 42rem; }
.brand { font-family: ${escapeHtml(visual.codeFont)}; letter-spacing: .08em; text-transform: uppercase; font-size: 12px; }
section { break-inside: avoid; }
footer { border-top: 1px solid #888; margin-top: 36px; padding-top: 16px; font-size: 11px; }
@media print { body { max-width: none; } }
</style>
</head>
<body>
<header>
<div class="brand">${escapeHtml(campaign.brand)}</div>
<h1>${escapeHtml(whitepaper.title)}</h1>
${subtitle}
</header>
${sections}
<footer>Human-reviewed ClearGlass deployment export. No automatic publishing is performed by Opal-Koboi.</footer>
</body>
</html>\n`;
}

function renderManifest(campaign, approved, generatedAt) {
  return JSON.stringify({
    schema: 'clearglass.content-deployment.v1',
    campaign: campaign.id,
    title: campaign.title,
    brand: campaign.brand,
    generatedAt,
    approval: approved ? 'human-approved-for-publication' : 'draft-awaiting-human-approval',
    externalSideEffects: false,
    channels: [...new Set(campaign.posts.flatMap((post) => post.channels))],
    artifacts: {
      postDrafts: campaign.posts.length,
      notionImport: true,
      printReadyWhitepaper: true,
      auditRecord: true
    }
  }, null, 2) + '\n';
}

function renderReadme(campaign, approved) {
  return `# ${campaign.title} — Deployment Bundle\n\nThis bundle is generated by Opal-Koboi as a **human-gated** deployment package. It does not publish to social platforms and does not call Notion or any external API.\n\n## Approval\n\nStatus: **${approved ? 'approved for manual publication' : 'draft — manual approval required'}**\n\n## Contents\n\n- \`deployment-manifest.json\` — machine-readable audit manifest\n- \`notion/content-calendar.csv\` — importable content queue\n- \`notion/README.md\` — Notion import instructions\n- \`drafts/*.md\` — channel-ready source drafts\n- \`pdf/whitepaper.html\` — print-ready whitepaper; use browser Print → Save as PDF\n- \`audit/deployment-audit.json\` — deterministic audit record\n\n## Operating rule\n\nReview every draft for factual support, institutional tone, platform policy, legal/compliance risk, and final approval before publication.\n`;
}

function renderNotionReadme(campaign) {
  return `# Notion Import — ${campaign.notion.database}\n\nImport \`content-calendar.csv\` into a Notion database. Suggested properties:\n\n- Name — title\n- Status — select\n- Pillar — select\n- Channels — multi-select\n- CTA — text\n- Body — text\n- Owner — ${campaign.notion.owner}\n\nNo Notion token is required because Opal-Koboi produces an import bundle rather than making external API calls.\n`;
}

export function buildDeploymentBundle(input, options = {}) {
  const campaign = normalizeCampaign(input);
  const approved = options.approved === true;
  const generatedAt = String(options.generatedAt ?? new Date().toISOString());
  const files = {
    'README.md': renderReadme(campaign, approved),
    'deployment-manifest.json': renderManifest(campaign, approved, generatedAt),
    'notion/content-calendar.csv': renderNotionCsv(campaign),
    'notion/README.md': renderNotionReadme(campaign),
    'pdf/whitepaper.html': renderWhitepaperHtml(campaign),
    'pdf/README.md': '# PDF Export\n\nOpen `whitepaper.html` in a browser and use Print → Save as PDF. The stylesheet is Letter-sized and print-safe.\n',
    'audit/deployment-audit.json': JSON.stringify({
      campaign: campaign.id,
      generatedAt,
      approved,
      humanGateRequired: !approved,
      automaticPublishing: false,
      externalApiCalls: false,
      postCount: campaign.posts.length,
      whitepaperSectionCount: campaign.whitepaper.sections.length
    }, null, 2) + '\n'
  };

  for (const post of campaign.posts) files[`drafts/${slugify(post.id)}.md`] = renderDraft(post);

  return {
    campaign,
    approved,
    generatedAt,
    files,
    summary: {
      fileCount: Object.keys(files).length,
      postCount: campaign.posts.length,
      whitepaperSectionCount: campaign.whitepaper.sections.length,
      status: approved ? 'ready-for-manual-publication' : 'draft-awaiting-human-approval'
    }
  };
}
