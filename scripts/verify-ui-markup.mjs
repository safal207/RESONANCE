#!/usr/bin/env node

import fs from 'node:fs';
import path from 'node:path';

const root = process.argv[2] || 'dist';

if (!fs.existsSync(root)) {
  console.error(`UI markup contract: directory does not exist: ${root}`);
  process.exit(2);
}

function walk(dir) {
  return fs.readdirSync(dir, { withFileTypes: true }).flatMap((entry) => {
    const full = path.join(dir, entry.name);
    return entry.isDirectory() ? walk(full) : [full];
  });
}

function attr(tag, name) {
  const pattern = new RegExp(`\\s${name}(?:\\s*=\\s*(?:"([^"]*)"|'([^']*)'|([^\\s>]+)))?`, 'i');
  const match = tag.match(pattern);
  if (!match) return null;
  return match[1] ?? match[2] ?? match[3] ?? '';
}

const htmlFiles = walk(root).filter((file) => file.endsWith('.html')).sort();
const failures = [];
const stats = {
  pages: htmlFiles.length,
  images: 0,
  buttons: 0,
  localImages: 0,
  responsiveLargeImages: 0,
};

for (const file of htmlFiles) {
  const html = fs.readFileSync(file, 'utf8');
  const rel = path.relative(root, file).replaceAll(path.sep, '/');

  for (const match of html.matchAll(/<img\b[^>]*>/gi)) {
    const tag = match[0];
    stats.images += 1;

    const alt = attr(tag, 'alt');
    const widthRaw = attr(tag, 'width');
    const heightRaw = attr(tag, 'height');
    const src = attr(tag, 'src');
    const srcset = attr(tag, 'srcset');

    if (alt === null) failures.push(`${rel}: <img> is missing alt`);

    const width = Number(widthRaw);
    const height = Number(heightRaw);
    if (widthRaw === null || heightRaw === null || !Number.isFinite(width) || !Number.isFinite(height) || width <= 0 || height <= 0) {
      failures.push(`${rel}: <img${src ? ` src="${src}"` : ''}> must declare positive intrinsic width and height`);
    }

    if (src && !/^(?:https?:|data:|blob:|\/\/)/i.test(src)) {
      stats.localImages += 1;
      const cleanSrc = src.split(/[?#]/)[0];
      const target = path.resolve(path.dirname(file), cleanSrc);
      if (!fs.existsSync(target)) {
        failures.push(`${rel}: local image target does not exist: ${src}`);
      } else {
        const bytes = fs.statSync(target).size;
        if (bytes > 750 * 1024) {
          failures.push(`${rel}: local image ${src} is ${(bytes / 1024).toFixed(0)} KiB; release budget is 750 KiB per image`);
        }
      }
    }

    if (Number.isFinite(width) && width >= 960) {
      stats.responsiveLargeImages += 1;
      if (!srcset) failures.push(`${rel}: image width ${width}px should provide srcset for responsive delivery`);
    }
  }

  for (const match of html.matchAll(/<button\b[^>]*>/gi)) {
    const tag = match[0];
    stats.buttons += 1;
    const type = attr(tag, 'type');
    if (!type) failures.push(`${rel}: <button> must declare type="button", "submit", or "reset"`);
    else if (!['button', 'submit', 'reset'].includes(type.toLowerCase())) failures.push(`${rel}: unsupported button type="${type}"`);
  }
}

const report = {
  schema: 'resonance.site-health.ui-markup.v1',
  root,
  stats,
  verdict: failures.length ? 'fail' : 'pass',
  failures,
};

fs.writeFileSync('ui-markup-summary.json', `${JSON.stringify(report, null, 2)}\n`);

const markdown = [
  '# RESONANCE UI Markup Contract',
  '',
  `**Verdict:** ${report.verdict.toUpperCase()}`,
  '',
  `- Pages checked: ${stats.pages}`,
  `- Images checked: ${stats.images}`,
  `- Local images checked: ${stats.localImages}`,
  `- Large responsive-image candidates: ${stats.responsiveLargeImages}`,
  `- Buttons checked: ${stats.buttons}`,
  '',
  '## Rules',
  '',
  '- Every image has an `alt` attribute.',
  '- Every image declares positive intrinsic `width` and `height` to reserve layout space.',
  '- Local image files must exist and stay at or below 750 KiB each.',
  '- Images with intrinsic width ≥ 960 px provide `srcset`.',
  '- Every `<button>` declares an explicit valid `type`.',
  '',
  ...(failures.length ? ['## Failures', '', ...failures.map((failure) => `- ${failure}`), ''] : []),
].join('\n');

fs.writeFileSync('ui-markup-summary.md', `${markdown}\n`);
console.log(markdown);

if (failures.length) process.exit(1);
