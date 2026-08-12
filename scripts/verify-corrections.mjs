#!/usr/bin/env node

import fs from 'node:fs';
import path from 'node:path';
import process from 'node:process';
import { execFileSync } from 'node:child_process';

const args = process.argv.slice(2);
const arg = (name, fallback = null) => {
  const index = args.indexOf(name);
  return index >= 0 && args[index + 1] ? args[index + 1] : fallback;
};

const root = path.resolve(arg('--root', 'site'));
const publicRoot = path.resolve(arg('--public-root', 'dist'));
const ledgerPath = path.resolve(arg('--ledger', 'site/corrections.json'));
const outputDir = path.resolve(arg('--output', 'corrections-history-results'));
const baseRef = arg('--base');
const enforce = args.includes('--enforce');
const semver = /^\d+\.\d+\.\d+$/;
const allowedTypes = new Set(['publication', 'correction', 'clarification', 'evidence-update', 'translation', 'structural']);
const allowedClaimImpacts = new Set(['none', 'presentation', 'clarifies', 'changes-claim']);

fs.mkdirSync(outputDir, { recursive: true });
const failures = [];
const notes = [];

function fail(message) {
  failures.push(message);
}

function isDate(value) {
  return typeof value === 'string' && /^\d{4}-\d{2}-\d{2}(?:T\d{2}:\d{2}:\d{2}Z)?$/.test(value) && !Number.isNaN(Date.parse(value.length === 10 ? `${value}T00:00:00Z` : value));
}

function readJson(file) {
  return JSON.parse(fs.readFileSync(file, 'utf8'));
}

function stable(value) {
  return JSON.stringify(value);
}

if (!fs.existsSync(ledgerPath)) {
  console.error(`Corrections ledger is missing: ${ledgerPath}`);
  process.exit(2);
}

let ledger;
try {
  ledger = readJson(ledgerPath);
} catch (error) {
  console.error(`Corrections ledger is not valid JSON: ${error.message}`);
  process.exit(2);
}

if (ledger.schema !== 'resonance.corrections.v1') fail(`schema must be resonance.corrections.v1 (found ${ledger.schema || '<missing>'})`);
if (!isDate(ledger.updatedAt)) fail('updatedAt must be an ISO date or UTC timestamp');
if (!Array.isArray(ledger.publications) || !ledger.publications.length) fail('publications must be a non-empty array');
if (!Array.isArray(ledger.entries) || !ledger.entries.length) fail('entries must be a non-empty array');

const publications = new Map();
const routeMeta = new Map();
for (const publication of ledger.publications || []) {
  if (!publication?.id || typeof publication.id !== 'string') {
    fail('every publication needs a string id');
    continue;
  }
  if (publications.has(publication.id)) fail(`duplicate publication id: ${publication.id}`);
  publications.set(publication.id, publication);
  if (!publication.title) fail(`${publication.id}: title is required`);
  const routes = publication.routes || {};
  const currentVersions = publication.currentVersions || {};
  const locales = Object.keys(routes);
  if (!locales.length) fail(`${publication.id}: routes must not be empty`);
  for (const locale of locales) {
    const route = routes[locale];
    const version = currentVersions[locale];
    if (!route || typeof route !== 'string') fail(`${publication.id}/${locale}: route is required`);
    if (!semver.test(version || '')) fail(`${publication.id}/${locale}: currentVersion must be semver`);
    if (route) {
      if (routeMeta.has(route)) fail(`route is registered more than once: ${route}`);
      routeMeta.set(route, { publication: publication.id, locale, currentVersion: version });
      if (!fs.existsSync(path.join(root, route))) fail(`${publication.id}/${locale}: registered route is missing from ${root}: ${route}`);
    }
  }
  for (const locale of Object.keys(currentVersions)) {
    if (!Object.prototype.hasOwnProperty.call(routes, locale)) fail(`${publication.id}/${locale}: currentVersion has no matching route`);
  }
}

const ids = new Set();
const state = new Map([...routeMeta.keys()].map((route) => [route, null]));
let previousEffectiveAt = null;
for (const entry of ledger.entries || []) {
  if (!entry?.id || typeof entry.id !== 'string') {
    fail('every history entry needs a string id');
    continue;
  }
  if (ids.has(entry.id)) fail(`duplicate history entry id: ${entry.id}`);
  ids.add(entry.id);
  if (!isDate(entry.effectiveAt)) fail(`${entry.id}: effectiveAt must be an ISO date or UTC timestamp`);
  if (previousEffectiveAt && isDate(entry.effectiveAt) && Date.parse(entry.effectiveAt.length === 10 ? `${entry.effectiveAt}T00:00:00Z` : entry.effectiveAt) < previousEffectiveAt) {
    fail(`${entry.id}: entries must be append-ordered by effectiveAt`);
  }
  if (isDate(entry.effectiveAt)) previousEffectiveAt = Date.parse(entry.effectiveAt.length === 10 ? `${entry.effectiveAt}T00:00:00Z` : entry.effectiveAt);
  if (!allowedTypes.has(entry.type)) fail(`${entry.id}: unsupported type ${entry.type || '<missing>'}`);
  if (!allowedClaimImpacts.has(entry.claimImpact)) fail(`${entry.id}: unsupported claimImpact ${entry.claimImpact || '<missing>'}`);
  if (!entry.summary || typeof entry.summary !== 'string') fail(`${entry.id}: summary is required`);
  if (!entry.reason || typeof entry.reason !== 'string') fail(`${entry.id}: reason is required`);
  if (!Array.isArray(entry.evidence) || !entry.evidence.length) fail(`${entry.id}: at least one evidence URL is required`);
  for (const evidence of entry.evidence || []) {
    if (typeof evidence !== 'string' || !/^https:\/\//.test(evidence)) fail(`${entry.id}: evidence must use https (${evidence})`);
  }
  if (entry.type !== 'publication' && !(entry.evidence || []).some((url) => /https:\/\/github\.com\/safal207\/RESONANCE\//.test(url))) {
    fail(`${entry.id}: non-publication changes require at least one RESONANCE GitHub evidence URL`);
  }
  if (!Array.isArray(entry.affected) || !entry.affected.length) {
    fail(`${entry.id}: affected must be a non-empty array`);
    continue;
  }
  for (const affected of entry.affected) {
    const meta = routeMeta.get(affected.path);
    if (!meta) {
      fail(`${entry.id}: affected path is not registered: ${affected.path || '<missing>'}`);
      continue;
    }
    if (meta.publication !== affected.publication || meta.locale !== affected.locale) {
      fail(`${entry.id}: affected identity does not match registry for ${affected.path}`);
    }
    if (affected.fromVersion !== null && !semver.test(affected.fromVersion || '')) fail(`${entry.id}/${affected.path}: fromVersion must be null or semver`);
    if (!semver.test(affected.toVersion || '')) fail(`${entry.id}/${affected.path}: toVersion must be semver`);
    const expectedFrom = state.get(affected.path);
    if (affected.fromVersion !== expectedFrom) {
      fail(`${entry.id}/${affected.path}: version chain breaks (${affected.fromVersion ?? '<null>'} != ${expectedFrom ?? '<null>'})`);
    }
    state.set(affected.path, affected.toVersion);
  }
}

for (const [route, meta] of routeMeta) {
  if (state.get(route) !== meta.currentVersion) {
    fail(`${route}: ledger ends at ${state.get(route) || '<none>'} but registry says ${meta.currentVersion}`);
  }
}

const publicFiles = ['corrections.html', 'corrections.json', 'corrections.js'];
for (const file of publicFiles) {
  if (!fs.existsSync(path.join(publicRoot, file))) fail(`public build is missing ${file}`);
}
if (fs.existsSync(path.join(publicRoot, 'corrections.html'))) {
  const html = fs.readFileSync(path.join(publicRoot, 'corrections.html'), 'utf8');
  if (!/id=["']version-history["']/.test(html)) fail('corrections.html must expose #version-history');
  if (!/src=["']corrections\.js["']/.test(html)) fail('corrections.html must load corrections.js');
  if (!/href=["']corrections\.json["']/.test(html)) fail('corrections.html must link the machine-readable corrections.json ledger');
}

let diffStatus = 'not-requested';
let changedManagedRoutes = [];
let newEntryIds = [];
if (baseRef) {
  diffStatus = 'checked';
  try {
    const baseLedgerText = execFileSync('git', ['show', `${baseRef}:site/corrections.json`], { encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'] });
    const baseLedger = JSON.parse(baseLedgerText);
    const baseEntries = Array.isArray(baseLedger.entries) ? baseLedger.entries : [];
    if ((ledger.entries || []).length < baseEntries.length) fail('history is append-only: existing entries cannot be deleted');
    for (let index = 0; index < baseEntries.length; index += 1) {
      if (stable(baseEntries[index]) !== stable(ledger.entries[index])) {
        fail(`history is append-only: existing entry ${baseEntries[index]?.id || index} was mutated or reordered`);
      }
    }
    newEntryIds = (ledger.entries || []).slice(baseEntries.length).map((entry) => entry.id);

    const basePublications = new Map((baseLedger.publications || []).map((publication) => [publication.id, publication]));
    for (const publication of ledger.publications || []) {
      const basePublication = basePublications.get(publication.id);
      if (!basePublication) continue;
      if (stable(basePublication.routes) !== stable(publication.routes)) {
        fail(`${publication.id}: registered routes are immutable; add a new publication id for route migration`);
      }
    }

    const registeredRoutes = [...routeMeta.keys()].map((route) => `site/${route}`);
    if (registeredRoutes.length) {
      const changed = execFileSync('git', ['diff', '--name-only', '--diff-filter=M', `${baseRef}...HEAD`, '--', ...registeredRoutes], { encoding: 'utf8' })
        .split(/\r?\n/)
        .map((value) => value.trim())
        .filter(Boolean);
      changedManagedRoutes = changed.map((value) => value.replace(/^site\//, ''));
    }
    const newEntries = (ledger.entries || []).slice(baseEntries.length);
    for (const route of changedManagedRoutes) {
      if (!newEntries.some((entry) => (entry.affected || []).some((affected) => affected.path === route))) {
        fail(`silent published-page edit blocked: ${route} changed without a new version-history entry`);
      }
    }
    if (changedManagedRoutes.length && !newEntries.length) fail('managed published pages changed but the append-only history has no new entry');
  } catch (error) {
    const stderr = error?.stderr ? String(error.stderr) : '';
    if (/exists on disk, but not in|does not exist in|Path .* does not exist/.test(stderr) || /fatal: path 'site\/corrections\.json'/.test(stderr)) {
      diffStatus = 'initialization';
      notes.push('Base branch has no corrections ledger yet; append-only diff enforcement starts after v0.5 is merged.');
    } else {
      fail(`could not compare corrections history with base ${baseRef}: ${error.message}`);
    }
  }
}

const summary = {
  schema: 'resonance.site-health.corrections-history.v1',
  version: 'v0.5',
  generatedAt: new Date().toISOString(),
  auditedCommit: process.env.GITHUB_SHA || null,
  baseRef,
  verdict: failures.length ? 'fail' : 'pass',
  publicationCount: publications.size,
  managedRouteCount: routeMeta.size,
  historyEntryCount: (ledger.entries || []).length,
  diffStatus,
  changedManagedRoutes,
  newEntryIds,
  failures,
  notes,
  evidenceBoundary: 'The contract proves append-only publication-version bookkeeping and evidence linkage for registered routes. It does not prove that an editorial correction is factually sufficient or that every unregistered page is version-managed.',
};

fs.writeFileSync(path.join(outputDir, 'corrections-history-summary.json'), `${JSON.stringify(summary, null, 2)}\n`);

const markdown = [
  '# RESONANCE Corrections + Version History Contract',
  '',
  `**Verdict:** ${summary.verdict.toUpperCase()}`,
  '',
  `- Managed publications: **${summary.publicationCount}**`,
  `- Managed routes: **${summary.managedRouteCount}**`,
  `- Append-only history entries: **${summary.historyEntryCount}**`,
  `- Diff gate: **${summary.diffStatus}**`,
  `- Changed managed routes in this diff: **${summary.changedManagedRoutes.length}**`,
  `- New history entries in this diff: **${summary.newEntryIds.length}**`,
  '',
  '## Release invariants',
  '',
  '- Registered published routes must exist and end at the version declared by the registry.',
  '- Version transitions must form an unbroken chain from initial publication to the current version.',
  '- Existing history entries are immutable and append-only once v0.5 exists on the base branch.',
  '- A modified managed published page must be covered by a newly appended history entry in the same change.',
  '- Every history entry records change type, claim impact, reason, affected versions and inspectable evidence URLs.',
  '- Non-publication updates require RESONANCE GitHub evidence.',
  '',
  '## Evidence boundary',
  '',
  'Passing this contract proves publication-version bookkeeping, append-only history integrity and evidence linkage for registered routes. It does **not** prove that the correction itself is editorially or factually sufficient, and it makes no claim about unregistered pages.',
  '',
  ...(notes.length ? ['## Notes', '', ...notes.map((note) => `- ${note}`), ''] : []),
  ...(failures.length ? ['## Hard failures', '', ...failures.map((failure) => `- ${failure}`), ''] : []),
].join('\n');

fs.writeFileSync(path.join(outputDir, 'corrections-history-summary.md'), `${markdown}\n`);
console.log(markdown);

if (enforce && failures.length) process.exit(1);
