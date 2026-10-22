# Lumoz setup

Install Lumoz skills and MCP tools in Codex or Claude Code without manually
cloning a repository. Requires uv (`uvx`) and the chosen client's CLI.

Install and configure either client:

```sh
uvx lumoz-setup codex
uvx lumoz-setup claude-code
```

Run one command for each client you use. Setup prompts for the full
`client_id:client_secret` API key with hidden input. No shell export is needed.
Run directly in a terminal; do not pipe the key into the command.

Codex setup adds the Lumoz marketplace, installs `lumoz-skills@lumoz`, and
registers the pinned MCP server with its API key in private `config.toml`.
Codex stores the key as plaintext. Rerunning setup replaces the full `lumoz`
MCP entry, including custom settings.

Claude Code setup adds the marketplace, installs `lumoz-skills@lumoz` and
`lumoz-mcp@lumoz` at user scope, then saves the key and absolute uvx path
through `claude plugin configure --values-stdin`. Claude Code 2.1.285+ is
required for that command. Existing installed plugins are kept and disabled
ones are enabled. An existing marketplace named `lumoz` keeps its source;
remove it first if it points to an outdated repository.

Restart the client, open `/mcp`, then ask:

> Use Lumoz to list the apps and environments I can access. Do not modify anything.

Ask for `lumoz-evals` to use the skill. Registration does not verify API access;
a successful tool call does. The first MCP connection downloads its server
through uvx if needed. Local stdio tools do not configure cloud Chat sessions.

## Uninstall

```sh
uvx lumoz-setup codex uninstall
uvx lumoz-setup claude-code uninstall
```

Uninstall removes the target client's Lumoz tools and skills, then removes the
Lumoz marketplace if no remaining plugins need it. Other integrations remain.
Codex removes the key with the MCP entry. Claude manages plugin settings and
secret deletion; credentials stay if the plugin remains installed in another
scope. Claude uninstall changes user scope only.

Restart active sessions to disconnect their running server. Uninstall does
not revoke API keys in Lumoz or erase package caches or credential copies
saved elsewhere. Codex MCP alone can also be removed with
`codex mcp remove lumoz` without uv or the installer.

## Development and release

Runtime code lives in `installer/src/lumoz_setup/`; maintainer tooling lives
in `scripts/`. Runtime defaults and the license are packaged with the wheel;
no checkout files are read by the installed CLI.

Before the first PyPI release, test from the repository root with:

```sh
uvx --from ./installer lumoz-setup --help
uvx --from ./installer lumoz-setup codex
```

See [release instructions](https://github.com/lumozai/lumoz-plugins/blob/main/docs/releases.md)
for package builds, versioning, and PyPI trusted-publisher configuration.
