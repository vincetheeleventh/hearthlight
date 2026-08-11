$source = @'
const productionState = {
  list: null,
  production: null,
  shot: null,
  loading: false,
};

const productionEls = {
  view: document.querySelector("#productionView"),
  content: document.querySelector("#productionContent"),
  projectsTab: document.querySelector("#projectsTab"),
  filmStudiesTab: document.querySelector("#filmStudiesTab"),
  legacyToolbar: document.querySelector("#legacyToolbar"),
  projectMeta: document.querySelector("#projectMeta"),
};

function node(tag, className = "", text = "") {
  const element = document.createElement(tag);
  if (className) element.className = className;
  if (text !== "") element.textContent = text;
  return element;
}

function currentStudioRoute() {
  const params = new URLSearchParams(window.location.search);
  const isFilmStudy = params.get("space") === "films" || params.has("project") || params.get("view") === "research";
  return {
    mode: isFilmStudy ? "films" : "projects",
    slug: params.get("production") || "",
    shotId: params.get("productionShot") || "",
  };
}

function studioUrl({ mode = "projects", slug = "", shotId = "" }) {
  const url = new URL(window.location.href);
  url.search = "";
  url.searchParams.set("space", mode);
  if (slug) url.searchParams.set("production", slug);
  if (shotId) url.searchParams.set("productionShot", shotId);
  return `${url.pathname}${url.search}`;
}

function goStudio(target, replace = false) {
  const method = replace ? "replaceState" : "pushState";
  window.history[method]({ hearthlightStudio: true }, "", studioUrl(target));
  restoreStudioRoute().catch(showProductionError);
}

async function fetchProductionJson(url) {
  const response = await fetch(url, { cache: "no-store" });
  if (!response.ok) throw new Error(await productionResponseError(response));
  return response.json();
}

async function postProductionJson(url, payload = {}) {
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) throw new Error(await productionResponseError(response));
  return response.json();
}

async function productionResponseError(response) {
  const text = await response.text();
  const match = text.match(/<p>(.*?)<\/p>/is);
  const message = (match?.[1] || text || response.statusText || `Request failed (${response.status})`)
    .replace(/<[^>]+>/g, " ")
    .replace(/&quot;/g, '"')
    .replace(/&#x27;/g, "'")
    .replace(/&amp;/g, "&")
    .replace(/\s+/g, " ")
    .trim();
  return message || `Request failed (${response.status})`;
}

function setProductionMeta(text) {
  productionEls.projectMeta.dataset.productionMeta = text;
  if (productionEls.projectMeta.textContent !== text) productionEls.projectMeta.textContent = text;
}

const productionMetaObserver = new MutationObserver(() => {
  const expected = productionEls.projectMeta.dataset.productionMeta;
  if (document.body.classList.contains("production-mode") && expected && productionEls.projectMeta.textContent !== expected) {
    productionEls.projectMeta.textContent = expected;
  }
});
productionMetaObserver.observe(productionEls.projectMeta, { childList: true, characterData: true, subtree: true });

function setStudioMode(mode) {
  const projects = mode === "projects";
  document.body.classList.toggle("production-mode", projects);
  productionEls.view.hidden = !projects;
  productionEls.projectsTab.classList.toggle("is-active", projects);
  productionEls.projectsTab.setAttribute("aria-current", projects ? "page" : "false");
  productionEls.filmStudiesTab.classList.toggle("is-active", !projects);
  productionEls.filmStudiesTab.setAttribute("aria-current", projects ? "false" : "page");
}

function formatRuntime(seconds) {
  const total = Math.max(0, Math.round(Number(seconds) || 0));
  const minutes = Math.floor(total / 60);
  const remainder = total % 60;
  return minutes ? `${minutes}m ${String(remainder).padStart(2, "0")}s` : `${remainder}s`;
}

function formatDate(value) {
  if (!value) return "No activity yet";
  const date = new Date(value);
  if (Number.isNaN(date.valueOf())) return String(value);
  return new Intl.DateTimeFormat(undefined, { month: "short", day: "numeric", hour: "numeric", minute: "2-digit" }).format(date);
}

function stageLabel(stage) {
  const labels = {
    "style-composition": "Style + composition",
    likeness: "Likeness",
    storyboard: "Storyboard",
    video: "Video",
    image: "Image",
  };
  return labels[stage] || String(stage || "Asset").replaceAll("-", " ");
}

function approvedState(value) {
  return ["approved", "done", "pass", "passed", "selected", "final", "composition-approved", "likeness-approved"].includes(String(value || "").toLowerCase());
}

function badge(text, tone = "") {
  return node("span", `production-badge ${tone}`.trim(), text);
}

function mediaElement(asset, { hero = false, fallback = null } = {}) {
  const frame = node("div", `production-media ${hero ? "is-hero" : ""}`.trim());
  if (!asset) {
    frame.append(node("div", "production-empty-media", "No visual asset yet"));
    return frame;
  }
  if (asset.kind === "video" && hero) {
    const video = node("video");
    video.src = asset.mediaUrl;
    video.poster = asset.thumbnailUrl || "";
    video.controls = true;
    video.preload = "metadata";
    video.playsInline = true;
    frame.append(video);
  } else {
    const image = node("img");
    image.src = asset.thumbnailUrl || asset.mediaUrl;
    image.alt = "";
    image.loading = hero ? "eager" : "lazy";
    image.decoding = "async";
    if (fallback && fallback !== image.src) {
      image.addEventListener("error", () => {
        if (image.src !== new URL(fallback, window.location.href).href) image.src = fallback;
      }, { once: true });
    }
    frame.append(image);
    if (asset.kind === "video") frame.append(badge("clip", "video"));
  }
  return frame;
}

function metric(label, value, tone = "") {
  const item = node("div", `production-metric ${tone}`.trim());
  item.append(node("strong", "", String(value)), node("span", "", label));
  return item;
}

function actionNotice() {
  const notice = node("p", "production-action-notice");
  notice.setAttribute("role", "status");
  notice.setAttribute("aria-live", "polite");
  return notice;
}

function showNotice(notice, message, tone = "") {
  notice.textContent = message;
  notice.className = `production-action-notice ${tone}`.trim();
}

async function runButton(button, task, workingLabel = "Working...") {
  const label = button.textContent;
  button.disabled = true;
  button.textContent = workingLabel;
  try {
    return await task();
  } finally {
    button.disabled = false;
    button.textContent = label;
  }
}

async function refreshProductionRoute() {
  productionState.list = null;
  productionState.production = null;
  productionState.shot = null;
  await restoreStudioRoute();
}

async function loadProductionList() {
  if (!productionState.list) productionState.list = await fetchProductionJson("/api/productions");
  return productionState.list;
}

function renderProductionLibrary(data) {
  setProductionMeta(`${data.productions.length} active ${data.productions.length === 1 ? "project" : "projects"}`);
  const page = node("div", "production-library");
  const heading = node("header", "production-library-heading");
  const title = node("div");
  title.append(node("span", "eyebrow", "Production cockpit"), node("h2", "", "Films in progress"), node("p", "", "Every shot, dependency, review, and revision in one visual holding place."));
  const refresh = node("button", "ghost-button", "Refresh");
  refresh.type = "button";
  refresh.addEventListener("click", refreshProductionRoute);
  heading.append(title, refresh);
  page.append(heading);

  if (!data.productions.length) {
    const empty = node("section", "production-library-empty");
    empty.append(node("h3", "", "No Hearthlight projects found"), node("p", "", "Projects appear here directly from Story Studio. Nothing is copied into this app."));
    page.append(empty);
    productionEls.content.replaceChildren(page);
    return;
  }

  const grid = node("section", "production-card-grid");
  for (const production of data.productions) {
    const card = node("button", "production-card");
    card.dataset.productionSlug = production.slug;
    card.type = "button";
    card.addEventListener("click", () => goStudio({ slug: production.slug }));
    const visual = mediaElement(production.coverAsset);
    visual.classList.add("production-card-cover");
    const body = node("div", "production-card-body");
    const kicker = node("div", "production-card-kicker");
    kicker.append(badge(production.format || "Unspecified"), node("span", "", formatDate(production.lastActivity)));
    body.append(kicker, node("h3", "", production.name));
    const metrics = node("div", "production-card-metrics");
    metrics.append(
      metric("shots", production.shotCount || 0),
      metric("runtime", formatRuntime(production.runtimeSeconds)),
      metric("blocked", production.blockerCount || 0, production.blockerCount ? "is-warning" : ""),
      metric("to review", production.pendingReviewCount || 0, production.pendingReviewCount ? "is-pending" : ""),
    );
    body.append(metrics);
    const progress = node("div", "gate-progress");
    const fill = node("span");
    const total = Number(production.gateProgress?.total) || 1;
    fill.style.width = `${Math.min(100, (Number(production.gateProgress?.approved) || 0) / total * 100)}%`;
    progress.append(fill);
    body.append(progress, node("p", "production-next", production.nextAction?.label || "Open project"));
    if (production.validationCount) body.append(badge(`${production.validationCount} validation ${production.validationCount === 1 ? "finding" : "findings"}`, "warning"));
    card.append(visual, body);
    grid.append(card);
  }
  page.append(grid);
  productionEls.content.replaceChildren(page);
}

function requirementCard(requirement) {
  const card = node("article", `requirement-card status-${String(requirement.status).replaceAll(" ", "-")}`);
  const heading = node("header");
  heading.append(node("strong", "", requirement.label), badge(requirement.status));
  card.append(heading);
  if (requirement.detail) card.append(node("p", "", requirement.detail));
  if (requirement.expectedPath) card.append(node("code", "", requirement.expectedPath));
  return card;
}

function renderGateRail(production) {
  const rail = node("section", "production-gate-rail");
  for (const gate of production.gates || []) {
    const item = node("div", `gate-stop state-${gate.state}`);
    item.append(node("span", "gate-dot"), node("strong", "", gate.gate || gate.label), node("small", "", gate.state));
    rail.append(item);
  }
  return rail;
}

function reviewAssetForShot(shot) {
  return shot.newerPendingAsset
    || (shot.assetHistory || []).find((asset) => asset.kind === "image" && asset.stage !== "storyboard" && !asset.stale)
    || (shot.heroAsset?.stage !== "storyboard" ? shot.heroAsset : null);
}

function promptEditor(production, shot, notice, compact = false) {
  const editor = node("div", compact ? "shot-card-prompt" : "prompt-workspace");
  const current = shot.currentPrompt || {};
  const stage = current.stage || "style-composition";
  const target = reviewAssetForShot(shot);
  const label = node("label", "prompt-field-label", compact ? "Prompt draft" : "Prompt for next generation");
  const textarea = node("textarea", compact ? "shot-prompt-input" : "prompt-editor");
  textarea.value = current.prompt || "";
  textarea.rows = compact ? 5 : 12;
  label.append(textarea);
  const actions = node("div", "prompt-actions");
  const save = node("button", "ghost-button", "Save prompt");
  save.type = "button";
  save.addEventListener("click", async () => {
    try {
      await runButton(save, async () => {
        await postProductionJson(`/api/productions/${encodeURIComponent(production.slug)}/shots/${encodeURIComponent(shot.shotId)}/prompt`, {
          prompt: textarea.value,
          stage,
          assetId: target?.assetId || current.assetId || "",
        });
      }, "Saving...");
      showNotice(notice, `Shot ${shot.displayNumber}: prompt saved.`, "success");
    } catch (error) {
      showNotice(notice, error.message, "error");
    }
  });
  actions.append(save);
  editor.append(label, actions);
  return editor;
}

function quickReviewControls(production, shot, notice) {
  const controls = node("section", "shot-quick-review");
  const target = reviewAssetForShot(shot);
  const note = node("textarea", "shot-feedback-input");
  note.rows = 2;
  note.placeholder = target ? "What needs to change?" : "No generated image to review yet";
  note.disabled = !target;
  if (target?.feedback) note.value = target.feedback;
  const buttons = node("div", "shot-review-actions");
  const flag = node("button", "ghost-button", "Flag change");
  flag.type = "button";
  flag.disabled = !target || target.stale;
  flag.addEventListener("click", async () => {
    try {
      await runButton(flag, () => postProductionJson(`/api/productions/${encodeURIComponent(production.slug)}/shots/${encodeURIComponent(shot.shotId)}/assets/${encodeURIComponent(target.assetId)}/flag`, { feedback: note.value }), "Flagging...");
      showNotice(notice, `Shot ${shot.displayNumber}: revision requested.`, "success");
      await refreshProductionRoute();
    } catch (error) {
      showNotice(notice, error.message, "error");
    }
  });
  const pass = node("button", "primary-button", "Pass stage");
  pass.type = "button";
  pass.disabled = !target || target.stale || approvedState(target.reviewState);
  pass.title = "Approves this asset stage only. It does not approve a Hearthlight gate.";
  pass.addEventListener("click", async () => {
    if (!window.confirm(`Pass Shot ${shot.displayNumber} for ${stageLabel(target.stage)}? This approves the asset stage only, not a Hearthlight gate.`)) return;
    try {
      await runButton(pass, () => postProductionJson(`/api/productions/${encodeURIComponent(production.slug)}/shots/${encodeURIComponent(shot.shotId)}/assets/${encodeURIComponent(target.assetId)}/approve`), "Passing...");
      await refreshProductionRoute();
    } catch (error) {
      showNotice(notice, error.message, "error");
    }
  });
  buttons.append(flag, pass);
  const details = node("details", "shot-card-prompt-details");
  details.append(node("summary", "", "Edit prompt"), promptEditor(production, shot, notice, true));
  controls.append(note, buttons, details);
  return controls;
}

function shotCard(production, shot, notice) {
  const card = node("article", "production-shot-card");
  card.dataset.shotId = shot.shotId;
  const open = node("button", "production-shot-open");
  open.type = "button";
  open.setAttribute("aria-label", `Open Shot ${shot.displayNumber}: ${shot.title}`);
  open.addEventListener("click", () => goStudio({ slug: production.slug, shotId: shot.shotId }));
  const fallback = shot.newerPendingAsset?.thumbnailUrl || shot.newerPendingAsset?.mediaUrl || "";
  open.append(mediaElement(shot.heroAsset, { fallback }));
  const text = node("div", "production-shot-card-copy");
  const header = node("div");
  header.append(node("strong", "", `Shot ${shot.displayNumber}`), node("span", "", formatRuntime(shot.durationSeconds)));
  text.append(header, node("h3", "", shot.title));
  const active = reviewAssetForShot(shot) || shot.heroAsset;
  if (active) text.append(node("p", "shot-card-stage", `${stageLabel(active.stage)}${active.model ? ` \u00b7 ${active.model}` : ""}`));
  const badges = node("div", "production-badges");
  for (const value of shot.badges || []) badges.append(badge(value, value.includes("missing") || value.includes("stale") || value.includes("unresolved") ? "warning" : value.includes("pending") ? "pending" : ""));
  text.append(badges);
  open.append(text);
  card.append(open, quickReviewControls(production, shot, notice));
  return card;
}

function renderProductionOverview(production) {
  setProductionMeta(`${production.shotCount} shots \u00b7 ${formatRuntime(production.runtimeSeconds)} \u00b7 ${production.pendingReviewCount} awaiting review`);
  const page = node("div", "production-overview");
  const notice = actionNotice();
  const back = node("button", "production-back", "\u2190 Projects");
  back.type = "button";
  back.addEventListener("click", () => goStudio({}));
  const heading = node("header", "production-overview-heading");
  const title = node("div");
  const kicker = node("div", "production-overview-kicker");
  kicker.append(badge(production.format), badge(production.client || "none"), badge(`${production.registrySource}${production.registryStatus === "inferred" ? " \u00b7 inferred" : ""}`));
  title.append(kicker, node("h2", "", production.name), node("p", "", production.chargedRegister || "No charged register declared"));
  const action = node("aside", "production-next-action");
  action.append(node("span", "eyebrow", "Next action"), node("strong", "", production.nextAction?.label || "Review project state"));
  heading.append(title, action);
  page.append(back, heading, notice, renderGateRail(production));

  const status = node("section", "production-status-grid");
  const now = node("div", "requirement-group");
  now.append(node("h3", "", `Missing now \u00b7 ${production.missingNow.length}`));
  if (production.missingNow.length) production.missingNow.forEach((item) => now.append(requirementCard(item)));
  else now.append(node("p", "production-clear", "No current dependency gaps."));
  const later = node("details", "requirement-group requirement-later");
  const laterSummary = node("summary", "", `Missing later \u00b7 ${production.missingLater.length}`);
  later.append(laterSummary);
  production.missingLater.forEach((item) => later.append(requirementCard(item)));
  status.append(now, later);
  page.append(status);

  const wallHeader = node("header", "production-wall-heading");
  wallHeader.append(node("div", "", ""), node("span", "", `${production.uniqueIllustratedSetups} illustrated setups`));
  wallHeader.firstChild.append(node("span", "eyebrow", "Visual wall"), node("h2", "", "Every shot"));
  page.append(wallHeader);

  const reviewToolbar = node("section", "production-review-toolbar");
  const reviewCopy = node("div");
  reviewCopy.append(node("strong", "", "Batch review"), node("span", "", "Approves only the latest unflagged asset in the selected stage. Gate status is unchanged."));
  const stageSelect = node("select", "production-stage-select");
  stageSelect.append(new Option("Style + composition", "style-composition"), new Option("Likeness", "likeness"));
  const approveAll = node("button", "primary-button", "Approve all unflagged");
  approveAll.type = "button";
  approveAll.addEventListener("click", async () => {
    const label = stageSelect.options[stageSelect.selectedIndex].text;
    if (!window.confirm(`Approve every latest unflagged ${label} image? Flagged images, images with feedback, and Hearthlight gates will not change.`)) return;
    try {
      const result = await runButton(approveAll, () => postProductionJson(`/api/productions/${encodeURIComponent(production.slug)}/bulk-approve`, { stage: stageSelect.value }), "Approving...");
      window.alert(`${result.count} ${result.count === 1 ? "image" : "images"} approved for ${label}.`);
      await refreshProductionRoute();
    } catch (error) {
      showNotice(notice, error.message, "error");
    }
  });
  reviewToolbar.append(reviewCopy, stageSelect, approveAll);
  page.append(reviewToolbar);

  const wall = node("section", "production-shot-wall");
  production.shots.forEach((shot) => wall.append(shotCard(production, shot, notice)));
  page.append(wall);

  if (production.validationFindings?.length || production.unmappedAssets?.length) {
    const validation = node("details", "production-validation");
    validation.append(node("summary", "", `Validation and unmapped assets \u00b7 ${(production.validationFindings?.length || 0) + (production.unmappedAssets?.length || 0)}`));
    const list = node("div", "production-validation-list");
    for (const finding of production.validationFindings || []) {
      const item = node("article");
      item.append(node("strong", "", String(finding.code || "finding").replaceAll("-", " ")), node("p", "", finding.detail || [finding.character, finding.path, finding.registered, finding.newest].filter(Boolean).join(" \u00b7 ")));
      list.append(item);
    }
    for (const asset of production.unmappedAssets || []) {
      const item = node("article");
      item.append(node("strong", "", "Unmapped asset"), node("p", "", `${asset.path} \u00b7 ${asset.reason}`));
      list.append(item);
    }
    validation.append(list);
    page.append(validation);
  }
  productionEls.content.replaceChildren(page);
}

function detailSection(label, text) {
  const section = node("section", "production-copy-section");
  section.append(node("span", "eyebrow", label), node("p", "", text || "Not written yet."));
  return section;
}

function referenceList(references = []) {
  const section = node("div", "production-reference-grid");
  if (!references.length) {
    section.append(node("p", "production-reference-empty", "No style or conditioning reference registered."));
    return section;
  }
  for (const reference of references) {
    const card = node("article", "production-reference-card");
    if (reference.thumbnailUrl || reference.mediaUrl) {
      const image = node("img");
      image.src = reference.thumbnailUrl || reference.mediaUrl;
      image.alt = reference.name || reference.id || "Reference image";
      image.loading = "lazy";
      card.append(image);
    } else {
      card.append(node("div", "production-reference-placeholder", reference.type === "moodboard" ? "Mood board" : "Reference"));
    }
    const copy = node("div");
    copy.append(node("strong", "", reference.name || reference.id || "Reference"));
    const facts = [reference.type, reference.strength, reference.status].filter(Boolean).join(" \u00b7 ");
    if (facts) copy.append(node("span", "", facts));
    if (!reference.mediaUrl && reference.id) copy.append(node("small", "", `${reference.id} \u00b7 no local preview registered`));
    card.append(copy);
    section.append(card);
  }
  return section;
}

function assetActionControls(production, shot, asset, notice) {
  const controls = node("div", "asset-actions");
  const choose = node("button", "ghost-button", shot.heroAsset?.assetId === asset.assetId ? "Current hero" : "Use as hero");
  choose.type = "button";
  choose.disabled = shot.heroAsset?.assetId === asset.assetId || asset.stale;
  choose.addEventListener("click", async () => {
    try {
      await runButton(choose, () => postProductionJson(`/api/productions/${encodeURIComponent(production.slug)}/shots/${encodeURIComponent(shot.shotId)}/assets/${encodeURIComponent(asset.assetId)}/select`), "Selecting...");
      await refreshProductionRoute();
    } catch (error) {
      showNotice(notice, error.message, "error");
    }
  });
  controls.append(choose);
  if (asset.stage !== "storyboard") {
    const pass = node("button", "primary-button", "Pass this stage");
    pass.type = "button";
    pass.disabled = asset.stale || approvedState(asset.reviewState);
    pass.title = "Approves this asset stage only. It does not approve a Hearthlight gate.";
    pass.addEventListener("click", async () => {
      if (!window.confirm(`Pass this ${stageLabel(asset.stage)} asset? This does not approve a Hearthlight gate.`)) return;
      try {
        await runButton(pass, () => postProductionJson(`/api/productions/${encodeURIComponent(production.slug)}/shots/${encodeURIComponent(shot.shotId)}/assets/${encodeURIComponent(asset.assetId)}/approve`), "Passing...");
        await refreshProductionRoute();
      } catch (error) {
        showNotice(notice, error.message, "error");
      }
    });
    controls.append(pass);
  }
  return controls;
}

function assetHistoryItem(production, shot, asset, notice) {
  const item = node("article", `asset-history-item ${asset.stale ? "is-stale" : ""}`);
  item.append(mediaElement(asset));
  const copy = node("div", "asset-history-copy");
  const heading = node("header");
  const state = shot.heroAsset?.assetId === asset.assetId ? "chosen hero" : asset.stale ? "stale" : asset.selectionState || asset.reviewState;
  heading.append(node("strong", "", `${stageLabel(asset.stage)}${asset.version ? ` \u00b7 v${asset.version}` : ""}`), badge(state, asset.stale ? "warning" : ""));
  copy.append(heading, node("p", "asset-model-line", `${asset.provider || "local"}${asset.model ? ` \u00b7 ${asset.model}` : " \u00b7 model not recorded"} \u00b7 ${formatDate(asset.createdAt)}`));
  copy.append(assetActionControls(production, shot, asset, notice));

  if (asset.stage !== "storyboard") {
    const feedback = node("div", "asset-feedback");
    const note = node("textarea");
    note.rows = 2;
    note.placeholder = "What needs to change?";
    note.value = asset.feedback || "";
    const flag = node("button", "ghost-button", "Flag change");
    flag.type = "button";
    flag.disabled = asset.stale;
    flag.addEventListener("click", async () => {
      try {
        await runButton(flag, () => postProductionJson(`/api/productions/${encodeURIComponent(production.slug)}/shots/${encodeURIComponent(shot.shotId)}/assets/${encodeURIComponent(asset.assetId)}/flag`, { feedback: note.value }), "Flagging...");
        await refreshProductionRoute();
      } catch (error) {
        showNotice(notice, error.message, "error");
      }
    });
    feedback.append(note, flag);
    copy.append(feedback);
  }

  if ((asset.references || []).length) {
    const references = node("details", "asset-reference-details");
    references.append(node("summary", "", `References used \u00b7 ${asset.references.length}`), referenceList(asset.references));
    copy.append(references);
  }

  const detail = node("details", "asset-technical");
  detail.append(node("summary", "", "Prompt and technical details"));
  if (asset.prompt) detail.append(node("pre", "asset-prompt", asset.prompt));
  const facts = node("dl");
  const fields = [["Stage", stageLabel(asset.stage)], ["Model", asset.model], ["Path", asset.path], ["Asset ID", asset.assetId], ["Parent", asset.parentAssetId], ["SHA-256", asset.sha256], ["Feedback", asset.feedback]];
  for (const [key, value] of fields) {
    if (!value) continue;
    facts.append(node("dt", "", key), node("dd", "", String(value)));
  }
  if (Object.keys(asset.settings || {}).length) facts.append(node("dt", "", "Settings"), node("dd", "", JSON.stringify(asset.settings, null, 2)));
  detail.append(facts);
  copy.append(detail);
  item.append(copy);
  return item;
}

function generationWorkspace(production, shot, notice) {
  const workspace = node("section", "shot-generation-workspace");
  const heading = node("header");
  heading.append(node("div", "", ""), badge("Image generation", "pending"));
  heading.firstChild.append(node("span", "eyebrow", "Regenerate"), node("h2", "", "Prompt and generate"));
  workspace.append(heading);

  const current = shot.currentPrompt || {};
  const target = reviewAssetForShot(shot);
  const fields = node("div", "generation-fields");
  const stageField = node("label", "prompt-field-label", "Stage");
  const stageSelect = node("select", "production-stage-select");
  for (const [key, config] of Object.entries(shot.generationStages || {})) {
    const option = new Option(config.label || stageLabel(key), key);
    option.disabled = config.status === "blocked";
    option.selected = key === (current.stage || "style-composition");
    stageSelect.append(option);
  }
  stageField.append(stageSelect);
  const modelField = node("div", "generation-model-field");
  modelField.append(node("span", "prompt-field-label", "Model"), node("strong", "", ""), node("small", "", ""));
  fields.append(stageField, modelField);
  workspace.append(fields);

  const used = node("details", "used-prompt-details");
  used.append(node("summary", "", current.usedPrompt ? `Prompt used for current image \u00b7 v${current.assetVersion || "?"}` : "No recorded generation prompt for the current image"));
  if (current.usedPrompt) used.append(node("pre", "asset-prompt", current.usedPrompt));
  workspace.append(used);

  const label = node("label", "prompt-field-label", "Prompt for next generation");
  const textarea = node("textarea", "prompt-editor");
  textarea.rows = 14;
  textarea.value = current.prompt || "";
  label.append(textarea);
  workspace.append(label);

  const stageInfo = node("div", "generation-stage-info");
  const refsHeading = node("h3", "", "References that will be used");
  const refsContainer = node("div");
  stageInfo.append(refsHeading, refsContainer);
  workspace.append(stageInfo);

  const actions = node("div", "prompt-actions");
  const save = node("button", "ghost-button", "Save prompt");
  const generate = node("button", "primary-button", "Generate image");
  const pass = node("button", "ghost-button", "Pass current image");
  [save, generate, pass].forEach((button) => { button.type = "button"; });
  pass.disabled = !target || target.stage === "storyboard" || target.stale || approvedState(target.reviewState);
  actions.append(save, generate, pass);
  workspace.append(actions);

  function stageConfig() {
    return (shot.generationStages || {})[stageSelect.value] || {};
  }

  function renderStageInfo() {
    const config = stageConfig();
    modelField.querySelector("strong").textContent = config.model || "Model not registered";
    const blockers = config.blockers || [];
    modelField.querySelector("small").textContent = blockers.length ? `Blocked by: ${blockers.join(", ")}` : `${config.status || "unknown"}${config.aspectRatio ? ` \u00b7 ${config.aspectRatio}` : ""}${config.resolution ? ` \u00b7 ${config.resolution}` : ""}`;
    refsContainer.replaceChildren(referenceList(config.references || []));
    generate.disabled = config.status !== "ready" || Boolean(shot.sharedSetupOwnerShotId);
    generate.title = shot.sharedSetupOwnerShotId ? "Generate from the shared setup owner." : blockers.join(", ");
  }

  async function savePrompt() {
    return postProductionJson(`/api/productions/${encodeURIComponent(production.slug)}/shots/${encodeURIComponent(shot.shotId)}/prompt`, {
      prompt: textarea.value,
      stage: stageSelect.value,
      assetId: target?.assetId || current.assetId || "",
    });
  }

  stageSelect.addEventListener("change", renderStageInfo);
  save.addEventListener("click", async () => {
    try {
      await runButton(save, savePrompt, "Saving...");
      showNotice(notice, "Prompt saved. No generation launched.", "success");
    } catch (error) {
      showNotice(notice, error.message, "error");
    }
  });
  pass.addEventListener("click", async () => {
    if (!window.confirm(`Pass the current image for ${stageLabel(target.stage)}? This approves the asset stage only, not a Hearthlight gate.`)) return;
    try {
      await runButton(pass, () => postProductionJson(`/api/productions/${encodeURIComponent(production.slug)}/shots/${encodeURIComponent(shot.shotId)}/assets/${encodeURIComponent(target.assetId)}/approve`), "Passing...");
      await refreshProductionRoute();
    } catch (error) {
      showNotice(notice, error.message, "error");
    }
  });
  generate.addEventListener("click", async () => {
    const config = stageConfig();
    if (!window.confirm(`Generate one ${config.label || stageLabel(stageSelect.value)} image with ${config.model || "the registered model"}? This may incur provider cost.`)) return;
    try {
      const result = await runButton(generate, async () => {
        await savePrompt();
        return postProductionJson(`/api/productions/${encodeURIComponent(production.slug)}/shots/${encodeURIComponent(shot.shotId)}/generate`, {
          prompt: textarea.value,
          stage: stageSelect.value,
          model: config.model,
        });
      }, "Queueing...");
      showNotice(notice, `Generation queued with ${result.model}. You can leave this page; the job is durable.`, "success");
      await pollGenerationJob(production.slug, result.jobId, notice);
    } catch (error) {
      showNotice(notice, error.message, "error");
    }
  });

  renderStageInfo();
  return workspace;
}

async function pollGenerationJob(slug, jobId, notice) {
  for (;;) {
    const job = await fetchProductionJson(`/api/production-jobs/${encodeURIComponent(slug)}/${encodeURIComponent(jobId)}`);
    if (job.status === "completed") {
      await refreshProductionRoute();
      return;
    }
    if (job.status === "failed") throw new Error(job.error || "Generation failed");
    showNotice(notice, job.status === "running" ? "Generating image..." : "Generation queued...", "pending");
    await new Promise((resolve) => window.setTimeout(resolve, 2500));
  }
}

function renderShotDetail(data) {
  const { production, shot } = data;
  setProductionMeta(`${production.name} \u00b7 Shot ${shot.displayNumber}`);
  const page = node("div", "production-shot-detail");
  const notice = actionNotice();
  const nav = node("nav", "production-shot-nav");
  const back = node("button", "production-back", `\u2190 ${production.name}`);
  back.type = "button";
  back.addEventListener("click", () => goStudio({ slug: production.slug }));
  const arrows = node("div");
  const previous = node("button", "", "Previous");
  previous.type = "button";
  previous.disabled = !data.previousShotId;
  previous.addEventListener("click", () => goStudio({ slug: production.slug, shotId: data.previousShotId }));
  const next = node("button", "", "Next");
  next.type = "button";
  next.disabled = !data.nextShotId;
  next.addEventListener("click", () => goStudio({ slug: production.slug, shotId: data.nextShotId }));
  arrows.append(previous, next);
  nav.append(back, arrows);
  page.append(nav, notice);

  const hero = node("section", "production-shot-hero");
  const fallback = shot.newerPendingAsset?.thumbnailUrl || shot.newerPendingAsset?.mediaUrl || "";
  hero.append(mediaElement(shot.heroAsset, { hero: true, fallback }));
  const intro = node("div", "production-shot-intro");
  intro.append(node("span", "eyebrow", `Shot ${shot.displayNumber} \u00b7 ${formatRuntime(shot.durationSeconds)}`), node("h2", "", shot.title));
  const heroAsset = shot.heroAsset;
  if (heroAsset) {
    const metadata = node("dl", "hero-metadata");
    metadata.append(node("dt", "", "Stage"), node("dd", "", stageLabel(heroAsset.stage)));
    metadata.append(node("dt", "", "Model"), node("dd", "", heroAsset.model || "Not recorded"));
    metadata.append(node("dt", "", "Version"), node("dd", "", heroAsset.version ? `v${heroAsset.version}` : "Unversioned"));
    intro.append(metadata);
  }
  const badges = node("div", "production-badges");
  (shot.badges || []).forEach((value) => badges.append(badge(value, value.includes("missing") || value.includes("stale") ? "warning" : value.includes("pending") ? "pending" : "")));
  intro.append(badges);
  if (shot.newerPendingAsset) intro.append(node("p", "pending-callout", "Newer work is waiting for review. The approved visual remains the hero."));
  if (shot.sharedSetupOwnerShotId) {
    const shared = node("button", "shared-setup-link", "Open shared setup owner");
    shared.type = "button";
    shared.addEventListener("click", () => goStudio({ slug: production.slug, shotId: shot.sharedSetupOwnerShotId }));
    intro.append(shared);
  }
  const heroRefs = heroAsset?.references?.length ? heroAsset.references : shot.currentPrompt?.references || [];
  const refs = node("div", "hero-references");
  refs.append(node("span", "eyebrow", "Style / conditioning used"), referenceList(heroRefs));
  intro.append(refs);
  hero.append(intro);
  page.append(hero);

  const copyGrid = node("section", "production-copy-grid");
  copyGrid.append(
    detailSection("Story", [shot.story.visualDescription, shot.story.dialogue && `Dialogue: ${shot.story.dialogue}`, shot.story.audio && `Audio: ${shot.story.audio}`, shot.story.notes].filter(Boolean).join("\n\n")),
    detailSection("Image direction", [shot.imageDirection.visualDescription, shot.imageDirection.continuityNote].filter(Boolean).join("\n\n")),
    detailSection("Video motion", [shot.videoMotion.actionDescription, shot.videoMotion.cameraMovement && `Camera: ${shot.videoMotion.cameraMovement}`].filter(Boolean).join("\n\n")),
  );
  page.append(copyGrid, generationWorkspace(production, shot, notice));

  const dependencies = node("section", "shot-dependencies");
  dependencies.append(node("h3", "", "Required for this shot"));
  if ((shot.missingDependencies || []).length) {
    dependencies.append(node("p", "dependency-explainer", "Missing dependencies are source inputs needed before a later stage can be finalized, such as a character sheet, setting sheet, timing, or image direction. They do not necessarily block Style + composition; the stage panel above shows what is actually blocked."));
  } else {
    dependencies.append(node("p", "dependency-explainer is-clear", "All declared shot dependencies are present."));
  }
  const dependencyGrid = node("div");
  for (const requirement of shot.requirements || []) dependencyGrid.append(requirementCard(requirement));
  dependencies.append(dependencyGrid);
  page.append(dependencies);

  const history = node("section", "asset-history");
  const historyHeading = node("header");
  historyHeading.append(node("div", "", ""), node("span", "", `${shot.assetHistory.length} ${shot.assetHistory.length === 1 ? "asset" : "assets"}`));
  historyHeading.firstChild.append(node("span", "eyebrow", "Lineage"), node("h2", "", "Asset history"));
  history.append(historyHeading);
  if (shot.assetHistory.length) shot.assetHistory.forEach((asset) => history.append(assetHistoryItem(production, shot, asset, notice)));
  else history.append(node("p", "production-clear", "No board, still, or clip has been registered for this shot."));
  page.append(history);
  productionEls.content.replaceChildren(page);
}

function showProductionLoading() {
  const loading = node("div", "production-loading");
  loading.append(node("span", "production-loading-mark"), node("strong", "", "Reading Hearthlight project state..."));
  productionEls.content.replaceChildren(loading);
}

function showProductionError(error) {
  console.error(error);
  setStudioMode("projects");
  const panel = node("section", "production-library-empty");
  panel.append(node("h3", "", "Could not read production state"), node("p", "", error?.message || String(error)));
  productionEls.content.replaceChildren(panel);
}

async function restoreStudioRoute() {
  const route = currentStudioRoute();
  setStudioMode(route.mode);
  if (route.mode === "films") return;
  showProductionLoading();
  if (route.shotId && route.slug) {
    productionState.shot = await fetchProductionJson(`/api/productions/${encodeURIComponent(route.slug)}/shots/${encodeURIComponent(route.shotId)}`);
    renderShotDetail(productionState.shot);
    return;
  }
  if (route.slug) {
    productionState.production = await fetchProductionJson(`/api/productions/${encodeURIComponent(route.slug)}`);
    renderProductionOverview(productionState.production);
    return;
  }
  renderProductionLibrary(await loadProductionList());
}

productionEls.projectsTab.addEventListener("click", () => goStudio({ mode: "projects" }));
productionEls.filmStudiesTab.addEventListener("click", () => {
  window.history.pushState({ hearthlightStudio: true }, "", studioUrl({ mode: "films" }));
  window.dispatchEvent(new PopStateEvent("popstate"));
});
window.addEventListener("popstate", () => restoreStudioRoute().catch(showProductionError));

const initialRoute = currentStudioRoute();
if (initialRoute.mode === "projects" && !new URLSearchParams(window.location.search).has("space")) {
  window.history.replaceState({ hearthlightStudio: true }, "", studioUrl(initialRoute));
}
restoreStudioRoute().catch(showProductionError);
'@
$path = 'staging/productions.js'
$temp = 'staging/productions.js.new'
[IO.File]::WriteAllText((Join-Path (Resolve-Path staging).Path 'productions.js.new'), $source, [Text.UTF8Encoding]::new($false))
$patch = (& git diff --no-index -- $path $temp 2>$null) -join "`n"
$patch = $patch.Replace('b/staging/productions.js.new', 'b/staging/productions.js')
$patch | git apply --ignore-space-change --ignore-whitespace --whitespace=nowarn
if ($LASTEXITCODE -ne 0) { throw 'git apply failed' }
Remove-Item -LiteralPath $temp
node --check staging/productions.js