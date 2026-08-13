#!/usr/bin/env node

import fs from 'node:fs';

const baseArg = process.argv.indexOf('--live-base');
const base = baseArg >= 0 ? process.argv[baseArg + 1] : 'https://safal207.github.io/RESONANCE/';
const modeArg = process.argv.indexOf('--mode');
const mode = modeArg >= 0 ? process.argv[modeArg + 1] : 'disabled';
const endpointArg = process.argv.indexOf('--expected-endpoint');
const expectedEndpoint = endpointArg >= 0 ? new URL(process.argv[endpointArg + 1]).toString() : '';
const outputArg = process.argv.indexOf('--output');
const output = outputArg >= 0 ? process.argv[outputArg + 1] : 'analytics-live-results';
const enforce = process.argv.includes('--enforce');

if (!['disabled', 'enabled'].includes(mode)) {
  console.error(`Unsupported mode: ${mode}`);
  process.exit(2);
}

const errors = [];
const check = (condition, message) => {
  if (!condition) errors.push(message);
};

async function fetchWithRetry(url, attempts = 8) {
  let lastError;
  for (let attempt = 1; attempt <= attempts; attempt += 1) {
    try {
      const response = await fetch(url, {
        headers: { 'cache-control': 'no-cache' },
        redirect: 'follow',
      });
      if (response.ok) return response;
      lastError = new Error(`${response.status} ${response.statusText}`);
    } catch (error) {
      lastError = error;
    }
    await new Promise((resolve) => setTimeout(resolve, attempt * 1000));
  }
  throw lastError;
}

const routes = [
  'measurement.html',
  'before-you-let-an-ai-agent-move-money.html',
  'before-you-let-an-ai-agent-move-money.ru.html',
  'before-you-let-an-ai-agent-move-money.zh.html',
];

const results = [];
for (const route of routes) {
  const url = new URL(route, base).toString();
  try {
    const response = await fetchWithRetry(url);
    const html = await response.text();
    const modeMatch = html.match(/<meta\s+name=["']resonance-analytics-mode["']\s+content=["']([^"']+)["'][^>]*>/i);
    const endpointMatches = [...html.matchAll(/<meta\s+name=["']resonance-analytics-endpoint["']\s+content=["']([^"']+)["'][^>]*>/gi)];
    const runtimeMatches = [...html.matchAll(/<script\s+src=["']analytics\.js["']\s+defer><\/script>/gi)];

    check(modeMatch?.[1] === mode, `${route}: live mode is ${modeMatch?.[1] || 'missing'}, expected ${mode}`);
    check(runtimeMatches.length === 1, `${route}: expected exactly one live analytics runtime script`);
    if (mode === 'disabled') {
      check(endpointMatches.length === 0, `${route}: disabled live page exposes analytics endpoint`);
    } else {
      check(endpointMatches.length === 1, `${route}: enabled live page requires exactly one endpoint`);
      if (endpointMatches.length === 1) {
        check(endpointMatches[0][1] === expectedEndpoint, `${route}: live endpoint differs from configured endpoint`);
      }
    }

    if (route === 'measurement.html') {
      const expectedStatus = mode === 'enabled'
        ? 'Enabled — privacy collector configured.'
        : 'Disabled — no event collector configured.';
      check(html.includes(expectedStatus), `measurement.html: public runtime status does not match ${mode}`);
      check(html.includes('Analytics is not demand evidence'), 'measurement.html: evidence boundary missing');
    }

    results.push({ route, status: response.status, mode: modeMatch?.[1] || null, runtime: runtimeMatches.length });
  } catch (error) {
    errors.push(`${route}: live fetch failed: ${error.message}`);
    results.push({ route, status: null, mode: null, runtime: 0 });
  }
}

try {
  const runtimeResponse = await fetchWithRetry(new URL('analytics.js', base).toString());
  const runtime = await runtimeResponse.text();
  check(runtime.includes("credentials: 'omit'"), 'live analytics.js missing credentials omit');
  check(runtime.includes("referrerPolicy: 'no-referrer'"), 'live analytics.js missing no-referrer policy');
  check(runtime.includes('navigator.globalPrivacyControl === true'), 'live analytics.js missing GPC opt-out');
  check(runtime.includes("navigator.doNotTrack === '1'"), 'live analytics.js missing DNT opt-out');
  check(runtime.includes('navigator.webdriver === true'), 'live analytics.js missing automated-browser suppression');
  results.push({ route: 'analytics.js', status: runtimeResponse.status, mode: 'runtime', runtime: 1 });
} catch (error) {
  errors.push(`analytics.js: live fetch failed: ${error.message}`);
  results.push({ route: 'analytics.js', status: null, mode: null, runtime: 0 });
}

fs.mkdirSync(output, { recursive: true });
const verdict = errors.length ? 'FAIL' : 'PASS';
const summary = `# RESONANCE Live Privacy Analytics Audit\n\n**Verdict:** ${verdict}\n**Expected mode:** ${mode}\n**Audited deploy SHA:** ${process.env.GITHUB_SHA || 'unknown'}\n\n| Public route | HTTP | Analytics mode | Runtime refs |\n|---|---:|---|---:|\n${results.map((row) => `| ${row.route} | ${row.status ?? 'ERR'} | ${row.mode ?? 'ERR'} | ${row.runtime} |`).join('\n')}\n\n## Evidence boundary\n\nPassing proves that the checked public GitHub Pages routes expose the expected analytics mode and privacy runtime after deployment. It does not prove collector-side handling, event delivery completeness, real-user behavior, demand or product-market fit.\n`;

fs.writeFileSync(`${output}/analytics-live-summary.md`, summary);
fs.writeFileSync(`${output}/analytics-live-summary.json`, JSON.stringify({
  verdict,
  mode,
  deployedSha: process.env.GITHUB_SHA || null,
  base,
  results,
  errors,
}, null, 2));

console.log(summary);
if (errors.length) {
  for (const error of errors) console.error(`- ${error}`);
  if (enforce) process.exit(1);
}
