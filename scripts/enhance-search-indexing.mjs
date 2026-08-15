#!/usr/bin/env node

import fs from 'node:fs';
import path from 'node:path';

const ROOT = process.cwd();
const DIST = path.join(ROOT, 'dist');
const BASE = 'https://safal207.github.io/RESONANCE/';
const GOOGLE_VERIFICATION = (process.env.RESONANCE_GOOGLE_SITE_VERIFICATION || '').trim();

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

function canonicalFor(file) {
  return file === 'index.html' ? BASE : `${BASE}${file}`;
}

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

function escapeHtml(value = '') {
  return String(value)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function xmlEscape(value = '') {
  return String(value)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&apos;');
}

function readTitle(html, file) {
  return stripTags(html.match(/<title>([\s\S]*?)<\/title>/i)?.[1] || file);
}

function readDescription(html) {
  return decodeHtml(html.match(/<meta\s+name=["']description["']\s+content=["']([^"']*)["'][^>]*>/i)?.[1] || '').trim();
}

function readLanguage(html, file) {
  const declared = html.match(/<html[^>]*\slang=["']([^"']+)["']/i)?.[1]?.trim();
  if (declared) return declared;
  if (file === 'index.ru.html' || file.endsWith('.ru.html')) return 'ru';
  if (file === 'index.zh.html' || file.endsWith('.zh.html')) return 'zh-CN';
  return 'en';
}

function readPublishedDate(html) {
  const iso = html.match(/<meta\s+property=["']article:published_time["']\s+content=["'](\d{4}-\d{2}-\d{2})/i)?.[1];
  if (iso) return iso;
  const english = html.match(/(?:Verified|Executed|Published)\s*·\s*(\d{1,2})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{4})/i);
  if (english) {
    const months = { Jan: '01', Feb: '02', Mar: '03', Apr: '04', May: '05', Jun: '06', Jul: '07', Aug: '08', Sep: '09', Oct: '10', Nov: '11', Dec: '12' };
    const month = months[english[2][0].toUpperCase() + english[2].slice(1, 3).toLowerCase()];
    return `${english[3]}-${month}-${String(english[1]).padStart(2, '0')}`;
  }
  const russian = html.match(/(?:Published|Опубликовано)\s*·?\s*(\d{1,2})[.\s-]+(\d{1,2}|январ[ья]|феврал[ья]|март[а]?|апрел[ья]|ма[йя]|июн[ья]|июл[ья]|август[а]?|сентябр[ья]|октябр[ья]|ноябр[ья]|декабр[ья])[.\s-]+(\d{4})/i);
  if (russian) {
    const months = { января: '01', январь: '01', февраля: '02', февраль: '02', марта: '03', март: '03', апреля: '04', апрель: '04', мая: '05', май: '05', июня: '06', июнь: '06', июля: '07', июль: '07', августа: '08', август: '08', сентября: '09', сентябрь: '09', октября: '10', октябрь: '10', ноября: '11', ноябрь: '11', декабря: '12', декабрь: '12' };
    const rawMonth = russian[2].toLowerCase();
    const month = /^\d+$/.test(rawMonth) ? String(Number(rawMonth)).padStart(2, '0') : months[rawMonth];
    if (month) return `${russian[3]}-${month}-${String(russian[1]).padStart(2, '0')}`;
  }
  return '';
}

function generatedSchemaMatch(html) {
  return html.match(/<script\s+type=["']application\/ld\+json["']\s+data-resonance-seo=["']true["'][^>]*>([\s\S]*?)<\/script>/i);
}

function parseGeneratedSchema(html) {
  const raw = generatedSchemaMatch(html)?.[1];
  if (!raw) return null;
  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

function nodes(schema) {
  if (!schema) return [];
  if (Array.isArray(schema['@graph'])) return schema['@graph'];
  return [schema];
}

function hasType(schema, type) {
  return nodes(schema).some((node) => {
    const value = node?.['@type'];
    return Array.isArray(value) ? value.includes(type) : value === type;
  });
}

function schemaKind(schema, file) {
  if (hasType(schema, 'CollectionPage')) return 'collection';
  if (hasType(schema, 'WebSite')) return 'website';
  if (hasType(schema, 'Article') || hasType(schema, 'NewsArticle') || hasType(schema, 'BlogPosting')) return 'article';
  if (utilityRoutes.has(file)) return 'page';
  return 'article';
}

function replaceGeneratedSchema(html, schema) {
  const match = generatedSchemaMatch(html);
  if (!match) return html;
  const replacement = `<script type="application/ld+json" data-resonance-seo="true">${JSON.stringify(schema)}</script>`;
  return html.replace(match[0], replacement);
}

function nodeUrl(node) {
  if (typeof node?.url === 'string') return node.url;
  if (typeof node?.mainEntityOfPage === 'string') return node.mainEntityOfPage;
  if (typeof node?.mainEntityOfPage?.['@id'] === 'string') return node.mainEntityOfPage['@id'];
  return '';
}

function isPrimaryPageType(node) {
  const types = Array.isArray(node?.['@type']) ? node['@type'] : [node?.['@type']];
  return types.some((type) => ['Article', 'NewsArticle', 'BlogPosting', 'CollectionPage', 'WebPage', 'WebSite'].includes(type));
}

function stripDuplicateManualPrimarySchema(html, canonical) {
  return html.replace(/<script\b([^>]*)\btype=["']application\/ld\+json["']([^>]*)>([\s\S]*?)<\/script>/gi, (match, before, after, body) => {
    const attrs = `${before || ''} ${after || ''}`;
    if (/data-resonance-seo\s*=\s*["']true["']/i.test(attrs)) return match;
    try {
      const schema = JSON.parse(body);
      const duplicate = nodes(schema).some((node) => isPrimaryPageType(node) && nodeUrl(node) === canonical);
      return duplicate ? '' : match;
    } catch {
      return match;
    }
  });
}

function searchBlock(file, language) {
  const feed = language === 'ru' ? 'feed.ru.xml' : language === 'zh-CN' ? 'feed.zh.xml' : 'feed.xml';
  const verification = file === 'index.html' && GOOGLE_VERIFICATION
    ? `\n  <meta name="google-site-verification" content="${escapeHtml(GOOGLE_VERIFICATION)}" />`
    : '';
  return `\n  <!-- SEARCH:START -->\n  <meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1" />\n  <link rel="alternate" type="application/rss+xml" title="RESONANCE RSS" href="${BASE}${feed}" />${verification}\n  <!-- SEARCH:END -->\n`;
}

function injectSearchBlock(html, file, language) {
  let clean = html.replace(/\n?\s*<!-- SEARCH:START -->[\s\S]*?<!-- SEARCH:END -->\s*\n?/i, '\n');
  clean = clean.replace(/\s*<meta\s+name=["']robots["'][^>]*>\s*/gi, '\n');
  clean = clean.replace(/\s*<meta\s+name=["']googlebot["'][^>]*>\s*/gi, '\n');
  clean = clean.replace(/\s*<meta\s+name=["']google-site-verification["'][^>]*>\s*/gi, '\n');
  return clean.replace('</head>', `${searchBlock(file, language)}</head>`);
}

function articleSchemaWithBreadcrumb(schema, record) {
  let article;
  if (schema?.['@type'] === 'Article' || schema?.['@type'] === 'NewsArticle' || schema?.['@type'] === 'BlogPosting') {
    article = { ...schema };
    delete article['@context'];
  } else {
    const existing = nodes(schema).find((node) => ['Article', 'NewsArticle', 'BlogPosting'].includes(node?.['@type']));
    if (!existing) return schema;
    article = { ...existing };
  }

  article['@id'] = `${record.canonical}#article`;
  article.url = record.canonical;
  article.mainEntityOfPage = { '@type': 'WebPage', '@id': record.canonical };
  article.inLanguage = record.language;
  if (record.published && !article.datePublished) article.datePublished = record.published;

  const breadcrumb = {
    '@type': 'BreadcrumbList',
    '@id': `${record.canonical}#breadcrumb`,
    itemListElement: [
      { '@type': 'ListItem', position: 1, name: 'RESONANCE', item: BASE },
      { '@type': 'ListItem', position: 2, name: 'The Age of Agents', item: `${BASE}issue-001.html` },
      { '@type': 'ListItem', position: 3, name: record.title.replace(/\s*\|\s*RESONANCE.*$/i, ''), item: record.canonical },
    ],
  };

  const other = nodes(schema).filter((node) => !['Article', 'NewsArticle', 'BlogPosting', 'BreadcrumbList'].includes(node?.['@type']));
  return { '@context': 'https://schema.org', '@graph': [article, breadcrumb, ...other] };
}

function collectionSchemaWithArticles(schema, articleRecords) {
  if (!schema || !hasType(schema, 'CollectionPage')) return schema;
  const articleParts = articleRecords.map((record) => ({
    '@type': 'Article',
    name: record.title.replace(/\s*\|\s*RESONANCE.*$/i, ''),
    url: record.canonical,
    inLanguage: record.language,
  }));
  if (schema['@type'] === 'CollectionPage') return { ...schema, hasPart: articleParts };
  return {
    ...schema,
    '@graph': nodes(schema).map((node) => node?.['@type'] === 'CollectionPage' ? { ...node, hasPart: articleParts } : node),
  };
}

function translationKey(file) {
  if (/^index(?:\.(?:ru|zh))?\.html$/.test(file)) return 'index';
  return file.replace(/\.(?:ru|zh)\.html$/, '.html');
}

function alternateMap(records) {
  const groups = new Map();
  for (const record of records) {
    const key = translationKey(record.file);
    const group = groups.get(key) || [];
    group.push(record);
    groups.set(key, group);
  }
  const byFile = new Map();
  for (const group of groups.values()) {
    const languages = new Set(group.map((record) => record.language));
    if (group.length < 2 || languages.size < 2) continue;
    const links = group.map((record) => [record.language, record.canonical]);
    const fallback = group.find((record) => record.language === 'en') || group[0];
    links.push(['x-default', fallback.canonical]);
    for (const record of group) byFile.set(record.file, links);
  }
  return byFile;
}

function buildArticleIndex(articleRecords) {
  const items = articleRecords
    .map((record) => `          <li><a href="${escapeHtml(record.file)}">${escapeHtml(record.title.replace(/\s*\|\s*RESONANCE.*$/i, ''))}</a>${record.published ? ` <span>· ${escapeHtml(record.published)}</span>` : ''}</li>`)
    .join('\n');
  return `\n    <!-- SEARCH-ARTICLE-INDEX:START -->\n    <section class="section rule-top wrap" data-search-article-index="true">\n      <div class="editorial-grid">\n        <div>\n          <p class="section-label">Search / Archive</p>\n          <h2>All published web articles</h2>\n        </div>\n        <div>\n          <p>Canonical crawlable index of RESONANCE web articles. Each entry resolves to the same URL used in sitemap.xml and structured data.</p>\n          <ul>\n${items}\n          </ul>\n        </div>\n      </div>\n    </section>\n    <!-- SEARCH-ARTICLE-INDEX:END -->\n`;
}

if (!fs.existsSync(DIST)) throw new Error('dist/ does not exist; run build-seo-site.mjs first');

const pageFiles = fs.readdirSync(DIST).filter((name) => name.endsWith('.html')).sort();
const records = pageFiles.map((file) => {
  const html = fs.readFileSync(path.join(DIST, file), 'utf8');
  const schema = parseGeneratedSchema(html);
  return {
    file,
    html,
    schema,
    canonical: canonicalFor(file),
    title: readTitle(html, file),
    description: readDescription(html),
    language: readLanguage(html, file),
    published: readPublishedDate(html),
    kind: schemaKind(schema, file),
  };
});

const articleRecords = records.filter((record) => record.kind === 'article' && !utilityRoutes.has(record.file));
const alternates = alternateMap(records);

for (const record of records) {
  let html = record.html;
  html = stripDuplicateManualPrimarySchema(html, record.canonical);
  html = injectSearchBlock(html, record.file, record.language);

  let schema = parseGeneratedSchema(html) || record.schema;
  if (record.kind === 'article' && !utilityRoutes.has(record.file)) {
    schema = articleSchemaWithBreadcrumb(schema, record);
  } else if (record.file === 'issue-001.html' || record.file === 'ai-agents.html') {
    schema = collectionSchemaWithArticles(schema, articleRecords);
  }
  if (schema) html = replaceGeneratedSchema(html, schema);

  if (record.file === 'issue-001.html') {
    html = html.replace(/\n?\s*<!-- SEARCH-ARTICLE-INDEX:START -->[\s\S]*?<!-- SEARCH-ARTICLE-INDEX:END -->\s*\n?/i, '\n');
    html = html.replace('</main>', `${buildArticleIndex(articleRecords)}</main>`);
  }

  fs.writeFileSync(path.join(DIST, record.file), html);
}

const sitemap = `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">\n${records.map((record) => {
  const alternateLinks = (alternates.get(record.file) || [])
    .map(([language, href]) => `    <xhtml:link rel="alternate" hreflang="${xmlEscape(language)}" href="${xmlEscape(href)}" />`)
    .join('\n');
  return `  <url>\n    <loc>${xmlEscape(record.canonical)}</loc>${record.published ? `\n    <lastmod>${record.published}</lastmod>` : ''}${alternateLinks ? `\n${alternateLinks}` : ''}\n  </url>`;
}).join('\n')}\n</urlset>\n`;
fs.writeFileSync(path.join(DIST, 'sitemap.xml'), sitemap);

const robots = `User-agent: *\nAllow: /\n\nSitemap: ${BASE}sitemap.xml\n`;
fs.writeFileSync(path.join(DIST, 'robots.txt'), robots);

console.log(`RESONANCE search indexing enhancement: ${records.length} pages · ${articleRecords.length} crawlable articles · ${alternates.size} localized URLs`);
