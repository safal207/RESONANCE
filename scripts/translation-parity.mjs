#!/usr/bin/env node

import fs from 'node:fs';
import path from 'node:path';
import process from 'node:process';

const args = process.argv.slice(2);
const arg = (name, fallback) => {
  const index = args.indexOf(name);
  return index >= 0 && args[index + 1] ? args[index + 1] : fallback;
};

const root = path.resolve(arg('--root', 'dist'));
const outputDir = path.resolve(arg('--output', 'translation-parity-results'));
const enforce = args.includes('--enforce');
const BASE = 'https://safal207.github.io/RESONANCE/';

const groups = [
  {
    id: 'homepage',
    profile: 'locale-shell',
    files: { en: 'index.html', ru: 'index.ru.html', 'zh-CN': 'index.zh.html' },
  },
  {
    id: 'article004',
    profile: 'article-semantic',
    files: {
      en: 'before-you-let-an-ai-agent-move-money.html',
      ru: 'before-you-let-an-ai-agent-move-money.ru.html',
      'zh-CN': 'before-you-let-an-ai-agent-move-money.zh.html',
    },
  },
  {
    id: 'article005',
    profile: 'article-semantic',
    files: {
      en: 'memory-can-be-true-and-still-be-unsafe.html',
      ru: 'memory-can-be-true-and-still-be-unsafe.ru.html',
      'zh-CN': 'memory-can-be-true-and-still-be-unsafe.zh.html',
    },
  },
];

const markerClasses = [
  'pull-quote',
  'trajectory-box',
  'claim-panel',
  'verification-chain',
  'market-kpi',
  'market-question',
  'market-prompts',
  'market-actions',
  'protocol-flow',
  'share-panel',
  'sources-block',
];

function attrs(tag) {
  const result = {};
  for (const match of tag.matchAll(/([:\w-]+)\s*=\s*(["'])([\s\S]*?)\2/g)) {
    result[match[1].toLowerCase()] = match[3];
  }
  return result;
}

function allTags(html, name) {
  return [...html.matchAll(new RegExp(`<${name}\\b[^>]*>`, 'gi'))].map((match) => ({ tag: match[0], attrs: attrs(match[0]) }));
}

function classCount(html, className) {
  let total = 0;
  for (const match of html.matchAll(/<[^>]+\bclass\s*=\s*(["'])([^"']+)\1[^>]*>/gi)) {
    if (match[2].split(/\s+/).includes(className)) total += 1;
  }
  return total;
}

function idCount(html, id) {
  return [...html.matchAll(new RegExp(`\\bid\\s*=\\s*(["'])${id}\\1`, 'gi'))].length;
}

function normalizeLocalHref(href) {
  const withoutFragment = (href || '').split('#')[0].split('?')[0];
  const cleaned = withoutFragment.replace(/^\.\//, '');
  if (!cleaned || cleaned === 'index.html') return 'index.html';
  return cleaned;
}

function canonicalFor(file) {
  return file === 'index.html' ? BASE : `${BASE}${file}`;
}

function alternates(html) {
  const result = {};
  for (const item of allTags(html, 'link')) {
    if ((item.attrs.rel || '').toLowerCase() !== 'alternate') continue;
    if (!item.attrs.hreflang || !item.attrs.href) continue;
    result[item.attrs.hreflang] = item.attrs.href;
  }
  return result;
}

function currentCanonical(html) {
  for (const item of allTags(html, 'link')) {
    if ((item.attrs.rel || '').toLowerCase() === 'canonical') return item.attrs.href || '';
  }
  return '';
}

function switcher(html) {
  const match = html.match(/<div\b[^>]*class=["'][^"']*\blanguage-switcher\b[^"']*["'][^>]*>([\s\S]*?)<\/div>/i);
  if (!match) return [];
  return allTags(match[1], 'a').map((item) => ({
    href: item.attrs.href || '',
    hreflang: item.attrs.hreflang || '',
    current: (item.attrs['aria-current'] || '').toLowerCase() === 'page',
  }));
}

function htmlLanguage(html) {
  const tag = html.match(/<html\b[^>]*>/i)?.[0] || '';
  return attrs(tag).lang || '';
}

function articleBody(html) {
  return html.match(/<article\b[^>]*class=["'][^"']*\barticle-body\b[^"']*["'][^>]*>([\s\S]*?)<\/article>/i)?.[1] || '';
}

function semanticOutline(body) {
  const tokens = [];
  const regex = /<(h2|h3|section|div|ul)\b([^>]*)>/gi;
  for (const match of body.matchAll(regex)) {
    const tag = match[1].toLowerCase();
    if (tag === 'h2' || tag === 'h3') {
      tokens.push(tag);
      continue;
    }
    const classes = (attrs(match[0]).class || '').split(/\s+/).filter(Boolean);
    const marker = markerClasses.find((candidate) => classes.includes(candidate));
    if (marker) tokens.push(`${tag}.${marker}`);
  }
  return tokens;
}

function ids(body) {
  return [...new Set([...body.matchAll(/\bid\s*=\s*(["'])([^"']+)\1/gi)].map((match) => match[2]))].sort();
}

function sectionByClass(body, className) {
  const pattern = new RegExp(`<section\\b[^>]*class=["'][^"']*\\b${className}\\b[^"']*["'][^>]*>([\\s\\S]*?)<\\/section>`, 'i');
  return body.match(pattern)?.[1] || '';
}

function anchorHrefs(html, classNames = null) {
  const hrefs = [];
  for (const item of allTags(html, 'a')) {
    if (!item.attrs.href) continue;
    if (classNames) {
      const classes = (item.attrs.class || '').split(/\s+/).filter(Boolean);
      if (!classNames.some((name) => classes.includes(name))) continue;
    }
    hrefs.push(item.attrs.href);
  }
  return hrefs;
}

function scriptSources(html) {
  return allTags(html, 'script').map((item) => item.attrs.src).filter(Boolean).sort();
}

function articleIdentity(html) {
  return html.match(/Issue\s+\d+\s*·\s*Article\s+\d+/i)?.[0].replace(/\s+/g, ' ') || '';
}

function equalArray(a, b) {
  return a.length === b.length && a.every((value, index) => value === b[index]);
}

function firstDiff(a, b) {
  const length = Math.max(a.length, b.length);
  for (let index = 0; index < length; index += 1) {
    if (a[index] !== b[index]) return { index, expected: a[index] ?? '<missing>', actual: b[index] ?? '<missing>' };
  }
  return null;
}

function expectedAlternates(group) {
  return {
    en: canonicalFor(group.files.en),
    ru: canonicalFor(group.files.ru),
    'zh-CN': canonicalFor(group.files['zh-CN']),
    'x-default': canonicalFor(group.files.en),
  };
}

function inspect(file) {
  const filePath = path.join(root, file);
  if (!fs.existsSync(filePath)) return { file, missing: true };
  const html = fs.readFileSync(filePath, 'utf8');
  const body = articleBody(html);
  const marketQuestion = body ? sectionByClass(body, 'market-question') : '';
  const sourcesBlock = body ? sectionByClass(body, 'sources-block') : '';
  return {
    file,
    missing: false,
    htmlLang: htmlLanguage(html),
    canonical: currentCanonical(html),
    alternates: alternates(html),
    switcher: switcher(html),
    scripts: scriptSources(html),
    articleIdentity: articleIdentity(html),
    hasArticleBody: Boolean(body),
    outline: body ? semanticOutline(body) : [],
    ids: body ? ids(body) : [],
    ctas: marketQuestion ? anchorHrefs(marketQuestion, ['button', 'text-link']) : [],
    sources: sourcesBlock ? anchorHrefs(sourcesBlock) : [],
    shell: {
      skipLinks: classCount(html, 'skip-link'),
      menuToggles: classCount(html, 'menu-toggle'),
      mainNavs: idCount(html, 'main-nav'),
      railCards: classCount(html, 'rail-card'),
    },
  };
}

if (!fs.existsSync(root)) {
  console.error(`Translation parity root does not exist: ${root}`);
  process.exit(2);
}
fs.mkdirSync(outputDir, { recursive: true });

const failures = [];
const results = [];

for (const group of groups) {
  const inspected = Object.fromEntries(Object.entries(group.files).map(([lang, file]) => [lang, inspect(file)]));
  const groupFailures = [];
  const expectedAlts = expectedAlternates(group);

  for (const [lang, file] of Object.entries(group.files)) {
    const page = inspected[lang];
    if (page.missing) {
      groupFailures.push(`${group.id}/${lang}: managed translation is missing (${file})`);
      continue;
    }
    if (page.htmlLang !== lang) groupFailures.push(`${group.id}/${lang}: html lang ${page.htmlLang || '<missing>'} != ${lang}`);
    if (page.canonical !== canonicalFor(file)) groupFailures.push(`${group.id}/${lang}: canonical mismatch (${page.canonical || '<missing>'})`);

    for (const [altLang, href] of Object.entries(expectedAlts)) {
      if (page.alternates[altLang] !== href) groupFailures.push(`${group.id}/${lang}: hreflang ${altLang} != ${href}`);
    }

    const links = page.switcher;
    if (links.length !== 3) groupFailures.push(`${group.id}/${lang}: language switcher must contain exactly 3 links`);
    const expectedSwitcher = Object.entries(group.files).map(([switchLang, switchFile]) => ({ hreflang: switchLang, href: switchFile }));
    for (const expected of expectedSwitcher) {
      const link = links.find((candidate) => candidate.hreflang === expected.hreflang);
      if (!link) {
        groupFailures.push(`${group.id}/${lang}: language switcher missing ${expected.hreflang}`);
        continue;
      }
      if (normalizeLocalHref(link.href) !== normalizeLocalHref(expected.href)) {
        groupFailures.push(`${group.id}/${lang}: switcher ${expected.hreflang} href ${link.href || '<missing>'} != ${expected.href}`);
      }
      if (expected.hreflang === lang && !link.current) groupFailures.push(`${group.id}/${lang}: current-language switcher link is not aria-current=page`);
      if (expected.hreflang !== lang && link.current) groupFailures.push(`${group.id}/${lang}: non-current ${expected.hreflang} switcher link is marked current`);
    }
  }

  if (group.profile === 'article-semantic' && !Object.values(inspected).some((page) => page.missing)) {
    const reference = inspected.en;
    if (!reference.hasArticleBody) groupFailures.push(`${group.id}/en: article-body missing`);
    if (!reference.articleIdentity) groupFailures.push(`${group.id}/en: Issue/Article identity missing`);
    if (!reference.sources.length) groupFailures.push(`${group.id}/en: sources block has no links`);
    if (!reference.ctas.length) groupFailures.push(`${group.id}/en: market CTA block has no critical links`);

    for (const lang of ['ru', 'zh-CN']) {
      const page = inspected[lang];
      if (!page.hasArticleBody) groupFailures.push(`${group.id}/${lang}: article-body missing`);
      if (page.articleIdentity !== reference.articleIdentity) {
        groupFailures.push(`${group.id}/${lang}: article identity ${page.articleIdentity || '<missing>'} != ${reference.articleIdentity || '<missing>'}`);
      }
      if (JSON.stringify(page.shell) !== JSON.stringify(reference.shell)) {
        groupFailures.push(`${group.id}/${lang}: article shell drift (${JSON.stringify(page.shell)} != ${JSON.stringify(reference.shell)})`);
      }
      if (!equalArray(reference.outline, page.outline)) {
        const diff = firstDiff(reference.outline, page.outline);
        groupFailures.push(`${group.id}/${lang}: semantic outline drift at token ${diff.index} (${diff.actual} != ${diff.expected})`);
      }
      if (!equalArray(reference.ids, page.ids)) {
        groupFailures.push(`${group.id}/${lang}: critical id set drift (${page.ids.join(', ') || '<none>'} != ${reference.ids.join(', ') || '<none>'})`);
      }
      if (!equalArray(reference.ctas, page.ctas)) {
        groupFailures.push(`${group.id}/${lang}: CTA destination drift (${page.ctas.join(' | ') || '<none>'})`);
      }
      if (!equalArray(reference.sources, page.sources)) groupFailures.push(`${group.id}/${lang}: primary/evidence source-link drift`);
      if (!equalArray(reference.scripts, page.scripts)) {
        groupFailures.push(`${group.id}/${lang}: runtime script set drift (${page.scripts.join(', ') || '<none>'} != ${reference.scripts.join(', ') || '<none>'})`);
      }
    }
  }

  failures.push(...groupFailures);
  results.push({
    id: group.id,
    profile: group.profile,
    verdict: groupFailures.length ? 'fail' : 'pass',
    files: group.files,
    pages: inspected,
    failures: groupFailures,
  });
}

const summary = {
  schema: 'resonance.site-health.translation-parity.v1',
  version: 'v0.4',
  generatedAt: new Date().toISOString(),
  auditedCommit: process.env.GITHUB_SHA || null,
  sourceRunId: process.env.GITHUB_RUN_ID || null,
  managedGroups: groups.map((group) => group.id),
  verdict: failures.length ? 'fail' : 'pass',
  failures,
  results,
  evidenceBoundary: 'Structural and destination parity only; this contract does not prove linguistic translation quality or semantic equivalence of prose.',
};

fs.writeFileSync(path.join(outputDir, 'translation-parity-summary.json'), `${JSON.stringify(summary, null, 2)}\n`);

const rows = results.map((group) => {
  const en = group.pages.en;
  const ru = group.pages.ru;
  const zh = group.pages['zh-CN'];
  const outline = group.profile === 'article-semantic' ? `${en.outline.length}/${ru.outline.length}/${zh.outline.length}` : 'shell';
  const ctas = group.profile === 'article-semantic' ? `${en.ctas.length}/${ru.ctas.length}/${zh.ctas.length}` : 'n/a';
  const sources = group.profile === 'article-semantic' ? `${en.sources.length}/${ru.sources.length}/${zh.sources.length}` : 'n/a';
  return `| ${group.id} | ${group.profile} | ${outline} | ${ctas} | ${sources} | ${group.verdict.toUpperCase()} |`;
});

const markdown = [
  '# RESONANCE Translation Parity Contract',
  '',
  `**Verdict:** ${summary.verdict.toUpperCase()}`,
  '',
  '| Managed group | Profile | Outline tokens EN/RU/ZH | CTA links EN/RU/ZH | Source links EN/RU/ZH | Verdict |',
  '|---|---|---:|---:|---:|---|',
  ...rows,
  '',
  '## Release invariants',
  '',
  '- EN / RU / zh-CN managed siblings must all exist and declare the correct `html lang`.',
  '- Canonical and reciprocal `hreflang` mappings must point to the same managed triplet.',
  '- The visible language switcher must contain EN / RU / zh-CN and mark only the current locale with `aria-current="page"`.',
  '- Article siblings must preserve the same shell controls/rail count and the same major semantic outline: heading levels plus evidence, trajectory, market-question, distribution and source blocks.',
  '- Article identity, critical IDs, CTA destinations, primary/evidence source URLs and runtime script set must not drift across translations.',
  '',
  '## Evidence boundary',
  '',
  'Passing this contract proves structural/destination parity for the managed triplets. It does **not** prove that translated prose is linguistically excellent, complete in nuance, or semantically equivalent sentence by sentence.',
  '',
  ...(failures.length ? ['## Hard failures', '', ...failures.map((failure) => `- ${failure}`), ''] : []),
].join('\n');

fs.writeFileSync(path.join(outputDir, 'translation-parity-summary.md'), `${markdown}\n`);
console.log(markdown);

if (enforce && failures.length) process.exit(1);
