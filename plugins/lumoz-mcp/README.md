# Lumoz MCP for Claude Code

Connect Claude Code to Lumoz traces, signals, problems, root cause analyses,
and eval suggestions. This plugin launches the published `lumoz-mcp` Python
package through `uvx`. It includes no skills or server implementation source.

After the repository is published, install from Claude Code:

```text
/plugin install lumoz-mcp --marketplace lumozai/lumoz-plugins
```

The marketplace installation ID is `lumoz-mcp@lumoz`. Configure your full
`client_id:client_secret` API key with `/plugin configure lumoz-mcp@lumoz`.
Install uv and Python 3.11+ first. If needed, set the uvx executable option to
its absolute path. The server appears as `lumoz-mcp:lumoz` in `/mcp`.

Install `lumoz-skills@lumoz` separately for the eval skill. Desktop Chat users
should use the Lumoz MCPB extension for tools and the skills plugin for skills;
this CLI MCP plugin is not the Desktop credential setup route.

See the [setup guide](https://github.com/lumozai/lumoz-plugins/blob/main/docs/setup.md)
for installation and updates. Licensed under Apache-2.0; see `LICENSE`.
