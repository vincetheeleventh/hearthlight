$chunk = @'
  const referenceSection = node("div", "generation-stage-info");
  referenceSection.append(node("h3", "", "References that will be used"), node("div"));
  workspace.append(referenceSection);
  const actions = node("div", "prompt-actions");
  const save = node("button", "ghost-button", "Save prompt");
  const generate = node("button", "primary-button", "Generate image");
  const pass = node("button", "ghost-button", "Pass current image");
  [save, generate, pass].forEach((button) => { button.type = "button"; });
  pass.disabled = !target || target.stage === "storyboard" || target.stale || assetApproved(target);
  actions.append(save, generate, pass);
  workspace.append(actions);

  const config = () => (shot.generationStages || {})[select.value] || {};
  const renderStage = () => {
    const stage = config();
    model.querySelector("strong").textContent = stage.model || "Model not registered";
    model.querySelector("small").textContent = (stage.blockers || []).length
      ? `Blocked by: ${stage.blockers.join(", ")}`
      : `${stage.status || "unknown"}${stage.aspectRatio ? ` \u00b7 ${stage.aspectRatio}` : ""}${stage.resolution ? ` \u00b7 ${stage.resolution}` : ""}`;
    referenceSection.lastChild.replaceChildren(productionReferences(stage.references || []));
    generate.disabled = stage.status !== "ready" || Boolean(shot.sharedSetupOwnerShotId);
    generate.title = shot.sharedSetupOwnerShotId ? "Generate from the shared setup owner." : (stage.blockers || []).join(", ");
  };
  const savePrompt = () => postProductionJson(`/api/productions/${encodeURIComponent(production.slug)}/shots/${encodeURIComponent(shot.shotId)}/prompt`, {
    prompt: prompt.value, stage: select.value, assetId: target?.assetId || current.assetId || "",
  });
  select.addEventListener("change", renderStage);
  save.addEventListener("click", async () => {
    try {
      await productionButton(save, savePrompt, "Saving...");
      showProductionNotice(notice, "Prompt saved. No generation launched.", "success");
    } catch (error) { showProductionNotice(notice, error.message, "error"); }
  });
  pass.addEventListener("click", async () => {
    if (!window.confirm(`Pass the current image for ${stageLabel(target.stage)}? This approves the asset stage only, not a Hearthlight gate.`)) return;
    try {
      await productionButton(pass, () => postProductionJson(`/api/productions/${encodeURIComponent(production.slug)}/shots/${encodeURIComponent(shot.shotId)}/assets/${encodeURIComponent(target.assetId)}/approve`), "Passing...");
      await refreshProductionRoute();
    } catch (error) { showProductionNotice(notice, error.message, "error"); }
  });
  generate.addEventListener("click", async () => {
    const stage = config();
    if (!window.confirm(`Generate one ${stage.label || stageLabel(select.value)} image with ${stage.model || "the registered model"}? This may incur provider cost.`)) return;
    try {
      const result = await productionButton(generate, async () => {
        await savePrompt();
        return postProductionJson(`/api/productions/${encodeURIComponent(production.slug)}/shots/${encodeURIComponent(shot.shotId)}/generate`, { prompt: prompt.value, stage: select.value, model: stage.model });
      }, "Queueing...");
      showProductionNotice(notice, `Generation queued with ${result.model}. You can leave this page; the job is durable.`, "success");
      await pollProductionGeneration(production.slug, result.jobId, notice);
    } catch (error) { showProductionNotice(notice, error.message, "error"); }
  });
  renderStage();
  return workspace;
}

function productionHeroInfo(shot) {
  const intro = node("div", "production-shot-intro");
  intro.append(node("span", "eyebrow", `Shot ${shot.displayNumber} \u00b7 ${formatRuntime(shot.durationSeconds)}`), node("h2", "", shot.title));
  const asset = shot.heroAsset;
  if (asset) {
    const meta = node("dl", "hero-metadata");
    meta.append(node("dt", "", "Stage"), node("dd", "", stageLabel(asset.stage)), node("dt", "", "Model"), node("dd", "", asset.model || "Not recorded"), node("dt", "", "Version"), node("dd", "", asset.version ? `v${asset.version}` : "Unversioned"));
    intro.append(meta);
  }
  const badges = node("div", "production-badges");
  (shot.badges || []).forEach((value) => badges.append(badge(value, value.includes("missing") || value.includes("stale") ? "warning" : value.includes("pending") ? "pending" : "")));
  intro.append(badges);
  if (shot.newerPendingAsset) intro.append(node("p", "pending-callout", "Newer work is waiting for review. The approved visual remains the hero."));
  const refs = node("div", "hero-references");
  refs.append(node("span", "eyebrow", "Style / conditioning used"), productionReferences(asset?.references?.length ? asset.references : shot.currentPrompt?.references || []));
  intro.append(refs);
  return intro;
}
'@
[IO.File]::AppendAllText((Resolve-Path staging).Path + '\productions.js.new', $chunk, [Text.UTF8Encoding]::new($false))