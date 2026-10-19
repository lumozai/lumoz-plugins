# Publishing Lumoz MCP tools and skills for Claude

Research notes: October 19, 2026. No directory submission or release-feed
registration has been completed. See [publishing.md](publishing.md) for the
longer publishing guide.

## Intended packages

| Package | Purpose | Users |
| --- | --- | --- |
| `lumoz-skills` plugin | Skills only; no MCP connection or credentials | Desktop Chat, Cowork, Claude Code |
| `lumoz-mcp` plugin | Starts the pinned PyPI server through `uvx` | Claude Code |
| `lumoz.mcpb` extension | Desktop MCP tools with a sensitive API-key settings form | Desktop Chat; Cowork requires separate verification |

The two plugins are implemented under `plugins/`; the repository root is only
a marketplace. Installing the skills plugin creates no MCP entry and requests
no credentials. Both MCP packages use the same server implementation on PyPI.

## Distribution options and complexity

| Route | Publishing and updates | Main limitation |
| --- | --- | --- |
| Our GitHub-backed plugin marketplace | Publish repository; users add marketplace and install plugins. Claude Code supports auto-update when enabled. | Third-party CLI marketplace auto-update is off by default; app discovery/distribution is separate. |
| Anthropic plugin directory | Submit GitHub plugin folder through [developer portal](https://claude.ai/directory/manage); validation, review, then publication. Later commits can be detected through scheduled checks/webhook. | Repository must be public before listing goes live; publishing depends on review/auto-publish settings. |
| Desktop extension directory | Initial MCPB submission through the [extension form](https://clau.de/desktop-extention-submission); directory extensions support automatic updates. | Need to arrange/confirm how Anthropic ingests subsequent releases. Separate from plugin submission. |
| Custom Team/Enterprise extension | Owner uploads MCPB under organization Connectors → Desktop and adds it to the team. Use “Upload new version” for updates. | Organization-scoped distribution; owner still uploads each release. |
| Manual MCPB installation | User installs the file through Settings → Extensions → Advanced settings. | Suitable for trials; no automatic discovery of GitHub releases. |
| Hosted MCP connector | Deploy authenticated remote MCP and submit as a connector separately; plugin supplies skills. | Adds hosting, authentication, and operational work; server updates are deployed centrally. |

Plugin publishing details: [submission and subsequent releases](https://claude.com/docs/plugins/submit).
Extension behavior: [installation and updates](https://support.claude.com/en/articles/10949351-getting-started-with-local-mcp-servers-on-claude-desktop).
Team workflow: [custom extension updates](https://support.claude.com/en/articles/12592343-enabling-and-using-the-desktop-extension-allowlist).

## What we learned about automatic MCPB ingestion

Desktop Commander's [maintainer release guide](https://github.com/wonderwhy-er/DesktopCommanderMCP/blob/main/PUBLISH.md#one-time-setup-repository-admin)
reports one-time registration with an Anthropic contact of the repository,
release-tag pattern, MCPB asset pattern, and maintainer contact. Their guide
says later GitHub release bundles are ingested automatically, with validation
taking a few days. Their [release workflow](https://github.com/wonderwhy-er/DesktopCommanderMCP/blob/main/.github/workflows/release.yml)
attaches the MCPB to GitHub releases.

This is maintainer evidence, not a guarantee for every new submitter. During
Lumoz's initial submission, explicitly request this arrangement for repository
`lumozai/lumoz-plugins`, tags `lumoz-desktop-v*`, and asset `lumoz.mcpb`. Do not assume that
publishing a GitHub release alone registers an update feed.

## Versioning and remaining work

- Keep manifest `name` stable and increase `version` for each release. A stable
  filename (`lumoz.mcpb`) works; versioned filenames also work. MotherDuck and
  Apify use stable names; Desktop Commander uses versioned names.
- All three distribution versions start at `0.1.0` and are independent; the
  shared server pin is `lumoz-mcp==0.4.3`. A PyPI release alone does not update
  installed integrations. Bump the affected distribution versions and server pin.
- Builds now emit `dist/lumoz.mcpb` and one ZIP per plugin. Component tags trigger
  GitHub release publishing after validation; this does not register an Anthropic
  feed. See [release instructions](releases.md) for tags and version ownership.
- Windows installation and authenticated calls still need testing. Submit each
  plugin folder and the Desktop extension through their separate routes. Keep
  customer skills distributed through the plugin, not manual ZIPs.
- Avoid duplicate MCP registrations within a client. Local stdio servers cannot
  run in cloud Cowork sessions; do not promise cross-surface tool availability.
- Publishing to PyPI or the official MCP Registry does not itself create an
  Anthropic directory listing.
