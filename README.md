# Lumoz plugins

Lumoz skills and MCP integrations, distributed separately so Desktop users can
install skills without enabling an unconfigured MCP server.

| Package | Contents | Client |
| --- | --- | --- |
| `lumoz-skills` | `lumoz-evals` skill; no MCP or credentials | Claude Desktop, Cowork, Claude Code, Codex CLI/app |
| `lumoz-mcp` | Pinned stdio server configuration; no skills | Claude Code |
| `lumoz-setup` | Marketplace, skills, MCP, hidden key prompt, and uninstall | Codex CLI/app, Claude Code |
| `lumoz.mcpb` | Desktop MCP extension with API-key form; no skills | Claude Desktop Chat |

**Preview:** MCP packages use a tested server release from PyPI. See
[release metadata](plugin-source/metadata.json) for distribution versions and
the server pin. No server source checkout is needed. Public listings and
Windows/macOS GUI verification are pending. Codex skills installation and MCP
setup are tested with the CLI; MCP uses private per-user configuration.

## Codex CLI and app

For skills and MCP together, the packaged installer provides:

```sh
uvx lumoz-setup codex
```

Requires Codex CLI and uv. The installer is available on
[PyPI](https://pypi.org/project/lumoz-setup/); no repository checkout is needed.

Setup adds the marketplace, installs the skills plugin, and saves the pinned
MCP connection and API key in private Codex `config.toml`. Input is hidden;
the saved key is plaintext. No environment export is required. Rerunning setup
keeps installed plugins and replaces the entire Lumoz MCP entry and key.
Restart Codex and check `/mcp`.

Uninstall skills, MCP, and the unused marketplace with:

```sh
uvx lumoz-setup codex uninstall
```

To remove only MCP and its saved key without the installer, run
`codex mcp remove lumoz`. Full uninstall preserves unrelated integrations;
package caches and API keys in your Lumoz account remain.
See the [setup guide](docs/setup.md#3-codex-cli-and-codex-app-today).

### Manual alternative: skills only

For skills without an MCP connection, run:

```sh
codex plugin marketplace add lumozai/lumoz-plugins
codex plugin add lumoz-skills@lumoz
```

Start a new session and ask Codex to use `lumoz-evals`. This is the same skills
plugin and skill content used by Claude; no API key or Python runtime is needed
to install the skill. No OpenAI directory approval is required for this route.

In the ChatGPT desktop app, restart the app, open the Plugins Directory in
Work or Codex, select the Lumoz marketplace, and install **Lumoz Skills** if
needed. Start a new conversation and ask it to use `lumoz-evals`. This is the
[documented local-marketplace route](https://developers.openai.com/plugins/build/plugins#add-a-marketplace-from-the-cli);
GUI installation has not yet been tested. Installing a local plugin does not
publish it to the universal directory or configure Lumoz tools in cloud Chat.

## Claude Code

The packaged installer uses the same hidden key prompt and also registers
both plugins:

```sh
uvx lumoz-setup claude-code
# Remove both plugins, their user-scope configuration, and unused marketplace:
uvx lumoz-setup claude-code uninstall
```

Requires uv and Claude Code with
`plugin configure --values-stdin` support (2.1.285+). Credentials are saved by
Claude's supported plugin configuration command. Other installation scopes
are preserved, and Claude retains credentials if another scope still uses
that plugin.

The existing manual route remains available. Run inside Claude Code:

```text
/plugin marketplace add lumozai/lumoz-plugins
/plugin install lumoz-skills@lumoz
/plugin install lumoz-mcp@lumoz
/plugin configure lumoz-mcp@lumoz
```

Enter the full Lumoz API key (`client_id:client_secret`). Install
[uv](https://docs.astral.sh/uv/getting-started/installation/) and Python 3.11+
first. Set the plugin's **uvx executable** to its absolute path if needed.
Restart the session and check `/mcp`: the connection is `lumoz-mcp:lumoz`.
The skill is `/lumoz-skills:lumoz-evals`.

To try a checkout, run `claude plugin marketplace add .` from its root, then
`claude plugin install lumoz-skills@lumoz` and
`claude plugin install lumoz-mcp@lumoz`. Configure the key in Claude Code.
Enable marketplace auto-update under **/plugin → Marketplaces → lumoz**;
third-party marketplace auto-update is off by default.

## Claude Desktop

1. Open **Customize → Plugins → Add → Add marketplace**. Choose
   **Add from a repository**, enter `lumozai/lumoz-plugins`, then install
   **Lumoz Skills** (`lumoz-skills`). Do not install the CLI MCP plugin here.
2. For MCP tools, [download `lumoz.mcpb`](https://github.com/lumozai/lumoz-plugins/releases/latest/download/lumoz.mcpb), then open
   **Settings → Extensions → Advanced settings → Install Extension…** and
   select the downloaded file.
3. Enter the full API key in the extension form and start a new Chat. Ask:
   **Use Lumoz to list the apps and environments I can access.**

```sh
# Optional: build the extension from a source checkout
python3 scripts/build_mcpb.py
```

This unsigned trial requires Desktop support for MCPB 0.4 and its managed `uv`
runtime. First launch downloads Python/dependencies as needed. Remove any
previous manual Lumoz entry from `claude_desktop_config.json` to avoid duplicate
tools; preserve other servers. The extension and skills plugin configure
independently. Cowork tool access requires separate verification; local stdio
servers cannot run in cloud sessions.

These installation routes do not require an Anthropic directory listing.
Plugins require a paid Claude plan, and organization policies can restrict
marketplaces and extensions. See [Claude's plugin instructions](https://support.claude.com/en/articles/13837440-use-plugins-in-claude).

Directory-installed extensions support automatic updates. Manually installed
files need updating manually. Anthropic release-feed registration is pending;
a GitHub release alone does not establish it. See the
[publishing options](docs/anthropic-publishing-options.md).

## Upgrading from the combined plugin

Uninstall `lumoz@lumoz` in each client where it was installed. In Claude Code,
refresh the marketplace with `/plugin marketplace update lumoz`, then install
the two plugins above and configure the MCP key again. If marketplace `lumoz`
still points to the old server repository or a different checkout, remove that
marketplace and add `lumozai/lumoz-plugins` instead. Desktop users replace the
old plugin with **Lumoz Skills** plus the MCPB. Credentials do not migrate
automatically between these packages.

## Build and release

Contributors should [enable the pre-commit secret scanner](docs/contributing.md)
before making commits. GitHub push protection and CI secret scanning provide
additional checks on every branch.

The repository root is a marketplace, not an installable plugin:

```text
.claude-plugin/marketplace.json
.agents/plugins/marketplace.json
plugins/lumoz-skills/    # Self-contained skills plugin
plugins/lumoz-mcp/       # Self-contained Claude Code MCP plugin
mcpb/                   # Desktop manifest, dependency declaration, launcher
plugin-source/metadata.json
installer/             # Customer CLI package
scripts/               # Maintainer build/release tools; legacy setup shim
docs/
```

```sh
python3 scripts/build_claude.py --zip
python3 scripts/build_mcpb.py
python3 scripts/build_claude.py --check
python3 scripts/build_mcpb.py --check
python3 scripts/build_installer.py --check
python3 -m pip install jsonschema==4.25.1
python3 scripts/validate_portable.py
python3 -m unittest discover -s tests -v
claude plugin validate . --strict
claude plugin validate plugins/lumoz-skills --strict
claude plugin validate plugins/lumoz-mcp --strict
npx --yes @anthropic-ai/mcpb@2.1.2 validate mcpb/manifest.json
```

Outputs: a versioned ZIP for each plugin and `dist/lumoz.mcpb`.
ZIP filenames use the corresponding version from `plugin-source/metadata.json`.
The skills ZIP includes portable and Claude manifests, a short README,
the license, and skill files. The Claude MCP ZIP includes its Claude manifest,
server configuration, README, and license. The MCPB contains its manifest,
`pyproject.toml`, launcher, and license. Optional `NOTICE` is also included.
The root license is copied into each plugin by the generator; check these
copies in with generated manifests. Documentation and build tooling stay out
of all three packages.

`scripts/build_claude.py` generates both portable and Claude metadata. Portable
skills use root `plugin.json`; Claude uses `.claude-plugin/plugin.json` in the
same skills folder. The MCP plugin retains its Claude-only configuration.
Install Codex CLI to run the integration test; CI uses the tested version
recorded in its workflow. The test installs into a temporary profile and checks
actual skill discovery and preservation of private MCP configuration using
dummy credentials.

Each distribution has its own version in
[plugin-source/metadata.json](plugin-source/metadata.json), separate from the
server pin. A skills release does not change either MCP distribution. A PyPI
release does not update any installed pin. The MCPB pins the top-level server;
uv resolves its transitive dependencies at installation.

The release workflow validates packages and publishes one selected GitHub
Release asset when its component tag is pushed. Desktop releases are marked
Latest so the stable Desktop download remains available. No release is
published by ordinary commits. See [release instructions](docs/releases.md)
for exact version changes, tags, and publishing boundaries.

The customer installer is an independent Python package in `installer/`.
Build its wheel and sdist with `uv build installer --out-dir dist/installer`
and validate with `python3 scripts/check_installer.py`. Its
`lumoz-setup-v<version>` tag runs a separate PyPI publishing workflow after
the trusted publisher is configured. See the installer section of the release
guide before making customer download commands available.

## Documentation

- [Setup and troubleshooting](docs/setup.md)
- [Release instructions](docs/releases.md)
- [Contributing and secret checks](docs/contributing.md)
- [Anthropic publishing options and complexity](docs/anthropic-publishing-options.md)
- [Registry and directory publishing](docs/publishing.md)
- [Implementation status](docs/implementation-plan.md)
- [Lumoz evals skill](plugins/lumoz-skills/skills/lumoz-evals/SKILL.md)

For help, open a [GitHub issue](https://github.com/lumozai/lumoz-plugins/issues)
or contact [Lumoz support](mailto:support@lumoz.ai). Keep keys and private trace
data out of public issues. Licensed under Apache-2.0; see [LICENSE](LICENSE).
