#!/usr/bin/env python3


from git import Repo

import github
import os
import re
import signal
import sys
import tomllib


###
# GLOBALS
###

PYPROJECT_TOML = "pyproject.toml"


###
# MAIN METHOD
###


def main():
    # Only execute on pull requests
    if get_env_var("GITHUB_REF") == "master":
        print("[INFO]  master branch detected")
        sys.exit()

    # Read version from pyproject.toml
    project_version = read_project_version()

    # Read expected "next" version
    next_version = read_next_version()

    # Compare versions
    if not project_version == next_version:
        die(
            [
                f"Version value in {PYPROJECT_TOML} does not match expected version",
                f"Project version       : {project_version}",
                f"Next expected version : {next_version}",
                "Aborting.",
            ]
        )

    else:
        print(f"[INFO]  NEXT VERSION MATCHES {PYPROJECT_TOML} VERSION:", next_version)


# Use "git describe" to retrieve most recent tag
def read_next_version():
    # Get latest tag
    git_describe = git_describe_version()

    # Get PR title
    pr_title = read_pr_title()

    # Parse PR header and increment tag
    next_version = determine_next_version(git_describe, pr_title)
    print("[DEBUG]  ")
    print("[DEBUG]  pr title             : '%s'" % pr_title)
    print("[DEBUG]  previous tag version : %s" % git_describe)
    print("[DEBUG]  next tag version     : %s" % next_version)
    print("[DEBUG]  ")

    return next_version


# Use PR title to determine next incremented version
def determine_next_version(git_describe, pr_title):
    # Work out which version part to increment
    if "[major]" in pr_title.lower():
        return increment_tag(git_describe, 0)

    elif "[minor]" in pr_title.lower():
        return increment_tag(git_describe, 1)

    elif "[patch]" in pr_title.lower():
        return increment_tag(git_describe, 2)

    elif "[notag]" in pr_title.lower():
        return git_describe

    else:
        die(
            [
                "One of the following - [major], [minor], [patch], [notag] - not found in PR title"
            ]
        )


# Increment tag based on PR title
def increment_tag(git_describe, position):
    # Split tag
    semver = git_describe.split(".")

    # Increment component
    semver[position] = str(int(semver[position]) + 1)

    # Reset version subcomponents to zero as required
    while position < 2:
        position += 1
        semver[position] = "0"

    # Return tag
    return ".".join(semver)


# Call git describe
def git_describe_version():
    # Read tag using git describe
    repo = Repo()
    git_tag = repo.git.describe("--abbrev=0", "--tags", "--match=v*.*.*")

    # String 'v' character
    return git_tag.replace("v", "")


# Read PR title using github client
def read_pr_title():
    # Load github params
    token = get_env_var("GITHUB_TOKEN")
    repo_name = get_env_var("GITHUB_REPOSITORY")
    pr_number = get_pr_number()

    # Fetch PR details
    gh = github.Github(token)
    repo = gh.get_repo(repo_name)
    pr = repo.get_pull(pr_number)

    # Return title
    return pr.title


# Extract PR number from GITHUB_REF
def get_pr_number():
    # Look up from env var (eg.: "refs/pull/123/merge")
    pr_ref = get_env_var("GITHUB_REF")

    # Extract number
    match = re.match("refs/pull/(.*?)/.*", pr_ref)

    if match:
        return int(match.group(1))

    else:
        die(["could not extract PR number from GITHUB_REF"])


# Extract version value from pyproject.toml
def read_project_version():
    with open(PYPROJECT_TOML, "rb") as config:
        data = tomllib.load(config)

    return data["project"]["version"]


# Look up env var
def get_env_var(env_var_name, strict=True):
    # Check env var
    value = os.getenv(env_var_name)

    # Handle missing value
    if not value:
        if strict:
            if env_var_name == "GITHUB_TOKEN":
                print(f"error: env var not found: {env_var_name}")
                print("""please ensure your workflow step includes
                env:
                    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}""")
                sys.exit(1)

            else:
                print(f"error: env var not found: {env_var_name}")
                sys.exit(1)

    return value


# Error message util
def die(messages):
    # Display message
    print("[ERROR]")

    for msg in messages:
        print(f"[ERROR]  {msg}")

    print("[ERROR]")

    # Exit non-zero
    sys.exit(1)


# Handle interrupt
def signal_handler(_, __):
    print(" ")
    sys.exit(0)


####
# MAIN
####

# Set up Ctrl-C handler
signal.signal(signal.SIGINT, signal_handler)

# Invoke main method
if __name__ == "__main__":
    main()
