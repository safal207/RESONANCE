import fs from 'node:fs';
import path from 'node:path';

const BASE = 'https://safal207.github.io/RESONANCE/';

const existingWebRoutes = new Map([
  ['01-the-agentic-turn.md', 'the-agentic-turn.html'],
  ['02-the-missing-trust-layer.md', 'the-missing-trust-layer.html'],
  ['03-when-agents-fail.md', 'when-agents-fail.html'],
  ['13-evidence-must-bind-the-transition.md', 'evidence-must-bind-the-transition.ru.html'],
]);

function escapeHtml(value = '') {
  return String(value)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function stripMarkdown(value = '') {
  return String(value)
    .replace(/!\[([^\]]*)\]\([^)]*\)/g, '$1')
    .replace(/\[([^\]]+)\]\([^)]*\)/g, '$1')
    .replace(/[`*_>#~]/g, '')
    .replace(/\s+/g, ' ')
    .trim();
}

function inline(value = '') {
  let text = escapeHtml(value);
  const placeholders = [];
  const stash = (html) => {
    const token = `@@R${placeholders.length}@@`;
    placeholders.push(html);
    return token;
  };

  text = text.replace(/`([^`]+)`/g, (_, code) => stash(`<code>${escapeHtml(code)}</code>`));
  text = text.replace(/\[([^\]]+)\]\((https?:\/\/[^)]+)\)/g, (_, label, href) => stash(`<a href="${escapeHtml(href)}" target="_blank" rel="noreferrer">${escapeHtml(label)}</a>`));
  text = text.replace(/\[([^\]]+)\]\(([^)]+)\)/g, (_, label, href) => stash(`<a href="${escapeHtml(href)}">${escapeHtml(label)}</a>`));
  text = text.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
  text = text.replace(/__([^_]+)__/g, '<strong>$1</strong>');
  text = text.replace(/(?<!\*)\*([^*]+)\*(?!\*)/g, '<em>$1</em>');
  text = text.replace(/~~([^~]+)~~/g, '<del>$1</del>');
  text = text.replace(/@@R(\d+)@@/g, (_, index) => placeholders[Number(index)] || '');
  return text;
}

function renderTable(lines) {
  const rows = lines.map((line) => line.trim().replace(/^\||\|$/g, '').split('|').map((cell) => cell.trim()));
  if (rows.length < 2) return '';
  const headers = rows[0];
  const body = rows.slice(2);
  return `<div class="table-wrap"><table><thead><tr>${headers.map((cell) => `<th>${inline(cell)}</th>`).join('')}</tr></thead><tbody>${body.map((row) => `<tr>${row.map((cell) => `<td>${inline(cell)}</td>`).join('')}</tr>`).join('')}</tbody></table></div>`;
}

function renderMarkdown(markdown) {
  const lines = markdown.replace(/\r\n/g, '\n').split('\n');
  const out = [];
  let index = 0;
  let firstHeadingSkipped = false;

  const flushParagraph = (parts) => {
    const content = parts.map((part) => part.trim()).filter(Boolean).join(' ');
    if (content) out.push(`<p>${inline(content)}</p>`);
  };

  while (index < lines.length) {
    const line = lines[index];
    const trimmed = line.trim();

    if (!trimmed) {
      index += 1;
      continue;
    }

    if (trimmed.startsWith('```')) {
      const language = trimmed.slice(3).trim();
      const code = [];
      index += 1;
      while (index < lines.length && !lines[index].trim().startsWith('```')) {
        code.push(lines[index]);
        index += 1;
      }
      index += 1;
      out.push(`<pre><code${language ? ` class="language-${escapeHtml(language)}"` : ''}>${escapeHtml(code.join('\n'))}</code></pre>`);
      continue;
    }

    const heading = trimmed.match(/^(#{1,6})\s+(.+)$/);
    if (heading) {
      const level = heading[1].length;
      if (level === 1 && !firstHeadingSkipped) {
        firstHeadingSkipped = true;
      } else {
        out.push(`<h${Math.max(2, Math.min(6, level))}>${inline(heading[2])}</h${Math.max(2, Math.min(6, level))}>`);
      }
      index += 1;
      continue;
    }

    if (/^---+$/.test(trimmed)) {
      out.push('<hr />');
      index += 1;
      continue;
    }

    if (trimmed.startsWith('>')) {
      const quote = [];
      while (index < lines.length && lines[index].trim().startsWith('>')) {
        quote.push(lines[index].trim().replace(/^>\s?/, ''));
        index += 1;
      }
      out.push(`<blockquote><p>${inline(quote.join(' '))}</p></blockquote>`);
      continue;
    }

    if (trimmed.includes('|') && index + 1 < lines.length && /^\s*\|?\s*:?-{3,}/.test(lines[index + 1])) {
      const table = [line, lines[index + 1]];
      index += 2;
      while (index < lines.length && lines[index].includes('|') && lines[index].trim()) {
        table.push(lines[index]);
        index += 1;
      }
      out.push(renderTable(table));
      continue;
    }

    const unordered = trimmed.match(/^[-*+]\s+(.+)$/);
    if (unordered) {
      const items = [];
      while (index < lines.length) {
        const match = lines[index].trim().match(/^[-*+]\s+(.+)$/);
        if (!match) break;
        items.push(match[1]);
        index += 1;
      }
      out.push(`<ul>${items.map((item) => `<li>${inline(item)}</li>`).join('')}</ul>`);
      continue;
    }

    const ordered = trimmed.match(/^\d+[.)]\s+(.+)$/);
    if (ordered) {
      const items = [];
      while (index < lines.length) {
        const match = lines[index].trim().match(/^\d+[.)]\s+(.+)$/);
        if (!match) break;
        items.push(match[1]);
        index += 1;
      }
      out.push(`<ol>${items.map((item) => `<li>${inline(item)}</li>`).join('')}</ol>`);
      continue;
    }

    const paragraph = [line];
    index += 1;
    while (index < lines.length) {
      const next = lines[index].trim();
      if (!next || /^(#{1,6})\s+/.test(next) || next.startsWith('```') || next.startsWith('>') || /^[-*+]\s+/.test(next) || /^\d+[.)]\s+/.test(next) || /^---+$/.test(next)) break;
      if (next.includes('|') && index + 1 < lines.length && /^\s*\|?\s*:?-{3,}/.test(lines[index + 1])) break;
      paragraph.push(lines[index]);
      index += 1;
    }
    flushParagraph(paragraph);
  }

  return out.join('\n');
}

function metadataValue(markdown, key) {
  const escaped = key.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const match = markdown.match(new RegExp(`^\\*\\*${escaped}:\\*\\*\\s*(.+?)\\s*$`, 'mi'));
  return stripMarkdown(match?.[1] || '');
}

function titleFrom(markdown, fallback) {
  return stripMarkdown(markdown.match(/^#\s+(.+)$/m)?.[1] || fallback);
}

function descriptionFrom(markdown, title) {
  const deck = metadataValue(markdown, 'Deck');
  let description = deck;
  if (!description) {
    const candidates = markdown
      .split(/\n\s*\n/)
      .map(stripMarkdown)
      .filter((value) => value.length >= 70 && !value.startsWith('Article ID:') && !value.startsWith(title));
    description = candidates[0] || `${title}. RESONANCE Issue 001 — The Age of Agents.`;
  }
  if (description.length > 180) description = `${description.slice(0, 176).replace(/\s+\S*$/, '')}…`;
  if (description.length < 70) description = `${description} RESONANCE исследует причинные границы, доказательства и надёжность автономных AI-систем.`;
  return description.slice(0, 190);
}

function seoTitle(number, title) {
  const compact = title.split(/\s+—\s+/)[0].trim();
  const prefix = `Article ${number}: `;
  const suffix = ' | RESONANCE';
  const maxCore = 72 - prefix.length - suffix.length;
  const core = compact.length > maxCore ? `${compact.slice(0, maxCore - 1).trim()}…` : compact;
  return `${prefix}${core}${suffix}`;
}

function detectLanguage(markdown) {
  const explicit = metadataValue(markdown, 'Languages').toLowerCase();
  if (explicit.includes('ru')) return 'ru';
  if (explicit.includes('zh')) return 'zh-CN';
  const letters = markdown.match(/[A-Za-zА-Яа-яЁё]/g) || [];
  const cyrillic = markdown.match(/[А-Яа-яЁё]/g) || [];
  return letters.length && cyrillic.length / letters.length > 0.16 ? 'ru' : 'en';
}

function publicationDates(issueReadme) {
  const dates = new Map();
  for (const line of issueReadme.split('\n')) {
    const match = line.match(/\]\(articles\/([^)]*?\.md)\).*?published\s+(\d{4}-\d{2}-\d{2})/i);
    if (match) dates.set(match[1], match[2]);
  }
  return dates;
}

function routeFor(filename) {
  const explicit = existingWebRoutes.get(filename);
  if (explicit) return explicit;
  return `article-${filename.replace(/\.md$/, '')}.html`;
}

function template({ number, title, seo, description, language, published, body, markdownPath, sourcesPath }) {
  const label = language === 'ru' ? 'Статья' : 'Article';
  const issueLabel = language === 'ru' ? 'Выпуск 001 · Эпоха агентов' : 'Issue 001 · The Age of Agents';
  const back = language === 'ru' ? '← Issue 001 · The Age of Agents' : '← Issue 001 · The Age of Agents';
  const sourceLabel = language === 'ru' ? 'Исходник и доказательства' : 'Source & evidence';
  const publishedText = published ? `Published · ${published}` : 'Published';
  return `<!doctype html>
<html lang="${escapeHtml(language)}">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <meta name="description" content="${escapeHtml(description)}" />
  ${published ? `<meta property="article:published_time" content="${published}" />` : ''}
  <title>${escapeHtml(seo)}</title>
  <link rel="stylesheet" href="styles.css" />
  <link rel="stylesheet" href="article.css" />
  <link rel="stylesheet" href="market.css" />
</head>
<body>
  <a class="skip-link" href="#article">${language === 'ru' ? 'К статье' : 'Skip to article'}</a>
  <header class="site-header">
    <div class="masthead wrap">
      <a class="brand" href="${language === 'ru' ? 'index.ru.html' : './'}" aria-label="RESONANCE home">RESONANCE</a>
      <p class="masthead-line">Journal of Intelligence, Technology & Human Progress</p>
      <button class="menu-toggle" type="button" aria-expanded="false" aria-controls="main-nav">Menu</button>
    </div>
    <nav class="nav wrap" id="main-nav" aria-label="Navigation">
      <a href="ai-agents.html">AI</a>
      <a href="science.html">Science</a>
      <a href="open-problems.html">Open Problems</a>
      <a href="verified-workflow.html">Verified Workflow</a>
      <a href="issue-001.html">Issue 001</a>
    </nav>
  </header>
  <main id="article">
    <header class="article-hero wrap">
      <a class="back-link" href="issue-001.html">${back}</a>
      <div class="article-meta-row">
        <p class="section-label">${label} #${escapeHtml(number)} · ${issueLabel}</p>
        <p class="article-status">${escapeHtml(publishedText)}</p>
      </div>
      <h1 class="article-title">${escapeHtml(title)}</h1>
      <p class="article-dek">${escapeHtml(description)}</p>
      <div class="byline-row"><p>By <strong>RESONANCE Editorial</strong></p><p>${issueLabel}</p></div>
    </header>
    <div class="article-layout wrap">
      <aside class="article-rail" aria-label="Article identity">
        <div class="rail-card rail-dark"><p class="section-label">Issue 001</p><strong>THE AGE OF AGENTS</strong><span>Evidence-first research on autonomous systems.</span></div>
        <div class="rail-card"><p class="section-label">Canonical source</p><a href="${escapeHtml(markdownPath)}" target="_blank" rel="noreferrer">Markdown ↗</a>${sourcesPath ? `<br /><a href="${escapeHtml(sourcesPath)}" target="_blank" rel="noreferrer">Evidence ledger ↗</a>` : ''}</div>
      </aside>
      <article class="article-body generated-markdown-article">
${body}
        <section class="sources-block">
          <p class="section-label">${sourceLabel}</p>
          <p><a href="${escapeHtml(markdownPath)}" target="_blank" rel="noreferrer">Canonical article source on GitHub ↗</a></p>
          ${sourcesPath ? `<p><a href="${escapeHtml(sourcesPath)}" target="_blank" rel="noreferrer">Dedicated evidence ledger ↗</a></p>` : ''}
        </section>
      </article>
    </div>
  </main>
  <footer class="site-footer"><div class="wrap footer-grid"><div><div class="brand footer-brand">RESONANCE</div><p>Find the signal. Verify the path. Understand the future.</p></div><div><p class="footer-title">Issue 001</p><p>The Age of Agents · Article ${escapeHtml(number)}</p></div><div><p>© <span id="year">2026</span> RESONANCE</p></div></div></footer>
  <script src="app.js"></script>
</body>
</html>`;
}

export function buildIssueWebArticles({ rootDir = process.cwd(), distDir = path.join(rootDir, 'dist') } = {}) {
  const articlesDir = path.join(rootDir, 'issues', '001-age-of-agents', 'articles');
  const issueReadmePath = path.join(rootDir, 'issues', '001-age-of-agents', 'README.md');
  if (!fs.existsSync(articlesDir) || !fs.existsSync(distDir)) return [];

  const issueReadme = fs.existsSync(issueReadmePath) ? fs.readFileSync(issueReadmePath, 'utf8') : '';
  const dates = publicationDates(issueReadme);
  const files = fs.readdirSync(articlesDir)
    .filter((name) => /^\d{2}-.*\.md$/.test(name) && !name.endsWith('.sources.md'))
    .sort();
  const generated = [];

  for (const filename of files) {
    const explicitRoute = existingWebRoutes.get(filename);
    if (explicitRoute && fs.existsSync(path.join(distDir, explicitRoute))) continue;

    const markdown = fs.readFileSync(path.join(articlesDir, filename), 'utf8');
    const number = filename.match(/^(\d{2})-/)?.[1] || '00';
    const title = titleFrom(markdown, filename.replace(/\.md$/, ''));
    const description = descriptionFrom(markdown, title);
    const language = detectLanguage(markdown);
    const published = dates.get(filename) || metadataValue(markdown, 'Published') || metadataValue(markdown, 'Last verified') || '';
    const route = routeFor(filename);
    const sourceUrl = `https://github.com/safal207/RESONANCE/blob/main/issues/001-age-of-agents/articles/${encodeURIComponent(filename)}`;
    const sourcesFilename = filename.replace(/\.md$/, '.sources.md');
    const sourcesExists = fs.existsSync(path.join(articlesDir, sourcesFilename));
    const sourcesUrl = sourcesExists ? `https://github.com/safal207/RESONANCE/blob/main/issues/001-age-of-agents/articles/${encodeURIComponent(sourcesFilename)}` : '';
    const html = template({
      number,
      title,
      seo: seoTitle(number, title),
      description,
      language,
      published,
      body: renderMarkdown(markdown),
      markdownPath: sourceUrl,
      sourcesPath: sourcesUrl,
    });
    fs.writeFileSync(path.join(distDir, route), html);
    generated.push({ filename, route, language, published, title });
  }

  console.log(`RESONANCE Issue 001 web publisher: ${generated.length} generated article pages (${files.length} canonical markdown articles scanned)`);
  return generated;
}

if (process.argv[1] && path.resolve(process.argv[1]) === path.resolve(new URL(import.meta.url).pathname)) {
  buildIssueWebArticles();
}
