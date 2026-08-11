const patch=`diff --git a/film_study_tool/ui_static/productions.js b/film_study_tool/ui_static/productions.js
--- a/film_study_tool/ui_static/productions.js
+++ b/film_study_tool/ui_static/productions.js
@@ -548 +548 @@
-function shotStructureControls(production, shot, notice) {
+function shotStructureControls(production, shot, notice, returnToOverview = false) {
@@ -559 +559 @@
-  remove.addEventListener("click", () => retireProductionShot(production, shot, notice));
+  remove.addEventListener("click", () => retireProductionShot(production, shot, notice, returnToOverview));
@@ -787 +787 @@
-  card.append(open, productionQuickReview(production, shot, notice));
+  card.append(open, productionQuickReview(production, shot, notice), shotStructureControls(production, shot, notice));
@@ -842 +842 @@
-  page.append(wallHeader, productionStageLegend(), productionBatchToolbar(production, notice));
+  page.append(wallHeader, productionStageLegend(), productionStructureToolbar(production, notice), productionBatchToolbar(production, notice));
@@ -845,0 +846,2 @@
+  const retired = retiredShotTray(production, notice);
+  if (retired) page.append(retired);
@@ -1079 +1082 @@
-  nav.append(back, arrows);
+  nav.append(back, arrows, shotStructureControls(production, shot, notice, true));
`;
text(await tools.shell_command({command:`@'\n${patch}\n'@ | git apply --unidiff-zero --whitespace=nowarn -`,workdir:"C:\\Users\\vxi\\OneDrive\\Documents\\Film Study Tool",timeout_ms:10000,sandbox_permissions:"require_escalated",justification:"Allow me to place insert/delete controls on every shot card and detail page, plus a restore tray on the overview?"}));