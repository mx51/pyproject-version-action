# INIT_SESSION.md

Audience: AI agents starting a new session in this repo.

## What this project is

`pyproject-version-action` is a **GitHub composite Action** that validates the
`version` in `pyproject.toml` against the next expected SemVer tag for a PR.
It is consumed by other repos via their workflows; this repo is the source of
the Action.

- `action.yaml` — composite Action definition. Sets up Python 3.13, installs
  `requirements.txt`, then runs `action.py`.
- `action.py` — main script. Reads `pyproject.toml` version, runs `git describe`
  to find the latest `vX.Y.Z` tag, reads the PR title to determine which
  semver component to bump (`[major]` / `[minor]` / `[patch]` / `[notag]`),
  then asserts the bumped version equals the one written in `pyproject.toml`.
- `tests/test_action.py` — pytest unit tests, all functions mocked (no real
  git / GitHub calls).

## Key behaviors to know

- On `master` branch the script exits early (no validation).
- PR title must contain one of `[major]`, `[minor]`, `[patch]`, `[notag]` —
  otherwise the script dies.
- `git describe` is called with `--match=v*.*.*`, `--exclude=*/*`, and
  `--exclude=*-rc[0-9]*` so that namespaced tags (e.g. `foo/v1.2.3`) and
  release-candidate tags (e.g. `v1.2.3-rc1`) are ignored.
- The `v` prefix is stripped from the discovered tag before comparison.

## Tooling / conventions

- Python 3.13, managed via a project `.venv` (`make venv` creates it).
- `make check` runs `ruff format --check`, `ruff check`, and `mypy`.
- `make test` runs `pytest` with `coverage`.
- `make fmt` reformats with `ruff` and applies lint fixes.

Every change to `action.py` should come with a corresponding test in
`tests/test_action.py`, and `make check` + `make test` should pass before
considering the work done.
