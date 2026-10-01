#!/usr/bin/env python3
"""
LLM 議會腳本 — 把同一份 brief 並行發給 ChatGPT(codex)、Gemini(agy)、Grok(grok),
收回三份意見,輸出 JSON 給主席(Claude)合成。

用法:
  python3 council.py "<brief 文字>"
  python3 council.py --brief-file /path/to/brief.md
  python3 council.py --only chatgpt,grok "<brief>"   # 只問部分議員
  python3 council.py --timeout 300 "<brief>"          # 自訂單家逾時秒數(預設 240)

設計原則:
  - 全部走「訂閱登入的 CLI」,零 API key、零額外計費。
  - 一家掛掉/逾時不影響其他家,結果照出,錯誤如實記錄。
  - 在空的「議事廳」目錄執行,避免 coding-agent 型 CLI 亂讀工作區檔案。
"""

import argparse
import concurrent.futures
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time

# 各議員的 CLI 呼叫方式(prompt 由 build_cmd 塞入)
# 三席全部明寫鎖定「該家訂閱可用的最強配置」(2026-07 實測可用):
#   ChatGPT = gpt-5.5 + xhigh 推理;Gemini = 3.1 Pro (High);Grok = grok-4.5 + high 推理。
# 若某家改版導致模型名失效,錯誤會如實出現在 JSON 的 error 欄,屆時再更新這裡。
MEMBERS = {
    "chatgpt": {
        "bin": "codex",
        "cmd": lambda p: ["codex", "exec", "--skip-git-repo-check",
                          "-m", "gpt-5.5", "-c", 'model_reasoning_effort="xhigh"', p],
        "label": "ChatGPT gpt-5.5 xhigh (codex CLI)",
    },
    "gemini": {
        "bin": "agy",
        "cmd": lambda p: ["agy", "--model", "Gemini 3.1 Pro (High)", "-p", p],
        "label": "Gemini 3.1 Pro High (Antigravity CLI)",
    },
    "grok": {
        "bin": "grok",
        "cmd": lambda p: ["grok", "-m", "grok-4.5", "--reasoning-effort", "high", "-p", p],
        "label": "Grok 4.5 high (Grok Build CLI)",
    },
}


def query_member(name: str, prompt: str, timeout: int, workdir: str) -> dict:
    member = MEMBERS[name]
    result = {"member": name, "label": member["label"], "ok": False,
              "response": None, "error": None, "elapsed_s": None}

    if shutil.which(member["bin"]) is None:
        result["error"] = f"{member['bin']} 未安裝或不在 PATH"
        return result

    start = time.time()
    try:
        proc = subprocess.run(
            member["cmd"](prompt),
            capture_output=True, text=True,
            timeout=timeout, cwd=workdir,
        )
        result["elapsed_s"] = round(time.time() - start, 1)
        out = (proc.stdout or "").strip()
        err = (proc.stderr or "").strip()
        if proc.returncode == 0 and out:
            result["ok"] = True
            result["response"] = out
        else:
            result["error"] = f"exit={proc.returncode}; stderr: {err[:500] or '(空)'}; stdout: {out[:200] or '(空)'}"
    except subprocess.TimeoutExpired:
        result["elapsed_s"] = round(time.time() - start, 1)
        result["error"] = f"逾時(>{timeout}s)"
    except Exception as e:  # noqa: BLE001
        result["elapsed_s"] = round(time.time() - start, 1)
        result["error"] = f"exception: {e}"
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="LLM 議會:並行諮詢 ChatGPT / Gemini / Grok")
    parser.add_argument("brief", nargs="?", help="brief 文字")
    parser.add_argument("--brief-file", help="從檔案讀 brief")
    parser.add_argument("--only", help="逗號分隔,只問這些議員(chatgpt,gemini,grok)")
    parser.add_argument("--timeout", type=int, default=360, help="單家逾時秒數(預設 360;xhigh 推理在長題會想比較久)")
    args = parser.parse_args()

    if args.brief_file:
        with open(args.brief_file, "r", encoding="utf-8") as f:
            brief = f.read().strip()
    elif args.brief:
        brief = args.brief.strip()
    else:
        parser.error("請提供 brief 文字或 --brief-file")

    names = list(MEMBERS)
    if args.only:
        names = [n.strip() for n in args.only.split(",") if n.strip() in MEMBERS]
        if not names:
            parser.error("--only 沒有匹配到任何議員(可用:chatgpt,gemini,grok)")

    # 空的議事廳目錄:避免 coding-agent CLI 掃使用者的工作區
    chamber = tempfile.mkdtemp(prefix="llm-council-")
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(names)) as pool:
            futures = {pool.submit(query_member, n, brief, args.timeout, chamber): n for n in names}
            results = {futures[f]: f.result() for f in concurrent.futures.as_completed(futures)}
    finally:
        shutil.rmtree(chamber, ignore_errors=True)

    output = {
        "brief_chars": len(brief),
        "members_queried": names,
        "results": [results[n] for n in names],
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))

    # 全滅才回非零
    if not any(r["ok"] for r in output["results"]):
        sys.exit(1)


if __name__ == "__main__":
    main()
