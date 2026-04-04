/**
 * Мобильное меню шапки: открытие/закрытие, Escape, ловушка фокуса, закрытие при resize → desktop.
 */
(function () {
  const openBtn = document.getElementById('mobile-nav-open');
  const overlay = document.getElementById('mobile-nav-overlay');
  const panel = document.getElementById('mobile-nav-panel');
  const closeBtn = document.getElementById('mobile-nav-close');
  if (!openBtn || !overlay || !panel) return;

  const backdrop = overlay.querySelector('[data-mobile-nav-backdrop]');
  const focusableSelector =
    'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])';

  function getFocusables() {
    return Array.from(panel.querySelectorAll(focusableSelector)).filter(function (el) {
      return el.offsetWidth > 0 || el.offsetHeight > 0 || el.getClientRects().length > 0;
    });
  }

  let panelKeydownHandler = null;

  function closeMenu() {
    overlay.classList.add('hidden');
    overlay.setAttribute('aria-hidden', 'true');
    openBtn.setAttribute('aria-expanded', 'false');
    document.body.style.overflow = '';
    if (panelKeydownHandler) {
      panel.removeEventListener('keydown', panelKeydownHandler);
      panelKeydownHandler = null;
    }
    openBtn.focus();
  }

  function onPanelKeydown(e) {
    if (e.key === 'Escape') {
      e.preventDefault();
      closeMenu();
      return;
    }
    if (e.key !== 'Tab') return;
    const focusables = getFocusables();
    if (focusables.length === 0) return;
    const first = focusables[0];
    const last = focusables[focusables.length - 1];
    if (e.shiftKey) {
      if (document.activeElement === first) {
        e.preventDefault();
        last.focus();
      }
    } else if (document.activeElement === last) {
      e.preventDefault();
      first.focus();
    }
  }

  function openMenu() {
    if (window.matchMedia('(min-width: 1024px)').matches) return;
    overlay.classList.remove('hidden');
    overlay.setAttribute('aria-hidden', 'false');
    openBtn.setAttribute('aria-expanded', 'true');
    document.body.style.overflow = 'hidden';
    panelKeydownHandler = onPanelKeydown;
    panel.addEventListener('keydown', panelKeydownHandler);
    const focusables = getFocusables();
    (focusables[0] || closeBtn || panel).focus();
  }

  openBtn.addEventListener('click', function () {
    if (window.matchMedia('(min-width: 1024px)').matches) return;
    openMenu();
  });

  if (closeBtn) closeBtn.addEventListener('click', closeMenu);
  if (backdrop) backdrop.addEventListener('click', closeMenu);

  panel.querySelectorAll('a[href]').forEach(function (link) {
    link.addEventListener('click', function () {
      closeMenu();
    });
  });

  window.addEventListener('resize', function () {
    if (window.matchMedia('(min-width: 1024px)').matches && !overlay.classList.contains('hidden')) {
      closeMenu();
    }
  });
})();
