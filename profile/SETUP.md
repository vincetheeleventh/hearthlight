# Hearthlight profile — setup checklist

Run these in your WSL terminal, in order. Each step is safe to re-run.

## 1. Update Hermes (gets you the missing ComfyUI skill)
```bash
hermes update
```
Verify afterwards: `hermes skills list | grep -i comfy` — if still missing:
```bash
hermes skills install NousResearch/hermes-agent/skills/creative/comfyui
```

## 2. Create the profile (clones your working config + OpenRouter key)
```bash
hermes profile create hearthlight --clone --description "Creative director's pipeline agent: turns spoken family stories into illustrated narrative media through gated stages."
```

## 3. Point it at Claude and the Story Studio workspace
```bash
hearthlight config set model.default anthropic/claude-sonnet-4.6
hearthlight config set terminal.cwd "/home/vxi/.hermes/Story Studio"
```
Then open `~/.hermes/profiles/hearthlight/config.yaml` and set:
```yaml
skills:
  external_dirs:
    - "/home/vxi/.hermes/Story Studio/skills"
```

## 4. Install the soul
```bash
cp "/home/vxi/.hermes/Story Studio/profile/SOUL.md" ~/.hermes/profiles/hearthlight/SOUL.md
```

## 5. Telegram bot (≈2 minutes)
1. In Telegram, message **@BotFather** → `/newbot` → name it (e.g. "Hearthlight Studio") → copy the token.
2. Add to `~/.hermes/profiles/hearthlight/.env`:
   ```
   TELEGRAM_BOT_TOKEN=<paste token>
   ```
3. Start it. Two modes — pick one:
   ```bash
   # A) Foreground (testing): terminal stays open, logs visible live
   hearthlight gateway start --foreground      # or `hearthlight gateway run` on some builds

   # B) Persistent service (survives reboots): MUST install first, then start
   hearthlight gateway install                 # registers hermes-gateway-hearthlight.service
   hearthlight gateway start
   ```
   PITFALL: a bare `hearthlight gateway start` defaults to SERVICE mode and fails with
   "Unit hermes-gateway-hearthlight.service not found" (exit 5) if you haven't run
   `gateway install` first. Either install first, or use `--foreground`.
   Confirm the token is present before starting: `grep -i telegram ~/.hermes/profiles/hearthlight/.env`

## 6. Image generation key (needed for Stage 4, can wait)
Add your OpenAI API key (gpt-image-2 access) to the same `.env`:
```
OPENAI_API_KEY=<key>
```

## 7. Smoke test
Message the new bot: *"what skills do you have?"* → `hearthlight-consolidate` should appear.
Then send a voice-note rant and reply `/hearthlight-consolidate`. Gate 0 awaits.

## Notes
- Each profile = its own gateway process + bot token. Hermes blocks duplicate tokens across profiles automatically.
- A profile does NOT sandbox the agent; `terminal.cwd` is a starting directory, not a wall.
- Model string: check `hearthlight config show` / OpenRouter for the exact current Claude model id you prefer.
