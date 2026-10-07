import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatINR(val: number | null | undefined): string {
  const num = typeof val === "number" && !isNaN(val) ? val : 0;
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 2
  }).format(num);
}

export function formatPercent(val: number | null | undefined): string {
  const num = typeof val === "number" && !isNaN(val) ? val : 0;
  const sign = num > 0 ? "+" : "";
  return `${sign}${num.toFixed(2)}%`;
}
