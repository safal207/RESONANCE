#!/usr/bin/env node

import fs from 'node:fs';
import path from 'node:path';

const ROOT = process.cwd();
const DIST = path.join(ROOT, 'dist');
const PROJECT_PREFIX = '/RESONANCE/';

if (!fs.existsSync(DIST)) {
  console.error('LINK VERIFY FAIL: dist/ does not exist; run build-seo-site.mjs first');
  process.exit(1);
}

const htmlFiles = fs.readdirSync(DIST).filter((name) => name.endsWith('.html')).sort();
const errors = [];
let checkedReferences = 0;

function normalizeLocalTarget(fromFile, rawValue) {
  const value = rawValue.trim();
  if (!value || value.startsWith('#')) return null;
  if (/^(?:https?:|mailto:|tel:|data:|javascript:)/i.test(value)) return null;

  const withoutFragment = value.split('#', 1)[0].split('?', 1)[0];
  if (!withoutFragment) return null;

  let candidate;
  if (withoutFragment.startsWith(PROJECT_PREFIX)) {
    candidate = withoutFragment.slice(PROJECT_PREFIX.length);
  } else if (withoutFragment.startsWith('/')) {
    // Absolute paths outside this GitHub Pages project are not local publication files.
    return null;
  } else {
    candidate = path.posix.normalize(path.posix.join(path.posix.dirname(fromFile), withoutFragment));
  }

  if (candidate === '.' || candidate === '') candidate = 'index.html';
  if (candidate.endsWith('/')) candidate += 'index.html';
  return candidate.replace(/^\.\//, '');
}

for (const file of htmlFiles) {
  const html = fs.readFileSync(path.join(DIST, file), 'utf8');
  const refs = [
    ...html.matchAll(/\b(?:href|src)=["']([^"']+)["']/gi),
  ].map((match) => match[1]);

  for (const rawValue of refs) {
    const target = normalizeLocalTarget(file, rawValue);
    if (!target) continue;
    checkedReferences += 1;

    const absoluteTarget = path.resolve(DIST, target);
    const relativeToDist = path.relative(DIST, absoluteTarget);
    if (relativeToDist.startsWith('..') || path.isAbsolute(relativeToDist)) {
      errors.push(`${file}: local reference escapes dist/: ${rawValue}`);
      continue;
    }

    if (!fs.existsSync(absoluteTarget)) {
      errors.push(`${file}: missing local target ${rawValue} → ${target}`);
    }
  }
}

if (errors.length > 0) {
  for (const error of errors) console.error(`LINK VERIFY FAIL: ${error}`);
  process.exit(1);
}

console.log(`RESONANCE link contract: PASS (${htmlFiles.length} pages, ${checkedReferences} local references checked)`);
