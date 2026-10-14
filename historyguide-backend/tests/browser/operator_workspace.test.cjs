"use strict";

// Run against a newly created, isolated local database; never use a live URL/key.
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const crypto = require("node:crypto");
const net = require("node:net");
const { spawn } = require("node:child_process");
const { chromium } = require("playwright");

const root = path.resolve(__dirname, "../..");
const python = process.platform === "win32"
  ? path.join(root, ".venv/Scripts/python.exe") : path.join(root, ".venv/bin/python");
const artifactDir = path.join(root, ".local/browser-artifacts");
fs.mkdirSync(artifactDir, { recursive: true });
const database = path.join(artifactDir, `browser-${crypto.randomUUID()}.db`);
const operatorKey = crypto.randomBytes(32).toString("hex");
const businessKey = crypto.randomBytes(32).toString("hex");
const env = { ...process.env, PYTHONIOENCODING: "utf-8", HISTORYGUIDE_DATABASE_URL: `sqlite:///${database.replaceAll("\\", "/")}`,
  HISTORYGUIDE_SCHEMA_MODE: "auto_create", HISTORYGUIDE_API_KEY: businessKey,
  HISTORYGUIDE_OPERATOR_API_KEY: operatorKey, HISTORYGUIDE_LOG_LEVEL: "WARNING", HISTORYGUIDE_CORS_ORIGINS: "" };
for (const name of ["HISTORYGUIDE_API_KEY_FILE", "HISTORYGUIDE_API_KEY_NEXT", "HISTORYGUIDE_API_KEY_NEXT_FILE", "HISTORYGUIDE_OPERATOR_API_KEY_FILE"]) delete env[name];

async function freePort() {
  const server = net.createServer();
  await new Promise((resolve, reject) => { server.once("error", reject); server.listen(0, "127.0.0.1", resolve); });
  const port = server.address().port;
  await new Promise((resolve) => server.close(resolve));
  return port;
}

async function waitForServer(baseUrl, child) {
  for (let attempt = 0; attempt < 100; attempt++) {
    if (child.exitCode !== null) throw new Error("Isolated test server stopped before readiness.");
    try { if ((await fetch(`${baseUrl}/ready`)).ok) return; } catch { /* Startup in progress. */ }
    await new Promise((resolve) => setTimeout(resolve, 100));
  }
  throw new Error("Isolated test server did not become ready.");
}

async function removeTestDatabase() {
  // Only this run's random database and its SQLite sidecars may be removed.
  assert.equal(path.dirname(database), artifactDir);
  assert.match(path.basename(database), /^browser-[0-9a-f-]{36}\.db$/);
  for (const suffix of ["", "-journal", "-wal", "-shm"]) {
    for (let attempt = 0; attempt < 12; attempt++) {
      try { await fs.promises.unlink(database + suffix); break; }
      catch (error) {
        if (error.code === "ENOENT") break;
        if (!["EBUSY", "EPERM", "EACCES"].includes(error.code) || attempt === 11) throw error;
        await new Promise((resolve) => setTimeout(resolve, 150 * (attempt + 1)));
      }
    }
  }
}

async function run() {
  const port = await freePort();
  const baseUrl = `http://127.0.0.1:${port}`;
  const child = spawn(python, ["-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", String(port)], { cwd: root, env, stdio: "pipe", windowsHide: true });
  // 'close' waits for the child AND its stdio handles, unlike 'exit'.
  const childClosed = new Promise((resolve) => child.once("close", resolve));
  let processError;
  child.on("error", (error) => { processError = error; });
  let startupError = "";
  child.stderr.on("data", (chunk) => { startupError += chunk.toString(); });
  child.stdout.resume();
  let browser;
  try {
    await waitForServer(baseUrl, child);
    if (processError) throw processError;
    const candidates = [process.env.BROWSER_EXECUTABLE_PATH,
      "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe", "C:/Program Files/Google/Chrome/Application/chrome.exe"];
    const executablePath = candidates.find((candidate) => candidate && fs.existsSync(candidate));
    browser = await chromium.launch({ headless: true, ...(executablePath ? { executablePath } : {}) });
    const context = await browser.newContext({ viewport: { width: 1440, height: 1100 } });
    const page = await context.newPage();
    const pageErrors = [];
    page.on("pageerror", (error) => pageErrors.push(error.message));
    const requests = [];
    page.on("request", (request) => requests.push(request));
    const checks = [];

    await page.goto(`${baseUrl}/operator`);
    await page.screenshot({ path: path.join(artifactDir, "login-desktop.png"), fullPage: true });
    await page.locator("#operator-key").fill("invalid-local-test-key");
    await page.locator("#reviewer").fill("Browser test reviewer");
    await page.locator("#login-form button").click();
    await page.waitForFunction(() => document.getElementById("notice").textContent.includes("密钥无效"));
    assert.equal(await page.locator("#workspace").isVisible(), false);
    checks.push("invalid key fails closed");

    await page.locator("#operator-key").fill(operatorKey);
    await page.locator("#reviewer").fill("Browser test reviewer");
    await page.locator("#login-form button").click();
    await page.waitForFunction(() => document.getElementById("draft-count").textContent === "0");
    assert.equal(await page.locator("#operator-key").inputValue(), "");
    assert.equal(await page.evaluate(() => localStorage.length + sessionStorage.length), 0);
    checks.push("authenticated connection without key persistence");

    const sources = [{ id: "browser-S01", title: '<img src=x onerror="window.injected=true">',
      source_uri: "javascript:window.injected=true", content_text: "Non-historical browser test excerpt. <script>window.injected=true</script>" }];
    await page.locator("#batch-json").fill(JSON.stringify({ sources }));
    await page.locator("#preview-batch").click();
    await page.locator("#preview-panel").waitFor({ state: "visible" });
    assert.equal(await page.locator("#draft-count").textContent(), "0");
    await page.locator("#batch-json").fill(JSON.stringify({ sources }, null, 2));
    assert.equal(await page.locator("#preview-panel").isVisible(), false);
    await page.locator("#preview-batch").click();
    await page.locator("#preview-panel").waitFor({ state: "visible" });
    await page.locator("#intake-confirm").check();
    await page.locator("#import-batch").click();
    await page.waitForFunction(() => document.getElementById("draft-count").textContent === "1");
    checks.push("read-only preview, invalidation on edit, and draft import");

    await page.locator("#records-body button").first().click();
    await page.locator("#detail-dialog").waitFor({ state: "visible" });
    assert.equal(await page.locator("#detail-content script").count(), 0);
    assert.equal(await page.locator("#detail-title img").count(), 0);
    assert.equal(await page.locator("#detail-meta a").count(), 0);
    assert.equal(await page.evaluate(() => window.injected), undefined);
    await page.locator("#review-confirm").check();
    await page.locator("#approve-record").click();
    await page.waitForFunction(() => document.getElementById("approved-count").textContent === "1");
    await page.locator("#close-detail").click();
    checks.push("source approval and inert untrusted text/URI");

    await page.locator("#batch-kind").selectOption("exhibits");
    const exhibits = [{ id: "browser-exhibit", name: "Non-historical browser exhibit", description: "Local test record, not museum evidence.",
      period: "test", importance: 3, source_reference: "local-browser-test:record" }];
    await page.locator("#batch-json").fill(JSON.stringify(exhibits));
    await page.locator("#preview-batch").click();
    await page.locator("#preview-panel").waitFor({ state: "visible" });
    await page.locator("#intake-confirm").check();
    await page.locator("#import-batch").click();
    await page.waitForFunction(() => document.getElementById("exhibit-count").textContent === "1");
    await page.locator('[data-tab="exhibits"]').click();
    await page.locator("#records-body button").first().click();
    await page.locator("#link-source-id").fill("browser-S01");
    await page.locator("#link-form button").click();
    await page.waitForFunction(() => document.getElementById("detail-meta").textContent.includes("关联来源：browser-S01"));
    await page.locator("#review-confirm").check();
    await page.locator("#approve-record").click();
    await page.waitForFunction(() => document.getElementById("detail-meta").textContent.includes("审批与快照一致"));
    await page.locator("#close-detail").click();
    checks.push("exhibit intake, source linking, and approval");

    await page.locator('[data-tab="sources"]').click();
    await page.locator("#status-filter").selectOption("approved");
    await page.locator("#records-body button").first().click();
    await page.locator("#review-confirm").check();
    await page.locator("#revoke-record").click();
    await page.waitForFunction(() => document.getElementById("approved-count").textContent === "0");
    await page.locator("#close-detail").click();
    await page.locator('[data-tab="exhibits"]').click();
    await page.waitForFunction(() => document.getElementById("records-body").textContent.includes("需重新核对"));
    await page.locator("#batch-json").fill("");
    await page.screenshot({ path: path.join(artifactDir, "workspace-desktop.png"), fullPage: true });
    checks.push("source revocation invalidates exhibit approval");

    await page.locator('[data-tab="audit"]').click();
    await page.waitForFunction(() => document.getElementById("records-body").textContent.includes("exhibit_approved"));
    checks.push("audit trail visible");

    await page.locator('[data-tab="exhibits"]').click();
    await page.setViewportSize({ width: 390, height: 844 });
    await page.waitForFunction(() => document.getElementById("records-body").textContent.includes("需重新核对"));
    assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth));
    await page.screenshot({ path: path.join(artifactDir, "workspace-mobile.png"), fullPage: true });
    await page.setViewportSize({ width: 320, height: 720 });
    assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth));
    await page.setViewportSize({ width: 390, height: 844 });
    checks.push("mobile layout without page overflow");

    let releasePreview;
    const previewArrived = new Promise((resolve) => {
      releasePreview = { arrived: resolve };
    });
    await page.route("**/api/evidence/exhibits/batch/preview", async (route) => {
      const hold = new Promise((resolve) => { releasePreview.continue = resolve; });
      releasePreview.arrived();
      await hold;
      await route.continue();
    });
    await page.locator("#batch-json").fill(JSON.stringify([{ ...exhibits[0], id: "browser-preview-only" }]));
    await page.locator("#preview-batch").click();
    await previewArrived;
    await page.locator("#batch-json").fill("new text while preview is in flight");
    const latePreviewResponse = page.waitForResponse((response) => response.url().endsWith("/exhibits/batch/preview"));
    releasePreview.continue();
    await (await latePreviewResponse).finished();
    await page.evaluate(() => new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve))));
    assert.equal(await page.locator("#preview-panel").isVisible(), false);
    assert.equal(await page.locator("#import-batch").isEnabled(), false);
    assert.equal(await page.locator("#preview-batch").isEnabled(), true);
    await page.unroute("**/api/evidence/exhibits/batch/preview");
    checks.push("late preview cannot revalidate edited input");

    // A late file decoding error must not erase a subsequent manual edit.
    await page.evaluate(() => {
      window.originalArrayBuffer = File.prototype.arrayBuffer;
      File.prototype.arrayBuffer = function () {
        return new Promise((resolve) => { window.resolveFileRead = resolve; });
      };
    });
    await page.locator("#batch-file").setInputFiles({ name: "delayed.json", mimeType: "application/json", buffer: Buffer.from([255]) });
    await page.waitForFunction(() => typeof window.resolveFileRead === "function");
    await page.locator("#batch-json").fill("manual replacement survives delayed file error");
    await page.evaluate(async () => {
      window.resolveFileRead(new Uint8Array([255]).buffer);
      await new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve)));
      File.prototype.arrayBuffer = window.originalArrayBuffer;
      delete window.originalArrayBuffer;
      delete window.resolveFileRead;
    });
    assert.equal(await page.locator("#batch-json").inputValue(), "manual replacement survives delayed file error");
    checks.push("late invalid UTF-8 file does not overwrite a newer edit");

    // Closing a dialog during a mutation must keep it closed on success.
    await page.locator("#records-body button").first().click();
    await page.locator("#detail-dialog").waitFor({ state: "visible" });
    let releaseRevoke;
    const revokeArrived = new Promise((resolve) => {
      releaseRevoke = { arrived: resolve };
    });
    await page.route("**/api/evidence/exhibits/browser-exhibit/revoke", async (route) => {
      const hold = new Promise((resolve) => { releaseRevoke.continue = resolve; });
      releaseRevoke.arrived();
      await hold;
      await route.continue();
    });
    await page.locator("#review-confirm").check();
    await page.locator("#revoke-record").click();
    await revokeArrived;
    await page.locator("#close-detail").click();
    const refreshedAfterRevoke = page.waitForResponse((response) => response.url().includes("evidence/exhibits?limit=20") && response.ok());
    releaseRevoke.continue();
    await refreshedAfterRevoke;
    await page.waitForFunction(() => !document.getElementById("refresh").disabled);
    assert.equal(await page.locator("#detail-dialog").isVisible(), false);
    await page.unroute("**/api/evidence/exhibits/browser-exhibit/revoke");
    checks.push("completed review does not reopen a dismissed detail dialog");

    // Expiration while list requests are running clears all displayed records.
    await page.route("**/api/evidence/exhibits?limit=20&offset=0", (route) => route.fulfill({ status: 401, contentType: "application/json", body: '{"detail":"unauthorized"}' }));
    await page.locator("#refresh").click();
    await page.locator("#login-panel").waitFor({ state: "visible" });
    assert.equal(await page.locator("#records-body").textContent(), "");
    assert.equal(await page.locator("#draft-count").textContent(), "—");
    await page.unroute("**/api/evidence/exhibits?limit=20&offset=0");
    await page.locator("#operator-key").fill(operatorKey);
    await page.locator("#reviewer").fill("Browser test reviewer");
    await page.locator("#login-form button").click();
    await page.waitForFunction(() => !document.getElementById("refresh").disabled && !document.getElementById("workspace").hidden);
    checks.push("401 cancels in-flight list results and supports a fresh connection");

    // A detail result delivered after logout must not restore the dialog.
    let releaseDetail;
    const detailArrived = new Promise((resolve) => {
      releaseDetail = { arrived: resolve };
    });
    await page.route("**/api/evidence/exhibits/browser-exhibit", async (route) => {
      const hold = new Promise((resolve) => { releaseDetail.continue = resolve; });
      releaseDetail.arrived();
      await hold;
      try { await route.continue(); } catch { /* Logout can abort this held request. */ }
    });
    await page.locator("#records-body button").first().click();
    await detailArrived;

    await page.locator("#disconnect").click();
    releaseDetail.continue();
    await page.evaluate(() => new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve))));
    assert.equal(await page.locator("#login-panel").isVisible(), true);
    assert.equal(await page.locator("#records-body").textContent(), "");
    assert.equal(await page.locator("#batch-json").inputValue(), "");
    assert.equal(await page.locator("#detail-dialog").isVisible(), false);
    checks.push("logout clears credentials and ignores a late detail result");
    assert.deepEqual(pageErrors, []);
    for (const request of requests) {
      assert.ok(!request.url().includes(operatorKey));
      assert.ok(!request.url().includes(businessKey));
      if (request.url().includes("/api/")) assert.equal(request.headers()["x-historyguide-api-key"], undefined);
    }
    fs.writeFileSync(path.join(artifactDir, "browser-check.json"), JSON.stringify({ checks, passed: checks.length, pageErrors }, null, 2));
    console.log(JSON.stringify({ passed: checks.length, checks, artifacts: artifactDir }, null, 2));
  } catch (error) {
    // Do not emit request objects, headers, source bodies, or generated keys.
    console.error(error.message);
    const testFrame = error.stack?.split("\n").find((line) => line.includes("operator_workspace.test.cjs:"));
    if (testFrame) console.error(testFrame.trim());
    if (!browser && startupError) console.error(startupError.replaceAll(operatorKey, "[redacted]").replaceAll(businessKey, "[redacted]"));
    process.exitCode = 1;
  } finally {
    if (browser) await browser.close();
    if (child.exitCode === null) child.kill();
    await childClosed;
    await removeTestDatabase();
  }
}

run().catch((error) => { console.error(error.message); process.exitCode = 1; });
