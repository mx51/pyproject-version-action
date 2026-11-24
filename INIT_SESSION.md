# INIT_SESSION.md

Audience: AI agents starting a new session in this repo.

## What this project is

`pyproject-version-action` is a **GitHub composite Action** that validates the
`version` in `pyproject.toml` against the next expected SemVer tag for a PR.
It is consumed by other repos via their workflows; this repo is the source of
the Action.

- `action.yaml` - composite Action definition. Installs uv, then runs
  `uv run --project <action path> --frozen --no-dev --python 3.14` on `action.py`.
  The working directory stays in the repo of the caller, so `action.py` reads the
  `pyproject.toml` of the caller, not the one of this repo.
- `action.py` - main script. Reads `pyproject.toml` version, runs `git describe`
  to find the latest `vX.Y.Z` tag, reads the PR title to determine which
  semver component to bump (`[major]` / `[minor]` / `[patch]` / `[notag]`),
  then asserts the bumped version equals the one written in `pyproject.toml`.
- `tests/test_action.py` - pytest unit tests, all functions mocked (no real
  git / GitHub calls).

## Key behaviors to know

- On `master` branch the script exits early (no validation).
- PR title must contain one of `[major]`, `[minor]`, `[patch]`, `[notag]`.
  If it does not, the script stops with an error.
- `git describe` is called with `--match=v*.*.*`, `--exclude=*/*`, and
  `--exclude=*-rc[0-9]*` so that namespaced tags (e.g. `foo/v1.2.3`) and
  release-candidate tags (e.g. `v1.2.3-rc1`) are ignored.
- The `v` prefix is stripped from the discovered tag before comparison.

## Tooling / conventions

- Python 3.14, managed with `uv` (`pyproject.toml` + `uv.lock`). There are no
  `requirements*.txt` files. `[tool.uv] package = false`: the project is not built.
- Layout is flat (`action.py` at the root), not `src/`, because `action.yaml` runs it by path.
- `make venv` runs `uv sync --frozen`. `make uvsync` upgrades the packages and the lock.
- `make check` runs `ruff format --check`, `ruff check`, and `mypy` (strict, as in
  `cicd-utils`), with `uv run`. It works with no `.venv/`.
- `make test` runs `pytest` with `coverage`. `make fmt` reformats and applies lint fixes.
- Dependabot uses the `uv` ecosystem with the `[notag] ` prefix.

Every change to `action.py` should come with a corresponding test in
`tests/test_action.py`, and `make check` + `make test` should pass before
considering the work done.
