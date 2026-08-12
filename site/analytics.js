(() => {
  const SCHEMA_VERSION = 1;
  const ALLOWED_EVENTS = new Set([
    'meaningful_read',
    'hot_question_view',
    'workflow_intake_open',
    'verified_workflow_open',
  ]);

  const endpoint = document
    .querySelector('meta[name="resonance-analytics-endpoint"]')
    ?.getAttribute('content')
    ?.trim() || '';

  const privacyOptOut =
    navigator.globalPrivacyControl === true ||
    navigator.doNotTrack === '1' ||
    window.doNotTrack === '1';

  const articlePage = Boolean(document.querySelector('article.article-body'));
  const language = document.documentElement.lang || 'en';
  const contentKind = articlePage ? 'article' : 'page';
  const emitted = new Set();

  function endpointAllowed(value) {
    if (!value) return false;
    try {
      const url = new URL(value);
      return url.protocol === 'https:' && !url.username && !url.password;
    } catch {
      return false;
    }
  }

  async function emit(event) {
    if (
      privacyOptOut ||
      !endpointAllowed(endpoint) ||
      !ALLOWED_EVENTS.has(event) ||
      emitted.has(event)
    ) {
      return false;
    }

    emitted.add(event);
    const payload = {
      schema_version: SCHEMA_VERSION,
      event,
      path: window.location.pathname || '/',
      language,
      content_kind: contentKind,
    };

    try {
      await fetch(endpoint, {
        method: 'POST',
        mode: 'cors',
        credentials: 'omit',
        referrerPolicy: 'no-referrer',
        cache: 'no-store',
        keepalive: true,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      return true;
    } catch {
      return false;
    }
  }

  if (articlePage) {
    let visibleSeconds = 0;
    let maxDepth = 0;

    const updateDepth = () => {
      const root = document.documentElement;
      const body = document.body;
      const totalHeight = Math.max(root.scrollHeight, body?.scrollHeight || 0, 1);
      const viewportBottom = (window.scrollY || root.scrollTop || 0) + (window.innerHeight || 0);
      maxDepth = Math.max(maxDepth, Math.min(1, viewportBottom / totalHeight));
    };

    updateDepth();
    window.addEventListener('scroll', updateDepth, { passive: true });
    window.addEventListener('resize', updateDepth, { passive: true });

    window.setInterval(() => {
      if (document.visibilityState === 'visible') {
        visibleSeconds += 1;
        updateDepth();
      }
      if (visibleSeconds >= 45 && maxDepth >= 0.6) {
        emit('meaningful_read');
      }
    }, 1000);
  }

  const hotQuestion = document.querySelector('.market-question .hot-question');
  if (hotQuestion && 'IntersectionObserver' in window) {
    const observer = new IntersectionObserver((entries) => {
      if (entries.some((entry) => entry.isIntersecting && entry.intersectionRatio >= 0.6)) {
        emit('hot_question_view');
        observer.disconnect();
      }
    }, { threshold: [0.6] });
    observer.observe(hotQuestion);
  }

  document.addEventListener('click', (event) => {
    const link = event.target.closest?.('a[href]');
    if (!link) return;

    let target;
    try {
      target = new URL(link.href, window.location.href);
    } catch {
      return;
    }

    const isMarketIntake =
      target.hostname === 'github.com' &&
      target.pathname === '/safal207/RESONANCE/issues/new' &&
      target.searchParams.get('template') === 'market-workflow.yml';

    if (isMarketIntake) {
      emit('workflow_intake_open');
      return;
    }

    const inMarketQuestion = Boolean(link.closest('.market-question'));
    if (inMarketQuestion && /\/verified-workflow\.html$/.test(target.pathname)) {
      emit('verified_workflow_open');
    }
  }, { capture: true });
})();
