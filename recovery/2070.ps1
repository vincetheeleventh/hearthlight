$chunk = @'

function assetHistoryItem(production, shot, asset, notice) {
  const item = node("article", `asset-history-item ${asset.stale ? "is-stale" : ""}`);
  item.append(mediaElement(asset));
  const copy = node("div", "asset-history-copy");
  const heading = node("header");
  const state = shot.heroAsset?.assetId === asset.assetId ? "chosen hero" : asset.stale ? "stale" : asset.selectionState || asset.reviewState;
  heading.append(node("strong", "", `${stageLabel(asset.stage)}${asset.version ? ` \u00b7 v${asset.version}` : ""}`), badge(state, asset.stale ? "warning" : ""));
  copy.append(heading, node("p", "asset-model-line", `${asset.provider || "local"}${asset.model ? ` \u00b7 ${asset.model}` : " \u00b7 model not recorded"} \u00b7 ${formatDate(asset.createdAt)}`));
  copy.append(productionAssetActions(production, shot, asset, notice));

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
        await productionButton(flag, () => postProductionJson(`/api/productions/${encodeURIComponent(production.slug)}/shots/${encodeURIComponent(shot.shotId)}/assets/${encodeURIComponent(asset.assetId)}/flag`, { feedback: note.value }), "Flagging...");
        await refreshProductionRoute();
      } catch (error) { showProductionNotice(notice, error.message, "error"); }
    });
    feedback.append(note, flag);
    copy.append(feedback);
  }

  if ((asset.references || []).length) {
    const references = node("details", "asset-reference-details");
    references.append(node("summary", "", `References used \u00b7 ${asset.references.length}`), productionReferences(asset.references));
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

async function pollProductionGeneration(slug, jobId, notice) {
  for (;;) {
    const job = await fetchProductionJson(`/api/production-jobs/${encodeURIComponent(slug)}/${encodeURIComponent(jobId)}`);
    if (job.status === "completed") { await refreshProductionRoute(); return; }
    if (job.status === "failed") throw new Error(job.error || "Generation failed");
    showProductionNotice(notice, job.status === "running" ? "Generating image..." : "Generation queued...", "pending");
    await new Promise((resolve) => window.setTimeout(resolve, 2500));
  }
}

function productionGenerationWorkspace(production, shot, notice) {
  const workspace = node("section", "shot-generation-workspace");
  const heading = node("header");
  heading.append(node("div", "", ""), badge("Image generation", "pending"));
  heading.firstChild.append(node("span", "eyebrow", "Regenerate"), node("h2", "", "Prompt and generate"));
  workspace.append(heading);
  const current = shot.currentPrompt || {};
  const target = reviewAssetForShot(shot);
  const fields = node("div", "generation-fields");
  const stageField = node("label", "prompt-field-label", "Stage");
  const select = node("select", "production-stage-select");
  for (const [key, config] of Object.entries(shot.generationStages || {})) {
    const option = new Option(config.label || stageLabel(key), key);
    option.disabled = config.status === "blocked";
    option.selected = key === (current.stage || "style-composition");
    select.append(option);
  }
  stageField.append(select);
  const model = node("div", "generation-model-field");
  model.append(node("span", "prompt-field-label", "Model"), node("strong"), node("small"));
  fields.append(stageField, model);
  workspace.append(fields);
  const used = node("details", "used-prompt-details");
  used.append(node("summary", "", current.usedPrompt ? `Prompt used for current image \u00b7 v${current.assetVersion || "?"}` : "No recorded generation prompt for the current image"));
  if (current.usedPrompt) used.append(node("pre", "asset-prompt", current.usedPrompt));
  workspace.append(used);
  const promptLabel = node("label", "prompt-field-label", "Prompt for next generation");
  const prompt = node("textarea", "prompt-editor");
  prompt.rows = 14;
  prompt.value = current.prompt || "";
  promptLabel.append(prompt);
  workspace.append(promptLabel);
'@
[IO.File]::AppendAllText((Resolve-Path staging).Path + '\productions.js.new', $chunk, [Text.UTF8Encoding]::new($false))