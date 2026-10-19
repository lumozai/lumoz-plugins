# Registry and directory publishing

Updated October 19, 2026. Component release automation is documented in
[releases.md](releases.md). These are publishing instructions and launch
requirements, not a claim that Lumoz is already listed. Confirm each channel's
publication status before advertising its listing.

## Where Lumoz should appear

| Destination | What it provides | Required deliverable |
| --- | --- | --- |
| PyPI | Downloadable Python server | Published, versioned `lumoz-mcp` package |
| Official MCP Registry | Standard server metadata for registry consumers | Verified namespace and `server.json` referencing the PyPI package; later a remote entry |
| Lumoz GitHub marketplaces | Direct/team installation | Claude catalog with separate skills/MCP plugins; Codex catalog planned |
| Claude directory | Discovery inside Claude | Reviewed remote connector or plugin bundle submitted through Claude's portal |
| Claude Desktop extensions directory | Local MCP discovery in Desktop | Reviewed `.mcpb` submitted through the desktop-extension route |
| OpenAI universal plugin directory | Discovery in ChatGPT and Codex | Reviewed plugin package and connected MCP integration |

Treat these as distinct channels. Do not promise that an official MCP Registry
entry automatically appears in Claude's or OpenAI's curated directory. The
acceptance test is a search and successful installation inside each app.

Use **Lumoz** as the public display name, with a description such as
“Investigate AI agent traces, signals, and root causes with Lumoz.” Keep search
terms consistent: Lumoz, observability, traces, RCA, agent reliability, evals.

## 1. Publish to the official MCP Registry

The [registry](https://modelcontextprotocol.io/registry/quickstart) stores
metadata; PyPI continues to host the actual package. The registry is currently
in preview, so validate against its current schema when implementing.

### Choose and verify the namespace

Proposed name: `io.github.lumozai/lumoz-mcp`, using Lumoz's GitHub organization.
Confirm the publishing identity has authorization for that organization.
Alternatively, verify `lumoz.ai` using the documented DNS/HTTP procedure and
use `ai.lumoz/lumoz-mcp`. Choose one identity before publishing and use it
consistently. [Registry authentication](https://modelcontextprotocol.io/registry/authentication).

### Add ownership evidence to the PyPI package

In the README used for the `lumoz-mcp` PyPI package description, add:

```html
<!-- mcp-name: io.github.lumozai/lumoz-mcp -->
```

The name must exactly match `server.json`. Publish a new package release whose
PyPI description contains the marker. Adding it only to this plugin repository
does not prove ownership of the Python package. Do not overwrite an existing
PyPI version. [PyPI ownership requirements](https://modelcontextprotocol.io/registry/package-types).

The following is a metadata template. Replace `REPLACE_WITH_SERVER_VERSION`
in both fields with the actual published package version containing the
ownership marker before validating or publishing:

```json
{
  "$schema": "https://static.modelcontextprotocol.io/schemas/2025-12-11/server.schema.json",
  "name": "io.github.lumozai/lumoz-mcp",
  "title": "Lumoz",
  "description": "Investigate AI agent traces, signals, problems, root causes, and eval suggestions.",
  "version": "REPLACE_WITH_SERVER_VERSION",
  "packages": [
    {
      "registryType": "pypi",
      "identifier": "lumoz-mcp",
      "version": "REPLACE_WITH_SERVER_VERSION",
      "transport": { "type": "stdio" },
      "environmentVariables": [
        {
          "name": "LUMOZ_API_KEY",
          "description": "Lumoz API key in client_id:client_secret format",
          "isRequired": true,
          "isSecret": true,
          "format": "string"
        }
      ]
    }
  ]
}
```

Use public documentation links and public package metadata. Customer
installation should reference the published package.

### Authenticate, publish, and verify

Install the publisher using the [official installation instructions](https://modelcontextprotocol.io/registry/quickstart).
For example, on a machine with Homebrew:

```sh
brew install mcp-publisher
mcp-publisher --help
```

From the directory holding the prepared `server.json`:

```sh
mcp-publisher login github
mcp-publisher publish
curl 'https://registry.modelcontextprotocol.io/v0.1/servers?search=io.github.lumozai/lumoz-mcp'
```

Review the returned namespace, version, package reference, transport, and
required-secret declaration. Test installation from a clean registry consumer.
For automation, publish metadata only after the underlying PyPI artifact and
description are available. Prefer GitHub Actions OIDC to a long-lived token;
the official flow uses `mcp-publisher login github-oidc` with `id-token: write`.
[Registry release automation](https://modelcontextprotocol.io/registry/github-actions).

Keep package-version ownership with the server release workflow. This
repository can hold the reviewed metadata template, but avoid two independent
workflows publishing competing versions of the same server identity.

After the hosted service is live, add a `remotes` entry to a new metadata
version while retaining the package entry if local installation stays supported:

```json
{
  "remotes": [
    { "type": "streamable-http", "url": "https://mcp.lumoz.ai/mcp" }
  ]
}
```

This is a fragment to merge, not a complete registry document. Publish the URL
only after it is operational. [Remote registry entries](https://modelcontextprotocol.io/registry/remote-servers).

## 2. Make Lumoz discoverable in Claude

### Recommended public listing

Use Claude's [directory submission portal](https://claude.ai/directory/manage/new).
The current portal accepts a single remote MCP connector or a GitHub-hosted
plugin bundle. Submit the existing skills plugin independently of the CLI MCP plugin.
A hosted connector is a future integration, not required for the skills listing.
[Claude's publishing announcement](https://claude.com/resources/articles/build-plugins-for-claude).

For a bundle referencing our own remote server, submit **both** the MCP
connector and the plugin bundle as separate submissions. Connect a GitHub
account with push access, select this repository with plugin path `plugins/lumoz-skills` or
`plugins/lumoz-mcp`,
and choose the tracked branch/tag. The plugin repository may be
private during submission but must be public before its directory listing
goes live. Publishing the plugin does not require publishing the server's
source repository.
Run `claude plugin validate` before portal validation. Each plugin folder has
its own submission. [Claude submission instructions](https://claude.com/docs/plugins/submit).

Prepare the production MCP URL, authentication instructions, a public plugin
repository/release, logo, support contact, privacy/terms links, and reproducible
sample workflows. Supply whatever additional review information the portal
requests; its current form is authoritative.

Submit, resolve validation/review findings, and publish after approval. Then
verify searching **Lumoz** from Claude's directory, installing it, completing
account consent, and listing apps. Repeat in chat and Cowork. A GitHub
marketplace install is a useful early distribution channel, but it is not
evidence that a public directory listing is live.

Choose scheduled checks or the offered GitHub push webhook for updates. A
passing scan and a live listing are separate states; follow the portal's
publish/reviewer controls and retain the last approved release until the new
one is live. [Claude release process](https://claude.com/docs/plugins/submit).

### Optional local Desktop listing

The trial extension is implemented under `mcpb/`. Build it with
`python3 scripts/build_mcpb.py`; the output is `dist/lumoz.mcpb`.
It uses manifest 0.4, the managed `uv` runtime, a Python import launcher, the
server pin from `plugin-source/metadata.json`, and a required sensitive API-key
field. It includes the license and no skills or server implementation source.
Validate it with `npx --yes @anthropic-ai/mcpb@2.1.2 validate mcpb/manifest.json`.

Before submitting this extension to the Desktop directory:

1. Install on clean Windows/macOS systems with a current Desktop version and
   verify managed `uv` support, the credential form, startup, restart, and a
   read-only authenticated tool call.
2. Confirm licensing and distribution requirements for a public listing.
3. Submit through the Desktop extension submission link in Claude's local-MCP
   guide. This is separate from the remote/plugin portal.

The extension format and runtime options are documented in the
[MCPB manifest reference](https://github.com/modelcontextprotocol/mcpb/blob/main/MANIFEST.md).
Desktop's installation/submission route is described in the
[local MCP guide](https://support.claude.com/en/articles/10949351-getting-started-with-local-mcp-servers-on-claude-desktop).
An MCPB listing alone does not supply browser chat access. Official-directory
extensions update automatically by default; privately distributed MCPB files
require users to install updated files manually. Keep skills distributed through
the plugin's marketplace/directory, independently of the extension.

## 3. Make Lumoz discoverable in Codex and ChatGPT

### Recommended public listing: hosted MCP with OAuth

Build the hosted package using OpenAI's supported portable plugin format.
Include the server connection in the first submission, along with the shared
skills. Prepare public branding and support/legal pages, a verified publisher
identity, and an isolated reviewer tenant with sample telemetry.

In OpenAI's [plugin submission portal](https://platform.openai.com/plugins):

1. Select the owning organization/project and verified publishing identity.
2. Upload the plugin ZIP and connect its production HTTPS MCP server.
3. Complete the domain-verification challenge and tool scan.
4. Resolve package/skill/server findings and provide review materials.
5. Submit, track feedback, and publish after approval.

The current review process requires five positive and three negative test
cases, a walkthrough, and reviewer access. Reviewer access must work without
interactive MFA, email/SMS codes, or magic-link approval. Provide a supported
reviewer sign-in flow; keep reviewer secrets
out of the ZIP. [OpenAI submission requirements](https://developers.openai.com/plugins/deploy/submission).

Use OAuth for the hosted integration. The current submission portal does not
complete API-key/Basic-auth connections simply from a manifest declaration.
Do not publish a shared Lumoz API key in headers as a workaround.
[OpenAI authentication limitations](https://developers.openai.com/plugins/deploy/submission).

### If keeping the public listing stdio-only

OpenAI currently restricts local MCP submissions to approved partners and marks
them Desktop only. Eligibility/allowlisting is a separate prerequisite; a
public PyPI package does not remove it. Local directory packages must include
their server and dependencies, so do not assume a `uvx` reference alone meets
submission requirements. Confirm the packaging with OpenAI before investing
in that route. [Desktop-only submission policy](https://developers.openai.com/plugins/deploy/desktop-only).

Continue offering direct MCP setup and repo-marketplace installation while
directory approval is pending. Those give users access but do not satisfy the
public in-app discovery objective.

## Launch tracking

Maintain a small release record for each channel:

| Channel | Track |
| --- | --- |
| PyPI | Version, artifact hash, release URL |
| Official MCP Registry | Namespace, metadata version, lookup result |
| GitHub marketplaces | Commit/tag, plugin versions, tested client versions |
| Claude directory | Submission ID, status, published listing URL, tested surfaces |
| Claude Desktop extension | Bundle version/hash, approval status, install result |
| OpenAI directory | Submission ID, status, listing URL, supported execution surfaces |

Before declaring discovery complete, test from accounts that did not author
the submission. Record search visibility, installation, authentication, and a
successful read in both app families. Account/workspace policy can affect
availability, so document those restrictions in the listing and setup guide.
