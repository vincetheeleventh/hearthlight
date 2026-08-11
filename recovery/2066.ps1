$chunk = @'

function renderProductionOverview(production) {
  setProductionMeta(`${production.shotCount} shots \u00b7 ${formatRuntime(production.runtimeSeconds)} \u00b7 ${production.pendingReviewCount} awaiting review`);
  const page = node("div", "production-overview");
  const notice = productionNotice();
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
  later.append(node("summary", "", `Missing later \u00b7 ${production.missingLater.length}`));
  production.missingLater.forEach((item) => later.append(requirementCard(item)));
  status.append(now, later);
  page.append(status);

  const wallHeader = node("header", "production-wall-heading");
  wallHeader.append(node("div", "", ""), node("span", "", `${production.uniqueIllustratedSetups} illustrated setups`));
  wallHeader.firstChild.append(node("span", "eyebrow", "Visual wall"), node("h2", "", "Every shot"));
  page.append(wallHeader, productionBatchToolbar(production, notice));
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

function productionAssetActions(production, shot, asset, notice) {
  const controls = node("div", "asset-actions");
  const choose = node("button", "ghost-button", shot.heroAsset?.assetId === asset.assetId ? "Current hero" : "Use as hero");
  choose.type = "button";
  choose.disabled = shot.heroAsset?.assetId === asset.assetId || asset.stale;
  choose.addEventListener("click", async () => {
    try {
      await productionButton(choose, () => postProductionJson(`/api/productions/${encodeURIComponent(production.slug)}/shots/${encodeURIComponent(shot.shotId)}/assets/${encodeURIComponent(asset.assetId)}/select`), "Selecting...");
      await refreshProductionRoute();
    } catch (error) { showProductionNotice(notice, error.message, "error"); }
  });
  controls.append(choose);
  if (asset.stage !== "storyboard") {
    const pass = node("button", "primary-button", "Pass this stage");
    pass.type = "button";
    pass.disabled = asset.stale || assetApproved(asset);
    pass.title = "Approves this asset stage only. It does not approve a Hearthlight gate.";
    pass.addEventListener("click", async () => {
      if (!window.confirm(`Pass this ${stageLabel(asset.stage)} asset? This does not approve a Hearthlight gate.`)) return;
      try {
        await productionButton(pass, () => postProductionJson(`/api/productions/${encodeURIComponent(production.slug)}/shots/${encodeURIComponent(shot.shotId)}/assets/${encodeURIComponent(asset.assetId)}/approve`), "Passing...");
        await refreshProductionRoute();
      } catch (error) { showProductionNotice(notice, error.message, "error"); }
    });
    controls.append(pass);
  }
  return controls;
}
'@
[IO.File]::AppendAllText((Resolve-Path staging).Path + '\productions.js.new', $chunk, [Text.UTF8Encoding]::new($false))