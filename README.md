# llm-council

A [Claude Code](https://docs.claude.com/en/docs/claude-code) skill that asks ChatGPT, Gemini and Grok the same question in parallel, then has Claude chair the answers into one decision. Claude marks where the models agree, what only one of them saw, and where they disagree.

It uses the CLIs you're already signed in to through your subscriptions (`codex`, `agy`, `grok`). It needs no API keys and adds no per-call billing.

[中文說明在下面](#中文說明)

## How it works

1. Claude writes a self-contained brief. The other models can't read your files, so the brief carries the context.
2. `scripts/council.py` sends the brief to all three CLIs at once, each in an empty temp directory so the coding agents can't read your workspace. It returns JSON with each member's answer, error and time taken. If one model fails, the others still report.
3. Claude writes the decision: where the models agree, a ranked list with sources, ideas only one model had, disagreements with a ruling, and who didn't answer.

The skill includes a privacy gate. A brief that mentions clients, unpublished numbers or trade secrets is shown to you or anonymized before it leaves the machine.

## Install

```bash
git clone https://github.com/Max-aiutopia/llm-council ~/.claude/skills/llm-council
```

Then sign in to each CLI yourself: `codex login`, run `agy` once, `grok login`. In Claude Code, say "開議會" or "consult the council".

You can also run the script on its own:

```bash
python3 scripts/council.py "Should we price the course monthly or one-off?"
python3 scripts/council.py --only chatgpt,grok --timeout 300 --brief-file brief.md
```

Model names are pinned in `MEMBERS` at the top of `scripts/council.py`. Update them when a vendor renames a model.

## 中文說明

Claude Code 的 skill：同一題同時問 ChatGPT、Gemini、Grok，再由 Claude 當主席合成決議，標出共識、各家獨有的觀點和互相矛盾的地方。走你已登入的訂閱制 CLI，不用 API key。安裝方式見上面的 Install。

## License

MIT
