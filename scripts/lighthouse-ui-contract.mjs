#!/usr/bin/env node

import fs from 'node:fs';
import path from 'node:path';

const args = process.argv.slice(2);
const readArg = (name, fallback = null) => {
  const index = args.indexOf(name);
  return index >= 0 && args[index + 1] ? args[index + 1] : fallback;
};

const inputDir = readArg('--input', 'lighthouse-results');
const outputPrefix = readArg('--output', 'ui-geometry-summary');
const enforce = args.includes('--enforce');

if (!fs.existsSync(inputDir)) {
  console.error(`UI geometry contract: Lighthouse directory does not exist: ${inputDir}`);
  process.exit(2);
}

const files = fs.readdirSync(inputDir)
  .filter((name) => name.endsWith('.json') && !name.includes('summary'))
  .sort();

const groups = [
  { key: 'target-size', label: 'Interactive target size', candidates: ['target-size', 'tap-targets'] },
  { key: 'image-alt', label: 'Image alternative text', candidates: ['image-alt'] },
  { key: 'image-dimensions', label: 'Image intrinsic dimensions', candidates: ['unsized-images'] },
  { key: 'image-aspect-ratio', label: 'Image aspect ratio', candidates: ['image-aspect-ratio'] },
  { key: 'responsive-images', label: 'Responsive image sizing', candidates: ['image-size-responsive', 'uses-responsive-images'] },
  { key: 'contrast', label: 'Foreground/background contrast', candidates: ['color-contrast'] },
  { key: 'viewport', label: 'Responsive viewport', candidates: ['viewport'] },
];

function resolveAudit(report, candidates) {
  for (const id of candidates) {
    if (report.audits?.[id]) return { id, audit: report.audits[id] };
  }
  return null;
}

function stateFor(audit) {
  if (!audit) return 'unavailable';
  if (['notApplicable', 'manual', 'informative'].includes(audit.scoreDisplayMode)) return 'n/a';
  if (audit.score === 1) return 'pass';
  return 'fail';
}

function samples(audit) {
  const items = Array.isArray(audit?.details?.items) ? audit.details.items : [];
  return items.slice(0, 5).map((item) => ({
    selector: item?.node?.selector ?? null,
    snippet: item?.node?.snippet ?? null,
    label: item?.label ?? item?.failureSummary ?? null,
  })).filter((item) => Object.values(item).some(Boolean));
}

const reports = [];
const failures = [];

for (const file of files) {
  const raw = JSON.parse(fs.readFileSync(path.join(inputDir, file), 'utf8'));
  const checks = groups.map((group) => {
    const resolved = resolveAudit(raw, group.candidates);
    const state = stateFor(resolved?.audit ?? null);
    const check = {
      key: group.key,
      label: group.label,
      auditId: resolved?.id ?? null,
      state,
      score: resolved?.audit?.score ?? null,
      displayValue: resolved?.audit?.displayValue ?? null,
      samples: samples(resolved?.audit),
    };
    if (state === 'fail') failures.push(`${file}: ${group.label} failed (${resolved.id})`);
    return check;
  });

  reports.push({ file, url: raw.finalDisplayedUrl || raw.finalUrl || null, checks });
}

const summary = {
  schema: 'resonance.site-health.ui-geometry.v1',
  generatedAt: new Date().toISOString(),
  auditedCommit: process.env.GITHUB_SHA ?? null,
  sourceRunId: process.env.GITHUB_RUN_ID ?? null,
  reports,
  verdict: failures.length ? 'fail' : 'pass',
  failures,
};

fs.writeFileSync(`${outputPrefix}.json`, `${JSON.stringify(summary, null, 2)}\n`);

const rows = reports.map((report) => {
  const map = Object.fromEntries(report.checks.map((check) => [check.key, check.state]));
  return `| ${report.file.replace('.json', '')} | ${map['target-size']} | ${map['image-alt']} | ${map['image-dimensions']} | ${map['image-aspect-ratio']} | ${map['responsive-images']} | ${map.contrast} | ${map.viewport} |`;
});

const detailLines = reports.flatMap((report) => {
  const failed = report.checks.filter((check) => check.state === 'fail');
  if (!failed.length) return [];
  const lines = [`### ${report.file}`, ''];
  for (const check of failed) {
    lines.push(`- **${check.label}** — ${check.auditId}`);
    for (const sample of check.samples) {
      const text = sample.selector || sample.snippet || sample.label;
      if (text) lines.push(`  - ${String(text).replace(/\s+/g, ' ').slice(0, 280)}`);
    }
  }
  lines.push('');
  return lines;
});

const markdown = [
  '# RESONANCE UI Geometry Contract',
  '',
  `**Verdict:** ${summary.verdict.toUpperCase()}`,
  '',
  '| Route / profile | Target size | Image alt | Width/height | Aspect ratio | Responsive image | Contrast | Viewport |',
  '|---|---|---|---|---|---|---|---|',
  ...rows,
  '',
  '## Interpretation',
  '',
  '- `pass` — Lighthouse rendered audit passed.',
  '- `n/a` — the audit does not apply to that page (for example, no images).',
  '- `unavailable` — the pinned Lighthouse profile did not expose that audit; this is recorded but does not fail the release.',
  '- Primary CTA controls use a 44 px minimum design target; Lighthouse target-size/tap-target audits provide the browser-level release guard.',
  '',
  ...(failures.length ? ['## Failures', '', ...failures.map((failure) => `- ${failure}`), '', ...detailLines] : []),
  '> This contract measures rendered UI mechanics. It does not prove visual taste, content quality, or identical rendering on every browser/device.',
  ''
].join('\n');

fs.writeFileSync(`${outputPrefix}.md`, markdown);
console.log(markdown);

if (enforce && failures.length) process.exit(1);
