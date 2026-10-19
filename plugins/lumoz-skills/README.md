# Lumoz Skills

Create regression evals from Lumoz eval suggestions using your project's test
framework. This plugin includes the `lumoz-evals` skill and has no MCP server,
API-key settings, or automatic dependency on another plugin.

After the repository is published, install from Claude Code:

```text
/plugin install lumoz-skills --marketplace lumozai/lumoz-plugins
```

The marketplace installation ID is `lumoz-skills@lumoz`. In Claude Code the skill
is available as `/lumoz-skills:lumoz-evals`. Desktop users install this plugin
through Customize → Plugins when available through their marketplace/directory.

The workflow needs Lumoz tools: Claude Code users can separately install
`lumoz-mcp@lumoz`; Desktop Chat users install the Lumoz MCPB extension and
configure their API key there. Tool access and authentication are separate from
installing this skill. Cowork tool access needs separate verification.

See the [setup guide](https://github.com/lumozai/lumoz-plugins/blob/main/docs/setup.md)
for installation and updates. Licensed under Apache-2.0; see `LICENSE`.
