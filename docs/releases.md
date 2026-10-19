# Release instructions

The server is released to PyPI from its own repository. This repository
releases distribution packages; it does not publish or copy the Python server.

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
marketplace name, `lumoz`, not a fourth release version.

## After a server update

1. Release and verify the new `lumoz-mcp` version on PyPI from the server repo.
2. Update `mcp.version` here. Increase `plugins.mcp.version` and
   `desktop.version` for the integrations that will adopt it. One shared pin
   keeps future builds of both routes aligned; installed packages retain the
   version they already received until their distribution is released/updated.
3. Leave `plugins.skills.version` unchanged unless the skill or its package
   changed. Tool/schema changes may require updating the skill too.
4. Regenerate, test, and commit the metadata and all generated files together:

```sh
python3 scripts/build_claude.py --zip
python3 scripts/build_mcpb.py
python3 scripts/build_claude.py --check
python3 scripts/build_mcpb.py --check
python3 -m unittest discover -s tests -v
claude plugin validate . --strict
claude plugin validate plugins/lumoz-skills --strict
claude plugin validate plugins/lumoz-mcp --strict
npx --yes @anthropic-ai/mcpb@2.1.2 validate mcpb/manifest.json
```

Test the new server through both clients with an authenticated read and record
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
