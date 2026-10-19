# Setup guide

Sections 1–4 configure MCP tools. Section 5 installs the separate Claude skills
and CLI MCP plugins. Codex plugin packaging and the
hosted endpoint in section 6 are still planned.

## 1. Prerequisites

1. Obtain a Lumoz API key from [Lumoz Console](https://console.lumoz.ai),
   **Settings → API Keys → Create Key**. An organization admin may need to
   create it. Preserve the full `client_id:client_secret` value.
2. Install [uv](https://docs.astral.sh/uv/getting-started/installation/), which
   supplies `uvx`, and make Python 3.11+ available. `uv python install 3.11`
   provides a managed Python if needed. This step is for CLI/manual setup;
   the MCPB route in section 4 uses Desktop's managed runtime.
3. Install/update the client you intend to use. Allow downloads from PyPI and
   access to the Lumoz API from the machine running the server.

Install the server from PyPI. No GitHub credentials or server source checkout
are needed.

Check the runtime:

```sh
uv --version
uvx --version
uvx --from lumoz-mcp python -c "from importlib.metadata import version; print(version('lumoz-mcp'))"
```

The last command downloads/caches dependencies and prints the installed
server version. It checks package availability, not authentication or a
working MCP connection. Manual examples below use the unpinned PyPI package;
plugin and extension builds keep their tested pin in
[release metadata](../plugin-source/metadata.json).

Use the production API default unless Lumoz has given you a different API
root. `LUMOZ_API_URL` names the REST API, not a hosted MCP endpoint. Do not put
an app ID or environment in the API URL.

## 2. Claude Code CLI today

For Bash, read the key without saving the literal value in shell history:

```bash
read -rsp 'Lumoz API key: ' LUMOZ_API_KEY
printf '\n'
export LUMOZ_API_KEY
claude mcp add --transport stdio --scope user lumoz -- uvx lumoz-mcp
claude
```

In Claude Code, open `/mcp`, check the `lumoz` connection, then ask:

> Use Lumoz to list all apps and environments I can access. Do not modify anything.

Keep launching Claude from an environment containing the key. The registration
above saves the command, not the exported key. A new terminal needs the key
again, or a suitable local secret-manager integration. A `.env` file by itself
does not configure this server.

User scope makes the command available across projects on this machine.
Use project scope only when intentionally sharing command configuration, and
never commit a real key. See
[Claude's MCP documentation](https://code.claude.com/docs/en/mcp) for host configuration.

## 3. Codex CLI and Codex app today

In your private `~/.codex/config.toml`, merge this table with existing settings:

```toml
[mcp_servers.lumoz]
command = "uvx"
args = ["lumoz-mcp"]
env_vars = ["LUMOZ_API_KEY"]
startup_timeout_sec = 60
```

For the CLI, read/export the key as in section 2, then run:

```sh
codex mcp list
codex
```

Open `/mcp` and run the same app-discovery prompt. `codex mcp list` confirms
registration; a successful tool call confirms API access.

For the app, open MCP server settings, add a stdio server with the same command
and arguments, and restart the connection. Local Codex clients on the same host
share configuration. A GUI launched from the operating system may not inherit
your terminal's exported variables or PATH.

If the app cannot inherit the key, use its supported credential/environment
configuration. A manual fallback is a private per-user TOML entry:

```toml
[mcp_servers.lumoz.env]
LUMOZ_API_KEY = "REPLACE_WITH_CLIENT_ID:CLIENT_SECRET"
```

In that fallback, remove `LUMOZ_API_KEY` from `env_vars` to avoid conflicting
sources. The key is stored as plaintext in the configuration: keep the file
private, outside source control. On macOS/Linux, `chmod 600 ~/.codex/config.toml`
restricts file permissions. Use your OS's file permissions on Windows.

If needed, replace `command = "uvx"` with the absolute executable path returned
by `command -v uvx` on macOS/Linux or `where.exe uvx` on Windows.
This config applies to local execution; it does not register a browser-chat
connector. [OpenAI MCP configuration](https://developers.openai.com/codex/mcp).

## 4. Claude Desktop Chat today

Open **Settings → Developer → Edit Config**. Merge the following into
`claude_desktop_config.json`; preserve other servers:

```json
{
  "mcpServers": {
    "lumoz": {
      "command": "uvx",
      "args": ["lumoz-mcp"],
      "env": {
        "LUMOZ_API_KEY": "REPLACE_WITH_CLIENT_ID:CLIENT_SECRET"
      }
    }
  }
}
```

Use an absolute `uvx` path if necessary. Fully quit and reopen Claude Desktop,
check the tools/connector menu, and run the discovery prompt. This manual
configuration stores the key in a local file; keep it private.

This is the Desktop **Chat** integration. As an alternative to editing JSON,
[download `lumoz.mcpb`](https://github.com/lumozai/lumoz-plugins/releases/latest/download/lumoz.mcpb).
To build from source, use `python3 scripts/build_mcpb.py`. In a current
Claude Desktop with MCPB 0.4/uv support, open **Settings → Extensions → Advanced
settings → Install Extension…**, select that file, and enter the full API key
in the extension form. The sensitive field uses Desktop's OS credential storage.
The managed runtime downloads Python and the pinned PyPI package as needed.
Choose either the extension or the manual entry to avoid duplicate tools.

The MCPB installs tools; the plugin in section 5 supplies the eval skill.
The trial is unsigned. Windows/macOS GUI installation and authenticated API
calls still need verification. Official-directory extensions can auto-update;
manually installed MCPB files need a new installation for each update.
[Claude local MCP and extension guide](https://support.claude.com/en/articles/10949351-getting-started-with-local-mcp-servers-on-claude-desktop).

## 5. Claude plugin installation

The `lumoz` marketplace lists two independently versioned plugins:
`lumoz-skills` supplies the eval skill with no MCP connection or credential
settings; `lumoz-mcp` configures tools for Claude Code with no skills.

### Claude Code

To try a checkout, run from its root:

```sh
claude plugin marketplace add .
claude plugin install lumoz-skills@lumoz
claude plugin install lumoz-mcp@lumoz
claude
```

Install inside Claude Code:

```text
/plugin marketplace add lumozai/lumoz-plugins
/plugin install lumoz-skills@lumoz
/plugin install lumoz-mcp@lumoz
/plugin configure lumoz-mcp@lumoz
```

Enter the full API key in the sensitive setting. If needed, use an absolute
path for the optional `uvx_path` setting. Restart, then check `/mcp` for
`lumoz-mcp:lumoz`. The skill is `/lumoz-skills:lumoz-evals`. Install uv/Python
first as described in section 1. Choose either this MCP plugin or direct MCP
registration; keeping both produces duplicate tools.

Enable marketplace auto-update under **/plugin → Marketplaces → lumoz**.
To uninstall, use `/plugin uninstall lumoz-skills@lumoz` and/or
`/plugin uninstall lumoz-mcp@lumoz`.

### Desktop skills and Cowork

1. Open **Customize → Plugins → Add → Add marketplace**.
2. Choose **Add from a repository** and enter `lumozai/lumoz-plugins`.
3. Install **Lumoz Skills** (`lumoz-skills`) from the added marketplace.

This installs the `lumoz-evals` skill, creates no MCP entry, and needs no API
key. Adding this Git marketplace does not require an Anthropic directory
listing. Plugins require a paid Claude plan. For Desktop Chat tools, install
`lumoz.mcpb` as described in section 4 and enter the key there; custom MCPB
installation also does not require a directory listing. Do not install the
CLI MCP plugin for Desktop Chat.

Cowork tool access still needs verification independently of skills. Local
stdio servers cannot run in cloud Cowork sessions. Organization policies can
restrict plugins and extensions.
[Claude plugin installation](https://support.claude.com/en/articles/13837440-use-plugins-in-claude).

### Migrating from the old combined plugin

Remove `lumoz@lumoz` using each client's plugin manager. Refresh the marketplace
and install the new packages above. If the `lumoz` marketplace points to the
server repository or an old checkout, remove that marketplace and add this
repository instead. Reconfigure credentials in the new MCP plugin/extension;
credentials do not migrate automatically. Remove old direct MCP registrations
in the same client when replacing them.

### Codex

Codex-specific plugin metadata and a catalog are not implemented. Use the
local MCP configuration in section 3; do not install Claude's manifests as
Codex plugins. The skill remains ordinary `SKILL.md` content at
`plugins/lumoz-skills/skills/lumoz-evals/`, ready for future Codex packaging.

## 6. Hosted connection after deployment

**Future setup:** `https://mcp.lumoz.ai/mcp` is the proposed endpoint. Its
availability and OAuth flow have not been verified. Use the actual published
URL once deployment is complete.

For Claude chat, open **Customize → Connectors → Add custom connector**, enter
the published HTTPS MCP URL, and complete Lumoz sign-in and consent. After
directory approval, users should instead find **Lumoz** in the plugin/connector
directory, select **Add/Connect**, and authenticate. Remote connections
originate from Anthropic's cloud, so a server accessible only on localhost or
a private VPN is insufficient.
[Claude remote connection guide](https://support.claude.com/en/articles/11175166-get-started-with-custom-connectors-using-remote-mcp).

The CLIs can use that hosted connection too:

```sh
claude mcp add --transport http --scope user lumoz https://mcp.lumoz.ai/mcp
```

Authenticate through `/mcp` in Claude. For Codex:

```sh
codex mcp add lumoz --url https://mcp.lumoz.ai/mcp
codex mcp login lumoz
```

Remove or disable an existing direct stdio entry first if using the same name.
For approved OpenAI directory distribution, find **Lumoz** in the app's Plugins
directory, install it, and complete the connection prompt. A custom connection
or Git marketplace is useful before public approval; it does not make the
plugin publicly searchable. [OpenAI plugin installation](https://developers.openai.com/codex/plugins).

## 7. First successful workflow

1. Call `list_apps` with `{}`. Choose an actual returned app/environment pair.
2. Ask for recent problems or traces in that app/environment.
3. Inspect a selected problem, its existing RCA, and supporting signal/trace
   evidence. If there is no RCA, distinguish generating one from reading one.
4. For eval work, retrieve the relevant suggestion and adapt it to the user's
   repository or provide a handoff when code execution is unavailable.

Do not use `report_fix` as a connection test: it resolves a problem, and the
current server has no reopen operation. Workflow suggestion discovery can also
generate data; `list_apps` is the preferred initial read-only smoke test.

## 8. Troubleshooting and updates

| Symptom | Action |
| --- | --- |
| `uvx` not found | Use an absolute executable path and restart the GUI client |
| First startup times out | Prewarm the pinned package using section 1; check network access |
| Unsupported Python | Install/select Python 3.11+; check which runtime uv chose |
| Missing/invalid API key | Supply the full colon-separated value in the environment of the actual server process |
| `.env` has no effect | Export variables or configure the host; the server does not automatically load it |
| `environment is required` / app not found | Rediscover with `list_apps`; pass the returned app ID and environment explicitly |
| Tools use `service_id` | An older process/package is loaded; verify the pin and fully restart |
| Duplicate Lumoz tools | Disable one of direct MCP configuration, local plugin, or remote connection |
| Browser cannot connect to stdio | Use a deployed remote connector; local config does not sync a running process |
| Directory search has no Lumoz | Public approval/publication is separate; use manual setup until the listing is live |

For a direct install, uv caches the tool environment. To adopt an update,
run `uvx --upgrade lumoz-mcp` with your API key set, stop that standalone
server, restart the client, and rerun discovery. To control adoption, pin a
chosen version with `uvx --from 'lumoz-mcp==<version>' lumoz-mcp` and change
that pin explicitly when upgrading. Plugin updates carry their tested server
pin and a new distribution version in release metadata. To uninstall direct integrations, use `claude mcp remove lumoz
--scope user` or `codex mcp remove lumoz`; remove Desktop JSON entries through
the configuration editor. Remove installed plugins through each client's
plugin manager, and revoke unused Lumoz keys separately.
