"use client";

import { useRef, useState } from "react";
import { createPortal } from "react-dom";

/**
 * Hover (mouse) / tap (touch) / keyboard tooltip. The bubble is portalled to
 * `document.body` and `position: fixed`, so it can't be clipped or painted over
 * by the table's stacking contexts.
 *
 * Touch taps synthesize a mouseenter + focus + click burst; without the
 * `lastPointerType` guard the enter/focus would open the bubble and the trailing
 * click would immediately toggle it back shut ("have to tap twice").
 */
export function Tooltip({
  text,
  children,
}: {
  text: string;
  children: React.ReactNode;
}) {
  const ref = useRef<HTMLSpanElement>(null);
  const lastPointerType = useRef<string>("");
  const [open, setOpen] = useState(false);
  const [pos, setPos] = useState({ x: 0, y: 0 });

  const place = () => {
    const r = ref.current?.getBoundingClientRect();
    if (r) setPos({ x: r.left + r.width / 2, y: r.bottom + 8 });
  };
  const openTip = () => {
    place();
    setOpen(true);
  };
  const closeTip = () => setOpen(false);
  const toggle = () => (open ? closeTip() : openTip());

  return (
    <span
      ref={ref}
      className="tip"
      tabIndex={0}
      onPointerDown={(e) => {
        lastPointerType.current = e.pointerType;
      }}
      onPointerEnter={(e) => {
        if (e.pointerType === "mouse") openTip();
      }}
      onPointerLeave={(e) => {
        if (e.pointerType === "mouse") closeTip();
      }}
      onClick={() => {
        // mouse hover already governs the mouse case
        if (lastPointerType.current !== "mouse") toggle();
      }}
      onFocus={() => {
        if (lastPointerType.current === "") openTip(); // keyboard focus only
      }}
      onBlur={() => {
        closeTip();
        lastPointerType.current = "";
      }}
      onKeyDown={(e) => {
        if (e.key === "Escape") closeTip();
        else if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          toggle();
        }
      }}
    >
      {children}
      {open &&
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
