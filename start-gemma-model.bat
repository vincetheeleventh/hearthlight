@echo off
REM ── Start the local llama.cpp server for the gemma profile (native Windows, 3090) ──
REM Serves an OpenAI-compatible endpoint at http://127.0.0.1:8081/v1 — exactly what
REM gemma's config dials. NOTE: llama-server serves whatever MODEL you load and ignores
REM the model NAME in the request, so the config's model string need not match this file.
REM Leave this window OPEN while using gemma; close to stop.
REM
set LLAMA=C:\llama.cpp\llama-server.exe

REM ── Model selection ── to switch models, comment out the active line (add REM in
REM front) and uncomment the one you want. Only ONE MODEL line may be active.
set MODELS=C:\Users\vxi\Documents\AI models

REM  [ACTIVE] Qwen3.6-35B-A3B, higher-quality quant — the current gemma-profile model.
set MODEL=%MODELS%\lmstudio-community\qwen3.6_q4_xl\Qwen3.6-35B-A3B-UD-Q4_K_XL.gguf
REM  Qwen3.6-35B-A3B, smaller/faster quant (use if Q4_K_XL is tight on VRAM):
REM set MODEL=%MODELS%\lmstudio-community\qwen3.6_q4_xs\Qwen3.6-35B-A3B-UD-IQ4_XS.gguf
REM  gemma-4-26B-A4B — the profile's original model. Copy it from WSL first (see
REM  LLAMACPP-WINDOWS.md Step 1b), then swap to this line:
REM set MODEL=%MODELS%\gemma-4-26B-A4B-it-UD-Q5_K_M.gguf
REM  supergemma4-26b (uncensored fast v2) — another gemma-family option already on disk:
REM set MODEL=%MODELS%\lmstudio-community\supergemma-26b\supergemma4-26b-uncensored-fast-v2-Q4_K_M.gguf

REM Args: full GPU offload to the 3090.
REM  -ngl 99   = offload all layers to GPU (24GB). Qwen3.6-35B-A3B is MoE (~3B active);
REM              weights at Q4_K_XL are ~20GB, so context KV cache is the tight bit.
REM  -c 32768  = safe context on 24GB with -ngl 99. If VRAM allows, raise toward 65536
REM              (config's max); if it OOMs on load, LOWER -c first, then -ngl.
REM  --host/--port must stay 127.0.0.1:8081 (that's the base_url gemma dials)
if not exist "%LLAMA%" (
  echo ERROR: llama-server.exe not found at %LLAMA%
  echo Edit this .bat and set LLAMA to the real path. See LLAMACPP-WINDOWS.md.
  pause & exit /b 1
)
if not exist "%MODEL%" (
  echo ERROR: model not found at %MODEL%
  echo Copy the .gguf to Windows first ^(it's currently inside WSL^). See LLAMACPP-WINDOWS.md.
  pause & exit /b 1
)

echo Starting llama.cpp server for gemma on 127.0.0.1:8081 ...
echo Leave this window open. Close it to stop the model server.
echo.
"%LLAMA%" -m "%MODEL%" --host 127.0.0.1 --port 8081 -ngl 99 -c 32768 --parallel 1

echo.
echo Model server stopped. Press any key to close.
pause >nul
