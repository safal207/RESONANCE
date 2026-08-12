#!/usr/bin/env node

import fs from 'node:fs';
import path from 'node:path';

const ROOT = process.cwd();
const DIST = path.join(ROOT, 'dist');
const modeArg = process.argv.indexOf('--mode');
const mode = modeArg >= 0 ? process.argv[modeArg + 1] : 'disabled';
const endpointArg = process.argv.indexOf('--expected-endpoint');
const expectedEndpoint = endpointArg >= 0 ? process.argv[endpointArg + 1] : '';

if (!['disabled', 'enabled'].includes(mode)) {
  console.error(`Unsupported mode: ${mode}`);
  process.exit(2);
}

const errors = [];
const check = (condition, message) => {
  if (!condition) errors.push(message);
};

const schemaPath = path.join(ROOT, 'analytics', 'event-schema.json');
const runtimePath = path.join(DIST, 'analytics.js');
const measurementPath = path.join(DIST, 'measurement.html');

check(fs.existsSync(schemaPath), 'analytics/event-schema.json is missing');
check(fs.existsSync(runtimePath), 'dist/analytics.js is missing');
check(fs.existsSync(measurementPath), 'dist/measurement.html is missing');

if (errors.length) {
  console.error(errors.join('\n'));
  process.exit(1);
}

const schema = JSON.parse(fs.readFileSync(schemaPath, 'utf8'));
const runtime = fs.readFileSync(runtimePath, 'utf8');
const measurement = fs.readFileSync(measurementPath, 'utf8');
const htmlFiles = fs.readdirSync(DIST).filter((name) => name.endsWith('.html')).sort();

const expectedFields = ['schema_version', 'event', 'path', 'language', 'content_kind'];
const expectedEvents = [
  'meaningful_read',
  'hot_question_view',
  'workflow_intake_open',
  'verified_workflow_open',
];

check(schema.schemaVersion === 1, 'analytics schemaVersion must be 1');
check(JSON.stringify(schema.allowedPayloadFields) === JSON.stringify(expectedFields), 'allowed payload field list drifted');
check(JSON.stringify(Object.keys(schema.events)) === JSON.stringify(expectedEvents), 'event taxonomy drifted from v0.7 contract');

const runtimeEventBlock = runtime.match(/const ALLOWED_EVENTS = new Set\(\[([\s\S]*?)\]\);/m)?.[1] || '';
const runtimeEvents = [...runtimeEventBlock.matchAll(/['"]([a-z_]+)['"]/g)].map((match) => match[1]);
check(JSON.stringify(runtimeEvents) === JSON.stringify(expectedEvents), 'runtime ALLOWED_EVENTS differs from event schema');

const requiredRuntimeFragments = [
  "navigator.webdriver === true",
  "navigator.globalPrivacyControl === true",
  "navigator.doNotTrack === '1'",
  "credentials: 'omit'",
  "referrerPolicy: 'no-referrer'",
  "cache: 'no-store'",
  "visibleSeconds >= 45",
  "maxDepth >= 0.6",
  "intersectionRatio >= 0.6",
];
for (const fragment of requiredRuntimeFragments) {
  check(runtime.includes(fragment), `runtime missing required privacy/measurement fragment: ${fragment}`);
}

const forbiddenRuntimePatterns = [
  [/document\.cookie/i, 'document.cookie'],
  [/\blocalStorage\b/i, 'localStorage'],
  [/\bsessionStorage\b/i, 'sessionStorage'],
  [/\bindexedDB\b/i, 'IndexedDB'],
  [/document\.referrer/i, 'document.referrer'],
  [/navigator\.userAgent/i, 'navigator.userAgent'],
  [/navigator\.deviceMemory/i, 'navigator.deviceMemory'],
  [/navigator\.hardwareConcurrency/i, 'navigator.hardwareConcurrency'],
  [/navigator\.plugins/i, 'navigator.plugins'],
  [/\bscreen\.(?:width|height|availWidth|availHeight)\b/i, 'screen dimensions'],
  [/getImageData\s*\(/i, 'canvas pixel read'],
  [/toDataURL\s*\(/i, 'canvas serialization'],
  [/RTCPeerConnection/i, 'WebRTC fingerprint surface'],
  [/AudioContext/i, 'audio fingerprint surface'],
  [/\bemail\b/i, 'email field'],
  [/\buser_id\b/i, 'user_id field'],
  [/\bvisitor_id\b/i, 'visitor_id field'],
  [/\bsession_id\b/i, 'session_id field'],
];
for (const [pattern, label] of forbiddenRuntimePatterns) {
  check(!pattern.test(runtime), `runtime uses prohibited collection surface: ${label}`);
}

const payloadBlock = runtime.match(/const payload = \{([\s\S]*?)\n\s*\};/m)?.[1] || '';
for (const field of expectedFields) {
  check(new RegExp(`\\b${field}\\b`).test(payloadBlock), `payload missing allowed field ${field}`);
}
for (const suspicious of ['timestamp', 'referrer', 'user_agent', 'screen', 'device', 'email', 'name', 'id']) {
  check(!new RegExp(`\\b${suspicious}\\b`, 'i').test(payloadBlock), `payload includes non-allowlisted concept: ${suspicious}`);
}

let pagesWithMode = 0;
let pagesWithEndpoint = 0;
let pagesWithRuntime = 0;
for (const file of htmlFiles) {
  const html = fs.readFileSync(path.join(DIST, file), 'utf8');
  const modeTags = [...html.matchAll(/<meta\s+name=["']resonance-analytics-mode["']\s+content=["']([^"']+)["'][^>]*>/gi)];
  const endpointTags = [...html.matchAll(/<meta\s+name=["']resonance-analytics-endpoint["']\s+content=["']([^"']+)["'][^>]*>/gi)];
  const runtimeTags = [...html.matchAll(/<script\s+src=["']analytics\.js["']\s+defer><\/script>/gi)];

  check(modeTags.length === 1, `${file}: expected exactly one analytics mode meta`);
  check(runtimeTags.length === 1, `${file}: expected exactly one analytics runtime script`);
  if (modeTags.length === 1) {
    pagesWithMode += 1;
    check(modeTags[0][1] === mode, `${file}: analytics mode ${modeTags[0][1]} != ${mode}`);
  }
  if (runtimeTags.length === 1) pagesWithRuntime += 1;

  if (mode === 'disabled') {
    check(endpointTags.length === 0, `${file}: disabled build must not expose an endpoint`);
  } else {
    check(endpointTags.length === 1, `${file}: enabled build requires exactly one endpoint`);
    if (endpointTags.length === 1) {
      pagesWithEndpoint += 1;
      check(endpointTags[0][1] === expectedEndpoint, `${file}: endpoint differs from expected enabled test endpoint`);
    }
  }
}

check(/data-analytics-status/.test(measurement), 'measurement page must expose runtime status');
if (mode === 'disabled') {
  check(measurement.includes('Disabled — no event collector configured.'), 'measurement page must disclose disabled transport');
} else {
  check(measurement.includes('Enabled — privacy collector configured.'), 'measurement page must disclose enabled transport');
}
check(measurement.includes('Cookies</td><td>Not used'), 'measurement page must disclose no-cookie rule');
check(measurement.includes('Fingerprinting</td><td>Not used'), 'measurement page must disclose no-fingerprinting rule');
check(measurement.includes('Analytics is not demand evidence'), 'measurement page must preserve evidence boundary');

for (const file of [
  'before-you-let-an-ai-agent-move-money.html',
  'before-you-let-an-ai-agent-move-money.ru.html',
  'before-you-let-an-ai-agent-move-money.zh.html',
]) {
  const html = fs.readFileSync(path.join(DIST, file), 'utf8');
  check(html.includes('class="market-question"'), `${file}: market-question surface missing`);
  check(html.includes('template=market-workflow.yml'), `${file}: market workflow intake link missing`);
}

const verdict = errors.length ? 'FAIL' : 'PASS';
const summary = `# RESONANCE Privacy-Aware Analytics Contract\n\n**Verdict:** ${verdict}\n**Mode:** ${mode}\n\n| Surface | Result |\n|---|---:|\n| HTML pages with analytics mode | ${pagesWithMode}/${htmlFiles.length} |\n| HTML pages with analytics runtime | ${pagesWithRuntime}/${htmlFiles.length} |\n| HTML pages exposing endpoint | ${pagesWithEndpoint}/${htmlFiles.length} |\n| Allowed payload fields | ${expectedFields.length} |\n| Allowed event types | ${expectedEvents.length} |\n\n## Privacy invariants\n\n- No persistent browser identity or storage.\n- GPC, DNT and automated browser audits suppress emission.\n- Requests omit credentials and referrer information.\n- Client payload is limited to event, path, language, content kind and schema version.\n- Transport is disabled unless an HTTPS collector is explicitly configured at build time.\n\n## Evidence boundary\n\nA passing contract proves the static measurement policy, default-off/enabled build behavior and client payload boundary. It does not prove collector-side IP handling, retention, delivery completeness, readership, comprehension, demand or product-market fit.\n`;

fs.writeFileSync(`analytics-summary-${mode}.md`, summary);
fs.writeFileSync(`analytics-summary-${mode}.json`, JSON.stringify({
  verdict,
  mode,
  htmlPages: htmlFiles.length,
  pagesWithMode,
  pagesWithRuntime,
  pagesWithEndpoint,
  allowedFields: expectedFields,
  allowedEvents: expectedEvents,
  errors,
}, null, 2));

console.log(summary);
if (errors.length) {
  for (const error of errors) console.error(`- ${error}`);
  process.exit(1);
}
