#!/usr/bin/env node

import fs from 'node:fs';
import path from 'node:path';

const args = process.argv.slice(2);
const readArg = (name, fallback = null) => {
  const index = args.indexOf(name);
  return index >= 0 && args[index + 1] ? args[index + 1] : fallback;
};

const inputDir = readArg('--input', 'lighthouse-results');
const outputPrefix = readArg('--output', 'lighthouse-summary');
const enforce = args.includes('--enforce');

const budgets = {
  mobile: {
    performance: 80,
    accessibility: 95,
    'best-practices': 95,
    seo: 95,
    lcpMs: 3500,
    tbtMs: 300,
    cls: 0.1
  },
  desktop: {
    performance: 90,
    accessibility: 95,
    'best-practices': 95,
    seo: 95,
    lcpMs: 2500,
    tbtMs: 200,
    cls: 0.1
  }
};

if (!fs.existsSync(inputDir)) {
  console.error(`Lighthouse input directory does not exist: ${inputDir}`);
  process.exit(2);
}

const files = fs.readdirSync(inputDir)
  .filter((name) => name.endsWith('.json') && !name.includes('summary'))
  .sort();

if (files.length === 0) {
  console.error(`No Lighthouse JSON reports found in ${inputDir}`);
  process.exit(2);
}

const score = (report, category) => Math.round((report.categories?.[category]?.score ?? 0) * 100);
const numeric = (report, id) => report.audits?.[id]?.numericValue ?? null;
const display = (report, id) => report.audits?.[id]?.displayValue ?? null;

function auditSamples(audit) {
  const items = Array.isArray(audit?.details?.items) ? audit.details.items : [];
  return items.slice(0, 4).map((item) => ({
    selector: item?.node?.selector ?? null,
    snippet: item?.node?.snippet ?? null,
    explanation: item?.node?.explanation ?? null,
    label: item?.label ?? item?.failureSummary ?? null,
  })).filter((item) => Object.values(item).some(Boolean));
}

const reports = files.map((file) => {
  const report = JSON.parse(fs.readFileSync(path.join(inputDir, file), 'utf8'));
  const profile = file.includes('desktop') ? 'desktop' : 'mobile';
  const categories = Object.fromEntries(
    ['performance', 'accessibility', 'best-practices', 'seo'].map((category) => [category, score(report, category)])
  );
  const metrics = {
    fcp: { numericValue: numeric(report, 'first-contentful-paint'), displayValue: display(report, 'first-contentful-paint') },
    lcp: { numericValue: numeric(report, 'largest-contentful-paint'), displayValue: display(report, 'largest-contentful-paint') },
    speedIndex: { numericValue: numeric(report, 'speed-index'), displayValue: display(report, 'speed-index') },
    tbt: { numericValue: numeric(report, 'total-blocking-time'), displayValue: display(report, 'total-blocking-time') },
    cls: { numericValue: numeric(report, 'cumulative-layout-shift'), displayValue: display(report, 'cumulative-layout-shift') }
  };
  const opportunities = Object.values(report.audits ?? {})
    .filter((audit) => audit?.details?.type === 'opportunity' && typeof audit.numericValue === 'number' && audit.numericValue > 0)
    .sort((a, b) => (b.numericValue ?? 0) - (a.numericValue ?? 0))
    .slice(0, 5)
    .map((audit) => ({ id: audit.id, title: audit.title, displayValue: audit.displayValue ?? null, score: audit.score }));
  const failedAudits = Object.values(report.audits ?? {})
    .filter((audit) => typeof audit?.score === 'number' && audit.score < 1 && !['notApplicable', 'informative', 'manual'].includes(audit.scoreDisplayMode))
    .sort((a, b) => (a.score ?? 1) - (b.score ?? 1))
    .slice(0, 20)
    .map((audit) => ({
      id: audit.id,
      title: audit.title,
      score: audit.score,
      displayValue: audit.displayValue ?? null,
      samples: auditSamples(audit),
    }));

  return {
    file,
    profile,
    lighthouseVersion: report.lighthouseVersion,
    url: report.finalDisplayedUrl || report.finalUrl || null,
    categories,
    metrics,
    opportunities,
    failedAudits
  };
});

const failures = [];
for (const report of reports) {
  const budget = budgets[report.profile];
  for (const category of ['performance', 'accessibility', 'best-practices', 'seo']) {
    if (report.categories[category] < budget[category]) {
      failures.push(`${report.file}: ${category} ${report.categories[category]} < ${budget[category]}`);
    }
  }
  if (typeof report.metrics.lcp.numericValue === 'number' && report.metrics.lcp.numericValue > budget.lcpMs) {
    failures.push(`${report.file}: LCP ${Math.round(report.metrics.lcp.numericValue)}ms > ${budget.lcpMs}ms`);
  }
  if (typeof report.metrics.tbt.numericValue === 'number' && report.metrics.tbt.numericValue > budget.tbtMs) {
    failures.push(`${report.file}: TBT ${Math.round(report.metrics.tbt.numericValue)}ms > ${budget.tbtMs}ms`);
  }
  if (typeof report.metrics.cls.numericValue === 'number' && report.metrics.cls.numericValue > budget.cls) {
    failures.push(`${report.file}: CLS ${report.metrics.cls.numericValue.toFixed(3)} > ${budget.cls}`);
  }
}

const summary = {
  schema: 'resonance.site-health.lighthouse.v1',
  generatedAt: new Date().toISOString(),
  auditedCommit: process.env.GITHUB_SHA ?? null,
  sourceRunId: process.env.GITHUB_RUN_ID ?? null,
  budgets,
  reports,
  verdict: failures.length === 0 ? 'pass' : 'fail',
  failures
};

fs.writeFileSync(`${outputPrefix}.json`, `${JSON.stringify(summary, null, 2)}\n`);

const rows = reports.map((report) => {
  const c = report.categories;
  return `| ${report.file.replace('.json', '')} | ${c.performance} | ${c.accessibility} | ${c['best-practices']} | ${c.seo} | ${report.metrics.lcp.displayValue ?? 'n/a'} | ${report.metrics.tbt.displayValue ?? 'n/a'} | ${report.metrics.cls.displayValue ?? 'n/a'} |`;
});

const failingReportSections = reports
  .filter((report) => report.failedAudits.length > 0)
  .flatMap((report) => {
    const lines = [`### ${report.file}`, ''];
    for (const audit of report.failedAudits) {
      lines.push(`- **${audit.id}** — ${audit.title}${audit.displayValue ? ` (${audit.displayValue})` : ''}`);
      for (const sample of audit.samples) {
        const target = sample.selector || sample.snippet || sample.label || sample.explanation;
        if (target) lines.push(`  - ${String(target).replace(/\s+/g, ' ').slice(0, 280)}`);
      }
    }
    lines.push('');
    return lines;
  });

const markdown = [
  '# RESONANCE Lighthouse Site Health',
  '',
  `**Verdict:** ${summary.verdict.toUpperCase()}`,
  '',
  '| Route / profile | Performance | Accessibility | Best practices | SEO | LCP | TBT | CLS |',
  '|---|---:|---:|---:|---:|---:|---:|---:|',
  ...rows,
  '',
  '## Budgets',
  '',
  `- Mobile: performance ≥ ${budgets.mobile.performance}, accessibility ≥ ${budgets.mobile.accessibility}, best practices ≥ ${budgets.mobile['best-practices']}, SEO ≥ ${budgets.mobile.seo}, LCP ≤ ${budgets.mobile.lcpMs} ms, TBT ≤ ${budgets.mobile.tbtMs} ms, CLS ≤ ${budgets.mobile.cls}.`,
  `- Desktop: performance ≥ ${budgets.desktop.performance}, accessibility ≥ ${budgets.desktop.accessibility}, best practices ≥ ${budgets.desktop['best-practices']}, SEO ≥ ${budgets.desktop.seo}, LCP ≤ ${budgets.desktop.lcpMs} ms, TBT ≤ ${budgets.desktop.tbtMs} ms, CLS ≤ ${budgets.desktop.cls}.`,
  '',
  ...(failures.length ? ['## Budget failures', '', ...failures.map((failure) => `- ${failure}`), ''] : []),
  ...(failingReportSections.length ? ['## Failing Lighthouse audits', '', ...failingReportSections] : []),
  '> Lighthouse is a repeatable lab measurement for a specific run. It is not a claim about search ranking, production field Core Web Vitals, or every user/device/network.',
  ''
].join('\n');

fs.writeFileSync(`${outputPrefix}.md`, markdown);
console.log(markdown);

if (enforce && failures.length > 0) {
  process.exit(1);
}
