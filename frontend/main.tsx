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
      springOptions={{ bounce: 0, duration: 0.4 }}
      className={cn(
        /* Translucent, and gone well before the edge: an opaque disc reads as a
           gold panel behind the card rather than light falling on it.
           blur-none cancels the component's own blur — spotlight-card.css
           blurs the box this sits in, which is what softens the clipped edge.
           Blurring twice only smears the light. */
        'bg-[radial-gradient(circle_at_center,rgba(217,178,95,0.55)_0%,rgba(201,150,45,0.22)_35%,transparent_70%)] blur-none',
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

  /* data-when: a media query the island needs before it is worth mounting.
     A decorative hover effect has no business running on a phone, where a tap
     fires mouseenter and the CSS that positions it never applies. */
  if (el.dataset.when && !window.matchMedia(el.dataset.when).matches) return;

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
