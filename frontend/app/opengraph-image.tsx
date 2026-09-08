import { ImageResponse } from "next/og";

export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

export default function OpengraphImage() {
  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          alignItems: "center",
          backgroundColor: "#17171b",
          backgroundImage:
            "radial-gradient(1200px 600px at 50% -10%, rgba(99,102,241,0.35), transparent 70%)",
          color: "#f6f7f9",
          fontFamily: "sans-serif",
        }}
      >
        <div
          style={{
            fontSize: 28,
            letterSpacing: 6,
            textTransform: "uppercase",
            color: "#a5a8ff",
          }}
        >
          IRONMAN Pro Series · 2026
        </div>
        <div
          style={{
            display: "flex",
            fontSize: 88,
            fontWeight: 700,
            marginTop: 20,
          }}
        >
          Pro Series Standings
        </div>
        <div style={{ display: "flex", fontSize: 32, marginTop: 24, color: "#9096a1" }}>
          Every athlete&rsquo;s ceiling — the most points they could still score
        </div>
      </div>
    ),
    { ...size },
  );
}
