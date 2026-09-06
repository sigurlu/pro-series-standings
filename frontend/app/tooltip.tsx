"use client";

import { useRef, useState } from "react";
import { createPortal } from "react-dom";

/**
 * Hover / focus / tap tooltip. The bubble is portalled to `document.body` and
 * `position: fixed`, so it can't be clipped or painted over by the table's
 * stacking contexts.
 */
export function Tooltip({
  text,
  children,
}: {
  text: string;
  children: React.ReactNode;
}) {
  const ref = useRef<HTMLSpanElement>(null);
  const [pos, setPos] = useState<{ x: number; y: number } | null>(null);

  const show = () => {
    const r = ref.current?.getBoundingClientRect();
    if (r) setPos({ x: r.left + r.width / 2, y: r.bottom + 8 });
  };
  const hide = () => setPos(null);

  return (
    <span
      ref={ref}
      className="tip"
      tabIndex={0}
      onMouseEnter={show}
      onMouseLeave={hide}
      onFocus={show}
      onBlur={hide}
      onClick={() => (pos ? hide() : show())}
    >
      {children}
      {pos &&
        typeof document !== "undefined" &&
        createPortal(
          <span
            role="tooltip"
            className="tip-bubble"
            style={{ left: pos.x, top: pos.y }}
          >
            {text}
          </span>,
          document.body,
        )}
    </span>
  );
}
