(function () {
  'use strict';

  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  function initNav() {
    const languageBtn = document.getElementById('languageBtn');
    const languageSwitcher = languageBtn?.closest('.language-switcher');

    languageBtn?.addEventListener('click', (e) => {
      e.stopPropagation();
      const open = !languageSwitcher?.classList.contains('active');
      languageSwitcher?.classList.toggle('active', open);
      languageBtn.setAttribute('aria-expanded', open ? 'true' : 'false');
    });

    document.addEventListener('click', (e) => {
      if (!e.target.closest('.language-switcher')) {
        languageSwitcher?.classList.remove('active');
        languageBtn?.setAttribute('aria-expanded', 'false');
      }
    });

    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        languageSwitcher?.classList.remove('active');
        languageBtn?.setAttribute('aria-expanded', 'false');
        closeMobileNav();
      }
    });

    const burger = document.getElementById('mobileMenuToggle');
    const nav = document.getElementById('navMenu');
    if (!burger || !nav) return;

    function closeMobileNav() {
      nav.classList.remove('active');
      burger.setAttribute('aria-expanded', 'false');
      document.body.style.overflow = '';
      window.__cuLenis?.start();
    }

    burger.addEventListener('click', () => {
      const open = !nav.classList.contains('active');
      nav.classList.toggle('active', open);
      burger.setAttribute('aria-expanded', open ? 'true' : 'false');
      document.body.style.overflow = open ? 'hidden' : '';
      window.__cuLenis?.[open ? 'stop' : 'start']();
    });

    nav.querySelectorAll('a').forEach((a) => {
      a.addEventListener('click', closeMobileNav);
    });
  }

  function initHeader() {
    const header = document.getElementById('cuHeader');
    if (!header) return;
    header.classList.add('is-solid');
  }

  function initLenis() {
    if (reduceMotion || typeof Lenis === 'undefined' || typeof gsap === 'undefined') return;
    gsap.registerPlugin(ScrollTrigger);
    const lenis = new Lenis({ lerp: 0.1 });
    lenis.on('scroll', ScrollTrigger.update);
    /* Own RAF — do not hitch Lenis onto gsap.ticker (can stall hero tweens) */
    function raf(time) {
      lenis.raf(time);
      requestAnimationFrame(raf);
    }
    requestAnimationFrame(raf);
    window.__cuLenis = lenis;
  }

  function initHero() {
    if (typeof gsap === 'undefined') return;
    const hero = document.querySelector('.cu-hero');
    if (!hero) return;

    const desk = hero.querySelector('.cu-hero__board--desk');
    const title = desk?.querySelector('.cu-hero__title') || hero.querySelector('.cu-hero__title');
    const cta = desk?.querySelector('.cu-hero__cta') || hero.querySelector('.cu-hero__cta');
    const shapes = desk?.querySelector('.cu-hero__shapes')
      || hero.querySelector('.cu-hero__board .cu-hero__shapes')
      || hero.querySelector('.cu-hero__shapes');
    const photos = desk?.querySelector('.cu-hero__photos') || hero.querySelector('.cu-hero__photos');
    const orbits = desk
      ? desk.querySelectorAll('.cu-orbit')
      : document.querySelectorAll('.cu-orbit');
    const shopDesk = desk?.querySelector('.cu-hero-shop--desk');

    if (reduceMotion) {
      if (shopDesk) gsap.set(shopDesk, { autoAlpha: 1 });
      return;
    }

    const artH = parseFloat(getComputedStyle(hero).getPropertyValue('--cu-art-h')) || 625;
    const vbH = parseFloat(getComputedStyle(hero).getPropertyValue('--cu-vb-h')) || artH;
    const originY = `${((artH * 0.5) / vbH) * 100}%`;

    if (shapes) {
      gsap.set(shapes, {
        autoAlpha: 0,
        scale: 1.04,
        transformOrigin: `50% ${originY}`,
      });
    }
    if (photos) {
      gsap.set(photos, {
        autoAlpha: 0,
        scale: 1.04,
        transformOrigin: `50% ${originY}`,
      });
    }
    if (title) gsap.set(title, { autoAlpha: 0, y: 16 });
    if (cta) gsap.set(cta, { autoAlpha: 0, y: 10, scale: 0.92 });
    if (orbits.length) gsap.set(orbits, { autoAlpha: 0, y: -8 });
    if (shopDesk) gsap.set(shopDesk, { autoAlpha: 0 });

    let magnetReady = false;
    const armMagnet = () => {
      if (magnetReady) return;
      magnetReady = true;
      initHeroMagnet();
    };

    const tl = gsap.timeline({
      defaults: { ease: 'power3.out' },
      onComplete: armMagnet,
    });
    if (shapes) tl.to(shapes, { autoAlpha: 1, scale: 1, duration: 1.35 }, 0);
    if (photos) tl.to(photos, { autoAlpha: 1, scale: 1, duration: 1.35 }, 0);
    if (orbits.length) {
      tl.to(orbits, { autoAlpha: 1, y: 0, duration: 0.65, stagger: 0.04 }, 0.15);
    }
    if (title) tl.to(title, { autoAlpha: 1, y: 0, duration: 1.05 }, 0.35);
    if (cta) {
      tl.to(cta, { autoAlpha: 1, y: 0, scale: 1, duration: 0.7, ease: 'back.out(1.5)' }, 0.65);
    }
    if (shopDesk) tl.to(shopDesk, { autoAlpha: 1, duration: 0.8 }, 0.55);

    /* Safety: if RAF/ticker stalls, still reveal + enable magnet */
    window.setTimeout(() => {
      if (tl.progress() < 1) tl.progress(1);
      armMagnet();
    }, 2200);
  }

  function initHeroMagnet() {
    if (reduceMotion || typeof gsap === 'undefined') return;
    if (!window.matchMedia('(pointer: fine)').matches) return;

    const stage = document.querySelector('.cu-hero__board--desk .cu-hero__stage--desk');
    if (!stage) return;
    const board = stage.closest('.cu-hero__board--desk');
    if (board && getComputedStyle(board).display === 'none') return;

    const photoEls = stage.querySelectorAll('.cu-photo');
    const svgEls = stage.querySelectorAll('.cu-magnet');
    const shopDesk = stage.querySelector('.cu-hero-shop--desk');
    if (!photoEls.length && !svgEls.length) return;

    /* Cursor near shape edge → push radially from stage center */
    const EDGE_PAD = 90;
    const items = [];

    function restOf(el) {
      const r = el.getBoundingClientRect();
      const x = parseFloat(gsap.getProperty(el, 'x')) || 0;
      const y = parseFloat(gsap.getProperty(el, 'y')) || 0;
      return {
        left: r.left - x,
        top: r.top - y,
        right: r.right - x,
        bottom: r.bottom - y,
        cx: (r.left + r.right) * 0.5 - x,
        cy: (r.top + r.bottom) * 0.5 - y,
      };
    }

    function makeItem(el, strength, linkEl) {
      gsap.set(el, { x: 0, y: 0, force3D: true });
      if (linkEl) gsap.set(linkEl, { x: 0, y: 0, force3D: true });
      const item = {
        el,
        linkEl: linkEl || null,
        strength,
        xTo: gsap.quickTo(el, 'x', { duration: 0.5, ease: 'power3.out' }),
        yTo: gsap.quickTo(el, 'y', { duration: 0.5, ease: 'power3.out' }),
        linkX: null,
        linkY: null,
      };
      if (linkEl) {
        item.linkX = gsap.quickTo(linkEl, 'x', { duration: 0.5, ease: 'power3.out' });
        item.linkY = gsap.quickTo(linkEl, 'y', { duration: 0.5, ease: 'power3.out' });
      }
      items.push(item);
    }

    function applyItem(item, x, y) {
      item.xTo(x);
      item.yTo(y);
      if (item.linkX) {
        item.linkX(x);
        item.linkY(y);
      }
    }

    photoEls.forEach((el) => makeItem(el, 14));
    svgEls.forEach((el) => {
      const s = parseFloat(el.getAttribute('data-magnet-strength')) || 8;
      const link = el.id === 'group-bottom' ? shopDesk : null;
      makeItem(el, s, link);
    });

    function edgeDist(px, py, rest) {
      const cx = Math.max(rest.left, Math.min(px, rest.right));
      const cy = Math.max(rest.top, Math.min(py, rest.bottom));
      const dx = px - cx;
      const dy = py - cy;
      return Math.sqrt(dx * dx + dy * dy);
    }

    function onMove(e) {
      const stageRect = stage.getBoundingClientRect();
      const ox = stageRect.left + stageRect.width * 0.5;
      const oy = stageRect.top + stageRect.height * 0.5;
      const px = e.clientX;
      const py = e.clientY;

      for (let i = 0; i < items.length; i++) {
        const item = items[i];
        const rest = restOf(item.el);
        const d = edgeDist(px, py, rest);
        if (d >= EDGE_PAD) {
          applyItem(item, 0, 0);
          continue;
        }
        const force = (1 - d / EDGE_PAD) ** 2;
        const rdx = rest.cx - ox;
        const rdy = rest.cy - oy;
        const rdist = Math.sqrt(rdx * rdx + rdy * rdy) || 1;
        applyItem(
          item,
          (rdx / rdist) * item.strength * force,
          (rdy / rdist) * item.strength * force
        );
      }
    }

    function onLeave() {
      for (let i = 0; i < items.length; i++) applyItem(items[i], 0, 0);
    }

    stage.addEventListener('pointermove', onMove);
    stage.addEventListener('pointerleave', onLeave);
  }

  function initReveals() {
    if (typeof gsap === 'undefined') {
      document.querySelectorAll('.reveal').forEach((el) => {
        el.style.opacity = '1';
        el.style.transform = 'none';
      });
      return;
    }
    if (reduceMotion) {
      gsap.set('.reveal', { clearProps: 'all', opacity: 1, y: 0 });
      return;
    }
    gsap.set('.reveal', { opacity: 0, y: 28 });
    ScrollTrigger.batch('.reveal', {
      start: 'top 92%',
      onEnter: (els) => {
        gsap.to(els, {
          opacity: 1,
          y: 0,
          duration: 0.9,
          ease: 'power3.out',
          stagger: 0.07,
          overwrite: true,
        });
      },
    });
  }

  document.addEventListener('DOMContentLoaded', () => {
    initNav();
    initLenis();
    initHeader();
    initHero();
    initReveals();
  });
})();
