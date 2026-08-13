#!/usr/bin/env node

import fs from 'node:fs';
import path from 'node:path';

const ROOT = process.cwd();
const workerPath = path.join(ROOT, 'collector', 'worker.mjs');
const configPath = path.join(ROOT, 'collector', 'wrangler.jsonc');
const decisionPath = path.join(ROOT, 'analytics', 'COLLECTOR_DECISION_V0_8.md');
const analyticsRuntimePath = path.join(ROOT, 'site', 'analytics.js');

const failures = [];
const requireText = (value, needle, label) => {
  if (!value.includes(needle)) failures.push(`${label}: missing ${needle}`);
};
const forbidText = (value, needle, label) => {
  if (value.toLowerCase().includes(needle.toLowerCase())) failures.push(`${label}: forbidden token ${needle}`);
};

for (const file of [workerPath, configPath, decisionPath, analyticsRuntimePath]) {
  if (!fs.existsSync(file)) failures.push(`missing required file: ${path.relative(ROOT, file)}`);
}

if (failures.length === 0) {
  const worker = fs.readFileSync(workerPath, 'utf8');
  const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
  const decision = fs.readFileSync(decisionPath, 'utf8');
  const runtime = fs.readFileSync(analyticsRuntimePath, 'utf8');

  for (const token of [
    'cf-connecting-ip',
    'x-forwarded-for',
    'user-agent',
    'referer',
    'cookie',
    'request.cf',
    'country',
    'city',
    'device',
    'session_id',
    'visitor_id',
    'distinct_id',
  ]) {
    forbidText(worker, token, 'collector/worker.mjs');
  }

  for (const field of ['schema_version', 'event', 'path', 'language', 'content_kind']) {
    requireText(worker, `'${field}'`, 'collector/worker.mjs');
  }
  for (const event of ['meaningful_read', 'hot_question_view', 'workflow_intake_open', 'verified_workflow_open']) {
    requireText(worker, `'${event}'`, 'collector/worker.mjs');
  }
  requireText(worker, "const ALLOWED_ORIGIN = 'https://safal207.github.io'", 'collector/worker.mjs');
  requireText(worker, "payload.path.startsWith('/RESONANCE/')", 'collector/worker.mjs');
  requireText(worker, 'writeDataPoint', 'collector/worker.mjs');

  if (config.name !== 'resonance-analytics-collector') failures.push('wrangler: unexpected worker name');
  if (config.main !== './worker.mjs') failures.push('wrangler: main must be ./worker.mjs');
  if (config.workers_dev !== true) failures.push('wrangler: workers_dev must be true for pre-domain activation');
  if (config.observability?.enabled !== false) failures.push('wrangler: observability logging must remain disabled');
  const dataset = config.analytics_engine_datasets?.find((entry) => entry.binding === 'RESONANCE_EVENTS');
  if (!dataset) failures.push('wrangler: missing RESONANCE_EVENTS Analytics Engine binding');
  if (dataset?.dataset !== 'resonance_market_events_v1') failures.push('wrangler: unexpected Analytics Engine dataset');

  requireText(decision, 'selected, not activated', 'collector decision');
  requireText(decision, 'Cloudflare Worker', 'collector decision');
  requireText(decision, 'five-field', 'collector decision');

  for (const forbidden of ['localStorage', 'sessionStorage', 'document.cookie']) {
    forbidText(runtime, forbidden, 'site/analytics.js');
  }
}

const verdict = failures.length ? 'fail' : 'pass';
const summary = {
  schema: 'resonance.collector.contract.v1',
  verdict,
  collector: 'cloudflare-worker-analytics-engine',
  productionActivated: false,
  allowedPayloadFields: 5,
  allowedEvents: 4,
  failures,
};

fs.writeFileSync('collector-contract-summary.json', `${JSON.stringify(summary, null, 2)}\n`);
const markdown = [
  '# RESONANCE Collector Contract v0.8',
  '',
  `**Verdict:** ${verdict.toUpperCase()}`,
  '**Selected collector:** Cloudflare Worker + Workers Analytics Engine',
  '**Production transport:** NOT ACTIVATED by this contract',
  '',
  '| Boundary | Value |',
  '|---|---:|',
  '| Allowed payload fields | 5 |',
  '| Allowed event types | 4 |',
  '| Persistent reader/session IDs | 0 |',
  '| IP / UA / referrer fields written by RESONANCE | 0 |',
  '',
  '## Evidence boundary',
  '',
  'Passing proves the repository collector source/configuration boundary and deployability checks. It does not prove provider-side account settings, production deployment, delivery completeness, readership, demand or product-market fit.',
  '',
  ...(failures.length ? ['## Failures', '', ...failures.map((failure) => `- ${failure}`), ''] : []),
].join('\n');
fs.writeFileSync('collector-contract-summary.md', `${markdown}\n`);
console.log(markdown);

if (failures.length) process.exit(1);
