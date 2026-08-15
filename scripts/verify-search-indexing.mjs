#!/usr/bin/env node

import fs from 'node:fs';
import path from 'node:path';

const ROOT = process.cwd();
const DIST = path.join(ROOT, 'dist');
const BASE = 'https://safal207.github.io/RESONANCE/';
const EXPECTED_GOOGLE_VERIFICATION = (process.env.RESONANCE_GOOGLE_SITE_VERIFICATION || '').trim();

const utilityRoutes = new Set([
  'index.html',
  'index.ru.html',
  'index.zh.html',
  'issue-001.html',
  'ai-agents.html',
  'open-problems.html',
  'verified-workflow.html',
  'measurement.html',
  'agent-payment-verification.html',
  'quality.html',
  'corrections.html',
  'subscribe.html',
  'science.html',
  'science.ru.html',
  'science.zh.html',
]);

function fail(message) {
  console.error(`SEARCH INDEX VERIFY FAIL: ${message}`);
  process.exitCode = 1;
}

function canonicalFor(file) {
  return file === 'index.html' ? BASE : `${BASE}${file}`;
}

function count(html, regex) {
  return [...html.matchAll(regex)].length;
}

function readLanguage(html, file) {
  const declared = html.match(/<html[^>]*\slang=["']([^"']+)["']/i)?.[1]?.trim();
  if (declared) return declared;
  if (file === 'index.ru.html' || file.endsWith('.ru.html')) return 'ru';
  if (file === 'index.zh.html' || file.endsWith('.zh.html')) return 'zh-CN';
  return 'en';
}

function readPublishedDate(html) {
  return html.match(/<meta\s+property=["']article:published_time["']\s+content=["'](\d{4}-\d{2}-\d{2})/i)?.[1]
    || html.match(/"datePublished"\s*:\s*"(\d{4}-\d{2}-\d{2})/i)?.[1]
    || '';
}

function parseJsonLdBlocks(html) {
  const blocks = [];
  for (const match of html.matchAll(/<script\b([^>]*)\btype=["']application\/ld\+json["']([^>]*)>([\s\S]*?)<\/script>/gi)) {
    try {
      blocks.push({ attrs: `${match[1] || ''} ${match[2] || ''}`, schema: JSON.parse(match[3]) });
    } catch (error) {
      fail(`invalid JSON-LD block: ${error.message}`);
    }
  }
  return blocks;
}

function nodes(schema) {
  if (!schema) return [];
  return Array.isArray(schema['@graph']) ? schema['@graph'] : [schema];
}

function hasType(schema, type) {
  return nodes(schema).some((node) => {
    const value = node?.['@type'];
    return Array.isArray(value) ? value.includes(type) : value === type;
  });
}

function nodeUrl(node) {
  if (typeof node?.url === 'string') return node.url;
  if (typeof node?.mainEntityOfPage === 'string') return node.mainEntityOfPage;
  if (typeof node?.mainEntityOfPage?.['@id'] === 'string') return node.mainEntityOfPage['@id'];
  return '';
}

function isPrimary(node) {
  const values = Array.isArray(node?.['@type']) ? node['@type'] : [node?.['@type']];
  return values.some((type) => ['Article', 'NewsArticle', 'BlogPosting', 'CollectionPage', 'WebPage', 'WebSite'].includes(type));
}

if (!fs.existsSync(DIST)) {
  fail('dist/ missing');
  process.exit(1);
}

const pages = fs.readdirSync(DIST).filter((name) => name.endsWith('.html')).sort();
const sitemapPath = path.join(DIST, 'sitemap.xml');
const robotsPath = path.join(DIST, 'robots.txt');
if (!fs.existsSync(sitemapPath)) fail('sitemap.xml missing');
if (!fs.existsSync(robotsPath)) fail('robots.txt missing');

const sitemap = fs.existsSync(sitemapPath) ? fs.readFileSync(sitemapPath, 'utf8') : '';
const robots = fs.existsSync(robotsPath) ? fs.readFileSync(robotsPath, 'utf8') : '';
const articleRecords = [];

if (!/xmlns:xhtml=["']http:\/\/www\.w3\.org\/1999\/xhtml["']/.test(sitemap)) fail('sitemap.xml missing xhtml namespace for language alternates');
if (!robots.includes(`Sitemap: ${BASE}sitemap.xml`)) fail('robots.txt missing canonical sitemap declaration');
if (!/User-agent:\s*\*[\s\S]*Allow:\s*\//i.test(robots)) fail('robots.txt does not allow crawling');

for (const file of pages) {
  const html = fs.readFileSync(path.join(DIST, file), 'utf8');
  const canonical = canonicalFor(file);
  const language = readLanguage(html, file);
  const expectedFeed = language === 'ru' ? 'feed.ru.xml' : language === 'zh-CN' ? 'feed.zh.xml' : 'feed.xml';

  if (count(html, /<meta\s+name=["']robots["'][^>]*>/gi) !== 1) fail(`${file}: expected exactly one robots meta`);
  if (!/<meta\s+name=["']robots["'][^>]*content=["'][^"']*index[^"']*follow/i.test(html)) fail(`${file}: robots meta must allow index,follow`);
  if (/noindex|nofollow/i.test(html.match(/<meta\s+name=["']robots["'][^>]*>/i)?.[0] || '')) fail(`${file}: robots meta blocks indexing or links`);
  if (!html.includes(`type="application/rss+xml"`) || !html.includes(`${BASE}${expectedFeed}`)) fail(`${file}: language-appropriate RSS discovery link missing`);
  if (!sitemap.includes(`<loc>${canonical.replace(/&/g, '&amp;')}</loc>`)) fail(`${file}: canonical URL missing from sitemap`);

  const generatedMatch = html.match(/<script\s+type=["']application\/ld\+json["']\s+data-resonance-seo=["']true["'][^>]*>([\s\S]*?)<\/script>/i);
  if (!generatedMatch) {
    fail(`${file}: generated RESONANCE JSON-LD missing`);
    continue;
  }

  let generated;
  try {
    generated = JSON.parse(generatedMatch[1]);
  } catch (error) {
    fail(`${file}: generated JSON-LD invalid (${error.message})`);
    continue;
  }

  const isArticle = hasType(generated, 'Article') || hasType(generated, 'NewsArticle') || hasType(generated, 'BlogPosting');
  if (isArticle && !utilityRoutes.has(file)) {
    articleRecords.push({ file, canonical });
    if (!hasType(generated, 'BreadcrumbList')) fail(`${file}: article missing BreadcrumbList schema`);
    const articleNode = nodes(generated).find((node) => ['Article', 'NewsArticle', 'BlogPosting'].includes(node?.['@type']));
    if (nodeUrl(articleNode) !== canonical) fail(`${file}: Article schema does not bind to canonical URL`);
    const visibleDate = readPublishedDate(html);
    if (visibleDate && !articleNode?.datePublished) fail(`${file}: visible publication date not reflected in Article schema`);
    if (visibleDate && !sitemap.includes(`<loc>${canonical}</loc>\n    <lastmod>${visibleDate}</lastmod>`)) fail(`${file}: sitemap lastmod missing or inconsistent with publication date`);
  }

  const primaryCount = parseJsonLdBlocks(html)
    .flatMap((block) => nodes(block.schema))
    .filter((node) => isPrimary(node) && nodeUrl(node) === canonical)
    .length;
  if (primaryCount > 1) fail(`${file}: duplicate primary structured-data entities for canonical URL (${primaryCount})`);
}

const issuePath = path.join(DIST, 'issue-001.html');
if (!fs.existsSync(issuePath)) {
  fail('issue-001.html missing');
} else {
  const issue = fs.readFileSync(issuePath, 'utf8');
  if (!/data-search-article-index=["']true["']/.test(issue)) fail('Issue 001 missing generated crawlable article index');
  for (const article of articleRecords) {
    if (!issue.includes(`href="${article.file}"`)) fail(`Issue 001 article index missing ${article.file}`);
  }
  const generatedMatch = issue.match(/<script\s+type=["']application\/ld\+json["']\s+data-resonance-seo=["']true["'][^>]*>([\s\S]*?)<\/script>/i);
  if (generatedMatch) {
    try {
      const schema = JSON.parse(generatedMatch[1]);
      const collection = nodes(schema).find((node) => node?.['@type'] === 'CollectionPage');
      const urls = new Set((collection?.hasPart || []).map((entry) => entry?.url));
      for (const article of articleRecords) if (!urls.has(article.canonical)) fail(`Issue 001 CollectionPage.hasPart missing ${article.canonical}`);
    } catch (error) {
      fail(`Issue 001 JSON-LD invalid (${error.message})`);
    }
  }
}

if (EXPECTED_GOOGLE_VERIFICATION) {
  const home = fs.readFileSync(path.join(DIST, 'index.html'), 'utf8');
  const escaped = EXPECTED_GOOGLE_VERIFICATION.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  if (!new RegExp(`<meta\\s+name=["']google-site-verification["']\\s+content=["']${escaped}["']`, 'i').test(home)) {
    fail('index.html missing configured Google Search Console verification meta');
  }
}

if (!process.exitCode) {
  console.log(`RESONANCE search indexing contract: PASS (${pages.length} pages · ${articleRecords.length} crawlable articles)`);
}
