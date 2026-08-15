#!/usr/bin/env node

import fs from 'node:fs';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { buildIssueWebArticles } from './build-issue-web-articles.mjs';

const ROOT = process.cwd();
const SITE_DIR = path.join(ROOT, 'site');
const ISSUE_README = path.join(ROOT, 'issues', '001-age-of-agents', 'README.md');
const GITHUB_ARTICLES = 'https://github.com/safal207/RESONANCE/blob/main/issues/001-age-of-agents/articles/';

const existingWebRoutes = new Map([
  ['01-the-agentic-turn.md', 'the-agentic-turn.html'],
  ['02-the-missing-trust-layer.md', 'the-missing-trust-layer.html'],
  ['03-when-agents-fail.md', 'when-agents-fail.html'],
  ['13-evidence-must-bind-the-transition.md', 'evidence-must-bind-the-transition.ru.html'],
]);

function routeFor(filename) {
  return existingWebRoutes.get(filename) || `article-${filename.replace(/\.md$/, '')}.html`;
}

function canonicalArticleFiles() {
  if (!fs.existsSync(ISSUE_README)) return new Set();
  const readme = fs.readFileSync(ISSUE_README, 'utf8');
  const section = readme.match(/## Published features([\s\S]*?)(?=\n##\s)/i)?.[1] || '';
  return new Set(
    [...section.matchAll(/\]\(articles\/([^)]*?\.md)\)/gi)]
      .map((match) => match[1])
      .filter((name) => !name.endsWith('.sources.md')),
  );
}

function rewriteGeneratedLinks(html, canonicalFiles) {
  return html.replace(/href="(\.\.?\/)?([^"#?]+\.(?:md|json|ya?ml))(#[^"]*)?"/gi, (match, prefix, target, fragment = '') => {
    const filename = path.basename(target);
    if (filename.endsWith('.md') && canonicalFiles.has(filename)) {
      return `href="${routeFor(filename)}${fragment}"`;
    }
    const githubTarget = `${GITHUB_ARTICLES}${target.replace(/^\.\//, '').split('/').map(encodeURIComponent).join('/')}${fragment}`;
    return `href="${githubTarget}" target="_blank" rel="noreferrer"`;
  });
}

const canonicalFiles = canonicalArticleFiles();
const allGenerated = buildIssueWebArticles({ rootDir: ROOT, distDir: SITE_DIR });
const generated = [];

for (const entry of allGenerated) {
  const generatedPath = path.join(SITE_DIR, entry.route);
  if (!canonicalFiles.has(entry.filename)) {
    if (fs.existsSync(generatedPath)) fs.rmSync(generatedPath);
    continue;
  }
  if (fs.existsSync(generatedPath)) {
    const html = fs.readFileSync(generatedPath, 'utf8');
    fs.writeFileSync(generatedPath, rewriteGeneratedLinks(html, canonicalFiles));
  }
  generated.push(entry);
}

try {
  const result = spawnSync(process.execPath, ['scripts/build-seo-site.mjs'], {
    cwd: ROOT,
    env: process.env,
    stdio: 'inherit',
  });
  if (result.error) throw result.error;
  if (result.status !== 0) process.exitCode = result.status || 1;
} finally {
  for (const entry of allGenerated) {
    const generatedPath = path.join(SITE_DIR, entry.route);
    if (fs.existsSync(generatedPath)) fs.rmSync(generatedPath);
  }
}

if (!process.exitCode) {
  console.log(`RESONANCE publication build: ${generated.length} canonical Markdown article pages added to dist/ (${canonicalFiles.size} published features registered)`);
}
