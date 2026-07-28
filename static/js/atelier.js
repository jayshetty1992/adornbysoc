/* ============================================================
   ADORN BY SOC — ATELIER MOTION (site-wide)
   Drives the GSAP + ScrollTrigger that base.html already loads.
   Loaded once, after gsap/Lenis, so every page gets the same
   motion grammar without any per-template wiring.

   Everything here is an enhancement: if this file never runs,
   or motion is reduced, the site renders complete and static.
   ============================================================ */
(function () {
  "use strict";

  var REDUCED = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var FINE = window.matchMedia("(pointer: fine)").matches;
  var gsap = window.gsap;

  /* ----------------------------------------------------------
     1. SCROLL REVEAL
     home.css ships .rv for the pages that load it; atelier.css
     hoists the same rules global. This is the one observer for
     the whole site — index.html's private copy was removed.
     ---------------------------------------------------------- */

  /* Pages built before .rv existed (product, collection, checkout,
     lookbook) get it applied here, so they animate without edits. */
  var AUTO_REVEAL = [
    ".pd-gallery", ".pd-side", ".pd-perks > *", ".pd-reviews",
    ".cl-card", ".coll-card", ".hero-grid > *",
    ".ck-card", ".ck-summary",
    ".lb-hero-copy", ".lb-grid > *", ".lb-split > *",
    ".prose > h2", ".prose > p", ".prose > ul",
    ".page-hero .jbx-h2", ".page-hero .lede"
  ].join(",");

  function reveal(el) { el.classList.add("in"); }

  /* Anything already on screen at load is content the visitor came for —
     a product image, a price, an Add to Bag. It renders immediately.
     Only what is below the fold is allowed to animate in. */
  function aboveFold(el) {
    var vh = window.innerHeight;
    if (!vh) return true;                    // no viewport to animate into
    return el.getBoundingClientRect().top < vh * 0.9;
  }

  function initReveal() {
    /* Some pages (collection list) ship their own .reveal/.is-visible
       system. Two systems animating the same element's opacity race each
       other and leave content blank. Theirs wins — we don't tag at all. */
    var pageHasOwnReveal = !!document.querySelector(".reveal");

    if (!pageHasOwnReveal) {
      document.querySelectorAll(AUTO_REVEAL).forEach(function (el, i) {
        if (el.closest(".rv")) return;        // already inside a revealed block
        el.classList.add("rv");
        if (!el.style.getPropertyValue("--rd")) {
          el.style.setProperty("--rd", (i % 6) * 70 + "ms");
        }
      });
    }

    var items = document.querySelectorAll(".rv");
    if (!items.length) return;

    if (!("IntersectionObserver" in window)) {
      items.forEach(reveal);
      return;
    }

    var io = new IntersectionObserver(function (entries, obs) {
      entries.forEach(function (e) {
        if (!e.isIntersecting) return;
        reveal(e.target);
        obs.unobserve(e.target);
      });
    }, { threshold: 0.12, rootMargin: "0px 0px -8% 0px" });

    items.forEach(function (el) {
      if (aboveFold(el)) {
        el.style.transition = "none";
        reveal(el);
        requestAnimationFrame(function () { el.style.transition = ""; });
      } else {
        io.observe(el);
      }
    });

    /* Safety net: nothing on this site is allowed to stay invisible
       because an observer misfired, or because the page was rendered
       in a zero-height viewport (hidden tab, print, headless capture).
       Unconditional on purpose — content beats choreography. */
    setTimeout(function () {
      document.querySelectorAll(".rv:not(.in)").forEach(reveal);
    }, 3000);
  }

  /* ----------------------------------------------------------
     2. HEADLINE WORD REVEAL
     The signature moment: display headings assemble word by word.
     Splits text nodes only, so <em>/<strong> markup survives.
     ---------------------------------------------------------- */
  /* Storytelling headlines only. The product title and price are never
     animated — nothing that closes a sale is allowed to arrive late. */
  var HEADLINES = ".jbx-h2, .ring-copy h1, .hero-title, .lb-hero h1, .page-hero .jbx-h2";

  function splitWords(el) {
    var words = [];
    (function walk(node) {
      Array.prototype.slice.call(node.childNodes).forEach(function (child) {
        if (child.nodeType === 3) {
          if (!child.textContent.trim()) return;
          var frag = document.createDocumentFragment();
          child.textContent.split(/(\s+)/).forEach(function (part) {
            if (!part) return;
            if (/^\s+$/.test(part)) {
              frag.appendChild(document.createTextNode(part));
              return;
            }
            var span = document.createElement("span");
            span.className = "rv-word";
            span.textContent = part;
            frag.appendChild(span);
            words.push(span);
          });
          node.replaceChild(frag, child);
        } else if (child.nodeType === 1 && child.tagName !== "BR") {
          walk(child);
        }
      });
    })(el);
    return words;
  }

  function initHeadlines() {
    if (!gsap || !window.ScrollTrigger) return;

    document.querySelectorAll(HEADLINES).forEach(function (el) {
      if (el.dataset.split) return;
      el.dataset.split = "1";

      var onScreen = aboveFold(el);
      var words = splitWords(el);
      if (!words.length || words.length > 40) return;   // don't shred long copy
      el.classList.add("rv-split");

      gsap.fromTo(words,
        { opacity: 0, filter: "blur(9px)" },
        {
          opacity: 1, filter: "blur(0px)",
          duration: onScreen ? 0.7 : 0.9,
          ease: "power3.out",
          stagger: 0.035,
          /* on screen at load = an entrance, plays at once.
             below the fold = waits for you to arrive. */
          scrollTrigger: onScreen ? null : { trigger: el, start: "top 88%", once: true }
        }
      );
    });
  }

  /* ----------------------------------------------------------
     3. MAGNETIC PRIMARY CTAs
     Was homepage-only and .btn-metal-only. Now every primary
     action on the site leans toward the cursor.
     ---------------------------------------------------------- */
  var MAGNETIC = ".btn-metal, .btn-gold, .btn-solid, .cs-checkout, .submit-btn, .btnpay, .policy-cta";

  function initMagnetic() {
    if (!FINE || !gsap) return;

    document.querySelectorAll(MAGNETIC).forEach(function (btn) {
      var toX = gsap.quickTo(btn, "x", { duration: 0.5, ease: "power3.out" });
      var toY = gsap.quickTo(btn, "y", { duration: 0.5, ease: "power3.out" });

      btn.addEventListener("mousemove", function (e) {
        var r = btn.getBoundingClientRect();
        toX((e.clientX - r.left - r.width / 2) * 0.22);
        toY((e.clientY - r.top - r.height / 2) * 0.32);
      });
      btn.addEventListener("mouseleave", function () { toX(0); toY(0); });
    });
  }

  /* ----------------------------------------------------------
     4. HEADER STATE + CURSOR LIGHT
     ---------------------------------------------------------- */
  function initChrome() {
    var root = document.documentElement;

    var onScroll = function () {
      root.classList.toggle("is-scrolled", window.scrollY > 40);
    };
    window.addEventListener("scroll", onScroll, { passive: true });
    /* Lenis drives the scroll and does not always emit a native scroll
       event (programmatic + immediate jumps don't), so listen to it too. */
    if (window.lenis && window.lenis.on) window.lenis.on("scroll", onScroll);
    onScroll();

    if (!FINE) return;
    root.classList.add("atelier-has-pointer");

    var raf = null, mx = 0, my = 0;
    window.addEventListener("mousemove", function (e) {
      mx = e.clientX; my = e.clientY;
      if (raf) return;
      raf = requestAnimationFrame(function () {
        raf = null;
        root.style.setProperty("--mx", mx + "px");
        root.style.setProperty("--my", my + "px");
      });
    }, { passive: true });
  }

  /* ----------------------------------------------------------
     5. ADD TO BAG — the piece flies to the cart
     The one micro-interaction that earns its keep: it confirms
     the add, and it shows you *where* the thing went.
     Runs alongside base.html's own [data-cart-add] handler.
     ---------------------------------------------------------- */
  function flyToBag(btn) {
    var cart = document.getElementById("cartBtn");
    var card = btn.closest(".bs-card, .pd-wrap, .cl-card, article, .card");
    var img = card && card.querySelector("img");
    if (!cart || !img || !gsap) return;

    var from = img.getBoundingClientRect();
    var to = cart.getBoundingClientRect();
    if (!from.width) return;

    var ghost = img.cloneNode();
    ghost.className = "fly-piece";
    ghost.style.left = from.left + "px";
    ghost.style.top = from.top + "px";
    ghost.style.width = from.width + "px";
    ghost.style.height = from.height + "px";
    document.body.appendChild(ghost);

    gsap.timeline({ onComplete: function () { ghost.remove(); } })
      .to(ghost, {
        left: to.left + to.width / 2, top: to.top + to.height / 2,
        width: 22, height: 22, opacity: 0.25, rotate: 14,
        xPercent: -50, yPercent: -50,
        duration: 0.85, ease: "power2.in"
      });
  }

  function initCartFeedback() {
    document.addEventListener("click", function (e) {
      var btn = e.target.closest("[data-cart-add]");
      if (btn && !REDUCED) flyToBag(btn);
    });

    /* base.html rewrites the badge text on every cart change —
       watch it rather than duplicating the fetch logic. */
    var badge = document.getElementById("cartCount");
    if (!badge || REDUCED) return;

    new MutationObserver(function () {
      badge.classList.remove("pop");
      void badge.offsetWidth;              // restart the keyframe
      badge.classList.add("pop");
    }).observe(badge, { childList: true, characterData: true, subtree: true });
  }

  /* ----------------------------------------------------------
     6. PAGE VEIL
     Django serves full page loads. The veil covers the white
     flash between them so navigation reads as one continuous
     surface instead of a reload.
     ---------------------------------------------------------- */
  function initVeil() {
    if (REDUCED || !gsap) return;

    var veil = document.querySelector(".atelier-veil");
    if (!veil) return;

    document.addEventListener("click", function (e) {
      var a = e.target.closest("a[href]");
      if (!a) return;
      if (a.target === "_blank" || a.hasAttribute("download")) return;
      if (a.dataset.cartAdd || a.dataset.wish) return;

      var href = a.getAttribute("href");
      if (!href || href.charAt(0) === "#" || /^(mailto|tel|javascript):/i.test(href)) return;
      if (a.origin && a.origin !== window.location.origin) return;
      if (a.pathname === window.location.pathname && a.search === window.location.search) return;
      if (e.metaKey || e.ctrlKey || e.shiftKey || e.button !== 0) return;

      var href = a.href;
      e.preventDefault();
      veil.style.visibility = "visible";
      gsap.to(veil, { opacity: 1, duration: 0.32, ease: "power2.in" });

      /* The timer owns the navigation, never the tween. requestAnimationFrame
         is throttled in background tabs and low-power mode, and an onComplete
         that never fires would strand the visitor on the page they just left. */
      setTimeout(function () { window.location.href = href; }, 320);
    });

    /* Back/forward can restore a cached page with the veil still up. */
    window.addEventListener("pageshow", function (ev) {
      if (!ev.persisted) return;
      gsap.killTweensOf(veil);
      veil.style.opacity = "";
      veil.style.visibility = "";
    });
  }

  /* ---------------------------------------------------------- */
  function boot() {
    initReveal();
    initChrome();
    initCartFeedback();
    if (REDUCED) return;
    initHeadlines();
    initMagnetic();
    initVeil();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
