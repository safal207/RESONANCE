#!/usr/bin/env node

import fs from 'node:fs';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { buildIssueWebArticles } from './build-issue-web-articles.mjs';

const ROOT = process.cwd();
const SITE_DIR = path.join(ROOT, 'site');

const generated = buildIssueWebArticles({ rootDir: ROOT, distDir: SITE_DIR });

try {
  const result = spawnSync(process.execPath, ['scripts/build-seo-site.mjs'], {
    cwd: ROOT,
    env: process.env,
    stdio: 'inherit',
  });
  if (result.error) throw result.error;
  if (result.status !== 0) process.exitCode = result.status || 1;
} finally {
  for (const entry of generated) {
    const generatedPath = path.join(SITE_DIR, entry.route);
    if (fs.existsSync(generatedPath)) fs.rmSync(generatedPath);
  }
}

if (!process.exitCode) {
  console.log(`RESONANCE publication build: ${generated.length} Markdown article pages added to dist/`);
}
