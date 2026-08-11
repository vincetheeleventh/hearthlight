$chunk = @'

function productionQuickReview(production, shot, notice) {
  const controls = node("section", "shot-quick-review");
  const target = reviewAssetForShot(shot);
  const note = node("textarea", "shot-feedback-input");
  note.rows = 2;
  note.placeholder = target ? "What needs to change?" : "No generated image to review yet";
  note.disabled = !target;
  note.value = target?.feedback || "";
  const actions = node("div", "shot-review-actions");
  const flag = node("button", "ghost-button", "Flag change");
  flag.type = "button";
  flag.disabled = !target || target.stale;
  flag.addEventListener("click", async () => {
    try {
      await productionButton(flag, () => postProductionJson(`/api/productions/${encodeURIComponent(production.slug)}/shots/${encodeURIComponent(shot.shotId)}/assets/${encodeURIComponent(target.assetId)}/flag`, { feedback: note.value }), "Flagging...");
      await refreshProductionRoute();
    } catch (error) { showProductionNotice(notice, error.message, "error"); }
  });
  const pass = node("button", "primary-button", "Pass stage");
  pass.type = "button";
  pass.disabled = !target || target.stale || assetApproved(target);
  pass.title = "Approves this asset stage only. It does not approve a Hearthlight gate.";
  pass.addEventListener("click", async () => {
    if (!window.confirm(`Pass Shot ${shot.displayNumber} for ${stageLabel(target.stage)}? This approves the asset stage only, not a Hearthlight gate.`)) return;
    try {
      await productionButton(pass, () => postProductionJson(`/api/productions/${encodeURIComponent(production.slug)}/shots/${encodeURIComponent(shot.shotId)}/assets/${encodeURIComponent(target.assetId)}/approve`), "Passing...");
      await refreshProductionRoute();
    } catch (error) { showProductionNotice(notice, error.message, "error"); }
  });
  actions.append(flag, pass);
  controls.append(note, actions, productionPromptEditor(production, shot, notice));
  return controls;
}

function shotCard(production, shot, notice) {
  const card = node("article", "production-shot-card");
  card.dataset.shotId = shot.shotId;
  const open = node("button", "production-shot-open");
  open.type = "button";
  open.addEventListener("click", () => goStudio({ slug: production.slug, shotId: shot.shotId }));
  open.append(mediaElement(shot.heroAsset, { fallback: shot.newerPendingAsset?.thumbnailUrl || shot.newerPendingAsset?.mediaUrl || "" }));
  const copy = node("div", "production-shot-card-copy");
  const header = node("div");
  header.append(node("strong", "", `Shot ${shot.displayNumber}`), node("span", "", formatRuntime(shot.durationSeconds)));
  copy.append(header, node("h3", "", shot.title));
  const active = reviewAssetForShot(shot) || shot.heroAsset;
  if (active) copy.append(node("p", "shot-card-stage", `${stageLabel(active.stage)}${active.model ? ` \u00b7 ${active.model}` : ""}`));
  const badges = node("div", "production-badges");
  for (const value of shot.badges || []) badges.append(badge(value, value.includes("missing") || value.includes("stale") || value.includes("unresolved") ? "warning" : value.includes("pending") ? "pending" : ""));
  copy.append(badges);
  open.append(copy);
  card.append(open, productionQuickReview(production, shot, notice));
  return card;
}

function productionBatchToolbar(production, notice) {
  const toolbar = node("section", "production-review-toolbar");
  const copy = node("div");
  copy.append(node("strong", "", "Batch review"), node("span", "", "Approves only latest unflagged assets. Hearthlight gates stay unchanged."));
  const select = node("select", "production-stage-select");
  select.append(new Option("Style + composition", "style-composition"), new Option("Likeness", "likeness"));
  const approve = node("button", "primary-button", "Approve all unflagged");
  approve.type = "button";
  approve.addEventListener("click", async () => {
    const label = select.options[select.selectedIndex].text;
    if (!window.confirm(`Approve every latest unflagged ${label} image? Flagged images, images with feedback, and Hearthlight gates will not change.`)) return;
    try {
      const result = await productionButton(approve, () => postProductionJson(`/api/productions/${encodeURIComponent(production.slug)}/bulk-approve`, { stage: select.value }), "Approving...");
      window.alert(`${result.count} ${result.count === 1 ? "image" : "images"} approved for ${label}.`);
      await refreshProductionRoute();
    } catch (error) { showProductionNotice(notice, error.message, "error"); }
  });
  toolbar.append(copy, select, approve);
  return toolbar;
}
'@
[IO.File]::AppendAllText((Resolve-Path staging).Path + '\productions.js.new', $chunk, [Text.UTF8Encoding]::new($false))