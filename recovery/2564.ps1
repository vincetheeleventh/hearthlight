$path='staging/productions.js'; $temp='staging/productions.js.new'; $text=[IO.File]::ReadAllText((Resolve-Path $path)); $old=@'
function productionNotice() {
'@; $new=@'
function overviewStageForShot(shot) {
  const history = (shot.assetHistory || []).filter((asset) => !asset.stale);
  const video = history.find((asset) => asset.kind === "video");
  const finalImage = history.find((asset) => asset.kind === "image" && (
    ["likeness", "final", "final-image"].includes(asset.stage)
    || asset.selectionState === "selected-final"
    || (asset.selectionPurposes || []).includes("final")
  ));
  const styleComposition = history.find((asset) => asset.kind === "image" && asset.stage === "style-composition");
  const workingImage = history.find((asset) => asset.kind === "image" && asset.stage !== "storyboard");
  const storyboard = history.find((asset) => asset.kind === "image" && asset.stage === "storyboard");
  const asset = video || finalImage || styleComposition || workingImage || storyboard || null;
  let key = "empty";
  let label = "No asset";
  if (asset === video) { key = "video"; label = "Video clip"; }
  else if (asset === finalImage) { key = "final-image"; label = "Final image"; }
  else if (asset === styleComposition) { key = "style-composition"; label = "Style + composition"; }
  else if (asset === workingImage) { key = "working-image"; label = "Working image"; }
  else if (asset === storyboard) { key = "storyboard"; label = "Storyboard"; }
  const review = !asset ? "waiting" : asset.reviewState === "revision-requested" ? "changes requested" : assetApproved(asset) ? "approved" : "pending review";
  return { key, label, asset, review };
}

function productionStageLegend() {
  const legend = node("section", "production-stage-legend");
  legend.setAttribute("aria-label", "Shot stage colours");
  legend.append(node("strong", "", "Stage colours"));
  for (const [key, label] of [["storyboard", "Storyboard"], ["style-composition", "Style + composition"], ["working-image", "Working image"], ["final-image", "Final image"], ["video", "Video clip"], ["empty", "No asset"]]) {
    const item = node("span", `stage-legend-item stage-${key}`);
    item.append(node("i"), node("span", "", label));
    legend.append(item);
  }
  return legend;
}

function productionNotice() {
'@; if(-not $text.Contains($old)){throw 'notice marker missing'}; $text=$text.Replace($old,$new)
$old=@'
shotCard = function(production, shot, notice) {
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
'@; $new=@'
shotCard = function(production, shot, notice) {
  const stage = overviewStageForShot(shot);
  const card = node("article", `production-shot-card stage-${stage.key}`);
  card.dataset.shotId = shot.shotId;
  card.dataset.productionStage = stage.key;
  const open = node("button", "production-shot-open");
  open.type = "button";
  open.addEventListener("click", () => goStudio({ slug: production.slug, shotId: shot.shotId }));
  open.append(mediaElement(shot.heroAsset, { fallback: shot.newerPendingAsset?.thumbnailUrl || shot.newerPendingAsset?.mediaUrl || "" }));
  const copy = node("div", "production-shot-card-copy");
  const header = node("div");
  header.append(node("strong", "", `Shot ${shot.displayNumber}`), node("span", "", formatRuntime(shot.durationSeconds)));
  copy.append(header, node("h3", "", shot.title));
  const stageLine = node("div", "shot-card-stage-line");
  stageLine.append(badge(stage.label, `stage-colour stage-${stage.key}`));
  const stageDetail = [stage.asset?.model || (stage.asset ? "model not recorded" : "waiting for asset"), stage.review].filter(Boolean).join(" \u00b7 ");
  stageLine.append(node("span", "", stageDetail));
  copy.append(stageLine);
  const badges = node("div", "production-badges");
  for (const value of shot.badges || []) badges.append(badge(value, value.includes("missing") || value.includes("stale") || value.includes("unresolved") ? "warning" : value.includes("pending") ? "pending" : ""));
  copy.append(badges);
  open.append(copy);
  card.append(open, productionQuickReview(production, shot, notice));
  return card;
}
'@; if(-not $text.Contains($old)){throw 'shotCard block missing'}; $text=$text.Replace($old,$new)
$old='  page.append(wallHeader, productionBatchToolbar(production, notice));'
$new='  page.append(wallHeader, productionStageLegend(), productionBatchToolbar(production, notice));'
if(-not $text.Contains($old)){throw 'wall header marker missing'}; $text=$text.Replace($old,$new)
[IO.File]::WriteAllText((Join-Path (Resolve-Path staging).Path 'productions.js.new'),$text,[Text.UTF8Encoding]::new($false)); Copy-Item $temp staging\check-productions.js -Force; node --check staging\check-productions.js; if($LASTEXITCODE-ne 0){throw 'syntax failed'}; $patch=(& git diff --no-index -- $path $temp 2>$null)-join "`n"; $patch=$patch.Replace('b/staging/productions.js.new','b/staging/productions.js'); $patch | git apply --ignore-space-change --ignore-whitespace --whitespace=nowarn; if($LASTEXITCODE-ne 0){throw 'git apply failed'}; Remove-Item $temp; Remove-Item staging\check-productions.js