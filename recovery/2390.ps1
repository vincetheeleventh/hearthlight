$path='staging/productions.js'; $temp='staging/productions.js.new'
$text=[IO.File]::ReadAllText((Resolve-Path $path)); $marker='/* Hearthlight Studio interactive production controls. */'; $index=$text.IndexOf($marker); if($index -lt 0){throw 'interactive marker missing'}
$head=$text.Substring(0,$index); $tail=$text.Substring($index)
$tail=$tail.Replace('function shotCard(production, shot, notice) {','shotCard = function(production, shot, notice) {')
$tail=$tail.Replace("  return card;`n}`n`nfunction productionBatchToolbar","  return card;`n};`n`nfunction productionBatchToolbar")
$tail=$tail.Replace('function renderProductionOverview(production) {','renderProductionOverview = function(production) {')
$tail=$tail.Replace("  productionEls.content.replaceChildren(page);`n}`n`nfunction productionAssetActions","  productionEls.content.replaceChildren(page);`n};`n`nfunction productionAssetActions")
$tail=$tail.Replace('function assetHistoryItem(production, shot, asset, notice) {','assetHistoryItem = function(production, shot, asset, notice) {')
$tail=$tail.Replace("  return item;`n}`n`nasync function pollProductionGeneration","  return item;`n};`n`nasync function pollProductionGeneration")
$tail=$tail.Replace('function renderShotDetail(data) {','renderShotDetail = function(data) {')
$tail=[Text.RegularExpressions.Regex]::Replace($tail,'  productionEls\.content\.replaceChildren\(page\);\r?\n}\r?\n?$','  productionEls.content.replaceChildren(page);'+"`n};`n")
$updated=$head+$tail
[IO.File]::WriteAllText((Join-Path (Resolve-Path staging).Path 'productions.js.new'),$updated,[Text.UTF8Encoding]::new($false))
Copy-Item $temp staging\check-productions.js -Force
node --check staging\check-productions.js
if($LASTEXITCODE-ne 0){throw 'JavaScript syntax failed'}
$patch=(& git diff --no-index -- $path $temp 2>$null)-join "`n"; $patch=$patch.Replace('b/staging/productions.js.new','b/staging/productions.js'); $patch | git apply --ignore-space-change --ignore-whitespace --whitespace=nowarn
if($LASTEXITCODE-ne 0){throw 'git apply failed'}
Remove-Item $temp; Remove-Item staging\check-productions.js
rg -n "^(function |shotCard =|renderProductionOverview =|assetHistoryItem =|renderShotDetail =)" staging\productions.js | Select-Object -Last 18