#!/usr/bin/env node

import fs from 'node:fs';
import path from 'node:path';

const ROOT = process.cwd();
const DIST_DIR = path.join(ROOT, 'dist');
const BASE = 'https://safal207.github.io/RESONANCE/';
const MAX_ITEMS = 50;

const feedProfiles = {
  en: {
    file: 'feed.xml',
    title: 'RESONANCE — Evidence-First AI & Trust Journal',
    description: 'Verified reports, research notes and evidence-first analysis from RESONANCE.',
  },
  ru: {
    file: 'feed.ru.xml',
    title: 'RESONANCE — русское издание',
    description: 'Русские публикации RESONANCE об AI-агентах, доверии, верификации и evidence-first инфраструктуре.',
  },
  'zh-CN': {
    file: 'feed.zh.xml',
    title: 'RESONANCE 中文版',
    description: 'RESONANCE 中文文章：AI Agent、信任、验证与 evidence-first 基础设施。',
  },
};

const utilityRoutes = new Set([
  'index.html',
  'index.ru.html',
  'index.zh.html',
  'issue-001.html',
  'ai-agents.html',
  'open-problems.html',
  'verified-workflow.html',
  'quality.html',
  'corrections.html',
  'subscribe.html',
]);

function decodeHtml(value = '') {
  return value
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'")
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&amp;/g, '&');
}

function stripTags(value = '') {
  return decodeHtml(value)
    .replace(/<script[\s\S]*?<\/script>/gi, ' ')
    .replace(/<style[\s\S]*?<\/style>/gi, ' ')
    .replace(/<[^>]+>/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
}

function xmlEscape(value = '') {
  return String(value)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&apos;');
}

function readLanguage(file, html) {
  const declared = html.match(/<html[^>]*\slang=["']([^"']+)["']/i)?.[1]?.trim();
  if (declared && feedProfiles[declared]) return declared;
  if (file === 'index.ru.html' || file.endsWith('.ru.html')) return 'ru';
  if (file === 'index.zh.html' || file.endsWith('.zh.html')) return 'zh-CN';
  return 'en';
}

function readPublishedDate(html) {
  const match = html.match(/(?:Verified|Executed|Published)\s*·\s*(\d{1,2})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{4})/i);
  if (!match) return null;
  const months = { Jan: '01', Feb: '02', Mar: '03', Apr: '04', May: '05', Jun: '06', Jul: '07', Aug: '08', Sep: '09', Oct: '10', Nov: '11', Dec: '12' };
  const key = match[2][0].toUpperCase() + match[2].slice(1, 3).toLowerCase();
  return `${match[3]}-${months[key]}-${String(match[1]).padStart(2, '0')}`;
}

function readCanonical(file, html) {
  return html.match(/<link\s+rel=["']canonical["']\s+href=["']([^"']+)["'][^>]*>/i)?.[1]?.trim() || `${BASE}${file}`;
}

function readDescription(html) {
  const raw = html.match(/<meta\s+name=["']description["']\s+content=["']([^"']*)["'][^>]*>/i)?.[1] || '';
  if (raw.trim()) return decodeHtml(raw.trim());
  return stripTags(html.match(/<p[^>]*class=["'][^"']*article-dek[^"']*["'][^>]*>([\s\S]*?)<\/p>/i)?.[1] || '');
}

function readTitle(file, html) {
  return stripTags(html.match(/<h1[^>]*>([\s\S]*?)<\/h1>/i)?.[1] || html.match(/<title[^>]*>([\s\S]*?)<\/title>/i)?.[1] || file);
}

function toRfc2822(date) {
  return new Date(`${date}T12:00:00Z`).toUTCString();
}

function feedFileFor(language) {
  return feedProfiles[language]?.file || feedProfiles.en.file;
}

function injectAutodiscovery(file, html) {
  const language = readLanguage(file, html);
  const profile = feedProfiles[language] || feedProfiles.en;
  const title = xmlEscape(`${profile.title} RSS`);
  const href = `${BASE}${profile.file}`;
  const tag = `  <link rel="alternate" type="application/rss+xml" title="${title}" href="${href}" />`;
  const stripped = html.replace(/\s*<link\s+rel=["']alternate["'][^>]*type=["']application\/rss\+xml["'][^>]*>\s*/gi, '\n');
  return stripped.replace('</head>', `${tag}\n</head>`);
}

function collectItems(htmlFiles) {
  const items = [];
  for (const file of htmlFiles) {
    const fullPath = path.join(DIST_DIR, file);
    const html = fs.readFileSync(fullPath, 'utf8');
    fs.writeFileSync(fullPath, injectAutodiscovery(file, html));

    if (utilityRoutes.has(file)) continue;
    const published = readPublishedDate(html);
    if (!published) continue;
    const title = readTitle(file, html);
    const description = readDescription(html) || title;
    if (!title) continue;
    items.push({
      file,
      language: readLanguage(file, html),
      published,
      title,
      description,
      url: readCanonical(file, html),
    });
  }
  return items.sort((a, b) => b.published.localeCompare(a.published) || a.file.localeCompare(b.file));
}

function buildFeed(language, allItems) {
  const profile = feedProfiles[language];
  const items = allItems.filter((item) => item.language === language).slice(0, MAX_ITEMS);
  const newest = items[0]?.published || '2026-08-12';
  const selfUrl = `${BASE}${profile.file}`;
  const itemXml = items.map((item) => `    <item>\n      <title>${xmlEscape(item.title)}</title>\n      <link>${xmlEscape(item.url)}</link>\n      <guid isPermaLink="true">${xmlEscape(item.url)}</guid>\n      <pubDate>${xmlEscape(toRfc2822(item.published))}</pubDate>\n      <description>${xmlEscape(item.description)}</description>\n    </item>`).join('\n');

  return `<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">\n  <channel>\n    <title>${xmlEscape(profile.title)}</title>\n    <link>${BASE}</link>\n    <description>${xmlEscape(profile.description)}</description>\n    <language>${xmlEscape(language)}</language>\n    <atom:link href="${xmlEscape(selfUrl)}" rel="self" type="application/rss+xml" />\n    <lastBuildDate>${xmlEscape(toRfc2822(newest))}</lastBuildDate>\n    <generator>RESONANCE deterministic feed builder</generator>\n    <ttl>60</ttl>\n${itemXml}\n  </channel>\n</rss>\n`;
}

if (!fs.existsSync(DIST_DIR)) {
  console.error('dist/ does not exist. Run scripts/build-seo-site.mjs first.');
  process.exit(2);
}

const htmlFiles = fs.readdirSync(DIST_DIR).filter((name) => name.endsWith('.html')).sort();
const items = collectItems(htmlFiles);
for (const language of Object.keys(feedProfiles)) {
  const profile = feedProfiles[language];
  fs.writeFileSync(path.join(DIST_DIR, profile.file), buildFeed(language, items));
}

const counts = Object.fromEntries(Object.keys(feedProfiles).map((language) => [language, items.filter((item) => item.language === language).slice(0, MAX_ITEMS).length]));
console.log(`RESONANCE RSS build: ${counts.en} EN / ${counts.ru} RU / ${counts['zh-CN']} zh-CN items`);
