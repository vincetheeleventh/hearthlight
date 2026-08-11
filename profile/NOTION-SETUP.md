# Hearthlight — Notion MCP setup

Goal: let the Hearthlight profile write notes to Notion directly, so Notion is a readable point of contact. One-time setup.

The page below is the original pilot page; a project page per film works the same way — share it with the integration and record its ID in `projects/{slug}/notion-log.md`.

Pilot page: **"Hearthlight Pilot: Don't Half Ass It"**
ID `37d4e5bccd028016b374d5afed3a2916`

## 1. Create a Notion integration (gives a token)
1. Go to https://www.notion.so/my-integrations → **New integration**.
2. Name it `Hearthlight`. Associate it with your workspace. Capabilities: **Read + Insert + Update content** (no user info needed).
3. Copy the **Internal Integration Secret** (starts `ntn_` or `secret_`).

## 2. Share the pilot page with the integration
Notion integrations only see pages explicitly shared with them.
- Open the pilot page → top-right **•••** → **Connections** (or "Add connections") → pick **Hearthlight**.
- Sharing the project page also shares its child pages — so the activity-log child page (created in step 4) is covered automatically.

## 3. Put the token in the profile .env (never in a skill or config file)
```bash
echo 'NOTION_API_KEY=ntn_paste_your_secret_here' >> ~/.hermes/profiles/hearthlight/.env
```

## 4. Add the Notion MCP server to the hearthlight profile
The official server is `@notionhq/notion-mcp-server` (npm). From WSL:
```bash
hermes -p hearthlight mcp add notion \
  --command npx \
  --args "-y @notionhq/notion-mcp-server" \
  --env "NOTION_TOKEN=${NOTION_API_KEY}"
```
If `hermes mcp add` isn't available on your build, add this block to
`~/.hermes/profiles/hearthlight/config.yaml` by hand instead:
```yaml
mcp_servers:
  notion:
    command: "npx"
    args: ["-y", "@notionhq/notion-mcp-server"]
    env:
      NOTION_TOKEN: "${NOTION_API_KEY}"
    # Start with a safe allowlist — read + create/append, no deletes:
    tools:
      include: [search, fetch, create-pages, update-page, create-comment]
      prompts: false
      resources: false
```
(Exact tool names vary by server version. Verify after loading — see step 5 — and adjust the include list to the real names.)

## 5. Reload and verify
```bash
hearthlight gateway restart      # or /reload-mcp inside a session
```
Then ask the bot: *"which MCP tools are available right now?"* — you should see Notion tools (search/fetch/create/update). If not, check: `.env` token present, page shared with the integration, `npx` available.

## 6. One-time: create the activity-log child page
Tell the bot once:
> "Create a child page under the pilot page (ID 37d4e5bccd028016b374d5afed3a2916) called 'Hearthlight Activity Log', then save its page ID into projects/{slug}/notion-log.md. From now on, append all activity-log entries there."

This keeps the full activity log on its own page so the pilot page stays a clean dashboard. The `hearthlight-notion-log` skill governs how it logs.

## Security & scope notes
- The Notion token lives ONLY in `.env`. Never commit it; `.gitignore` already excludes `.env`.
- Allowlist excludes delete operations on purpose — a logging agent should never delete Notion content.
- This is scoped to pages you share with the integration. It cannot see the rest of your Notion unless you share more.
