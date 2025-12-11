import { useMemo } from "react";

/**
 * Resolve backend base URL with safe fallbacks:
 * 1) Explicit env override REACT_APP_BACKEND_URL if provided
 * 2) Try window.location.origin with port replaced 3000 -> 3001
 * 3) Fallback to current origin (useful if proxying) or last resort to http://localhost:3001
 */
export function resolveBackendBaseUrl() {
  const envUrl = process.env.REACT_APP_BACKEND_URL && process.env.REACT_APP_BACKEND_URL.trim();
  if (envUrl) return envUrl;

  if (typeof window !== "undefined" && window.location && window.location.origin) {
    try {
      const url = new URL(window.location.origin);
      if (url.port === "3000") {
        url.port = "3001";
        return url.toString();
      }
      // If running directly on 3001 already or via proxy, use origin
      return window.location.origin;
    } catch {
      // ignore
    }
  }
  return "http://localhost:3001";
}

/**
 * Normalize a single growth result row to frontend-friendly keys:
 * - absolute_return from abs_return
 * - data_points from points_count
 * Keeps original keys if already present.
 */
export function normalizeResultRow(row) {
  if (!row || typeof row !== "object") return row;
  const mapped = { ...row };
  if (mapped.absolute_return === undefined && mapped.abs_return !== undefined) {
    mapped.absolute_return = mapped.abs_return;
  }
  if (mapped.data_points === undefined && mapped.points_count !== undefined) {
    mapped.data_points = mapped.points_count;
  }
  return mapped;
}

/**
 * Perform POST to /analyze-growth and return {results, warnings}
 * Throws an Error with message for UI visibility on HTTP or network failures.
 */
export async function analyzeGrowth(payload) {
  const base = resolveBackendBaseUrl().replace(/\/+$/, "");
  const url = `${base}/analyze-growth`;
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  // Some failure modes still return 200 but with empty results and warnings.
  // If true HTTP error, surface clearly.
  if (!res.ok) {
    let msg = `Request failed (${res.status})`;
    try {
      const data = await res.json();
      if (data && (data.detail || data.message)) {
        msg = data.detail || data.message;
      }
    } catch {
      // ignore json parse error
    }
    throw new Error(msg);
  }

  const data = await res.json();
  const results = Array.isArray(data?.results) ? data.results.map(normalizeResultRow) : [];
  const warnings = Array.isArray(data?.warnings) ? data.warnings : [];
  return { results, warnings };
}
