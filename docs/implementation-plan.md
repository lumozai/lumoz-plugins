# Implementation status and remaining work

## Architecture

This public repository owns distribution metadata, skills, installation docs,
and builds. The server implementation and PyPI publishing stay in the server
repository. Customers install the public `lumoz-mcp` package, never a private
source checkout.

| Component | Location | Responsibility |
| --- | --- | --- |
| Marketplace | `.claude-plugin/marketplace.json` | Lists two independent plugins |
| Codex marketplace | `.agents/plugins/marketplace.json` | Lists the shared skills plugin only |
| Skills plugin | `plugins/lumoz-skills/` | Canonical `lumoz-evals` skill, no MCP or credentials |
| CLI MCP plugin | `plugins/lumoz-mcp/` | Pinned server through `uvx`; Claude Code key setting |
| Desktop extension | `mcpb/` | MCPB 0.4 managed uv runtime, Python import launcher, sensitive API-key form |
| Versions | `plugin-source/metadata.json` | Three independent distribution versions and a shared server pin |
| Builds | `scripts/build_claude.py`, `scripts/build_mcpb.py` | Generate metadata and package only intended inputs |
| Release workflow | `.github/workflows/release.yml` | Validates component tag, checks PyPI for MCP releases, publishes selected GitHub asset |

Distribution versions and the shared server pin live in `plugin-source/metadata.json`.
The server console entry point is `lumoz_mcp.server:main`, requires Python
3.11+, and speaks stdio. The Desktop launcher calls that same entry point.
The runtime reads `LUMOZ_API_KEY` in `client_id:client_secret` form. A `.env`
file alone does not configure the process.

## Why the packages are separate

Installing a combined skills/MCP plugin in Desktop created an unusable MCP
entry because the required plugin credential prompt was unavailable. The
skills plugin now contains no MCP configuration, credential settings, or
plugin dependencies. Desktop users install it alongside the MCPB. Claude Code
users install the skills and MCP plugins independently. Codex users install
the skills plugin and keep MCP credentials in private user configuration.

Keep the existing `lumoz-evals` skill name for standalone portability. Its
Claude Code command becomes `/lumoz-skills:lumoz-evals`. MCP tools appear under
`lumoz-mcp:lumoz` in Claude Code. No runtime tool names are hardcoded into the
skill. The root repository is no longer an installable plugin.

## Implemented checks

- Independent-version and dependency-pin generation checks.
- Package boundaries, required licenses, credential-file/symlink rejection.
- Tests that server/MCP-plugin updates do not change the skills plugin and
  plugin versions do not change Desktop metadata.
- Strict Claude marketplace/plugin validation and official MCPB validation.
- Portable skills manifest and Codex catalog generated from shared metadata.
- Real Codex CLI integration check: skills installation and discovery through
  the app-server protocol, with private MCP configuration preserved on plugin
  reinstall and removal. The published Claude-format skills plugin was also
  installed and discovered successfully by Codex CLI.
- Release tag-to-component/version validation, selected-asset publication.
- Successful GitHub workflow publication of all three distributions.
- Pre-commit Gitleaks hook, CI history scanning, and repository-wide GitHub
  secret scanning and push protection. See [contributing](contributing.md).
- Earlier Linux MCPB startup test initialized and discovered 27 tools using
  dummy credentials; no authenticated Lumoz tool was called.

The skill content was moved without rewriting its workflow. It adapts eval
suggestions to the user's repository framework and preserves evidence and
provenance. `list_apps` is the preferred first read-only API smoke test.

## Remaining work

1. Test Windows/macOS GUI installation, API-key persistence, restart, and an
   authenticated read. Verify Desktop managed uv support and Cowork separately.
2. Verify customer upgrade behavior for later component releases. GitHub
   release publication alone does not establish a directory listing.
3. Keep the retired combined plugin and duplicate skill out of the server
   repository; the public plugin repository owns these distributions.
4. Submit plugin folders individually and the MCPB through its separate route.
   Arrange Anthropic release-feed registration; see [publishing options](anthropic-publishing-options.md).
5. Prepare official MCP Registry ownership evidence and server metadata. Keep
   server identity publishing under one workflow owner.
6. Verify Codex app skills installation and an authenticated tool call through
   private MCP configuration on Windows/macOS. Skills are tested with the CLI.
7. For cloud chat/Cowork, deploy authenticated hosted MCP. Local stdio cannot
   run in cloud sessions. Hosting requires transport, identity, tenant isolation,
   revocation, monitoring, and separate directory review.

No public listing or hosted endpoint is claimed. Minimum client versions and
platform compatibility must be confirmed through installation tests.
