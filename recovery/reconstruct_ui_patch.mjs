import fs from "node:fs";
import path from "node:path";

const root = process.cwd();

function extractTemplate(source, marker) {
  const markerAt = source.indexOf(marker);
  if (markerAt < 0) throw new Error(`Missing marker: ${marker}`);
  const start = source.indexOf("`", markerAt) + 1;
  let escaped = false;
  for (let index = start; index < source.length; index += 1) {
    const char = source[index];
    if (char === "`" && !escaped) return source.slice(start, index);
    if (char === "\\" && !escaped) escaped = true;
    else escaped = false;
  }
  throw new Error(`Unclosed template: ${marker}`);
}

function evaluateTemplate(template, names = [], values = []) {
  return Function(...names, `return \`${template}\`;`)(...values);
}

const source3126 = fs.readFileSync(path.join(root, "recovery", "3126.js"), "utf8");
const addition = evaluateTemplate(extractTemplate(source3126, "const addition="));
const patch3126 = evaluateTemplate(extractTemplate(source3126, "const patch="), ["addition"], [addition])
  .replaceAll("a/film_study_tool/ui_static/productions.js", "a/staging/productions.js")
  .replaceAll("b/film_study_tool/ui_static/productions.js", "b/staging/productions.js");

const source3139 = fs.readFileSync(path.join(root, "recovery", "3139.js"), "utf8");
const patch3139 = evaluateTemplate(extractTemplate(source3139, "const patch="))
  .replaceAll("a/film_study_tool/ui_static/productions.js", "a/staging/productions.js")
  .replaceAll("b/film_study_tool/ui_static/productions.js", "b/staging/productions.js");

fs.writeFileSync(path.join(root, "recovery", "3126.patch"), patch3126, "utf8");
fs.writeFileSync(path.join(root, "recovery", "3139.patch"), patch3139, "utf8");
fs.writeFileSync(path.join(root, "recovery", "shot_structure_addition.js"), addition, "utf8");
