#!/usr/bin/env node

import { pathToFileURL } from 'node:url';

const DATASET = 'resonance_market_events_v1';

function arg(name) {
  const index = process.argv.indexOf(name);
  return index >= 0 ? process.argv[index + 1] : '';
}

export function normalizeUtcSecond(value, label) {
  if (!value) throw new Error(`${label} is required`);
  if (!/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$/.test(value)) {
    throw new Error(`${label} must use exact UTC-second format YYYY-MM-DDTHH:mm:ssZ`);
  }
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime()) || parsed.toISOString().replace('.000Z', 'Z') !== value) {
    throw new Error(`${label} is not a valid UTC timestamp`);
  }
  return value;
}

export function toCloudflareDateTime(value) {
  return normalizeUtcSecond(value, 'timestamp').replace('T', ' ').replace('Z', '');
}

export function buildQuery(windowStart, windowEnd) {
  const start = normalizeUtcSecond(windowStart, 'window_start');
  const end = normalizeUtcSecond(windowEnd, 'window_end');
  if (new Date(start) >= new Date(end)) throw new Error('window_start must be earlier than window_end');

  return `SELECT
  blob1 AS event,
  blob2 AS path,
  blob3 AS language,
  blob4 AS content_kind,
  blob5 AS schema_version,
  SUM(_sample_interval * double1) AS event_count
FROM ${DATASET}
WHERE timestamp >= toDateTime('${toCloudflareDateTime(start)}')
  AND timestamp < toDateTime('${toCloudflareDateTime(end)}')
GROUP BY event, path, language, content_kind, schema_version
ORDER BY path ASC, language ASC, content_kind ASC, event ASC`;
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  try {
    process.stdout.write(`${buildQuery(arg('--window-start'), arg('--window-end'))}\n`);
  } catch (error) {
    console.error(error.message);
    process.exit(2);
  }
}
