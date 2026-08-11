Copy-Item -LiteralPath staging\productions.js -Destination staging\productions.js.new -Force
$chunk = @'

/* Hearthlight Studio interactive production controls. */
async function postProductionJson(url, payload = {}) {
  const response = await fetch(url, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
  if (!response.ok) {
    const text = await response.text();
    const match = text.match(/<p>(.*?)<\/p>/is);
    throw new Error((match?.[1] || text || response.statusText).replace(/<[^>]+>/g, " ").replace(/&quot;/g, '"').replace(/&#x27;/g, "'").replace(/&amp;/g, "&").replace(/\s+/g, " ").trim());
  }
  return response.json();
}

function stageLabel(stage) {
  return ({ "style-composition": "Style + composition", likeness: "Likeness", storyboard: "Storyboard", video: "Video", image: "Image" })[stage]
    || String(stage || "Asset").replaceAll("-", " ");
}

function assetApproved(asset) {
  return ["approved", "done", "pass", "passed", "selected", "final", "composition-approved", "likeness-approved"].includes(String(asset?.reviewState || "").toLowerCase());
}

function reviewAssetForShot(shot) {
  return shot.newerPendingAsset
    || (shot.assetHistory || []).find((asset) => asset.kind === "image" && asset.stage !== "storyboard" && !asset.stale)
    || (shot.heroAsset?.stage !== "storyboard" ? shot.heroAsset : null);
}

function productionNotice() {
  const element = node("p", "production-action-notice");
  element.setAttribute("role", "status");
  element.setAttribute("aria-live", "polite");
  return element;
}

function showProductionNotice(element, message, tone = "") {
  element.textContent = message;
  element.className = `production-action-notice ${tone}`.trim();
}

async function productionButton(button, task, working = "Working...") {
  const label = button.textContent;
  button.disabled = true;
  button.textContent = working;
  try { return await task(); }
  finally { button.disabled = false; button.textContent = label; }
}

async function refreshProductionRoute() {
  productionState.list = null;
  productionState.production = null;
  productionState.shot = null;
  await restoreStudioRoute();
}

function productionReferences(references = []) {
  const grid = node("div", "production-reference-grid");
  if (!references.length) {
    grid.append(node("p", "production-reference-empty", "No style or conditioning reference registered."));
    return grid;
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
    grid.append(card);
  }
  return grid;
}

function productionPromptEditor(production, shot, notice) {
  const details = node("details", "shot-card-prompt-details");
  details.append(node("summary", "", "Edit prompt"));
  const body = node("div", "shot-card-prompt");
  const textarea = node("textarea", "shot-prompt-input");
  textarea.rows = 5;
  textarea.value = shot.currentPrompt?.prompt || "";
  const save = node("button", "ghost-button", "Save prompt");
  save.type = "button";
  save.addEventListener("click", async () => {
    try {
      await productionButton(save, () => postProductionJson(`/api/productions/${encodeURIComponent(production.slug)}/shots/${encodeURIComponent(shot.shotId)}/prompt`, {
        prompt: textarea.value,
        stage: shot.currentPrompt?.stage || "style-composition",
        assetId: reviewAssetForShot(shot)?.assetId || shot.currentPrompt?.assetId || "",
      }), "Saving...");
      showProductionNotice(notice, `Shot ${shot.displayNumber}: prompt saved.`, "success");
    } catch (error) { showProductionNotice(notice, error.message, "error"); }
  });
  body.append(textarea, save);
  details.append(body);
  return details;
}
'@
[IO.File]::AppendAllText((Resolve-Path staging).Path + '\productions.js.new', $chunk, [Text.UTF8Encoding]::new($false))