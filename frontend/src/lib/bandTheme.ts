import type { AssessResponse } from "@/lib/api";

export type BandKey = AssessResponse["band"];

export function bandTheme(band: BandKey) {
  switch (band) {
    case "green":
      return {
        ring: "ring-emerald-500/30",
        bg: "bg-emerald-500/10",
        text: "text-emerald-800",
        badge: "bg-emerald-600 text-white",
        bar: "bg-emerald-500",
      };
    case "yellow":
      return {
        ring: "ring-amber-400/40",
        bg: "bg-amber-500/10",
        text: "text-amber-900",
        badge: "bg-amber-500 text-white",
        bar: "bg-amber-500",
      };
    case "orange":
      return {
        ring: "ring-orange-400/40",
        bg: "bg-orange-500/10",
        text: "text-orange-950",
        badge: "bg-orange-600 text-white",
        bar: "bg-orange-500",
      };
    default:
      return {
        ring: "ring-rose-400/40",
        bg: "bg-rose-500/10",
        text: "text-rose-950",
        badge: "bg-rose-600 text-white",
        bar: "bg-rose-500",
      };
  }
}
