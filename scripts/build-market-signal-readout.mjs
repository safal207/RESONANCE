#!/usr/bin/env node

import fs from 'node:fs';
import path from 'node:path';
import { pathToFileURL } from 'node:url';
import { normalizeUtcSecond } from './build-market-signal-query.mjs';

export const ALLOWED_EVENTS = [
  'meaningful_read',
  'hot_question_view',
  'workflow_intake_open',
  'verified_workflow_open',
];

const ALLOWED_LANGUAGES = new Set(['en', 'ru', 'zh-CN']);
const ALLOWED_CONTENT_KINDS = new Set(['article', 'page']);
const SYNTHETIC_SMOKE_PATH = /^\/RESONANCE\/__collector-smoke-\d+-\d+\.html$/;

function arg(name, fallback = '') {
  const index = process.argv.indexOf(name);
  return index >= 0 ? process.argv[index + 1] : fallback;
}

function finiteCount(value) {
  const count = Number(value);
  if (!Number.isFinite(count) || count < 0) throw new Error(`invalid event_count: ${value}`);
  return count;
}

function blankEvents() {
  return Object.fromEntries(ALLOWED_EVENTS.map((event) => [event, 0]));
}

function ratio(numerator, denominator) {
  if (denominator === 0) return null;
  return Number((numerator / denominator).toFixed(6));
}

export function buildReadout(raw, windowStart, windowEnd) {
  const start = normalizeUtcSecond(windowStart, 'window_start');
  const end = normalizeUtcSecond(windowEnd, 'window_end');
  if (new Date(start) >= new Date(end)) throw new Error('window_start must be earlier than window_end');
  if (!raw || !Array.isArray(raw.data)) throw new Error('Cloudflare SQL response must contain a data array');

  const totals = blankEvents();
  const bySurface = new Map();
  let syntheticExcluded = 0;
  let sourceRows = 0;

  for (const row of raw.data) {
    sourceRows += 1;
    const event = String(row.event ?? '');
    const eventPath = String(row.path ?? '');
    const language = String(row.language ?? '');
    const contentKind = String(row.content_kind ?? '');
    const schemaVersion = String(row.schema_version ?? '');
    const count = finiteCount(row.event_count ?? 0);

    if (!ALLOWED_EVENTS.includes(event)) throw new Error(`unexpected event: ${event}`);
    if (!eventPath.startsWith('/RESONANCE/') || eventPath.includes('?') || eventPath.includes('#')) {
      throw new Error(`unexpected path: ${eventPath}`);
    }
    if (!ALLOWED_LANGUAGES.has(language)) throw new Error(`unexpected language: ${language}`);
    if (!ALLOWED_CONTENT_KINDS.has(contentKind)) throw new Error(`unexpected content_kind: ${contentKind}`);
    if (schemaVersion !== '1') throw new Error(`unexpected schema_version: ${schemaVersion}`);

    if (SYNTHETIC_SMOKE_PATH.test(eventPath)) {
      syntheticExcluded += count;
      continue;
    }

    totals[event] += count;
    const key = `${eventPath}\u0000${language}\u0000${contentKind}`;
    if (!bySurface.has(key)) {
      bySurface.set(key, { path: eventPath, language, content_kind: contentKind, events: blankEvents() });
    }
    bySurface.get(key).events[event] += count;
  }

  const surfaces = [...bySurface.values()].sort((a, b) =>
    a.path.localeCompare(b.path) || a.language.localeCompare(b.language) || a.content_kind.localeCompare(b.content_kind)
  );

  const aggregateSignalRatios = {
    hot_question_per_meaningful_read: ratio(totals.hot_question_view, totals.meaningful_read),
    workflow_intake_per_hot_question: ratio(totals.workflow_intake_open, totals.hot_question_view),
    verified_workflow_per_hot_question: ratio(totals.verified_workflow_open, totals.hot_question_view),
  };

  return {
    schema: 'resonance.market-signals.v0.9',
    verdict: 'pass',
    window: { start, end, timezone: 'UTC' },
    source: {
      dataset: 'resonance_market_events_v1',
      schema_version: 1,
      count_expression: 'SUM(_sample_interval * double1)',
      source_rows: sourceRows,
    },
    totals,
    aggregate_signal_ratios: aggregateSignalRatios,
    by_surface: surfaces,
    exclusions: {
      synthetic_collector_smoke_events: syntheticExcluded,
      rule: '/RESONANCE/__collector-smoke-<run_id>-<attempt>.html',
    },
    interpretation: {
      ratios_are: 'aggregate signal ratios across the same closed time window',
      ratios_are_not: 'user-level conversion rates or causal funnels',
      demand_boundary: 'Browser events are attention/action signals only. Demand begins with explicit workflow submission and downstream Problem Card / Product Signal / pilot evidence.',
    },
  };
}

export function renderMarkdown(report) {
  const e = report.totals;
  const r = report.aggregate_signal_ratios;
  const show = (value) => value === null ? 'n/a' : value.toFixed(3);
  const lines = [
    '# RESONANCE Market Signal Readout v0.9',
    '',
    '**Verdict:** PASS',
    `**Window:** ${report.window.start} → ${report.window.end} (UTC, end-exclusive)`,
    '',
    '| Signal | Count |',
    '|---|---:|',
    `| meaningful_read | ${e.meaningful_read} |`,
    `| hot_question_view | ${e.hot_question_view} |`,
    `| workflow_intake_open | ${e.workflow_intake_open} |`,
    `| verified_workflow_open | ${e.verified_workflow_open} |`,
    `| synthetic collector smoke excluded | ${report.exclusions.synthetic_collector_smoke_events} |`,
    '',
    '## Aggregate signal ratios',
    '',
    `- hot-question / meaningful-read: ${show(r.hot_question_per_meaningful_read)}`,
    `- workflow-intake / hot-question: ${show(r.workflow_intake_per_hot_question)}`,
    `- verified-workflow / hot-question: ${show(r.verified_workflow_per_hot_question)}`,
    '',
    'These are aggregate ratios across the same closed interval. They are **not** user-level conversion rates because RESONANCE intentionally has no visitor/session identity.',
    '',
    '## Evidence boundary',
    '',
    'This readout can establish aggregate attention/action signals for the five-field measurement contract. It cannot establish readership identity, comprehension, causal conversion, qualified demand, product-market fit or revenue. Demand begins only with explicit workflow submission and downstream Market OS evidence.',
  ];
  return `${lines.join('\n')}\n`;
}

export function writeReadout(raw, windowStart, windowEnd, outputDir) {
  const report = buildReadout(raw, windowStart, windowEnd);
  fs.mkdirSync(outputDir, { recursive: true });
  fs.writeFileSync(path.join(outputDir, 'market-signals.json'), `${JSON.stringify(report, null, 2)}\n`);
  fs.writeFileSync(path.join(outputDir, 'market-signals.md'), renderMarkdown(report));
  return report;
}

if (import.meta.url === pathToFileURL(process.argv[1]).href) {
  try {
    const input = arg('--input', 'market-signals-raw.json');
    const outputDir = arg('--output-dir', 'market-signals-evidence');
    const windowStart = arg('--window-start');
    const windowEnd = arg('--window-end');
    const raw = JSON.parse(fs.readFileSync(input, 'utf8'));
    const report = writeReadout(raw, windowStart, windowEnd, outputDir);
    process.stdout.write(renderMarkdown(report));
  } catch (error) {
    console.error(error.message);
    process.exit(1);
  }
}
