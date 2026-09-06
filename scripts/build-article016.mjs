import fs from 'node:fs';
import path from 'node:path';
import { renderMarkdown } from './build-issue-web-articles.mjs';

const slug = 'how-repositories-constrain-hallucinations';
const stem = `16-${slug}`;
const articleDir = 'issues/001-age-of-agents/articles';
const base = 'https://safal207.github.io/RESONANCE/';
const git = 'https://github.com/safal207/RESONANCE/blob/main/';
const routes = { en: `${slug}.html`, ru: `${slug}.ru.html`, 'zh-CN': `${slug}.zh.html` };
const sources = [
  ['S1', 'Lewis et al. · Retrieval-Augmented Generation · 2020', 'https://arxiv.org/abs/2005.11401'],
  ['S2', 'Min et al. · FActScore · EMNLP 2023', 'https://aclanthology.org/2023.emnlp-main.741/'],
  ['S3', 'CML · approval-lineage example · 7a3a98c', 'https://github.com/safal207/Causal-Memory-Layer/blob/7a3a98c60a402d394e4d286da956823898454b8a/examples/agent_approval_lineage_audit.py'],
  ['S4', 'ContractGraph-QA · payment-recovery evaluator · f861b93', 'https://github.com/safal207/ContractGraph-QA/blob/f861b934d77e64fd35f768e2a33bb4a00963bc19/contractgraph_qa/payment_recovery.py'],
  ['S5', 'PythiaLabs · limitations · dadc0f1', 'https://github.com/safal207/pythiaLabs/blob/dadc0f18a0c4e5d65fe50a3bab32ee34512975b9/docs/LIMITATIONS.md'],
  ['S6', 'LiminalQA · typed decisions · fb1fc77', 'https://github.com/safal207/LiminalQAengineer/blob/fb1fc7771e7ba29d4edc30ee38b09b4d9dce3c86/liminalqa-core/src/decision.rs'],
  ['S7', 'RESONANCE · Article 016 · native replay JSON', `${git}evidence/article016/native-replay.json`],
];
const locale = {
  en: {
    source: `${articleDir}/translations/${stem}.en.md`, home: 'index.html',
    skip: 'Read the article', nav: 'Navigation', menu: 'Menu', language: 'Language',
    back: '← Issue 001 · The Age of Agents', label: 'Article #016 · Agent reliability',
    published: 'Published · 6 Sep 2026', author: 'By Aleksei Safonov',
    rail: 'Evidence and scope', result: 'Local reproduction', six: '6 seed cases',
    resultText: 'Three positive cases pass. Three negative cases are detected. No LLM was called.',
    boundary: 'Measurement boundary', boundaryText: 'The reduction in model hallucinations has not yet been measured.',
    replay: 'Reproduce the evidence', replayText: 'Inspect the preregistered plan, replay runner and full native output.',
    plan: 'Reproduction plan', runner: 'Replay runner', output: 'Native results',
    sourceLabel: 'Sources and evidence', ledger: 'Claim and source ledger', text: 'Article source',
    table: 'Article table; scroll horizontally if needed',
    sourceTitle: 'How to Reduce AI Hallucinations with Evidence | RESONANCE',
  },
  ru: {
    source: `${articleDir}/${stem}.md`, home: 'index.ru.html',
    skip: 'К статье', nav: 'Навигация', menu: 'Меню', language: 'Язык',
    back: '← Выпуск 001 · Эпоха агентов', label: 'Статья #016 · Надёжность агентов',
    published: 'Опубликовано · 6 сен 2026', author: 'Автор: Алексей Сафонов',
    rail: 'Доказательства и границы', result: 'Локальное воспроизведение', six: '6 сценариев',
    resultText: 'Три положительных случая проходят. Три негативных обнаружены. LLM не вызывалась.',
    boundary: 'Граница измерения', boundaryText: 'Снижение галлюцинаций модели пока не измерено.',
    replay: 'Воспроизвести доказательства', replayText: 'Откройте предварительный план, скрипт воспроизведения и полный вывод проверяющих компонентов.',
    plan: 'План воспроизведения', runner: 'Скрипт воспроизведения', output: 'Результаты компонентов',
    sourceLabel: 'Источники и доказательства', ledger: 'Реестр утверждений и источников', text: 'Исходный текст',
    table: 'Таблица статьи; при необходимости прокручивается по горизонтали',
    sourceTitle: 'Как уменьшить галлюцинации AI через доказательства | RESONANCE',
  },
  'zh-CN': {
    source: `${articleDir}/translations/${stem}.zh.md`, home: 'index.zh.html',
    skip: '阅读文章', nav: '导航', menu: '菜单', language: '语言',
    back: '← 第 001 期 · 智能体时代', label: '第 016 篇 · 智能体可靠性',
    published: '发布 · 2026年9月6日', author: '作者：Aleksei Safonov',
    rail: '证据与范围', result: '本地复现', six: '6 个案例',
    resultText: '三个正例通过，三个反例被发现。没有调用 LLM。',
    boundary: '测量边界', boundaryText: '模型幻觉率的降低尚未测量。',
    replay: '重放证据', replayText: '查看预先记录的计划、重放脚本和完整的原生输出。',
    plan: '复现计划', runner: '重放脚本', output: '原生结果',
    sourceLabel: '来源与证据', ledger: '断言与来源登记表', text: '文章源文件',
    table: '文章表格；需要时可水平滚动',
    sourceTitle: '如何减少 AI 幻觉：证据、检查与可验证结果 | RESONANCE',
  },
};

const esc = (v) => String(v).replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;').replaceAll('"', '&quot;');
const external = (href, label, extra = '') => `<a href="${esc(href)}" target="_blank" rel="noreferrer"${extra}>${esc(label)}</a>`;

export function buildArticle016(root) {
  for (const [language, l] of Object.entries(locale)) {
    const markdown = fs.readFileSync(path.join(root, l.source), 'utf8');
    const title = markdown.match(/^# (.+)$/m)[1];
    const deck = markdown.match(/^\*\*Deck:\*\* (.+)$/m)[1];
    const article = markdown.slice(markdown.indexOf('\n## ') + 1);
    let body = renderMarkdown(article).replace(/\[S([1-7])\]/g, '<a href="#source-$1">[S$1]</a>');
    body = body.replaceAll('<div class="table-wrap">', `<div class="table-wrap" tabindex="0" role="region" aria-label="${esc(l.table)}">`).replaceAll('<th>', '<th scope="col">');
    const page = `<!doctype html>
<html lang="${language}">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <meta name="description" content="${esc(deck)}" />
  <meta property="article:published_time" content="2026-09-06" />
  <link rel="canonical" href="${base}${routes[language]}" />
  ${Object.entries(routes).map(([lang, route]) => `<link rel="alternate" hreflang="${lang}" href="${base}${route}" />`).join('\n  ')}
  <link rel="alternate" hreflang="x-default" href="${base}${routes.en}" />
  <title>${esc(l.sourceTitle)}</title>
  <link rel="stylesheet" href="styles.css" />
  <link rel="stylesheet" href="article.css" />
  <link rel="stylesheet" href="article016.css" />
</head>
<body class="evidence-article">
  <a class="skip-link" href="#article">${l.skip}</a>
  <header class="site-header">
    <div class="masthead wrap">
      <a class="brand" href="${l.home}" aria-label="RESONANCE">RESONANCE</a>
      <p class="masthead-line">Journal of Intelligence, Technology & Human Progress</p>
      <button class="menu-toggle" type="button" aria-expanded="false" aria-controls="main-nav">${l.menu}</button>
    </div>
    <nav class="nav wrap" id="main-nav" aria-label="${l.nav}"><a href="ai-agents.html">AI</a><a href="science.html">Science</a><a href="open-problems.html">Open Problems</a><a href="verified-workflow.html">Verified Workflow</a><a href="issue-001.html">Issue 001</a></nav>
  </header>
  <main id="article">
    <header class="article-hero wrap">
      <div class="language-switcher" aria-label="${l.language}">${Object.entries(routes).map(([lang, route]) => `<a href="${route}" hreflang="${lang}"${lang === language ? ' aria-current="page"' : ''}>${lang === 'zh-CN' ? '中文' : lang.toUpperCase()}</a>`).join('')}</div>
      <a class="back-link" href="issue-001.html">${l.back}</a>
      <div class="article-meta-row"><p class="section-label">${l.label}</p><p class="article-status">${l.published}</p></div>
      <h1 class="article-title">${esc(title)}</h1>
      <p class="article-dek">${esc(deck)}</p>
      <div class="byline-row"><p>${l.author}</p><p>Issue 001 · Article 016</p></div>
    </header>
    <div class="article-layout wrap">
      <aside class="article-rail" aria-label="${l.rail}">
        <div class="rail-card rail-dark"><p class="section-label">${l.result}</p><strong>${l.six}</strong><span>${l.resultText}</span><a href="#replay">${l.replay}</a></div>
        <div class="rail-card"><p class="section-label">${l.boundary}</p><span>${l.boundaryText}</span></div>
        <div class="rail-card"><p class="section-label">${l.sourceLabel}</p>${external(`${git}${l.source}`, l.text)}${external(`${git}${articleDir}/${stem}.sources.md`, l.ledger)}</div>
      </aside>
      <article class="article-body generated-markdown-article">
${body}
        <section class="market-question" id="replay"><h2>${l.replay}</h2><p>${l.replayText}</p><p>${external(`${git}evidence/article016/plan.md`, l.plan, ' class="text-link"')} · ${external(`${git}scripts/reproduce-article016.py`, l.runner, ' class="text-link"')} · ${external(`${git}evidence/article016/native-replay.json`, l.output, ' class="text-link"')}</p></section>
        <section class="sources-block"><h2>${l.sourceLabel}</h2><ol>${sources.map(([id, label, href]) => `<li id="source-${id.slice(1)}">${external(href, `${id} · ${label}`)}</li>`).join('')}</ol><p>${external(`${git}${articleDir}/${stem}.sources.md`, l.ledger)}</p></section>
      </article>
    </div>
  </main>
  <footer class="site-footer"><div class="wrap footer-grid"><div><div class="brand footer-brand">RESONANCE</div><p>Find the signal. Verify the path. Understand the future.</p></div><div><p class="footer-title">Issue 001</p><p>Issue 001 · Article 016</p></div><div><p>© <span id="year">2026</span> RESONANCE</p></div></div></footer>
  <script src="app.js"></script>
</body>
</html>
`;
    fs.writeFileSync(path.join(root, 'site', routes[language]), page);
  }
}
