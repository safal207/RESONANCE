import fs from 'node:fs';
import path from 'node:path';

const ROOT = process.cwd();
const SITE_DIR = path.join(ROOT, 'site');
const DIST_DIR = path.join(ROOT, 'dist');
const BASE = 'https://safal207.github.io/RESONANCE/';

const metadata = {
  'index.html': {
    title: 'RESONANCE — AI Agents, Trust, Verification & Human Progress',
    description: 'RESONANCE is an independent evidence-first journal covering AI agents, trust, verification, technology, science and human progress.',
    kind: 'website',
  },
  'issue-001.html': {
    title: 'The Age of Agents — AI Agent Trust, Safety & Verification | RESONANCE',
    description: 'RESONANCE Issue 001 explores AI agents, trust, failure, containment, recovery, verification and evidence through analysis, benchmarks and reproducible reports.',
    kind: 'collection',
  },
  'ai-agents.html': {
    title: 'AI Agent Reliability, Security & Verification | RESONANCE',
    description: 'A RESONANCE research hub for AI agent reliability, security, failure taxonomy, containment, recovery, evidence and verification.',
    kind: 'collection',
  },
  'the-agentic-turn.html': {
    title: 'AI Agents: From Chat to Action — The Agentic Turn | RESONANCE',
    kind: 'article',
    keywords: ['AI agents', 'agentic AI', 'AI infrastructure', 'agent verification'],
  },
  'the-missing-trust-layer.html': {
    title: 'AI Agent Trust & Verification Framework — The Missing Trust Layer | RESONANCE',
    kind: 'article',
    keywords: ['AI agent trust', 'agent verification', 'AI reliability', 'agent safety'],
  },
  'when-agents-fail.html': {
    title: 'AI Agent Failure Taxonomy & Benchmark — When Agents Fail | RESONANCE',
    kind: 'article',
    keywords: ['AI agent failures', 'agent failure taxonomy', 'AI agent benchmark', 'agent reliability'],
  },
  'verified-001-openai-agents-sdk.html': {
    title: 'OpenAI Agents SDK Verification Baseline | RESONANCE',
    kind: 'article',
    keywords: ['OpenAI Agents SDK', 'AI agent verification', 'agent benchmark'],
  },
  'verified-002-openai-agents-containment.html': {
    title: 'AI Agent Docker Containment Verification | RESONANCE',
    kind: 'article',
    keywords: ['AI agent containment', 'Docker sandbox', 'agent security'],
  },
  'verified-003-openai-agents-recovery.html': {
    title: 'AI Agent Recovery Under Ambiguity | RESONANCE',
    kind: 'article',
    keywords: ['AI agent recovery', 'idempotency', 'reconciliation', 'agent reliability'],
  },
  'verified-004-openai-agents-ambiguous-reconciliation.html': {
    title: 'AI Agent Ambiguous Reconciliation Verification | RESONANCE',
    kind: 'article',
    keywords: ['AI agent reconciliation', 'uncertainty', 'agent recovery'],
  },
  'verified-005-openai-agents-conflicting-evidence.html': {
    title: 'AI Agent Conflicting Evidence Verification | RESONANCE',
    kind: 'article',
    keywords: ['AI agent evidence', 'conflicting evidence', 'agent verification'],
  },
  'verified-006-openai-agents-evidence-authority.html': {
    title: 'AI Agent Evidence Authority Verification | RESONANCE',
    kind: 'article',
    keywords: ['evidence authority', 'AI agent verification', 'provenance'],
  },
  'verified-007-openai-agents-revoked-authority.html': {
    title: 'AI Agent Revoked Authority Verification | RESONANCE',
    kind: 'article',
    keywords: ['revoked authority', 'AI agent authorization', 'agent verification'],
  },
};

function escapeRegExp(value) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

function canonicalFor(file) {
  return file === 'index.html' ? BASE : `${BASE}${file}`;
}

function textContent(value = '') {
  return value
    .replace(/<script[\s\S]*?<\/script>/gi, ' ')
    .replace(/<style[\s\S]*?<\/style>/gi, ' ')
    .replace(/<[^>]+>/g, ' ')
    .replace(/&amp;/g, '&')
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'")
    .replace(/\s+/g, ' ')
    .trim();
}

function readMetaDescription(html) {
  return html.match(/<meta\s+name=["']description["']\s+content=["']([^"']*)["'][^>]*>/i)?.[1]?.trim() || '';
}

function readH1(html) {
  return textContent(html.match(/<h1[^>]*>([\s\S]*?)<\/h1>/i)?.[1] || '');
}

function readAuthor(html) {
  const match = html.match(/By\s*<strong>([\s\S]*?)<\/strong>/i);
  return textContent(match?.[1] || 'RESONANCE Editorial');
}

function readPublishedDate(html) {
  const match = html.match(/(?:Verified|Executed|Published)\s*·\s*(\d{1,2})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{4})/i);
  if (!match) return null;
  const months = { Jan: '01', Feb: '02', Mar: '03', Apr: '04', May: '05', Jun: '06', Jul: '07', Aug: '08', Sep: '09', Oct: '10', Nov: '11', Dec: '12' };
  return `${match[3]}-${months[match[2][0].toUpperCase() + match[2].slice(1, 3).toLowerCase()]}-${String(match[1]).padStart(2, '0')}`;
}

function stripExistingSeo(html) {
  return html
    .replace(/\n?\s*<!-- SEO:START -->[\s\S]*?<!-- SEO:END -->\s*\n?/i, '\n')
    .replace(/\s*<link\s+rel=["']canonical["'][^>]*>\s*/gi, '\n')
    .replace(/\s*<meta\s+property=["']og:(?:title|description|type|url)["'][^>]*>\s*/gi, '\n')
    .replace(/\s*<meta\s+name=["']twitter:(?:card|title|description)["'][^>]*>\s*/gi, '\n')
    .replace(/\s*<script\s+type=["']application\/ld\+json["']\s+data-resonance-seo=["']true["'][^>]*>[\s\S]*?<\/script>\s*/gi, '\n');
}

function replaceTitle(html, title) {
  if (/<title>[\s\S]*?<\/title>/i.test(html)) {
    return html.replace(/<title>[\s\S]*?<\/title>/i, `<title>${title}</title>`);
  }
  return html.replace('</head>', `  <title>${title}</title>\n</head>`);
}

function replaceDescription(html, description) {
  const escaped = description.replace(/"/g, '&quot;');
  const tag = `<meta name="description" content="${escaped}" />`;
  if (/<meta\s+name=["']description["'][^>]*>/i.test(html)) {
    return html.replace(/<meta\s+name=["']description["'][^>]*>/i, tag);
  }
  return html.replace('</head>', `  ${tag}\n</head>`);
}

function buildSchema(file, html, cfg, canonical, description) {
  const headline = readH1(html) || cfg.title.replace(/\s*\|\s*RESONANCE.*$/i, '');
  const organization = {
    '@type': 'Organization',
    name: 'RESONANCE',
    url: BASE,
    sameAs: ['https://github.com/safal207/RESONANCE'],
  };

  if (cfg.kind === 'website') {
    return {
      '@context': 'https://schema.org',
      '@graph': [
        organization,
        {
          '@type': 'WebSite',
          name: 'RESONANCE',
          url: BASE,
          description,
          publisher: { '@type': 'Organization', name: 'RESONANCE', url: BASE },
          inLanguage: 'en',
        },
      ],
    };
  }

  if (cfg.kind === 'collection') {
    const articleFiles = Object.entries(metadata)
      .filter(([, value]) => value.kind === 'article')
      .map(([name]) => ({ '@type': 'Article', url: canonicalFor(name) }));
    return {
      '@context': 'https://schema.org',
      '@type': 'CollectionPage',
      name: headline,
      url: canonical,
      description,
      isPartOf: { '@type': 'WebSite', name: 'RESONANCE', url: BASE },
      publisher: organization,
      hasPart: articleFiles,
      inLanguage: 'en',
    };
  }

  const schema = {
    '@context': 'https://schema.org',
    '@type': 'Article',
    headline,
    description,
    url: canonical,
    mainEntityOfPage: canonical,
    isPartOf: { '@type': 'CreativeWorkSeries', name: 'RESONANCE Issue 001 — The Age of Agents', url: canonicalFor('issue-001.html') },
    author: { '@type': 'Organization', name: readAuthor(html), url: BASE },
    publisher: organization,
    inLanguage: 'en',
  };
  const published = readPublishedDate(html);
  if (published) schema.datePublished = published;
  if (cfg.keywords?.length) schema.keywords = cfg.keywords;
  return schema;
}

function injectSeo(file, source) {
  const cfg = metadata[file] || {
    title: textContent(source.match(/<title>([\s\S]*?)<\/title>/i)?.[1] || file),
    kind: file === 'index.html' ? 'website' : 'article',
  };
  let html = stripExistingSeo(source);
  const description = cfg.description || readMetaDescription(html) || readH1(html);
  const canonical = canonicalFor(file);
  html = replaceTitle(html, cfg.title);
  html = replaceDescription(html, description);

  // Turn the visual AI anchor into a crawlable topic hub in the deployed build.
  html = html
    .replace(/href=["']#intelligence["']/g, 'href="ai-agents.html"')
    .replace(/href=["']index\.html#intelligence["']/g, 'href="ai-agents.html"');

  const schema = buildSchema(file, html, cfg, canonical, description);
  const safeDescription = description.replace(/"/g, '&quot;');
  const safeTitle = cfg.title.replace(/"/g, '&quot;');
  const seoBlock = `\n  <!-- SEO:START -->\n  <link rel="canonical" href="${canonical}" />\n  <meta property="og:title" content="${safeTitle}" />\n  <meta property="og:description" content="${safeDescription}" />\n  <meta property="og:type" content="${cfg.kind === 'article' ? 'article' : 'website'}" />\n  <meta property="og:url" content="${canonical}" />\n  <meta name="twitter:card" content="summary" />\n  <meta name="twitter:title" content="${safeTitle}" />\n  <meta name="twitter:description" content="${safeDescription}" />\n  <script type="application/ld+json" data-resonance-seo="true">${JSON.stringify(schema)}</script>\n  <!-- SEO:END -->\n`;
  return html.replace('</head>', `${seoBlock}</head>`);
}

fs.rmSync(DIST_DIR, { recursive: true, force: true });
fs.cpSync(SITE_DIR, DIST_DIR, { recursive: true });

const htmlFiles = fs.readdirSync(SITE_DIR).filter((name) => name.endsWith('.html')).sort();
for (const file of htmlFiles) {
  const source = fs.readFileSync(path.join(SITE_DIR, file), 'utf8');
  fs.writeFileSync(path.join(DIST_DIR, file), injectSeo(file, source));
}

const urls = htmlFiles.map(canonicalFor);
const sitemap = `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${urls.map((url) => `  <url><loc>${url}</loc></url>`).join('\n')}\n</urlset>\n`;
fs.writeFileSync(path.join(DIST_DIR, 'sitemap.xml'), sitemap);

const robots = `User-agent: *\nAllow: /\n\nSitemap: ${BASE}sitemap.xml\n`;
fs.writeFileSync(path.join(DIST_DIR, 'robots.txt'), robots);

console.log(`RESONANCE SEO build: ${htmlFiles.length} HTML pages → dist/`);
