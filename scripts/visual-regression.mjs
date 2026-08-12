#!/usr/bin/env node

import fs from 'node:fs';
import path from 'node:path';
import process from 'node:process';
import puppeteer from 'puppeteer-core';
import pixelmatch from 'pixelmatch';
import { PNG } from 'pngjs';

const args = process.argv.slice(2);
const arg = (name, fallback = null) => {
  const index = args.indexOf(name);
  return index >= 0 && args[index + 1] ? args[index + 1] : fallback;
};

const candidateBase = arg('--candidate', 'http://127.0.0.1:8080/');
const baselineBase = arg('--baseline', 'https://safal207.github.io/RESONANCE/');
const outputDir = arg('--output', 'visual-results');
const enforce = args.includes('--enforce');

const viewports = [
  { id: 'phone', width: 390, height: 844, deviceScaleFactor: 1 },
  { id: 'tablet', width: 768, height: 1024, deviceScaleFactor: 1 },
  { id: 'desktop', width: 1440, height: 900, deviceScaleFactor: 1 },
];

const routes = [
  { id: 'home', route: '' },
  { id: 'article004-en', route: 'before-you-let-an-ai-agent-move-money.html' },
  { id: 'article004-ru', route: 'before-you-let-an-ai-agent-move-money.ru.html' },
  { id: 'article004-zh', route: 'before-you-let-an-ai-agent-move-money.zh.html' },
  { id: 'article005-en', route: 'memory-can-be-true-and-still-be-unsafe.html' },
  { id: 'article005-ru', route: 'memory-can-be-true-and-still-be-unsafe.ru.html' },
  { id: 'article005-zh', route: 'memory-can-be-true-and-still-be-unsafe.zh.html' },
  { id: 'quality', route: 'quality.html' },
  { id: 'corrections', route: 'corrections.html' },
  { id: 'measurement', route: 'measurement.html' },
];

const chromeCandidates = [
  process.env.CHROME_BIN,
  '/usr/bin/google-chrome-stable',
  '/usr/bin/google-chrome',
  '/usr/bin/chromium',
  '/usr/bin/chromium-browser',
].filter(Boolean);
const executablePath = chromeCandidates.find((candidate) => fs.existsSync(candidate));
if (!executablePath) {
  console.error(`Chrome/Chromium not found. Checked: ${chromeCandidates.join(', ')}`);
  process.exit(2);
}

fs.mkdirSync(outputDir, { recursive: true });
for (const dir of ['candidate', 'baseline', 'diff']) fs.mkdirSync(path.join(outputDir, dir), { recursive: true });

const browser = await puppeteer.launch({
  executablePath,
  headless: true,
  args: ['--no-sandbox', '--disable-gpu', '--font-render-hinting=none'],
});

const normalizeBase = (base) => base.endsWith('/') ? base : `${base}/`;
const candidateRoot = normalizeBase(candidateBase);
const baselineRoot = normalizeBase(baselineBase);

async function settle(page, url) {
  const response = await page.goto(url, { waitUntil: 'networkidle0', timeout: 45000 });
  if (!response || response.status() >= 400) return response;
  await page.evaluate(async () => { if (document.fonts?.ready) await document.fonts.ready; });
  await page.addStyleTag({ content: `
    *, *::before, *::after {
      animation-duration: 0s !important;
      animation-delay: 0s !important;
      transition-duration: 0s !important;
      scroll-behavior: auto !important;
      caret-color: transparent !important;
    }
  ` });
  return response;
}

async function inspectGeometry(page) {
  return await page.evaluate(() => {
    const viewportWidth = window.innerWidth;
    const root = document.documentElement;
    const horizontalOverflow = Math.max(0, root.scrollWidth - viewportWidth);
    const clipped = [];
    const outside = [];
    const watched = 'button, a.button, h1, h2, h3, th, td, img, pre, code';

    const insideHorizontalScroller = (element) => {
      let node = element.parentElement;
      while (node && node !== document.body) {
        const style = getComputedStyle(node);
        if (['auto', 'scroll'].includes(style.overflowX) && node.scrollWidth - node.clientWidth > 2) return true;
        node = node.parentElement;
      }
      return false;
    };

    for (const el of document.querySelectorAll(watched)) {
      const style = getComputedStyle(el);
      const rect = el.getBoundingClientRect();
      if (rect.width <= 0 || rect.height <= 0 || style.visibility === 'hidden' || style.display === 'none') continue;
      const label = `${el.tagName.toLowerCase()}${el.id ? `#${el.id}` : ''}${el.classList.length ? `.${[...el.classList].slice(0, 3).join('.')}` : ''}`;
      if (!insideHorizontalScroller(el) && (rect.left < -2 || rect.right > viewportWidth + 2)) {
        outside.push({ label, left: Math.round(rect.left), right: Math.round(rect.right), viewportWidth });
      }
      if (['BUTTON', 'A', 'H1', 'H2', 'H3', 'TH', 'TD'].includes(el.tagName)) {
        const xClip = el.scrollWidth - el.clientWidth > 3 && ['hidden', 'clip'].includes(style.overflowX);
        const yClip = el.scrollHeight - el.clientHeight > 3 && ['hidden', 'clip'].includes(style.overflowY);
        if (xClip || yClip) {
          clipped.push({ label, clientWidth: el.clientWidth, scrollWidth: el.scrollWidth, clientHeight: el.clientHeight, scrollHeight: el.scrollHeight });
        }
      }
    }

    const tooSmallTargets = [];
    for (const el of document.querySelectorAll('button, a.button')) {
      const style = getComputedStyle(el);
      const rect = el.getBoundingClientRect();
      if (rect.width <= 0 || rect.height <= 0 || style.visibility === 'hidden' || style.display === 'none') continue;
      if (rect.width < 44 || rect.height < 44) {
        tooSmallTargets.push({ text: (el.textContent || '').trim().slice(0, 80), width: Math.round(rect.width), height: Math.round(rect.height) });
      }
    }

    const images = [...document.images].map((img) => {
      const rect = img.getBoundingClientRect();
      return {
        src: img.getAttribute('src'),
        naturalWidth: img.naturalWidth,
        naturalHeight: img.naturalHeight,
        renderedWidth: Math.round(rect.width),
        renderedHeight: Math.round(rect.height),
        complete: img.complete,
      };
    });

    return { horizontalOverflow, clipped, outside, tooSmallTargets, images };
  });
}

function diffPng(candidatePath, baselinePath, diffPath) {
  const candidate = PNG.sync.read(fs.readFileSync(candidatePath));
  const baseline = PNG.sync.read(fs.readFileSync(baselinePath));
  if (candidate.width !== baseline.width || candidate.height !== baseline.height) {
    return { comparable: false, reason: 'image-dimensions-differ', candidate: [candidate.width, candidate.height], baseline: [baseline.width, baseline.height], ratio: 1 };
  }
  const diff = new PNG({ width: candidate.width, height: candidate.height });
  const mismatched = pixelmatch(candidate.data, baseline.data, diff.data, candidate.width, candidate.height, { threshold: 0.12, includeAA: false });
  fs.writeFileSync(diffPath, PNG.sync.write(diff));
  return { comparable: true, mismatchedPixels: mismatched, totalPixels: candidate.width * candidate.height, ratio: mismatched / (candidate.width * candidate.height) };
}

const results = [];
const hardFailures = [];

for (const viewport of viewports) {
  for (const route of routes) {
    const key = `${route.id}-${viewport.id}`;
    const candidatePath = path.join(outputDir, 'candidate', `${key}.png`);
    const baselinePath = path.join(outputDir, 'baseline', `${key}.png`);
    const diffPath = path.join(outputDir, 'diff', `${key}.png`);

    const candidatePage = await browser.newPage();
    await candidatePage.setViewport(viewport);
    const candidateUrl = `${candidateRoot}${route.route}`;
    const candidateResponse = await settle(candidatePage, candidateUrl);
    if (!candidateResponse || candidateResponse.status() >= 400) {
      hardFailures.push(`${key}: candidate route unavailable (${candidateResponse?.status() ?? 'no response'})`);
      await candidatePage.close();
      continue;
    }
    const geometry = await inspectGeometry(candidatePage);
    await candidatePage.screenshot({ path: candidatePath, fullPage: true, captureBeyondViewport: true });
    await candidatePage.close();

    if (geometry.horizontalOverflow > 2) hardFailures.push(`${key}: horizontal overflow ${geometry.horizontalOverflow}px`);
    for (const item of geometry.clipped) hardFailures.push(`${key}: clipped ${item.label}`);
    for (const item of geometry.outside) hardFailures.push(`${key}: outside viewport ${item.label} (${item.left}..${item.right} of ${item.viewportWidth})`);
    for (const item of geometry.tooSmallTargets) hardFailures.push(`${key}: target ${item.width}×${item.height}px < 44×44 (${item.text || 'unnamed'})`);

    let baselineStatus = 'captured';
    let visualDiff = null;
    const baselinePage = await browser.newPage();
    try {
      await baselinePage.setViewport(viewport);
      const baselineResponse = await settle(baselinePage, `${baselineRoot}${route.route}?visual-baseline=${process.env.GITHUB_RUN_ID ?? Date.now()}`);
      if (!baselineResponse || baselineResponse.status() >= 400) {
        baselineStatus = `unavailable:${baselineResponse?.status() ?? 'no-response'}`;
      } else {
        await baselinePage.screenshot({ path: baselinePath, fullPage: true, captureBeyondViewport: true });
        visualDiff = diffPng(candidatePath, baselinePath, diffPath);
      }
    } catch (error) {
      baselineStatus = `error:${error.message}`;
    } finally {
      await baselinePage.close();
    }

    results.push({ key, route: route.route || '/', viewport, candidateUrl, baselineStatus, geometry, visualDiff });
  }
}

await browser.close();

const summary = {
  schema: 'resonance.site-health.visual.v1',
  generatedAt: new Date().toISOString(),
  auditedCommit: process.env.GITHUB_SHA ?? null,
  sourceRunId: process.env.GITHUB_RUN_ID ?? null,
  candidateBase: candidateRoot,
  baselineBase: baselineRoot,
  viewports,
  results,
  verdict: hardFailures.length ? 'fail' : 'pass',
  hardFailures,
  visualDiffPolicy: 'advisory-v0.3',
};
fs.writeFileSync(path.join(outputDir, 'visual-summary.json'), `${JSON.stringify(summary, null, 2)}\n`);

const rows = results.map((result) => {
  const diff = result.visualDiff?.comparable ? `${(result.visualDiff.ratio * 100).toFixed(2)}%` : (result.visualDiff?.reason || result.baselineStatus);
  const g = result.geometry;
  return `| ${result.key} | ${g.horizontalOverflow}px | ${g.clipped.length} | ${g.outside.length} | ${g.tooSmallTargets.length} | ${g.images.length} | ${diff} |`;
});

const markdown = [
  '# RESONANCE Visual Regression Contract',
  '',
  `**Verdict:** ${summary.verdict.toUpperCase()}`,
  '',
  '| Route / viewport | Horizontal overflow | Clipped | Outside viewport | Small targets | Images | Pixel diff vs public main |',
  '|---|---:|---:|---:|---:|---:|---:|',
  ...rows,
  '',
  '## Policy',
  '',
  '- Horizontal overflow, clipped key text/controls, key elements outside the viewport and primary button targets below 44×44 px are release-blocking.',
  '- Elements inside intentional horizontal scroll regions (for example dense tables or code blocks) are not treated as page-overflow defects.',
  '- Pixel diffs are advisory in v0.3 because legitimate editorial/content changes can alter screenshots.',
  '- Candidate, public-main baseline and diff PNGs are retained as workflow artifacts for human inspection.',
  '- Reference viewports: 390×844 phone, 768×1024 tablet, 1440×900 desktop.',
  '',
  ...(hardFailures.length ? ['## Hard failures', '', ...hardFailures.map((failure) => `- ${failure}`), ''] : []),
].join('\n');

fs.writeFileSync(path.join(outputDir, 'visual-summary.md'), `${markdown}\n`);
console.log(markdown);

if (enforce && hardFailures.length) process.exit(1);
