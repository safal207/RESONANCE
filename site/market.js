(() => {
  const canonical = document.querySelector('link[rel="canonical"]')?.href || window.location.href.split('#')[0];
  const title = document.querySelector('h1')?.textContent?.trim() || document.title;
  const bodyText = document.body.dataset.shareText || title;
  const enc = encodeURIComponent;

  const shareUrls = {
    x: () => `https://twitter.com/intent/tweet?text=${enc(bodyText)}&url=${enc(canonical)}`,
    linkedin: () => `https://www.linkedin.com/sharing/share-offsite/?url=${enc(canonical)}`,
    reddit: () => `https://www.reddit.com/submit?url=${enc(canonical)}&title=${enc(title)}`,
    telegram: () => `https://t.me/share/url?url=${enc(canonical)}&text=${enc(bodyText)}`,
    vk: () => `https://vk.com/share.php?url=${enc(canonical)}&title=${enc(title)}`,
    weibo: () => `https://service.weibo.com/share/share.php?url=${enc(canonical)}&title=${enc(bodyText)}`,
  };

  async function copy(value, button) {
    try {
      await navigator.clipboard.writeText(value);
      const old = button.textContent;
      button.textContent = button.dataset.copiedLabel || 'Copied';
      window.setTimeout(() => { button.textContent = old; }, 1400);
    } catch {
      window.prompt('Copy this text:', value);
    }
  }

  document.querySelectorAll('[data-share]').forEach((button) => {
    button.addEventListener('click', async () => {
      const target = button.dataset.share;
      if (target === 'native' && navigator.share) {
        await navigator.share({ title, text: bodyText, url: canonical });
        return;
      }
      if (target === 'copy') {
        await copy(canonical, button);
        return;
      }
      if (target === 'copy-text') {
        const value = button.dataset.copyText || `${bodyText}\n${canonical}`;
        await copy(value, button);
        return;
      }
      const url = shareUrls[target]?.();
      if (url) window.open(url, '_blank', 'noopener,noreferrer');
    });
  });
})();
