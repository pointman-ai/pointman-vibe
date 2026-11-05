# Pointman Mistral Vibe client

A client extension for [Mistral Vibe](https://github.com/mistralai/mistral-vibe),
Mistral's coding agent. Repository: `pointman-ai/pointman-vibe`.
Requires Pointman node 0.4.15 or newer, with the `vibe-stream` decoder and the
PyPI installer.

## Connect once

Create an API key at <https://console.mistral.ai/api-keys>, then run `/vibe add`
in Pointman and paste it into the private form. The key is sealed as `vibe.key`
in the vault and covers every agent on the machine. The node opens it for each
run and passes it only as `MISTRAL_API_KEY` in the process environment, never
in command arguments or saved launch metadata.

## Install and home

Pointman installs the `mistral-vibe` package from PyPI when needed.

Each agent gets its own `HOME`, and runs set `VIBE_HOME={home}/.vibe`, so
Vibe's config, agent instructions, sessions and logs stay inside that agent's
home. No existing Vibe login, config or another client's credentials are copied.

## Runs

A wake is one headless run that exits when the turn ends:

```sh
vibe -p <prompt> --output streaming --output-dir <home>/.vibe/run --trust \
  [--resume <session>] [--model <model>] --agent auto-approve [--add-dir <dir>]
```

- The first wake starts a session; later wakes pass its id to `--resume`.
- `--trust` trusts the working folder without a prompt; stdin is closed.
- Behaviours are written to `<home>/.vibe/AGENTS.md`.
- The node merges MCP servers into `<home>/.vibe/config.toml` under
  `mcp_servers`, with automatic updates and update checks turned off.
- Limit errors are spotted by their text (rate limit, too many requests,
  capacity or quota exceeded, usage limit).

## Modes

| Pointman mode | Vibe | What it does |
|---|---|---|
| default | `--agent auto-approve` | Tools, shell and edits run without asking. |
| auto | `--agent auto-approve` | The same: a headless run can't stop to ask. |

Not supported:

- **plan** and **acceptEdits**: Vibe has no headless agent that matches either,
  so the extension doesn't offer them.
- **Live calls**: Vibe runs one text turn per wake.
- **Posts during a turn**: the prompt is an argument, so posts that arrive
  while a run is going wait for the next wake.

## Stream and checks

`tests/fixtures/native.jsonl` is a real capture of `--output streaming`: a
resumed turn that recalls a word from the previous turn and runs `echo hi`
through Vibe's bash tool. Each line is one JSON entry (`message`, `reasoning` or
`effect`) carrying the run's `sessionId`.

The decoder lives in the Pointman node. CI here checks only the manifest
contract and the fixture's shape, without running Vibe or calling Mistral:

```sh
python3 -m unittest discover -s tests -v
```

## Icon

`icon.png` is Mistral Vibe's own mark; see `ICON-SOURCE.md`.
