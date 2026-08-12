(() => {
  const root = document.querySelector('#version-history');
  const status = document.querySelector('#history-status');
  if (!root) return;

  const escapeHtml = (value) => String(value ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;');

  const versionLabel = (value) => value === null ? 'initial publication' : `v${value}`;

  fetch('corrections.json', { cache: 'no-store' })
    .then((response) => {
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return response.json();
    })
    .then((ledger) => {
      const publications = new Map((ledger.publications || []).map((publication) => [publication.id, publication]));
      const current = (ledger.publications || []).map((publication) => {
        const versions = Object.entries(publication.currentVersions || {})
          .map(([locale, version]) => `<span><strong>${escapeHtml(locale)}</strong> v${escapeHtml(version)}</span>`)
          .join('');
        return `<article class="signal-card"><p class="section-label">${escapeHtml(publication.id)}</p><h3>${escapeHtml(publication.title)}</h3><div class="version-badges">${versions}</div></article>`;
      }).join('');

      const entries = [...(ledger.entries || [])].reverse().map((entry) => {
        const affected = (entry.affected || []).map((item) => {
          const publication = publications.get(item.publication);
          const title = publication?.title || item.publication;
          const from = versionLabel(item.fromVersion);
          const to = `v${item.toVersion}`;
          return `<li><a href="${escapeHtml(item.path)}">${escapeHtml(title)} · ${escapeHtml(item.locale)}</a>: ${escapeHtml(from)} → ${escapeHtml(to)}</li>`;
        }).join('');
        const evidence = (entry.evidence || []).map((url, index) => `<li><a href="${escapeHtml(url)}" target="_blank" rel="noreferrer">Evidence ${index + 1} ↗</a></li>`).join('');
        return `<article class="history-entry">
          <div class="history-meta"><span>${escapeHtml(entry.effectiveAt)}</span><span>${escapeHtml(entry.type)}</span><span>claim impact: ${escapeHtml(entry.claimImpact)}</span></div>
          <h2>${escapeHtml(entry.summary)}</h2>
          <p><strong>Why:</strong> ${escapeHtml(entry.reason)}</p>
          <h3>Affected versions</h3>
          <ul>${affected}</ul>
          <h3>Evidence</h3>
          <ul>${evidence}</ul>
          <p class="history-id"><code>${escapeHtml(entry.id)}</code></p>
        </article>`;
      }).join('');

      root.innerHTML = `
        <section class="section rule-top">
          <p class="section-label">Current registered versions</p>
          <div class="signal-grid-market">${current}</div>
        </section>
        <section class="section rule-top">
          <p class="section-label">Append-only history · newest first</p>
          <div class="history-list">${entries}</div>
        </section>`;
      if (status) status.textContent = `${ledger.entries?.length || 0} recorded publication events · ledger updated ${ledger.updatedAt}`;
    })
    .catch((error) => {
      root.innerHTML = `<p class="error-note">The public corrections ledger could not be loaded. Inspect the machine-readable ledger or GitHub workflow evidence.</p>`;
      if (status) status.textContent = `Ledger load failed: ${error.message}`;
    });
})();
