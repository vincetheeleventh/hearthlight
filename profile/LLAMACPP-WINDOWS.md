# Native llama.cpp on Windows (3090) + retiring WSL Hermes

Goal: run the gemma local model natively on Windows so gemma stops failing "provider
authentication failed," THEN shut down the now-redundant WSL Hermes.

**Order is critical.** The model file lives inside WSL. Shut WSL down before copying it
and you lose access to it. So: copy model → set up llama.cpp → verify → THEN stop WSL.

---

## Step 1 — Copy the model to Windows (WSL must still be running)
The GGUF is at `\\wsl.localhost\ubuntu\home\vxi\models\gemma-4-26B-A4B-it-UD-Q5_K_M.gguf`
(~18 GB). Copy it to a Windows folder so native llama.cpp can reach it after WSL is off.

Vince's Windows models folder: **`C:\Users\vxi\Documents\AI models\`**
```powershell
copy "\\wsl.localhost\ubuntu\home\vxi\models\gemma-4-26B-A4B-it-UD-Q5_K_M.gguf" "C:\Users\vxi\Documents\AI models\"
```
(Ensure C: has ~20 GB free. This takes a few minutes. If the .gguf is already there, skip.)

## Step 2 — Get the llama.cpp CUDA build for Windows
Prebuilt, no compiling. From the llama.cpp releases page (github.com/ggml-org/llama.cpp/releases):
1. Download the **CUDA** Windows asset — named like `llama-b####-bin-win-cuda-x64.zip`
   (pick the CUDA build, not the CPU/Vulkan one — you have a 3090).
2. It may also list a **cudart** zip (`cudart-llama-bin-win-cuda-*.zip`) — download that too;
   it has the CUDA runtime DLLs llama-server needs.
3. Extract BOTH zips into the same folder: `C:\llama.cpp\`
   (so `C:\llama.cpp\llama-server.exe` and the `.dll`s sit together.)

Your NVIDIA driver already includes CUDA support for the 3090, so no separate CUDA install.

## Step 3 — Start the model server (double-click)
`start-gemma-model.bat` (in Story Studio). It runs:
```
llama-server.exe -m C:\models\...gemma....gguf --host 127.0.0.1 --port 8081 -ngl 99 -c 65536 --parallel 1
```
- Edit the two paths at the top of the .bat if you used different folders.
- `-ngl 99` offloads all layers to the 3090; `-c 65536` matches gemma's context.
- Leave the window open while using gemma. First load takes ~10-30s (loading 18 GB into VRAM).

## Step 4 — Verify BEFORE shutting down WSL
```powershell
curl http://127.0.0.1:8081/v1/models
```
Returns JSON with the model → server is up. Then message the **gemma** Telegram bot — the
"provider authentication failed" should be gone. (gemma's config already points at
127.0.0.1:8081, so nothing to change — the server just needs to be running.)

---

## Step 5 — ONLY NOW: shut down the WSL side of Hermes
The model is safe on Windows and native Hermes runs. Retire WSL's Hermes gateways.

In a **WSL terminal**:
```bash
# stop every hermes gateway service (all profiles)
systemctl --user stop 'hermes-gateway-*' 2>/dev/null

# disable them so they don't auto-start on WSL boot
systemctl --user disable 'hermes-gateway-*' 2>/dev/null

# confirm none are running
systemctl --user list-units 'hermes-gateway-*'
```
If a profile was installed as a service under a specific name, also:
`hermes -p <profile> gateway stop` for each (hearthlight, gemma, faithreview, architect, hermeslite).

**Do NOT delete the WSL Hermes data or uninstall WSL itself** — you may still have other
things in WSL (projects, the models folder). This only stops the redundant gateways. If you
later want the WSL Hermes data gone entirely, that's a separate, deliberate cleanup — back up first.

## What "done" looks like
- Native Windows: hearthlight gateway (Claude/OpenRouter) + gemma model server (3090) both running.
- WSL: Hermes gateways stopped and disabled; nothing auto-starting.
- One machine, one Hermes (native), your GPU serving gemma locally.
