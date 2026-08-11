$chunk = @'

function renderShotDetail(data) {
  const { production, shot } = data;
  setProductionMeta(`${production.name} \u00b7 Shot ${shot.displayNumber}`);
  const page = node("div", "production-shot-detail");
  const notice = productionNotice();
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
  hero.append(mediaElement(shot.heroAsset, { hero: true, fallback: shot.newerPendingAsset?.thumbnailUrl || shot.newerPendingAsset?.mediaUrl || "" }));
  const intro = productionHeroInfo(shot);
  if (shot.sharedSetupOwnerShotId) {
    const shared = node("button", "shared-setup-link", "Open shared setup owner");
    shared.type = "button";
    shared.addEventListener("click", () => goStudio({ slug: production.slug, shotId: shot.sharedSetupOwnerShotId }));
    intro.append(shared);
  }
  hero.append(intro);
  page.append(hero);

  const copyGrid = node("section", "production-copy-grid");
  copyGrid.append(
    detailSection("Story", [shot.story.visualDescription, shot.story.dialogue && `Dialogue: ${shot.story.dialogue}`, shot.story.audio && `Audio: ${shot.story.audio}`, shot.story.notes].filter(Boolean).join("\n\n")),
    detailSection("Image direction", [shot.imageDirection.visualDescription, shot.imageDirection.continuityNote].filter(Boolean).join("\n\n")),
    detailSection("Video motion", [shot.videoMotion.actionDescription, shot.videoMotion.cameraMovement && `Camera: ${shot.videoMotion.cameraMovement}`].filter(Boolean).join("\n\n")),
  );
  page.append(copyGrid, productionGenerationWorkspace(production, shot, notice));

  const dependencies = node("section", "shot-dependencies");
  dependencies.append(node("h3", "", "Required for this shot"));
  dependencies.append(node("p", `dependency-explainer ${(shot.missingDependencies || []).length ? "" : "is-clear"}`.trim(),
    (shot.missingDependencies || []).length
      ? "Missing dependencies are source inputs needed before a later stage can be finalized, such as a character sheet, setting sheet, timing, or image direction. They do not necessarily block Style + composition; the generation panel above shows what is actually blocked."
      : "All declared shot dependencies are present."));
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
'@
[IO.File]::AppendAllText((Resolve-Path staging).Path + '\productions.js.new', $chunk, [Text.UTF8Encoding]::new($false))
node --check staging\productions.js.new