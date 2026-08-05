'use client';
import React, { useRef, useState, useCallback, useEffect } from 'react';
import { motion, useSpring, useTransform, SpringOptions } from 'motion/react';
import { cn } from '@/lib/utils';

export type SpotlightProps = {
  className?: string;
  size?: number;
  springOptions?: SpringOptions;
  /* Local addition. By default the spotlight both follows and is clipped by
     its own parent. Pass a selector and it follows the nearest ancestor
     matching it instead, while still being drawn (and clipped) inside the
     parent — which is how a product card lights the space around itself
     without anything landing on the photograph. */
  track?: string;
};

export function Spotlight({
  className,
  size = 200,
  springOptions = { bounce: 0 },
  track,
}: SpotlightProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [isHovered, setIsHovered] = useState(false);
  const [parentElement, setParentElement] = useState<HTMLElement | null>(null);
  /* The element the cursor is read from; the same as the parent unless
     `track` moves it up the tree. */
  const [hoverElement, setHoverElement] = useState<HTMLElement | null>(null);

  const mouseX = useSpring(0, springOptions);
  const mouseY = useSpring(0, springOptions);

  const spotlightLeft = useTransform(mouseX, (x) => `${x - size / 2}px`);
  const spotlightTop = useTransform(mouseY, (y) => `${y - size / 2}px`);

  useEffect(() => {
    if (containerRef.current) {
      const parent = containerRef.current.parentElement;
      if (parent) {
        /* Left to the stylesheet when tracking an ancestor: the parent is
           already positioned and clipped by then, and forcing it here would
           undo the offset that puts the light outside the card. */
        if (!track) {
          parent.style.position = 'relative';
          parent.style.overflow = 'hidden';
        }
        setParentElement(parent);
        setHoverElement((track && parent.closest<HTMLElement>(track)) || parent);
      }
    }
  }, [track]);

  const handleMouseMove = useCallback(
    (event: MouseEvent) => {
      if (!parentElement) return;
      /* Position stays relative to the parent it is drawn in, whichever
         element the cursor came from. */
      const { left, top } = parentElement.getBoundingClientRect();
      mouseX.set(event.clientX - left);
      mouseY.set(event.clientY - top);
    },
    [mouseX, mouseY, parentElement]
  );

  useEffect(() => {
    if (!hoverElement) return;

    const abortController = new AbortController();

    hoverElement.addEventListener('mousemove', handleMouseMove, {
      signal: abortController.signal,
    });
    hoverElement.addEventListener('mouseenter', () => setIsHovered(true), {
      signal: abortController.signal,
    });
    hoverElement.addEventListener('mouseleave', () => setIsHovered(false), {
      signal: abortController.signal,
    });

    return () => {
      abortController.abort();
    };
  }, [hoverElement, handleMouseMove]);

  return (
    <motion.div
      ref={containerRef}
      className={cn(
        'pointer-events-none absolute rounded-full bg-[radial-gradient(circle_at_center,var(--tw-gradient-stops),transparent_80%)] blur-xl transition-opacity duration-200',
        'from-zinc-100 via-zinc-200 to-zinc-400 dark:from-zinc-50 dark:via-zinc-100 dark:to-zinc-200',
        isHovered ? 'opacity-100' : 'opacity-0',
        className
      )}
      style={{
        width: size,
        height: size,
        left: spotlightLeft,
        top: spotlightTop,
      }}
    />
  );
}
