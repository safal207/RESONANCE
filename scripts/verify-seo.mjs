import fs from 'node:fs';
import path from 'node:path';

const ROOT = process.cwd();
const DIST = path.join(ROOT, 'dist');
const BASE = 'https://safal207.github.io/RESONANCE/';

function fail(message) {
  console.error(`SEO VERIFY FAIL: ${message}`);
  process.exitCode = 1;
}

function count(html, regex) {
  return [...html.matchAll(regex)].length;
}

function attr(html, regex) {
  return html.match(regex)?.[1] || '';
}

function schemaLanguage(schema) {
  if (schema?.inLanguage) return schema.inLanguage;
  if (Array.isArray(schema?.['@graph'])) {
    return schema['@graph'].find((node) => node?.inLanguage)?.inLanguage || '';
  }
  return '';
}

if (!fs.existsSync(DIST)) {
  fail('dist/ does not exist; run build-seo-site.mjs first');
  process.exit(1);
}

const pages = fs.readdirSync(DIST).filter((name) => name.endsWith('.html')).sort();
const sitemap = fs.readFileSync(path.join(DIST, 'sitemap.xml'), 'utf8');
const robots = fs.readFileSync(path.join(DIST, 'robots.txt'), 'utf8');
const titles = new Map();
const descriptions = new Map();

for (const file of pages) {
  const html = fs.readFileSync(path.join(DIST, file), 'utf8');
  const expectedCanonical = file === 'index.html' ? BASE : `${BASE}${file}`;

  if (count(html, /<title>[\s\S]*?<\/title>/gi) !== 1) fail(`${file}: expected exactly one <title>`);
  if (count(html, /<h1\b[^>]*>[\s\S]*?<\/h1>/gi) !== 1) fail(`${file}: expected exactly one H1`);
  if (count(html, /<meta\s+name=["']description["'][^>]*>/gi) !== 1) fail(`${file}: expected exactly one meta description`);
  if (count(html, /<link\s+rel=["']canonical["'][^>]*>/gi) !== 1) fail(`${file}: expected exactly one canonical`);
  if (count(html, /<script\s+type=["']application\/ld\+json["']\s+data-resonance-seo=["']true["'][^>]*>[\s\S]*?<\/script>/gi) !== 1) fail(`${file}: expected one RESONANCE JSON-LD block`);

  const canonical = attr(html, /<link\s+rel=["']canonical["']\s+href=["']([^"']+)["'][^>]*>/i);
  if (canonical !== expectedCanonical) fail(`${file}: canonical mismatch (${canonical || 'missing'})`);

  const ogUrl = attr(html, /<meta\s+property=["']og:url["']\s+content=["']([^"']+)["'][^>]*>/i);
  if (ogUrl !== expectedCanonical) fail(`${file}: og:url mismatch`);

  for (const property of ['og:title', 'og:description', 'og:type', 'og:url', 'og:locale']) {
    if (!new RegExp(`<meta\\s+property=["']${property.replace(':', '\\:')}["'][^>]*>`, 'i').test(html)) fail(`${file}: missing ${property}`);
  }
  for (const name of ['twitter:card', 'twitter:title', 'twitter:description']) {
    if (!new RegExp(`<meta\\s+name=["']${name.replace(':', '\\:')}["'][^>]*>`, 'i').test(html)) fail(`${file}: missing ${name}`);
  }

  const title = attr(html, /<title>([\s\S]*?)<\/title>/i).replace(/<[^>]+>/g, '').trim();
  const description = attr(html, /<meta\s+name=["']description["']\s+content=["']([^"']*)["'][^>]*>/i).trim();
  if (title.length < 20 || title.length > 75) fail(`${file}: title length ${title.length} outside 20–75`);
  if (description.length < 70 || description.length > 190) fail(`${file}: description length ${description.length} outside 70–190`);
  if (titles.has(title)) fail(`${file}: duplicate title with ${titles.get(title)}`); else titles.set(title, file);
  if (descriptions.has(description)) fail(`${file}: duplicate description with ${descriptions.get(description)}`); else descriptions.set(description, file);

  const schemaRaw = attr(html, /<script\s+type=["']application\/ld\+json["']\s+data-resonance-seo=["']true["'][^>]*>([\s\S]*?)<\/script>/i);
  try {
    const schema = JSON.parse(schemaRaw);
    if (schema['@context'] !== 'https://schema.org') fail(`${file}: JSON-LD missing schema.org context`);
    const htmlLang = attr(html, /<html\s+lang=["']([^"']+)["']/i) || 'en';
    const structuredLang = schemaLanguage(schema);
    if (structuredLang && structuredLang !== htmlLang) fail(`${file}: JSON-LD inLanguage ${structuredLang} does not match html lang ${htmlLang}`);
  } catch (error) {
    fail(`${file}: invalid JSON-LD (${error.message})`);
  }

  if (!sitemap.includes(`<loc>${expectedCanonical}</loc>`)) fail(`${file}: missing from sitemap.xml`);
  if (/noindex/i.test(html)) fail(`${file}: unexpected noindex`);
  if (/href=["'](?:index\.html)?#intelligence["']/i.test(html)) fail(`${file}: AI nav still points to fragment instead of topic hub`);
  if (/href=["']index\.html(?:#[^"']*)?["']/i.test(html)) fail(`${file}: internal navigation exposes non-canonical index.html URL`);
}

function verifyAlternates(group, hrefs) {
  for (const file of group) {
    if (!pages.includes(file)) {
      fail(`${file}: multilingual page is missing`);
      continue;
    }
    const html = fs.readFileSync(path.join(DIST, file), 'utf8');
    for (const [language, href] of Object.entries(hrefs)) {
      const escapedLanguage = language.replace('-', '\\-');
      const pattern = new RegExp(`<link\\s+rel=["']alternate["']\\s+hreflang=["']${escapedLanguage}["']\\s+href=["']${href.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}["'][^>]*>`, 'i');
      if (!pattern.test(html)) fail(`${file}: missing hreflang ${language} → ${href}`);
    }
  }
}

verifyAlternates(
  ['index.html', 'index.ru.html', 'index.zh.html'],
  {
    en: BASE,
    ru: `${BASE}index.ru.html`,
    'zh-CN': `${BASE}index.zh.html`,
    'x-default': BASE,
  },
);

verifyAlternates(
  [
    'before-you-let-an-ai-agent-move-money.html',
    'before-you-let-an-ai-agent-move-money.ru.html',
    'before-you-let-an-ai-agent-move-money.zh.html',
  ],
  {
    en: `${BASE}before-you-let-an-ai-agent-move-money.html`,
    ru: `${BASE}before-you-let-an-ai-agent-move-money.ru.html`,
    'zh-CN': `${BASE}before-you-let-an-ai-agent-move-money.zh.html`,
    'x-default': `${BASE}before-you-let-an-ai-agent-move-money.html`,
  },
);

if (!robots.includes(`Sitemap: ${BASE}sitemap.xml`)) fail('robots.txt does not advertise sitemap.xml');
if (!pages.includes('ai-agents.html')) fail('AI Agents topic hub is missing');
if (!pages.includes('open-problems.html')) fail('Open Problems market view is missing');
if (!pages.includes('verified-workflow.html')) fail('Verified Workflow pilot page is missing');

const marketArticle = fs.readFileSync(path.join(DIST, 'before-you-let-an-ai-agent-move-money.html'), 'utf8');
if (!marketArticle.includes('issues/new?template=market-workflow.yml')) fail('Article #004: market workflow intake CTA missing');
if (!marketArticle.includes('market.js')) fail('Article #004: distribution script missing');

const openProblems = fs.readFileSync(path.join(DIST, 'open-problems.html'), 'utf8');
if (!/Real signals[\s\S]*?<strong>0<\/strong>/i.test(openProblems)) fail('Open Problems must start with zero real signals until real evidence is recorded');
if (!/Synthetic example/i.test(openProblems)) fail('Open Problems must visibly label illustrative synthetic patterns');

const hub = fs.readFileSync(path.join(DIST, 'ai-agents.html'), 'utf8');
const hubArticleLinks = count(hub, /href=["'](?:the-|when-|verified-)[^"']+\.html["']/gi);
if (hubArticleLinks < 8) fail(`ai-agents.html: expected at least 8 editorial/research links, found ${hubArticleLinks}`);

if (!process.exitCode) {
  console.log(`RESONANCE publication contract: PASS (${pages.length} pages, ${hubArticleLinks} hub links)`);
}
