# Release instructions

The server is released to PyPI from its own repository. This repository
releases distribution packages and the separate `lumoz-setup` installer to
PyPI; it does not publish or copy the Python server.

## Version ownership

Edit `plugin-source/metadata.json`, then regenerate the affected files:

| Metadata | Change when |
| --- | --- |
| `plugins.skills.version` | Skills, their manifest, README, or license change |
| `plugins.mcp.version` | CLI MCP configuration, server pin, README, or license change |
| `desktop.version` | MCPB launcher, manifest, server pin, or license change |
| `mcp.version` | Adopting a tested PyPI server release |

Names are installation identities: keep them stable. The MCPB filename stays
`lumoz.mcpb`; its internal version and containing release tag identify a release.
The plugin ZIP filenames include their respective versions. Root `name` is the
marketplace name, `lumoz`, not a release version. The installer has its own
version in `installer/pyproject.toml`.

Claude and Codex use the same skills folder and version. The generator updates
the skills plugin's portable and Claude manifests and both marketplace catalogs
together. No separate Codex skills version or release tag is needed. The MCP
plugin is for Claude Code; the `lumoz-setup` installer handles marketplaces,
skills, and MCP configuration for both Codex and Claude Code. Its wheel embeds
the tested server pin generated from `mcp.version`. Desktop MCPB keeps its own
version. Changing installer code or its embedded pin requires a new installer
version and PyPI release; installed tools do not update themselves.

## After a server update

1. Release and verify the new `lumoz-mcp` version on PyPI from the server repo.
2. Update `mcp.version` here. Increase `plugins.mcp.version` and
   `desktop.version` for the integrations that will adopt it. One shared pin
   keeps future builds and Codex setup aligned; installed packages retain the
   version they already received until their distribution is released/updated.
3. Leave `plugins.skills.version` unchanged unless the skill or its package
   changed. Tool/schema changes may require updating the skill too.
4. Regenerate, test, and commit the metadata and all generated files together:

```sh
python3 scripts/build_claude.py --zip
python3 scripts/build_mcpb.py
python3 scripts/build_installer.py
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

Test the new server through Claude Code, Codex, and Claude Desktop with an authenticated read and record
tested client versions. Do not check API keys into the repository.

## Publish a distribution release

After the release commit is pushed, tag each changed component separately.
Use the version recorded for that component in metadata. For example, these
commands read the skills version and publish only its tag:

```sh
skills_version=$(python3 -c 'import json; print(json.load(open("plugin-source/metadata.json"))["plugins"]["skills"]["version"])')
git tag "lumoz-skills-v${skills_version}"
git push origin "lumoz-skills-v${skills_version}"
```

For the CLI MCP plugin use `plugins.mcp.version` and prefix `lumoz-mcp-v`.
For Desktop use `desktop.version` and prefix `lumoz-desktop-v`.

Push only the tags for components being released. A skills-only change needs
only a skills tag. A server-pin update normally needs MCP and Desktop tags.
Do not move a published tag; ship a new version for corrections.

The release workflow reuses package validation, downloads the checked build
artifacts from the same run, checks the tag against component metadata, and
publishes only that component's asset as a GitHub Release. MCP releases also
check that the pinned PyPI package version has downloadable artifacts. Desktop
releases are marked Latest; other component releases do not replace that
Latest release. Reusing an existing published release fails instead of
overwriting its asset. No repository publishing credentials are needed beyond
GitHub Actions' scoped `contents: write` token.

Local preparation can verify a tag without publishing:

```sh
desktop_version=$(python3 -c 'import json; print(json.load(open("plugin-source/metadata.json"))["desktop"]["version"])')
python3 scripts/prepare_release.py "lumoz-desktop-v${desktop_version}"
```

## Customer delivery is a separate stage

- GitHub-backed plugin marketplaces read the committed plugin directories;
  they do not consume the release ZIP. Bump the plugin version with changes.
  Claude Code users must enable auto-update for our third-party marketplace.
  Codex users refresh with `codex plugin marketplace upgrade lumoz`, reinstall
  `lumoz-skills` using `codex plugin add lumoz-skills@lumoz`, and start a new
  session. Their MCP configuration and saved key are independent of skills updates.
- Installer users run `uvx lumoz-setup@latest codex` or
  `uvx lumoz-setup@latest claude-code` and enter their key again. Setup keeps
  existing skills installations; refresh their marketplace separately when
  updating skills. Codex setup replaces the complete `lumoz` MCP entry.
  Claude's MCP plugin pin follows its plugin release, not the installer's
  embedded Codex server pin. Skills updates alone do not change Codex MCP.
- Anthropic plugin directory submissions track the relevant plugin folder and
  branch/tag, with checks and publishing controls. Submit
  `plugins/lumoz-skills` and `plugins/lumoz-mcp` separately if listing both.
- The MCPB release workflow does not register or notify Anthropic. Request
  one-time ingestion setup for tags `lumoz-desktop-v*` and asset `lumoz.mcpb`.
  An existing maintainer reports this arrangement; availability for Lumoz is
  not yet confirmed. See [the research notes](anthropic-publishing-options.md).
- Manual Desktop installs still require installing a newer MCPB file. For
  custom Team extensions, an Owner uploads the new version to the organization.
- Official MCP Registry publication, PyPI publication, and hosted MCP deployment
  are separate operations, not performed by this release workflow.

The initial releases of all three components were published successfully through
the GitHub release workflow. Directory submissions, feed registration,
signing, and live GUI acceptance tests remain pending.

## Publish the customer installer

The first release, `lumoz-setup` 0.1.0, is available on
[PyPI](https://pypi.org/project/lumoz-setup/). Customers run
`uvx lumoz-setup codex` or `uvx lumoz-setup claude-code`.
Maintainers can test from a checkout using
`uvx --from ./installer lumoz-setup codex` (or `claude-code`).

One-time PyPI configuration: register a pending trusted publisher for a new
project named `lumoz-setup` (or a trusted publisher on the existing project),
with GitHub owner `lumozai`, repository `lumoz-plugins`, workflow filename
`publish-installer.yml`, and environment `pypi`. Configure the matching GitHub
Actions environment and its release permissions. This requires a PyPI account
with ownership rights; no API token is committed to the repository. See
[PyPI's trusted publishing instructions](https://docs.pypi.org/trusted-publishers/creating-a-project-through-oidc/).

Use the same PyPI account that owns `lumoz-mcp`. Its publisher trusts
`lumozai/lumoz-mcp` and `publish-mcp.yml`; that registration does not authorize
this new project or repository. `lumoz-setup` uses the same OIDC authentication
method with its own registration. No shared PyPI password or API token is
needed. Register it under [account Publishing](https://pypi.org/manage/account/publishing/)
using these exact values:

| Field | Value |
| --- | --- |
| PyPI project name | `lumoz-setup` |
| GitHub owner | `lumozai` |
| Repository name | `lumoz-plugins` |
| Workflow filename | `publish-installer.yml` |
| Environment name | `pypi` |

For each installer release:

1. Update `installer/pyproject.toml`'s version. If adopting a new server pin,
   update `plugin-source/metadata.json` and regenerate installer defaults too.
2. Run from the repository root:

```sh
python3 scripts/build_installer.py
python3 scripts/build_installer.py --check
python3 -m unittest discover -s tests -v
uv build installer --out-dir dist/installer
python3 scripts/check_installer.py
```

3. Commit the source, generated defaults, and license. Push the release commit.
4. Tag that commit `lumoz-setup-v<version>` and push the tag. The
   `publish-installer.yml` workflow runs package validation, including isolated
   setup tests on Linux, then publishes the tested wheel
   and sdist through PyPI trusted publishing.
5. Verify the package version on PyPI and run `uvx lumoz-setup@<version> --help`
   outside a checkout. After the first successful release, remove the
   release-preparation notices from customer documentation.

The installer has a separate tag and publication workflow from the skills,
Claude MCP plugin, and MCPB distributions. Ordinary pushes do not publish it.
