$path='staging/productions.js'; $temp='staging/productions.js.new'; $text=[IO.File]::ReadAllText((Resolve-Path $path)); $old=@'
function reviewAssetForShot(shot) {
  return shot.newerPendingAsset
    || (shot.assetHistory || []).find((asset) => asset.kind === "image" && asset.stage !== "storyboard" && !asset.stale)
    || (shot.heroAsset?.stage !== "storyboard" ? shot.heroAsset : null);
}
'@; $new=@'
function reviewAssetForShot(shot) {
  const newerImage = shot.newerPendingAsset?.kind === "image" ? shot.newerPendingAsset : null;
  return newerImage
    || (shot.assetHistory || []).find((asset) => asset.kind === "image" && ["style-composition", "likeness"].includes(asset.stage) && !asset.stale)
    || (shot.assetHistory || []).find((asset) => asset.kind === "image" && asset.stage !== "storyboard" && !asset.stale)
    || (shot.heroAsset?.kind === "image" && shot.heroAsset?.stage !== "storyboard" ? shot.heroAsset : null);
}
'@; if(-not $text.Contains($old)){throw 'review target function missing'}; $text=$text.Replace($old,$new); [IO.File]::WriteAllText((Join-Path (Resolve-Path staging).Path 'productions.js.new'),$text,[Text.UTF8Encoding]::new($false)); Copy-Item $temp staging\check-productions.js -Force; node --check staging\check-productions.js; if($LASTEXITCODE-ne 0){throw 'syntax failed'}; $patch=(& git diff --no-index -- $path $temp 2>$null)-join "`n"; $patch=$patch.Replace('b/staging/productions.js.new','b/staging/productions.js'); $patch | git apply --ignore-space-change --ignore-whitespace --whitespace=nowarn; if($LASTEXITCODE-ne 0){throw 'git apply failed'}; Remove-Item $temp; Remove-Item staging\check-productions.js