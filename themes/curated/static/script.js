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
    const lenis = new Lenis({ autoRaf: false, lerp: 0.1 });
    lenis.on('scroll', ScrollTrigger.update);
    gsap.ticker.add((t) => lenis.raf(t * 1000));
    gsap.ticker.lagSmoothing(0);
    window.__cuLenis = lenis;
  }

  function initHero() {
    if (typeof gsap === 'undefined') return;
    const hero = document.querySelector('.cu-hero');
    if (!hero) return;

    const title = hero.querySelector('.cu-hero__title');
    const cta = hero.querySelector('.cu-hero__cta');
    const shapes = hero.querySelector('.cu-hero__board .cu-hero__shapes')
      || hero.querySelector('.cu-hero__shapes');
    const orbits = document.querySelectorAll('.cu-orbit');

    if (reduceMotion) return;

    // Scale from artboard center (within taller bleed viewBox), not SVG midpoint
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
    gsap.set(title, { autoAlpha: 0, filter: 'blur(10px)', y: 16 });
    gsap.set(cta, { autoAlpha: 0, y: 10, scale: 0.92 });
    gsap.set(orbits, { autoAlpha: 0, y: -8 });

    const tl = gsap.timeline({ defaults: { ease: 'power3.out' } });
    if (shapes) tl.to(shapes, { autoAlpha: 1, scale: 1, duration: 1.35 }, 0);
    tl.to(orbits, { autoAlpha: 1, y: 0, duration: 0.65, stagger: 0.04 }, 0.15)
      .to(title, { autoAlpha: 1, filter: 'blur(0px)', y: 0, duration: 1.05 }, 0.35)
      .to(cta, { autoAlpha: 1, y: 0, scale: 1, duration: 0.7, ease: 'back.out(1.5)' }, 0.65);
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
