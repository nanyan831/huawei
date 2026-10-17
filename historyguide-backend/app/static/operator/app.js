"use strict";

(() => {
  const $ = (id) => document.getElementById(id);
  const PAGE_SIZE = 20;
  const MAX_FILE_BYTES = 8 * 1024 * 1024;
  const statusNames = { draft: "待审核", approved: "已批准", revoked: "已撤销" };
  let key = "";
  let reviewer = "";
  let tab = "sources";
  let offset = 0;
  let epoch = 0;
  let listVersion = 0;
  let intakeVersion = 0;
  let detailVersion = 0;
  let claimVersion = 0;
  let claimDetailVersion = 0;
  let claimOffset = 0;
  let claimSelected = null;
  let preview = null;
  let selected = null;
  let writing = false;
  let controller = new AbortController();

  const formats = {
    sources: { sources: [{ id: "S01", title: "资料标题", source_uri: "museum-archive:原始档案号", content_text: "在此填写经人工核对的原文摘录" }] },
    exhibits: { exhibits: [{ id: "museum-001", name: "展品名称", description: "经核对的展品描述", period: "所属时期", importance: 3, keywords: [], people: [], themes: [], source_reference: "可追溯的原始档案引用" }] },
  };

  function showMessage(text, error = false, target = "notice") {
    const node = $(target);
    node.textContent = text;
    node.classList.toggle("error", error);
    node.hidden = false;
  }

  function isCancelled(error) { return error.name === "AbortError"; }
  function report(error, target = "notice") {
    if (!isCancelled(error)) showMessage(error.message, true, target);
  }

  function resetConnection() {
    epoch += 1;
    controller.abort();
    controller = new AbortController();
    key = "";
    reviewer = "";
    selected = null;
    preview = null;
    writing = false;
    listVersion += 1;
    intakeVersion += 1;
    detailVersion += 1;
    claimVersion += 1;
    claimDetailVersion += 1;
    claimSelected = null;
    claimOffset = 0;
    $("operator-key").value = "";
    $("reviewer").value = "";
    $("workspace").hidden = true;
    $("login-panel").hidden = false;
    $("disconnect").hidden = true;
    $("connection-state").textContent = "尚未连接";
    $("records-body").replaceChildren();
    $("detail-dialog").close();
    $("claim-dialog").close();
    $("claim-rows").replaceChildren();
    for (const id of ["claim-source-id", "claim-quote", "claim-text"]) $(id).value = "";
    $("claim-source-content").textContent = "";
    $("claim-detail-quote").textContent = "";
    $("claim-detail-text").textContent = "";
    $("claim-page-status").textContent = "尚未载入";
    $("detail-content").textContent = "";
    $("detail-title").textContent = "";
    $("reviewer-label").textContent = "";
    $("detail-meta").replaceChildren();
    for (const id of ["draft-count", "approved-count", "exhibit-count"]) $(id).textContent = "—";
    $("batch-json").value = "";
    $("batch-file").value = "";
    $("single-exhibit-form").reset();
    $("exhibit-importance").value = "3";
    $("preview-batch").disabled = false;
    $("page-status").textContent = "尚未载入";
    $("previous").disabled = true;
    $("next").disabled = true;
    invalidatePreview();
    updateSingleExhibitForm();
  }

  async function api(path, { method = "GET", payload } = {}) {
    const startedEpoch = epoch;
    const response = await fetch(`/api/${path}`, {
      method,
      headers: { "X-HistoryGuide-Operator-Key": key, ...(payload ? { "Content-Type": "application/json" } : {}) },
      body: payload ? JSON.stringify(payload) : undefined,
      cache: "no-store",
      credentials: "omit",
      redirect: "error",
      signal: controller.signal,
    });
    if (startedEpoch !== epoch) throw new DOMException("连接已结束", "AbortError");
    if (response.status === 401) {
      resetConnection();
      throw new Error("操作员密钥无效或已撤销，请重新连接。");
    }
    if (response.status === 503) throw new Error("服务尚未配置操作员密钥，请由部署负责人完成配置。");
    if (response.status === 413) throw new Error("上传内容超过 8 MiB，请拆分为较小批次。");
    if (response.status >= 500) throw new Error("服务暂时不可用。请保留当前资料，稍后刷新核对操作结果。");
    const data = await response.json();
    if (startedEpoch !== epoch) throw new DOMException("连接已结束", "AbortError");
    if (!response.ok) {
      const detail = Array.isArray(data.detail)
        ? data.detail.map((item) => `${item.loc.join(".")}: ${item.msg}`).join("；")
        : data.detail || `请求失败（${response.status}）`;
      throw new Error(detail);
    }
    return data;
  }

  function textNode(tag, text, className) {
    const node = document.createElement(tag);
    node.textContent = text;
    if (className) node.className = className;
    return node;
  }

  function badge(status, label) { return textNode("span", label || statusNames[status] || status, `badge ${status}`); }
  function formatDate(value) { return value ? new Date(value).toLocaleString("zh-CN", { timeZone: "Asia/Shanghai", hour12: false }) : "尚未审核"; }

  async function refresh() {
    if (tab === "claims") return refreshClaims();
    const version = ++listVersion;
    const currentTab = tab;
    const filter = $("status-filter").value;
    $("refresh").disabled = true;
    $("previous").disabled = true;
    $("next").disabled = true;
    renderRows([]);
    $("records-body").firstChild.firstChild.textContent = "正在载入资料…";
    $("records-body").setAttribute("aria-busy", "true");
    $("page-status").textContent = "正在载入…";
    try {
      const path = currentTab === "sources"
        ? `evidence/sources?limit=${PAGE_SIZE}&offset=${offset}${filter ? `&status=${filter}` : ""}`
        : currentTab === "exhibits"
          ? `evidence/exhibits?limit=${PAGE_SIZE}&offset=${offset}`
          : `audit-logs?limit=${PAGE_SIZE}&offset=${offset}`;
      const [page, drafts, approved, exhibits] = await Promise.all([
        api(path), api("evidence/sources?status=draft&limit=1"),
        api("evidence/sources?status=approved&limit=1"), api("evidence/exhibits?limit=1"),
      ]);
      if (version !== listVersion) return;
      $("draft-count").textContent = drafts.total;
      $("approved-count").textContent = approved.total;
      $("exhibit-count").textContent = exhibits.total;
      const items = currentTab === "audit" ? page : page.items;
      renderRows(items);
      $("previous").disabled = offset === 0;
      $("next").disabled = currentTab === "audit" ? items.length < PAGE_SIZE : offset + PAGE_SIZE >= page.total;
      $("page-status").textContent = currentTab === "audit"
        ? `第 ${Math.floor(offset / PAGE_SIZE) + 1} 页 · 本页 ${items.length} 条记录`
        : `${page.total} 条记录 · 第 ${Math.floor(offset / PAGE_SIZE) + 1} 页`;
    } catch (error) { if (version === listVersion || (!key && !isCancelled(error))) report(error); }
    finally {
      if (version === listVersion) {
        $("refresh").disabled = false;
        $("records-body").setAttribute("aria-busy", "false");
      }
    }
  }

  function renderRows(items) {
    const labels = tab === "sources" ? ["来源 ID / 名称", "状态", "审核人", "操作"]
      : tab === "exhibits" ? ["展品 ID / 名称", "审批状态", "关联来源", "操作"]
        : ["时间（北京时间）", "操作", "对象", "操作人"];
    const heading = document.createElement("tr");
    labels.forEach((label) => heading.append(textNode("th", label)));
    $("records-head").replaceChildren(heading);
    $("records-body").replaceChildren();
    if (!items.length) {
      const row = document.createElement("tr");
      const cell = textNode("td", tab === "audit" ? "暂无操作记录" : "暂无资料。可在导入区整理第一批记录。", "empty-cell");
      cell.colSpan = 4;
      row.append(cell);
      $("records-body").append(row);
      return;
    }
    for (const item of items) {
      const row = document.createElement("tr");
      if (tab === "audit") {
        [formatDate(item.created_at), item.action, `${item.resource_type} / ${item.resource_id}`, item.actor].forEach((value) => row.append(textNode("td", value)));
      } else {
        const sourceMode = tab === "sources";
        const record = sourceMode ? item : item.exhibit;
        const name = document.createElement("td");
        name.append(textNode("span", record.id, "record-uri"), textNode("span", sourceMode ? record.title : record.name, "record-name"));
        const state = document.createElement("td");
        const status = sourceMode ? record.status : item.approval?.status || "draft";
        state.append(badge(!sourceMode && status === "approved" && item.approval_issue ? "stale" : status,
          !sourceMode && status === "approved" && item.approval_issue ? "需重新核对" : undefined));
        const reviewerCell = textNode("td", sourceMode ? record.reviewed_by || "—" : item.source_ids.join(", ") || "尚未关联");
        const actionCell = document.createElement("td");
        const button = textNode("button", "核对详情", "table-link");
        button.type = "button";
        const kind = tab;
        button.addEventListener("click", () => openDetail(kind, record.id).catch((error) => report(error)));
        actionCell.append(button);
        row.append(name, state, reviewerCell, actionCell);
      }
      $("records-body").append(row);
    }
  }

  async function refreshClaims() {
    const version = ++claimVersion;
    const filter = $("claim-status-filter").value;
    $("refresh-claims").disabled = true;
    $("claim-previous").disabled = true;
    $("claim-next").disabled = true;
    $("claim-page-status").textContent = "正在载入…";
    $("claim-rows").replaceChildren();
    try {
      const page = await api(`evidence/claim-support?limit=${PAGE_SIZE}&offset=${claimOffset}${filter ? `&status=${filter}` : ""}`);
      if (version !== claimVersion || tab !== "claims") return;
      if (!page.items.length) {
        const row = document.createElement("tr");
        const cell = textNode("td", "暂无审核记录。", "empty-cell"); cell.colSpan = 4; row.append(cell);
        $("claim-rows").append(row);
      }
      for (const item of page.items) {
        const row = document.createElement("tr");
        const summary = document.createElement("td");
        summary.append(textNode("span", item.source_id, "record-uri"), textNode("span", item.claim_text, "record-name"));
        const state = document.createElement("td"); state.append(badge(item.status));
        const action = document.createElement("td");
        const button = textNode("button", "核对详情", "table-link"); button.type = "button";
        button.addEventListener("click", () => openClaimDetail(item.id).catch((error) => report(error)));
        action.append(button);
        row.append(summary, state, textNode("td", item.reviewed_by || "—"), action);
        $("claim-rows").append(row);
      }
      $("claim-previous").disabled = claimOffset === 0;
      $("claim-next").disabled = claimOffset + PAGE_SIZE >= page.total;
      $("claim-page-status").textContent = `${page.total} 条记录 · 第 ${Math.floor(claimOffset / PAGE_SIZE) + 1} 页`;
    } catch (error) { if (version === claimVersion || (!key && !isCancelled(error))) report(error); }
    finally { if (version === claimVersion) $("refresh-claims").disabled = false; }
  }

  function updateClaimButtons() {
    const confirmed = claimSelected && $("claim-confirm").checked && !writing;
    $("approve-claim").disabled = !confirmed || claimSelected.status !== "draft" || !claimSelected.sourceCurrent;
    $("revoke-claim").disabled = !confirmed || claimSelected.status !== "approved";
  }

  async function openClaimDetail(id) {
    const version = ++claimDetailVersion;
    claimSelected = null;
    $("claim-confirm").checked = false;
    updateClaimButtons();
    const review = await api(`evidence/claim-support/${encodeURIComponent(id)}`);
    if (version !== claimDetailVersion || !key) return;
    const source = await api(`evidence/sources/${encodeURIComponent(review.source_id)}`);
    if (version !== claimDetailVersion || !key) return;
    const sourceCurrent = source.status === "approved" && source.approved_fingerprint === review.source_fingerprint;
    claimSelected = { id, status: review.status, sourceCurrent };
    $("claim-detail-title").textContent = `${review.source_id} · 声明审核`;
    $("claim-detail-meta").replaceChildren(
      textNode("div", `来源：${source.title} · ${source.source_uri}`),
      textNode("div", `状态：${statusNames[review.status]} · 审核人：${review.reviewed_by || "—"} · ${formatDate(review.reviewed_at)}`),
      textNode("div", sourceCurrent ? "来源版本与审核记录一致" : "来源版本或审批状态已变更，不能批准此候选"),
    );
    $("claim-source-content").textContent = source.content_text;
    $("claim-detail-quote").textContent = review.evidence_quote;
    $("claim-detail-text").textContent = review.claim_text;
    $("claim-reviewer-label").textContent = `本次审核人：${reviewer}`;
    $("claim-detail-notice").hidden = true;
    updateClaimButtons();
    if (!$("claim-dialog").open) $("claim-dialog").showModal();
  }

  function invalidatePreview() {
    intakeVersion += 1;
    $("preview-batch").disabled = false;
    preview = null;
    $("preview-panel").hidden = true;
    $("preview-items").replaceChildren();
    $("intake-confirm").checked = false;
    $("import-batch").disabled = true;
  }

  function splitTerms(value) {
    return value.split(/[,，\n]/).map((item) => item.trim()).filter(Boolean);
  }

  function updateSingleExhibitForm() {
    $("single-exhibit-form").hidden = $("batch-kind").value !== "exhibits";
    $("upload-single-exhibit").disabled = !$("single-exhibit-confirm").checked || writing;
  }

  function parseBatch() {
    const raw = $("batch-json").value;
    if (new TextEncoder().encode(raw).length > MAX_FILE_BYTES) throw new Error("JSON 内容超过 8 MiB，请拆分批次。");
    let data;
    try { data = JSON.parse(raw.replace(/^\uFEFF/, "")); }
    catch { throw new Error("JSON 格式有误，请检查引号、逗号和括号。"); }
    const kind = $("batch-kind").value;
    if (Array.isArray(data)) data = { [kind]: data };
    if (!data || !Array.isArray(data[kind])) throw new Error(`请提供 JSON 数组或带 ${kind} 数组的对象。`);
    if (!data[kind].length || data[kind].length > 20) throw new Error("每批需要 1 至 20 条记录，请拆分较大批次。");
    return { kind, payload: data };
  }

  $("login-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const button = event.submitter;
    reviewer = $("reviewer").value.trim();
    key = $("operator-key").value.trim();
    if (!reviewer || !key) { showMessage("请输入操作员密钥和实际审核人姓名。", true); return; }
    if (!/^[\x21-\x7e]+$/.test(key)) { key = ""; showMessage("密钥需使用无空格的 ASCII 字符。", true); return; }
    $("operator-key").value = "";
    button.disabled = true;
    try {
      await api("evidence/sources?limit=1");
      $("login-panel").hidden = true;
      $("workspace").hidden = false;
      $("disconnect").hidden = false;
      $("connection-state").textContent = `已连接 · ${reviewer}`;
      $("notice").hidden = true;
      offset = 0;
      await refresh();
    } catch (error) { key = ""; report(error); }
    finally { button.disabled = false; }
  });

  $("disconnect").addEventListener("click", () => { resetConnection(); showMessage("已退出，当前页面中的密钥和资料已清除。"); });
  window.addEventListener("pagehide", resetConnection);
  $("batch-json").addEventListener("input", invalidatePreview);
  $("batch-kind").addEventListener("change", () => {
    invalidatePreview();
    $("batch-file").value = "";
    $("format-example").textContent = JSON.stringify(formats[$("batch-kind").value], null, 2);
    updateSingleExhibitForm();
  });
  $("batch-file").addEventListener("change", async () => {
    invalidatePreview();
    const version = intakeVersion;
    const file = $("batch-file").files[0];
    if (!file) return;
    try {
      if (!file.name.toLowerCase().endsWith(".json")) throw new Error("请选择 .json 文件。");
      if (file.size > MAX_FILE_BYTES) throw new Error("文件超过 8 MiB，请拆分批次。");
      const text = new TextDecoder("utf-8", { fatal: true }).decode(await file.arrayBuffer());
      if (version === intakeVersion) $("batch-json").value = text;
    } catch (error) {
      if (version === intakeVersion) { $("batch-json").value = ""; report(error); }
    }
  });
  $("preview-batch").addEventListener("click", async () => {
    invalidatePreview();
    const version = intakeVersion;
    $("preview-batch").disabled = true;
    try {
      const batch = parseBatch();
      const result = await api(`evidence/${batch.kind}/batch/preview`, { method: "POST", payload: batch.payload });
      if (version !== intakeVersion) return;
      preview = batch;
      for (const item of result.items) {
        const node = textNode("div", `${item.id} · ${item.title || item.name}`, "preview-item");
        node.append(textNode("small", batch.kind === "sources" ? `${item.content_length} 字符 · ${item.source_uri}` : item.source_reference));
        $("preview-items").append(node);
      }
      $("preview-panel").hidden = false;
      showMessage(`预览通过，共 ${result.count} 条记录。尚未写入资料库。`);
    } catch (error) { if (version === intakeVersion || (!key && !isCancelled(error))) report(error); }
    finally { if (version === intakeVersion) $("preview-batch").disabled = false; }
  });
  $("intake-confirm").addEventListener("change", () => { $("import-batch").disabled = !preview || !$("intake-confirm").checked || writing; });
  $("import-batch").addEventListener("click", async () => {
    if (!preview || !$("intake-confirm").checked || writing) return;
    const batch = preview;
    const startedEpoch = epoch;
    const version = intakeVersion;
    writing = true;
    $("import-batch").disabled = true;
    try {
      const result = await api(`evidence/${batch.kind}/batch`, { method: "POST", payload: batch.payload });
      if (version === intakeVersion) invalidatePreview();
      showMessage(`已导入 ${result.imported_count ?? result.count} 条待审批记录。请逐条核对并审批。`);
      offset = 0;
      await refresh();
    } catch (error) {
      if (version === intakeVersion) invalidatePreview();
      report(error);
    } finally {
      if (startedEpoch === epoch) {
        writing = false;
        $("import-batch").disabled = !preview || !$("intake-confirm").checked;
      }
    }
  });

  $("single-exhibit-confirm").addEventListener("change", updateSingleExhibitForm);
  $("single-exhibit-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    if (writing || !$("single-exhibit-confirm").checked) return;
    const form = event.currentTarget;
    const sourceIds = splitTerms($("exhibit-source-ids").value);
    if (sourceIds.length > 20) { showMessage("每件展品最多关联 20 个来源 ID。", true); return; }
    if (new Set(sourceIds).size !== sourceIds.length) { showMessage("关联来源 ID 不能重复。", true); return; }
    const payload = {
      exhibit: {
        id: $("exhibit-id").value.trim(),
        name: $("exhibit-name").value.trim(),
        description: $("exhibit-description").value.trim(),
        period: $("exhibit-period").value.trim(),
        importance: Number($("exhibit-importance").value),
        source_reference: $("exhibit-source-reference").value.trim(),
        keywords: splitTerms($("exhibit-keywords").value),
        people: splitTerms($("exhibit-people").value),
        themes: splitTerms($("exhibit-themes").value),
        time_range: $("exhibit-time-range").value.trim() || null,
      },
      source_ids: sourceIds,
    };
    const startedEpoch = epoch;
    writing = true;
    updateSingleExhibitForm();
    try {
      const result = await api("evidence/exhibits", { method: "POST", payload });
      if (startedEpoch !== epoch) return;
      form.reset();
      $("exhibit-importance").value = "3";
      updateSingleExhibitForm();
      showMessage(`展品 ${result.exhibit.id} 已保存为待审核记录，并关联 ${result.source_ids.length} 个来源。`);
      document.querySelector('[data-tab="exhibits"]').click();
    } catch (error) { report(error); }
    finally {
      if (startedEpoch === epoch) { writing = false; updateSingleExhibitForm(); }
    }
  });

  async function openDetail(kind, id, expectedVersion = null) {
    if (expectedVersion !== null && (expectedVersion !== detailVersion || !$("detail-dialog").open)) return false;
    const version = ++detailVersion;
    selected = null;
    $("review-confirm").checked = false;
    updateReviewButtons();
    let data;
    try { data = await api(`evidence/${kind}/${encodeURIComponent(id)}`); }
    catch (error) { if (version === detailVersion || (!key && !isCancelled(error))) throw error; return false; }
    if (version !== detailVersion) return false;
    const record = kind === "sources" ? data : data.exhibit;
    selected = { kind, id, data };
    $("detail-title").textContent = `${id} · ${record.title || record.name}`;
    $("detail-meta").replaceChildren();
    const status = kind === "sources" ? data.status : data.approval?.status || "draft";
    const reviewed = kind === "sources" ? data : data.approval;
    $("detail-meta").append(textNode("div", `状态：${statusNames[status]} · 审核人：${reviewed?.reviewed_by || "—"} · ${formatDate(reviewed?.reviewed_at)}`));
    const uri = kind === "sources" ? record.source_uri : record.source_reference;
    $("detail-meta").append(textNode("div", `原始出处：${uri}`));
    if (kind === "sources") {
      try {
        const url = new URL(uri);
        if (["https:", "http:"].includes(url.protocol)) {
          const link = textNode("a", "打开原始出处 ↗");
          link.href = url.href; link.target = "_blank"; link.rel = "noopener noreferrer";
          $("detail-meta").append(link);
        }
      } catch { /* Archive references are displayed as text. */ }
      $("detail-meta").append(textNode("div", `正文指纹：${record.content_sha256}`));
      $("detail-content").textContent = record.content_text;
    } else {
      $("detail-meta").append(textNode("div", `关联来源：${data.source_ids.join(", ") || "尚未关联"}`));
      $("detail-meta").append(textNode("div", `当前门禁：${data.approval_issue || "审批与快照一致"}`));
      $("detail-content").textContent = `${record.description}\n\n时期：${record.period}\n关键词：${record.keywords.join("、")}\n人物：${record.people.join("、")}\n主题：${record.themes.join("、")}`;
    }
    $("link-form").hidden = kind === "sources";
    $("link-source-id").value = "";
    $("detail-notice").hidden = true;
    $("review-confirm").checked = false;
    $("reviewer-label").textContent = `本次审核人：${reviewer}`;
    updateReviewButtons();
    if (!$("detail-dialog").open) $("detail-dialog").showModal();
    return true;
  }

  function updateReviewButtons() {
    const active = selected && $("review-confirm").checked && !writing;
    const status = selected?.kind === "sources" ? selected.data.status : selected?.data.approval?.status;
    $("approve-record").disabled = !active || (selected?.kind === "sources" && status !== "draft");
    $("revoke-record").disabled = !active || status === "revoked" || (selected?.kind === "exhibits" && !status);
  }

  async function reviewAction(action) {
    if (!selected || !$("review-confirm").checked || writing) return;
    const { kind, id } = selected;
    const version = detailVersion;
    const startedEpoch = epoch;
    writing = true;
    updateReviewButtons();
    try {
      await api(`evidence/${kind}/${encodeURIComponent(id)}/${action}`, { method: "POST", payload: { reviewer } });
      if (await openDetail(kind, id, version)) {
        showMessage(action === "approve" ? "已记录批准，请继续核对其他资料。" : "已撤销。相关回答需重新准备和审核。", false, "detail-notice");
      }
      await refresh();
    } catch (error) { report(error, $("detail-dialog").open ? "detail-notice" : "notice"); }
    finally { if (startedEpoch === epoch) { writing = false; updateReviewButtons(); } }
  }

  $("review-confirm").addEventListener("change", updateReviewButtons);
  $("approve-record").addEventListener("click", () => reviewAction("approve"));
  $("revoke-record").addEventListener("click", () => reviewAction("revoke"));
  $("close-detail").addEventListener("click", () => $("detail-dialog").close());
  $("detail-dialog").addEventListener("close", () => { detailVersion += 1; selected = null; updateReviewButtons(); });
  $("link-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!selected || selected.kind !== "exhibits" || writing) return;
    const id = selected.id;
    const version = detailVersion;
    const startedEpoch = epoch;
    const sourceId = $("link-source-id").value.trim();
    if (!sourceId) { showMessage("请输入需要关联的来源 ID。", true, "detail-notice"); return; }
    writing = true;
    event.submitter.disabled = true;
    updateReviewButtons();
    try {
      await api(`evidence/exhibits/${encodeURIComponent(id)}/sources/${encodeURIComponent(sourceId)}`, { method: "POST" });
      if (await openDetail("exhibits", id, version)) {
        showMessage("来源已关联。请重新核对后进行展品审批。", false, "detail-notice");
      }
      await refresh();
    } catch (error) { report(error, $("detail-dialog").open ? "detail-notice" : "notice"); }
    finally {
      if (startedEpoch === epoch) { writing = false; updateReviewButtons(); }
      event.submitter.disabled = false;
    }
  });

  $("claim-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    if (writing || !key) return;
    const startedEpoch = epoch;
    const payload = {
      source_id: $("claim-source-id").value.trim(),
      evidence_quote: $("claim-quote").value.trim(),
      claim_text: $("claim-text").value.trim(),
    };
    writing = true;
    $("create-claim").disabled = true;
    try {
      await api("evidence/claim-support", { method: "POST", payload });
      if (startedEpoch !== epoch) return;
      $("claim-quote").value = "";
      $("claim-text").value = "";
      claimOffset = 0;
      $("claim-status-filter").value = "draft";
      showMessage("候选已创建，尚未获得支持审批。请打开详情核对完整来源。");
      await refreshClaims();
    } catch (error) { report(error); }
    finally { if (startedEpoch === epoch) { writing = false; $("create-claim").disabled = false; } }
  });

  $("claim-confirm").addEventListener("change", updateClaimButtons);
  $("close-claim").addEventListener("click", () => $("claim-dialog").close());
  $("claim-dialog").addEventListener("close", () => {
    claimDetailVersion += 1; claimSelected = null; $("claim-confirm").checked = false; updateClaimButtons();
  });
  for (const action of ["approve", "revoke"]) {
    $(`${action}-claim`).addEventListener("click", async () => {
      if (!claimSelected || !$("claim-confirm").checked || writing) return;
      const { id } = claimSelected;
      const version = claimDetailVersion;
      const startedEpoch = epoch;
      writing = true;
      updateClaimButtons();
      try {
        await api(`evidence/claim-support/${encodeURIComponent(id)}/${action}`, {
          method: "POST",
          payload: action === "approve" ? { reviewer, support_confirmed: true } : { reviewer },
        });
        if (version === claimDetailVersion && $("claim-dialog").open) {
          await openClaimDetail(id);
          showMessage(action === "approve" ? "已批准该声明支持关系。" : "已撤销支持；新答案不能再使用该审核记录。", false, "claim-detail-notice");
        }
        $("claim-status-filter").value = "";
        claimOffset = 0;
        await refreshClaims();
      } catch (error) { report(error, $("claim-dialog").open ? "claim-detail-notice" : "notice"); }
      finally { if (startedEpoch === epoch) { writing = false; updateClaimButtons(); } }
    });
  }

  $("claim-status-filter").addEventListener("change", () => { claimOffset = 0; refreshClaims(); });
  $("refresh-claims").addEventListener("click", refreshClaims);
  $("claim-previous").addEventListener("click", () => { claimOffset = Math.max(0, claimOffset - PAGE_SIZE); refreshClaims(); });
  $("claim-next").addEventListener("click", () => { claimOffset += PAGE_SIZE; refreshClaims(); });

  document.querySelectorAll("[data-tab]").forEach((button) => button.addEventListener("click", () => {
    tab = button.dataset.tab;
    offset = 0;
    document.querySelectorAll("[data-tab]").forEach((node) => {
      const active = node === button;
      node.classList.toggle("active", active);
      if (active) node.setAttribute("aria-current", "page"); else node.removeAttribute("aria-current");
    });
    $("claims-panel").hidden = tab !== "claims";
    document.querySelector(".workspace-grid").hidden = tab === "claims";
    if (tab === "claims") { refreshClaims(); return; }
    if (tab === "sources" || tab === "exhibits") {
      $("batch-kind").value = tab;
      $("format-example").textContent = JSON.stringify(formats[tab], null, 2);
      updateSingleExhibitForm();
    }
    $("records-title").textContent = { sources: "来源资料", exhibits: "展品资料", audit: "操作记录" }[tab];
    $("source-filters").hidden = tab !== "sources";
    $("intake-panel").hidden = tab === "audit";
    document.querySelector(".workspace-grid").classList.toggle("audit-mode", tab === "audit");
    $("records-note").textContent = tab === "audit" ? "操作记录用于追踪审批与导入，不代替原文核对。"
      : tab === "exhibits" ? "展品需要关联已批准来源并由馆员批准；开发样例不能进入正式讲解。"
        : "导入草稿不会自动批准，也不会同步到 Coze 知识库。";
    refresh();
  }));
  $("status-filter").addEventListener("change", () => { offset = 0; refresh(); });
  $("refresh").addEventListener("click", refresh);
  $("previous").addEventListener("click", () => { offset = Math.max(0, offset - PAGE_SIZE); refresh(); });
  $("next").addEventListener("click", () => { offset += PAGE_SIZE; refresh(); });
  $("format-example").textContent = JSON.stringify(formats.sources, null, 2);
  updateSingleExhibitForm();
})();
