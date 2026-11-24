# pyproject-version-action

## Overview

This Github Action is intended for use in conjunction with the [mx51/merge-tag-action](https://github.com/mx51/merge-tag-action) project.

The `merge-tag-action` project will automatically create a new Git tag once a Pull-Request is merged. It relies on labels set in the Pull-Request title to determine what component of the version will be incremented. This table shows an example of how a version will be updated based on the label used:

| Label     | Current Tag | New Tag  |
|-----------|-------------|----------|
| `[patch]` | `v1.2.3`    | `v1.2.4` |
| `[minor]` | `v1.2.3`    | `v1.3.0` |
| `[major]` | `v1.2.3`    | `v2.0.0` |
| `[notag]` | `v1.2.3`    | N/A      |

See the [merge-tag-action README.md](https://github.com/mx51/merge-tag-action/blob/master/README.md) for more details.

This project runs before a Pull-Request is merged, and checks that the version value set in `pyproject.toml` matches what the PR author intends to set based on the label used in their PR title.

## Usage

### Repository Settings

**IMPORTANT**: This action requires repository read permission on any project it is used with. Ensure this permission is enabled by going to your project's **Settings** -> **Actions** -> **General** and under **Workflow permissions** select **Read and write permissions**.

### Github Action Config

Below is an example of how Github Action can be enabled on a Github project:

```yaml
# When a pull request is opened, updated or merged, run the tag check
on:
  pull_request:
    types: [ opened, synchronize, reopened, edited ]
    branches-ignore:
      - 'dependabot/**'

jobs:
  tag_check:
    runs-on: ubuntu-latest
    name: "PyProject Version Check"
    permissions:
      pull-requests: read
    
    steps:
    - uses: actions/checkout@v6
      with:
        fetch-depth: 0

    - uses: mx51/pyproject-version-action@master
      with:
        repo-token: ${{ secrets.GITHUB_TOKEN }}
```

**Important**: The `permissions: pull-requests: read` is required for the action to access PR details via the GitHub API.

## Development

### Prerequisites

- Python 3.14 or later
- [uv](https://docs.astral.sh/uv/)
- A Git repository with tags that follow the `v*.*.*` pattern

The Action itself installs uv and runs `action.py` with Python 3.14. The packages come from `uv.lock`.

### Setup

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd pyproject-version-action
   ```

2. Create the virtual environment in `.venv/` from `uv.lock`:
   ```bash
   make venv
   ```

### Development Commands

| Command | Description |
|---------|-------------|
| `make uvsync` | Upgrade the packages and write a new `uv.lock` |
| `make venv` | Create the virtual environment from `uv.lock` |
| `make test` | Run unit tests with coverage |
| `make fmt` | Format the code and apply lint fixes with ruff |
| `make check` | Run format, lint, and type checks |
| `make check-fmt` | Check code formatting |
| `make check-lint` | Run linting checks |
| `make check-type` | Run type checking with mypy |
| `make clean` | Remove generated files |

Each `make` target runs its tools with `uv run`. If `.venv/` does not exist, uv creates it.

### Running Tests

```bash
# Direct pytest execution
uv run pytest -v

# Via Makefile (includes coverage)
make test
```

### Project Structure

```
├── action.py              # Main action script
├── action.yaml            # GitHub Action configuration
├── pyproject.toml         # Project metadata, dependencies and tool configuration
├── uv.lock                # Locked package versions
├── tests/
│   └── test_action.py     # Unit tests
├── reports/
│   └── coverage.xml       # Test coverage report
└── Makefile               # Development commands
```
