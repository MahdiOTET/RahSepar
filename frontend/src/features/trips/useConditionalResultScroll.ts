import { useCallback, useEffect, useRef, useState } from "react";

function isVisible(element: HTMLElement): boolean {
  const bounds = element.getBoundingClientRect();
  return bounds.bottom > 0 && bounds.top < window.innerHeight;
}

function preferredScrollBehavior(): ScrollBehavior {
  return window.matchMedia("(prefers-reduced-motion: reduce)").matches
    ? "auto"
    : "smooth";
}

export function useConditionalResultScroll(loading: boolean) {
  const headingRef = useRef<HTMLDivElement>(null);
  const [pending, setPending] = useState(false);

  useEffect(() => {
    if (loading || !pending) return;

    const animationFrame = window.requestAnimationFrame(() => {
      const heading = headingRef.current;
      if (heading && !isVisible(heading)) {
        heading.scrollIntoView({
          behavior: preferredScrollBehavior(),
          block: "start",
        });
      }
      setPending(false);
    });

    return () => window.cancelAnimationFrame(animationFrame);
  }, [loading, pending]);

  const requestScroll = useCallback(() => setPending(true), []);
  return { headingRef, requestScroll };
}
