# Syncthing ignore rules — canonical copies

`projects/` is gitignored (D-006), so an ignore file living inside it cannot travel by git. The
authoritative copies live here instead; the working copies are placed by hand on each machine.

| Canonical (tracked here) | Working copy (on each machine) |
|---|---|
| `projects.stignore` | `<Story Studio>/projects/.stignore` |
| `film-study-outputs.stignore` | `<Film Study Tool>/outputs/.stignore` |

## Placing them

**Windows**

```powershell
copy "governance\syncthing\projects.stignore" "projects\.stignore"
```

**macOS / Linux**

```bash
cp governance/syncthing/projects.stignore projects/.stignore
cp governance/syncthing/film-study-outputs.stignore \
   ~/Documents/"Film Study Tool"/outputs/.stignore
```

Then confirm Syncthing picked them up: **Folder → Edit → Ignore Patterns** should show the file's
contents. If it is empty, paste them in through the GUI — Syncthing only reads `.stignore` at the
folder root, and only when the folder is rescanned.

## If you change a rule

Edit the copy **here**, commit it, then re-place it on both machines. Editing only the working copy
means the next machine you set up gets the old rules — and an ignore rule that exists on one side but
not the other is how 4 GB of source footage ends up on a laptop.

## Why these rules matter

`projects.stignore` excludes `00-source/**`. That media is immutable, large, and in the McConaughey
case **private use only**. Excluding it by rule rather than by discipline means it cannot leak by
accident. See D-021.
