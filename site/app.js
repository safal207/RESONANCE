const toggle = document.querySelector('.menu-toggle');
const nav = document.querySelector('#main-nav');

if (toggle && nav) {
  toggle.addEventListener('click', () => {
    const open = nav.classList.toggle('open');
    toggle.setAttribute('aria-expanded', String(open));
  });

  nav.querySelectorAll('a').forEach((link) => {
    link.addEventListener('click', () => {
      nav.classList.remove('open');
      toggle.setAttribute('aria-expanded', 'false');
    });
  });
}

const year = document.querySelector('#year');
if (year) year.textContent = new Date().getFullYear();

const route = window.location.pathname.split('/').pop() || 'index.html';
const article006EntryPoints = new Set(['index.html', 'index.ru.html', 'index.zh.html', 'issue-001.html']);

if (article006EntryPoints.has(route)) {
  const language = document.documentElement.lang || 'en';
  const copy = {
    en: {
      label: 'Article #006 · Agent Payments',
      title: 'When Is an AI Agent Allowed to Pay Again?',
      body: 'Payment finality, retry authority and fulfillment finality are different proofs. The new synthesis asks what must be established before an autonomous agent may create the next financial effect.',
      read: 'Read Article #006 →',
      pilot: 'Agent Payment Verification Pilot →',
    },
    ru: {
      label: 'Новая статья · Article #006 · EN',
      title: 'Когда AI-агенту разрешено платить снова?',
      body: 'Payment finality, право на retry и fulfillment finality — это разные доказательства. Новая англоязычная статья собирает их в один вопрос: что должно быть доказано до следующего денежного действия агента?',
      read: 'Читать Article #006 (EN) →',
      pilot: 'Agent Payment Verification Pilot →',
    },
    'zh-CN': {
      label: '新文章 · Article #006 · EN',
      title: 'AI Agent 何时可以再次付款？',
      body: '支付终局、重试权限与履约终局是不同的证明。新的英文综述把它们统一为一个问题：在 Agent 发起下一次资金动作之前，系统必须证明什么？',
      read: '阅读 Article #006（英文）→',
      pilot: 'Agent Payment Verification Pilot →',
    },
  };
  const localized = copy[language] || copy.en;
  const main = document.querySelector('main');
  const firstSection = main?.querySelector(':scope > section');

  if (main && firstSection && !main.querySelector('[data-article-discovery="006"]')) {
    const discovery = document.createElement('section');
    discovery.className = 'section rule-top wrap';
    discovery.dataset.articleDiscovery = '006';
    discovery.innerHTML = `
      <div class="editorial-grid">
        <div>
          <p class="section-label">${localized.label}</p>
          <h2>${localized.title}</h2>
        </div>
        <div>
          <p>${localized.body}</p>
          <a class="button" href="when-is-an-ai-agent-allowed-to-pay-again.html">${localized.read}</a>
          <p><a class="text-link" href="agent-payment-verification.html">${localized.pilot}</a></p>
        </div>
      </div>`;
    firstSection.after(discovery);
  }
}

const article013EntryPoints = new Set(['index.ru.html', 'issue-001.html']);

if (article013EntryPoints.has(route)) {
  const language = document.documentElement.lang || 'en';
  const copy = {
    en: {
      label: 'Article #013 · RU · Causal Evidence',
      title: 'Evidence Must Bind the Transition',
      body: 'Execution Binding and Terminality Binding converge on one invariant: correct evidence and correct ordering are not enough unless the exact evidence occurrence is causally bound to the exact consequential transition.',
      read: 'Read Article #013 (RU) →',
    },
    ru: {
      label: 'Новая статья · Article #013 · Causal Evidence',
      title: 'Evidence Must Bind the Transition',
      body: 'Execution Binding и Terminality Binding сходятся в одном инварианте: корректного доказательства и правильного порядка событий недостаточно, если exact evidence occurrence не связано с exact consequential transition.',
      read: 'Читать Article #013 →',
    },
  };
  const localized = copy[language] || copy.en;
  const main = document.querySelector('main');
  const firstSection = main?.querySelector(':scope > section');

  if (main && firstSection && !main.querySelector('[data-article-discovery="013"]')) {
    const discovery = document.createElement('section');
    discovery.className = 'section rule-top wrap';
    discovery.dataset.articleDiscovery = '013';
    discovery.innerHTML = `
      <div class="editorial-grid">
        <div>
          <p class="section-label">${localized.label}</p>
          <h2>${localized.title}</h2>
        </div>
        <div>
          <p>${localized.body}</p>
          <a class="button" href="evidence-must-bind-the-transition.ru.html">${localized.read}</a>
        </div>
      </div>`;
    firstSection.after(discovery);
  }
}
