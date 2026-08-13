import assert from 'node:assert/strict';
import fs from 'node:fs';
import test from 'node:test';

import { buildQuery } from '../build-market-signal-query.mjs';
import { buildReadout, renderMarkdown } from '../build-market-signal-readout.mjs';

const fixture = JSON.parse(fs.readFileSync(new URL('../../analytics/fixtures/market-signals-sample.json', import.meta.url), 'utf8'));

const START = '2026-08-12T00:00:00Z';
const END = '2026-08-13T00:00:00Z';

test('query uses explicit closed UTC interval and sampling-aware count', () => {
  const sql = buildQuery(START, END);
  assert.match(sql, /SUM\(_sample_interval \* double1\) AS event_count/);
  assert.match(sql, /timestamp >= toDateTime\('2026-08-12 00:00:00'\)/);
  assert.match(sql, /timestamp < toDateTime\('2026-08-13 00:00:00'\)/);
  assert.match(sql, /ORDER BY path ASC, language ASC, content_kind ASC, event ASC/);
  assert.doesNotMatch(sql, /NOW\(\)/);
});

test('query rejects non-canonical or reversed windows', () => {
  assert.throws(() => buildQuery('2026-08-12T00:00:00.000Z', END), /exact UTC-second format/);
  assert.throws(() => buildQuery(END, START), /earlier than/);
});

test('readout excludes collector smoke and preserves aggregate evidence boundary', () => {
  const report = buildReadout(fixture, START, END);
  assert.equal(report.schema, 'resonance.market-signals.v0.9');
  assert.deepEqual(report.totals, {
    meaningful_read: 13,
    hot_question_view: 4,
    workflow_intake_open: 1,
    verified_workflow_open: 2,
  });
  assert.equal(report.exclusions.synthetic_collector_smoke_events, 1);
  assert.equal(report.aggregate_signal_ratios.hot_question_per_meaningful_read, 0.307692);
  assert.equal(report.aggregate_signal_ratios.workflow_intake_per_hot_question, 0.25);
  assert.equal(report.aggregate_signal_ratios.verified_workflow_per_hot_question, 0.5);
  assert.equal(report.by_surface.length, 2);
  assert.ok(report.interpretation.ratios_are_not.includes('user-level'));
});

test('markdown never describes aggregate ratios as conversion rates or demand', () => {
  const markdown = renderMarkdown(buildReadout(fixture, START, END));
  assert.match(markdown, /not\*\* user-level conversion rates/i);
  assert.match(markdown, /Demand begins only with explicit workflow submission/i);
  assert.match(markdown, /synthetic collector smoke excluded \| 1/);
});

test('readout fails closed on unknown dimensions', () => {
  const bad = structuredClone(fixture);
  bad.data[0].language = 'xx';
  assert.throws(() => buildReadout(bad, START, END), /unexpected language/);

  const extraEvent = structuredClone(fixture);
  extraEvent.data[0].event = 'page_view';
  assert.throws(() => buildReadout(extraEvent, START, END), /unexpected event/);
});
