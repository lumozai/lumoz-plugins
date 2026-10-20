# Lumoz Skills

Create regression evals from Lumoz eval suggestions using your project's test
framework. This plugin includes the `lumoz-evals` skill and has no MCP server,
API-key settings, or automatic dependency on another plugin.

For Claude Code, run inside the client:

```text
/plugin marketplace add lumozai/lumoz-plugins
/plugin install lumoz-skills@lumoz
```

The marketplace installation ID is `lumoz-skills@lumoz`. In Claude Code the skill
is available as `/lumoz-skills:lumoz-evals`. Desktop users install this plugin
through **Customize → Plugins → Add → Add marketplace**, using repository
`lumozai/lumoz-plugins`, then choosing **Lumoz Skills**.

For Codex CLI or app, run in your terminal:

```sh
codex plugin marketplace add lumozai/lumoz-plugins
codex plugin add lumoz-skills@lumoz
```

Start a new session and ask Codex to use `lumoz-evals`. The portable and Claude
manifests share one version and the same skill files. Marketplace installation
does not require a public directory listing.

In the ChatGPT desktop app, restart the app, open the Plugins Directory in
Work or Codex, select the Lumoz marketplace, and install **Lumoz Skills** if
needed. Start a new conversation and ask it to use `lumoz-evals`. This is the
[documented local-marketplace route](https://developers.openai.com/plugins/build/plugins#add-a-marketplace-from-the-cli);
GUI installation has not yet been tested. Installing a local plugin does not
publish it to the universal directory or configure Lumoz tools in cloud Chat.

The workflow needs Lumoz tools: Claude Code users can separately install
`lumoz-mcp@lumoz`; Desktop Chat users install the Lumoz MCPB extension and
configure their API key there. Codex users keep their Lumoz MCP command and API
key in private `~/.codex/config.toml`. Tool access and authentication are separate from
installing this skill. Cowork tool access needs separate verification.

See the [setup guide](https://github.com/lumozai/lumoz-plugins/blob/main/docs/setup.md)
for installation and updates. Licensed under Apache-2.0; see `LICENSE`.
