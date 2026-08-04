# GitHub Setup — Hearthlight system repo

Versions the **instruction layer** (skills, docs, AGENTS.md, the pipeline). Private repo, lives in
the Windows copy (the canonical files). Project media + secrets are git-ignored.

Run all commands in a terminal, in the Story Studio folder:
```bash
cd "C:\Users\vxi\AppData\Local\hermes\Story Studio"
```

## 0. One-time: is git configured? (skip if you've used git here before)
```bash
git --version                      # confirm git exists
git config --global user.name  "Vince"
git config --global user.email "talefeatherbooks@gmail.com"
```

## 1. Initialize the repo and verify the ignore is working FIRST
```bash
git init
git add -A
git status            # ← READ THIS before committing
```
**Critical check:** in the `git status` list you should see skills/, the *.md docs, AGENTS.md,
_git/ — and you should NOT see: any .env, the projects/ folder, any .png/.mp4/.wav/.webm.
If you see a secret or media file staged, STOP — the .gitignore isn't catching it; fix before commit.
```bash
git ls-files | grep -iE '\.env|/projects/|\.(png|jpg|mp4|mov|wav|webm|m4a)$'   # should print NOTHING
```

## 2. First commit
```bash
git commit -m "Hearthlight instruction layer v0.1 — 15 skills, pipeline, crew, docs"
```

## 3. Create the private GitHub repo
Two ways — pick one:

**A) GitHub CLI (easiest, if `gh` is installed):**
```bash
gh auth login            # once, follow prompts
gh repo create hearthlight-system --private --source=. --remote=origin --push
```
Done — that creates the private repo AND pushes. Skip step 4.

**B) Manually:**
1. On github.com → New repository → name `hearthlight-system` → **Private** → do NOT add README/.gitignore (you have them) → Create.
2. Copy the repo URL it shows (e.g. `https://github.com/<you>/hearthlight-system.git`).

## 4. (If you used B) connect and push
```bash
git remote add origin https://github.com/<you>/hearthlight-system.git
git branch -M main
git push -u origin main
```
GitHub will ask for auth — use a Personal Access Token (github.com → Settings → Developer settings →
Tokens) as the password, not your account password.

## Daily use after setup
```bash
git add -A
git commit -m "what changed"
git push
```
Commit whenever you've revised skills/docs. Each commit is a restore point.

## What's tracked vs not
- **Tracked:** skills/, *.md docs (README, AGENTS, USER-GUIDE, AUDIENCE-CONTEXT, TASTE…), profile/ docs,
  _git/. The reusable system.
- **NOT tracked:** projects/ (all project work + the storyteller's media + rights-constrained refs),
  any .env/secret, any media file, logs. These stay local only.
