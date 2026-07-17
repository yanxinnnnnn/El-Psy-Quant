// @vitest-environment node

import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

import { describe, expect, it } from "vitest";

const css = readFileSync(fileURLToPath(new URL("./globals.css", import.meta.url)), "utf8");

function tokenHex(name: string): string {
  const match = css.match(new RegExp(`${name}:\\s*(#[0-9a-fA-F]{6});`));
  if (!match) throw new Error(`Missing hex token ${name}`);
  return match[1];
}

function luminance(hex: string): number {
  const channels = [1, 3, 5].map((offset) => Number.parseInt(hex.slice(offset, offset + 2), 16) / 255)
    .map((channel) => channel <= 0.04045 ? channel / 12.92 : ((channel + 0.055) / 1.055) ** 2.4);
  return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2];
}

function contrast(first: string, second: string): number {
  const firstLuminance = luminance(first);
  const secondLuminance = luminance(second);
  return (Math.max(firstLuminance, secondLuminance) + 0.05) /
    (Math.min(firstLuminance, secondLuminance) + 0.05);
}

describe("Founder Web visual-system contract", () => {
  it("owns the required semantic tokens in one root system", () => {
    for (const token of [
      "--color-canvas",
      "--color-surface-primary",
      "--color-surface-elevated",
      "--color-surface-muted",
      "--color-surface-inset",
      "--color-text-primary",
      "--color-text-secondary",
      "--color-border-subtle",
      "--color-border-strong",
      "--color-accent",
      "--color-link",
      "--color-focus",
      "--color-state-neutral",
      "--color-state-info",
      "--color-state-success",
      "--color-state-warning",
      "--color-state-danger",
      "--color-state-unavailable",
      "--color-state-disabled",
      "--color-demo",
      "--font-sans",
      "--font-mono",
      "--space-4",
      "--radius-medium",
      "--border-subtle",
      "--elevation-raised",
      "--control-height",
      "--motion-standard",
      "--breakpoint-narrow",
      "--breakpoint-tablet",
      "--breakpoint-desktop",
    ]) {
      expect(css).toContain(`${token}:`);
    }

    expect(css).toContain("--canvas: var(--color-canvas);");
    expect(css).not.toMatch(/--canvas:\s*#/);
    expect(css).not.toMatch(/font-family:\s*(?:Inter|Georgia)/);
    expect(css).not.toContain("backdrop-filter");
    expect(css).not.toContain("radial-gradient");
  });

  it("defines bounded responsive, raw-value, table, focus, and reduced-motion behavior", () => {
    expect(css).toContain("@media (max-width: 1024px)");
    expect(css).toContain("@media (max-width: 767px)");
    expect(css).toContain("@media (max-width: 480px)");
    expect(css).toContain("@media (prefers-reduced-motion: reduce)");
    expect(css).toMatch(/\.table-scroll\s*\{[\s\S]*?overflow-x:\s*auto;/);
    expect(css).toMatch(/code,[\s\S]*?pre\s*\{[\s\S]*?overflow-wrap:\s*anywhere;/);
    expect(css).toContain("outline: 3px solid var(--color-focus)");
    expect(css).toContain("transition-duration: 0.01ms !important");
  });

  it("uses the opaque semantic focus token for language-switcher options", () => {
    const rule = css.match(/\.language-switcher__option:focus-visible\s*\{([^}]*)\}/)?.[1];
    expect(rule).toBeDefined();
    expect(rule).toMatch(/outline:\s*3px solid var\(--color-focus\);/);
  });

  it("keeps body, interaction, operational-state, and Demo text at AA contrast", () => {
    for (const [foreground, background] of [
      ["--color-text-primary", "--color-surface-primary"],
      ["--color-text-secondary", "--color-surface-primary"],
      ["--color-text-tertiary", "--color-surface-primary"],
      ["--color-accent", "--color-surface-primary"],
      ["--color-link", "--color-surface-primary"],
      ["--color-focus", "--color-canvas"],
      ["--color-state-neutral", "--color-state-neutral-soft"],
      ["--color-state-info", "--color-state-info-soft"],
      ["--color-state-success", "--color-state-success-soft"],
      ["--color-state-warning", "--color-state-warning-soft"],
      ["--color-state-danger", "--color-state-danger-soft"],
      ["--color-state-unavailable", "--color-state-unavailable-soft"],
      ["--color-demo", "--color-demo-surface"],
    ]) {
      expect(contrast(tokenHex(foreground), tokenHex(background))).toBeGreaterThanOrEqual(4.5);
    }
    expect(contrast(tokenHex("--color-state-disabled"), tokenHex("--color-state-disabled-soft")))
      .toBeGreaterThanOrEqual(3);
  });

  it("provides the complete action, state, disclosure, and Demo class contracts", () => {
    for (const selector of [
      ".primary-button",
      ".secondary-button",
      ".quiet-button",
      ".warning-button",
      ".danger-button",
      ".status-badge--neutral",
      ".status-badge--info",
      ".status-badge--success",
      ".status-badge--warning",
      ".status-badge--danger",
      ".status-badge--unavailable",
      ".state-panel--loading",
      ".state-panel--empty",
      ".state-panel--error",
      ".audit-disclosure",
      ".demo-identity",
    ]) {
      expect(css).toContain(selector);
    }
    expect(css).not.toContain(".retry-button");
    expect(css).not.toContain(".job-status");
  });
});
