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
import { cn } from '@/lib/utils';
import './tailwind.css';

import { Spotlight, type SpotlightProps } from '@/components/motion-primitives/spotlight';
import { TextEffect } from '@/components/motion-primitives/text-effect';

/* The product-card light, in Adorn's gold.

   The gradient is written out here rather than with from-/via-/to- classes:
   those resolve through --tw-gradient-stops, which needs the position variable
   that only the bg-linear and bg-radial utilities set. A plain arbitrary value
   needs none of that plumbing.

   It also has to live in a file Tailwind scans. The Django templates are
   deliberately out of scope — scanning them would mint utilities out of class
   names the site already styles itself (.container, .hidden), and those would
   land on top of the real ones. */
function CardSpotlight({ className, ...props }: SpotlightProps) {
  return (
    <Spotlight
      {...props}
      className={cn(
        'bg-[radial-gradient(circle_at_center,#D9B25F_0%,#C9962D_38%,transparent_72%)] blur-2xl',
        className
      )}
    />
  );
}

const registry: Record<string, ComponentType<any>> = {
  CardSpotlight,
  Spotlight,
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
