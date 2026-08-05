/* ============================================================
   ADORN BY SOC — REACT ISLANDS
   Django renders the page; React only takes over the elements that
   ask for it. Mark one up in any template:

     <div data-react="TextEffect"
          data-props='{"children": "Adorn by SOC", "per": "char"}'></div>

   and load this bundle on that page (see templates/dev/motion.html).
   Pages without an island pay nothing — the bundle is opt-in per
   template, not loaded in base.html.

   To add a component:
     npx motion-primitives@latest add <name>
   then import it below and put it in the registry.
   ============================================================ */
import type { ComponentType } from 'react';
import { createRoot } from 'react-dom/client';
import './tailwind.css';

import { TextEffect } from '@/components/motion-primitives/text-effect';

const registry: Record<string, ComponentType<any>> = {
  TextEffect,
};

document.querySelectorAll<HTMLElement>('[data-react]').forEach((el) => {
  const name = el.dataset.react!;
  const Component = registry[name];
  if (!Component) {
    console.warn(`[islands] no component registered as "${name}"`, el);
    return;
  }

  let props: Record<string, unknown> = {};
  if (el.dataset.props) {
    try {
      props = JSON.parse(el.dataset.props);
    } catch {
      /* A malformed data-props would otherwise take down every island after
         it — skip this one and leave the rest of the page alone. */
      console.warn(`[islands] "${name}" has unparseable data-props`, el);
      return;
    }
  }

  createRoot(el).render(<Component {...props} />);
});
