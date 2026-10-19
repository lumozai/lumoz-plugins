# Contributing

Install [Gitleaks](https://github.com/gitleaks/gitleaks#installing) v8.30.1
and place its executable on your PATH. Alternatively, put the executable in
`.tools/bin/gitleaks` (`.tools` is ignored by Git).

Enable the repository's pre-commit hook in each clone:

```sh
git config --local core.hooksPath .githooks
```

The hook scans staged changes before every commit and refuses to commit if
Gitleaks is missing or detects a secret. It applies to every local branch.
Git hooks are local configuration and must be enabled separately in each clone.

To scan all committed history manually:

```sh
gitleaks git --redact --no-banner --log-opts="--all"
```

GitHub secret scanning and push protection are enabled for this repository.
Push protection blocks supported secret patterns on pushes to every branch;
it does not require contributors to install the local hook. CI also scans the
full fetched Git history on every push and pull request, and before releases.
These tools cannot detect every possible credential. Keep real Lumoz keys in
local client configuration or environment variables, and use placeholders in
documentation.
