#!/usr/bin/env node

import fs from "node:fs";
import path from "node:path";
import { createRequire } from "node:module";
import { fileURLToPath, pathToFileURL } from "node:url";

const require = createRequire(import.meta.url);
const { chromium } = require(process.env.GALLERY_PLAYWRIGHT_MODULE || "playwright");
const repo = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const outputDir = path.join(repo, "docs", "screenshots");
fs.mkdirSync(outputDir, { recursive: true });

const browser = await chromium.launch({
  headless: true,
  executablePath: process.env.PLAYWRIGHT_CHROME || "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
});
const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
await page.emulateMedia({ reducedMotion: "reduce" });
await page.goto(pathToFileURL(path.join(repo, "index.html")).href);
await page.waitForSelector('.layout-card[data-id="350"]');
await page.locator(".layout-card").first().locator("img").waitFor({ state: "visible" });

const screenshot = (name) =>
  page.screenshot({
    path: path.join(outputDir, name),
    type: "jpeg",
    quality: 88,
    fullPage: false,
  });

await screenshot("gallery-overview.jpg");

const hoverCard = page.locator('.layout-card[data-id="044"]');
await hoverCard.scrollIntoViewIfNeeded();
await hoverCard.hover();
await page.waitForTimeout(260);
await screenshot("gallery-hover.jpg");

await hoverCard.locator(".card-trigger").click();
await page.waitForSelector("#detailDialog[open]");
await page.waitForFunction(() => !document.querySelector("#detailDialog")?.classList.contains("is-loading"));
await screenshot("gallery-detail.jpg");

await browser.close();
console.log(`gallery screenshots written to ${outputDir}`);
