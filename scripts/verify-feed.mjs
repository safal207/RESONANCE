#!/usr/bin/env node

import fs from 'node:fs';
import path from 'node:path';
import process from 'node:process';

const args = process.argv.slice(2);
const arg = (name, fallback = null) => {
  const index = args.indexOf(name);
  return index >= 0 && args[index + 1] ? args[index + 1] : fallback;
};

const root = path.resolve(arg('--root', 'dist'));
const outputDir = path.resolve(arg('--output', 'feed-results'));
const liveBase = arg('--live-base', null);
const enforce = args.includes('--enforce');
const BASE = 'https://safal207.github.io/RESONANCE/';

const profiles = {
  en: { file: 'feed.xml' },
  ru: { file: 'feed.ru.xml' },
  'zh-CN': { file: 'feed.zh.xml' },
};

const utilityRoutes = new Set([
  'index.html', 'index.ru.html', 'index.zh.html', 'issue-001.html', 'ai-agents.html',
  'open-problems.html', 'verified-workflow.html', 'quality.html', 'corrections.html', 'subscribe.html',
]);

function xmlDecode(value = '') {
  return String(value)
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"')
    .replace(/&apos;/g, "'")
    .replace(/&amp;/g, '&');
}

function escapeRegex(value) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

function tagValue(block, tag) {
  const match = block.match(new RegExp(`<${escapeRegex(tag)}(?:\\s[^>]*)?>([\\s\\S]*?)<\\/${escapeRegex(tag)}>`, 'i'));
  return xmlDecode(match?.[1]?.trim() || '');
}

function parseFeed(xml) {
  const channel = xml.match(/<channel>([\s\S]*?)<\/channel>/i)?.[1] || '';
  const items = [...channel.matchAll(/<item>([\s\S]*?)<\/item>/gi)].map((match) => {
    const block = match[1];
    return {
      title: tagValue(block, 'title'),
      link: tagValue(block, 'link'),
      guid: tagValue(block, 'guid'),
      pubDate: tagValue(block, 'pubDate'),
      description: tagValue(block, 'description'),
    };
  });
  const selfLink = channel.match(/<atom:link\s+[^>]*href=["']([^"']+)["'][^>]*rel=["']self["'][^>]*type=["']application\/rss\+xml["'][^>]*\/?\s*>/i)?.[1]
    || channel.match(/<atom:link\s+[^>]*rel=["']self["'][^>]*href=["']([^"']+)["'][^>]*\/?\s*>/i)?.[1]
    || '';
  return {
    version: xml.match(/<rss\s+[^>]*version=["']([^"']+)["']/i)?.[1] || '',
    title: tagValue(channel, 'title'),
    link: tagValue(channel, 'link'),
    description: tagValue(channel, 'description'),
    language: tagValue(channel, 'language'),
    lastBuildDate: tagValue(channel, 'lastBuildDate'),
    selfLink: xmlDecode(selfLink),
    items,
  };
}

function routeFromUrl(url) {
  try {
    const parsed = new URL(url);
    if (parsed.origin !== new URL(BASE).origin) return null;
    const prefix = '/RESONANCE/';
    return parsed.pathname.startsWith(prefix) ? decodeURIComponent(parsed.pathname.slice(prefix.length)) : null;
  } catch {
    return null;
  }
}

function routeMatchesLanguage(route, language) {
  if (!route) return false;
  if (language === 'ru') return route.endsWith('.ru.html');
  if (language === 'zh-CN') return route.endsWith('.zh.html');
  return route.endsWith('.html') && !route.endsWith('.ru.html') && !route.endsWith('.zh.html');
}

function validateFeed(profileLanguage, feed, localRoot = null) {
  const errors = [];
  const expected = profiles[profileLanguage];
  const expectedSelf = `${BASE}${expected.file}`;

  if (feed.version !== '2.0') errors.push(`${expected.file}: RSS version must be 2.0`);
  if (!feed.title) errors.push(`${expected.file}: channel title missing`);
  if (feed.link !== BASE) errors.push(`${expected.file}: channel link must be ${BASE}`);
  if (!feed.description) errors.push(`${expected.file}: channel description missing`);
  if (feed.language !== profileLanguage) errors.push(`${expected.file}: language ${feed.language || '(missing)'} != ${profileLanguage}`);
  if (feed.selfLink !== expectedSelf) errors.push(`${expected.file}: atom self link must be ${expectedSelf}`);
  if (!feed.items.length) errors.push(`${expected.file}: feed must contain at least one published item`);
  if (feed.items.length > 50) errors.push(`${expected.file}: feed exceeds 50-item deterministic cap`);

  const links = new Set();
  let previousTime = Number.POSITIVE_INFINITY;
  for (const [index, item] of feed.items.entries()) {
    const prefix = `${expected.file} item ${index + 1}`;
    if (!item.title) errors.push(`${prefix}: title missing`);
    if (!item.description) errors.push(`${prefix}: description missing`);
    if (!item.link || !item.link.startsWith(BASE)) errors.push(`${prefix}: link must stay under ${BASE}`);
    if (item.guid !== item.link) errors.push(`${prefix}: GUID must equal permalink`);
    if (links.has(item.link)) errors.push(`${prefix}: duplicate link ${item.link}`);
    links.add(item.link);

    const time = Date.parse(item.pubDate);
    if (!Number.isFinite(time)) errors.push(`${prefix}: invalid pubDate ${item.pubDate}`);
    if (time > previousTime) errors.push(`${prefix}: items are not sorted newest-first`);
    previousTime = Math.min(previousTime, time);

    const route = routeFromUrl(item.link);
    if (!routeMatchesLanguage(route, profileLanguage)) errors.push(`${prefix}: route ${route || '(invalid)'} does not match ${profileLanguage}`);
    if (route && utilityRoutes.has(route)) errors.push(`${prefix}: utility route ${route} must not appear in RSS`);
    if (localRoot && route && !fs.existsSync(path.join(localRoot, route))) errors.push(`${prefix}: published route missing from build: ${route}`);
  }

  if (feed.items.length) {
    const newest = Date.parse(feed.items[0].pubDate);
    const build = Date.parse(feed.lastBuildDate);
    if (!Number.isFinite(build)) errors.push(`${expected.file}: lastBuildDate invalid`);
    else if (build !== newest) errors.push(`${expected.file}: lastBuildDate must equal newest item pubDate for deterministic builds`);
  }

  return errors;
}

function expectedFeedHref(language) {
  return `${BASE}${profiles[language]?.file || profiles.en.file}`;
}

function localAutodiscoveryErrors() {
  const errors = [];
  const htmlFiles = fs.readdirSync(root).filter((name) => name.endsWith('.html'));
  for (const file of htmlFiles) {
    const html = fs.readFileSync(path.join(root, file), 'utf8');
    const language = html.match(/<html[^>]*\slang=["']([^"']+)["']/i)?.[1] || 'en';
    const expected = expectedFeedHref(language);
    const rssLinks = [...html.matchAll(/<link\s+rel=["']alternate["'][^>]*type=["']application\/rss\+xml["'][^>]*href=["']([^"']+)["'][^>]*>/gi)].map((match) => match[1]);
    if (rssLinks.length !== 1) errors.push(`${file}: expected exactly one RSS autodiscovery link, found ${rssLinks.length}`);
    else if (rssLinks[0] !== expected) errors.push(`${file}: RSS autodiscovery ${rssLinks[0]} != ${expected}`);
  }

  const subscribePath = path.join(root, 'subscribe.html');
  if (!fs.existsSync(subscribePath)) errors.push('subscribe.html missing from build');
  else {
    const subscribe = fs.readFileSync(subscribePath, 'utf8');
    for (const profile of Object.values(profiles)) {
      if (!subscribe.includes(`href="${profile.file}"`)) errors.push(`subscribe.html: missing link to ${profile.file}`);
    }
  }
  return errors;
}

async function fetchText(url) {
  const response = await fetch(url, { redirect: 'follow', signal: AbortSignal.timeout(15000) });
  if (!response.ok) throw new Error(`${response.status} ${response.statusText}`);
  return await response.text();
}

async function verifyLocal() {
  const results = [];
  const errors = [];
  for (const [language, profile] of Object.entries(profiles)) {
    const filePath = path.join(root, profile.file);
    if (!fs.existsSync(filePath)) {
      errors.push(`${profile.file}: missing from build`);
      results.push({ language, file: profile.file, itemCount: 0, verdict: 'fail' });
      continue;
    }
    const feed = parseFeed(fs.readFileSync(filePath, 'utf8'));
    const feedErrors = validateFeed(language, feed, root);
    errors.push(...feedErrors);
    results.push({ language, file: profile.file, itemCount: feed.items.length, newest: feed.items[0]?.pubDate || null, verdict: feedErrors.length ? 'fail' : 'pass' });
  }
  const autodiscoveryErrors = localAutodiscoveryErrors();
  errors.push(...autodiscoveryErrors);
  return { mode: 'local', results, autodiscoveryErrors, liveRouteChecks: [], errors };
}

async function verifyLive() {
  const base = liveBase.endsWith('/') ? liveBase : `${liveBase}/`;
  const results = [];
  const errors = [];
  const liveRouteChecks = [];
  const candidateLinks = new Set();

  for (const [language, profile] of Object.entries(profiles)) {
    const url = new URL(profile.file, base).href;
    try {
      const xml = await fetchText(url);
      const feed = parseFeed(xml);
      const feedErrors = validateFeed(language, feed, null);
      errors.push(...feedErrors);
      for (const item of feed.items.slice(0, 5)) candidateLinks.add(item.link);
      results.push({ language, file: profile.file, itemCount: feed.items.length, newest: feed.items[0]?.pubDate || null, verdict: feedErrors.length ? 'fail' : 'pass' });
    } catch (error) {
      errors.push(`${profile.file}: live fetch failed: ${error.message}`);
      results.push({ language, file: profile.file, itemCount: 0, verdict: 'fail' });
    }
  }

  for (const url of [new URL('subscribe.html', base).href, ...candidateLinks]) {
    try {
      const response = await fetch(url, { redirect: 'follow', signal: AbortSignal.timeout(15000) });
      const ok = response.ok;
      liveRouteChecks.push({ url, status: response.status, ok });
      if (!ok) errors.push(`live route ${url}: HTTP ${response.status}`);
    } catch (error) {
      liveRouteChecks.push({ url, status: null, ok: false, error: error.message });
      errors.push(`live route ${url}: ${error.message}`);
    }
  }

  return { mode: 'live', results, autodiscoveryErrors: [], liveRouteChecks, errors };
}

function writeSummary(summary) {
  fs.mkdirSync(outputDir, { recursive: true });
  fs.writeFileSync(path.join(outputDir, 'feed-summary.json'), `${JSON.stringify(summary, null, 2)}\n`);
  const rows = summary.results.map((result) => `| ${result.language} | ${result.file} | ${result.itemCount} | ${result.newest || 'n/a'} | ${result.verdict.toUpperCase()} |`);
  const markdown = [
    '# RESONANCE RSS / Subscribe Contract',
    '',
    `**Verdict:** ${summary.verdict.toUpperCase()}`,
    `**Mode:** ${summary.mode}`,
    '',
    '| Language | Feed | Items | Newest item | Verdict |',
    '|---|---|---:|---|---|',
    ...rows,
    '',
    '## Invariants',
    '',
    '- RSS 2.0 + Atom self-link identity is stable for EN / RU / zh-CN feeds.',
    '- Items are derived from published HTML with explicit publication dates, sorted newest-first and capped at 50.',
    '- `lastBuildDate` equals the newest item date, so identical publication state produces identical feed bytes.',
    '- Utility pages are excluded; item language must match its locale route.',
    '- Local builds require one language-appropriate RSS autodiscovery link on every HTML page.',
    '- Live mode re-fetches public feeds, the Subscribe page and representative recent item URLs.',
    '',
    '## Evidence boundary',
    '',
    'Passing proves feed structure, deterministic ordering/identity, local route linkage and live reachability for the checked surfaces. It does not prove subscriber delivery by a particular RSS reader, email delivery, readership or engagement.',
    '',
    ...(summary.errors.length ? ['## Failures', '', ...summary.errors.map((error) => `- ${error}`), ''] : []),
  ].join('\n');
  fs.writeFileSync(path.join(outputDir, 'feed-summary.md'), `${markdown}\n`);
  console.log(markdown);
}

const result = liveBase ? await verifyLive() : await verifyLocal();
const summary = {
  schema: 'resonance.site-health.feed.v1',
  generatedAt: new Date().toISOString(),
  auditedCommit: process.env.GITHUB_SHA || null,
  sourceRunId: process.env.GITHUB_RUN_ID || null,
  ...result,
  verdict: result.errors.length ? 'fail' : 'pass',
};
writeSummary(summary);

if (enforce && summary.errors.length) process.exit(1);
