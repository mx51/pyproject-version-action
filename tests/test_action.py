import os
from unittest.mock import MagicMock, mock_open, patch

import pytest

import action


class TestIncrementTag:
    def test_increment_major(self) -> None:
        result = action.increment_tag("1.2.3", 0)
        assert result == "2.0.0"

    def test_increment_minor(self) -> None:
        result = action.increment_tag("1.2.3", 1)
        assert result == "1.3.0"

    def test_increment_patch(self) -> None:
        result = action.increment_tag("1.2.3", 2)
        assert result == "1.2.4"

    def test_increment_from_zero(self) -> None:
        result = action.increment_tag("0.0.1", 0)
        assert result == "1.0.0"


class TestDetermineNextVersion:
    def test_major_increment(self) -> None:
        result = action.determine_next_version("1.2.3", "[major] Add new feature")
        assert result == "2.0.0"

    def test_minor_increment(self) -> None:
        result = action.determine_next_version("1.2.3", "[minor] Update API")
        assert result == "1.3.0"

    def test_patch_increment(self) -> None:
        result = action.determine_next_version("1.2.3", "[patch] Fix bug")
        assert result == "1.2.4"

    def test_notag_no_increment(self) -> None:
        result = action.determine_next_version("1.2.3", "[notag] Documentation update")
        assert result == "1.2.3"

    def test_invalid_tag_exits(self) -> None:
        with pytest.raises(SystemExit):
            action.determine_next_version("1.2.3", "No valid tag")


class TestGetPrNumber:
    @patch("action.get_env_var")
    def test_valid_pr_ref(self, mock_get_env_var: MagicMock) -> None:
        mock_get_env_var.return_value = "refs/pull/123/merge"
        result = action.get_pr_number()
        assert result == 123

    @patch("action.get_env_var")
    def test_invalid_pr_ref_exits(self, mock_get_env_var: MagicMock) -> None:
        mock_get_env_var.return_value = "refs/heads/main"
        with pytest.raises(SystemExit):
            action.get_pr_number()


class TestGetEnvVar:
    @patch.dict(os.environ, {"TEST_VAR": "test_value"})
    def test_existing_env_var(self) -> None:
        result = action.get_env_var("TEST_VAR")
        assert result == "test_value"

    @patch.dict(os.environ, {}, clear=True)
    def test_missing_env_var_strict(self) -> None:
        with pytest.raises(SystemExit):
            action.get_env_var("MISSING_VAR")

    @patch.dict(os.environ, {}, clear=True)
    def test_missing_env_var_not_strict(self) -> None:
        result = action.get_env_var("MISSING_VAR", strict=False)
        assert result is None

    @patch.dict(os.environ, {}, clear=True)
    @patch("builtins.print")
    def test_missing_github_token_shows_help(self, mock_print: MagicMock) -> None:
        with pytest.raises(SystemExit):
            action.get_env_var("GITHUB_TOKEN")

        mock_print.assert_any_call("error: env var not found: GITHUB_TOKEN")


class TestReadProjectVersion:
    def test_read_valid_pyproject_toml(self) -> None:
        toml_content = b'[project]\nversion = "1.2.3"\n'
        with patch("builtins.open", mock_open(read_data=toml_content)):
            result = action.read_project_version()
            assert result == "1.2.3"

    def test_read_missing_file(self) -> None:
        with patch("builtins.open", side_effect=FileNotFoundError):
            with pytest.raises(FileNotFoundError):
                action.read_project_version()


class TestGitDescribeVersion:
    @patch("action.Repo")
    def test_git_describe_with_v_prefix(self, mock_repo: MagicMock) -> None:
        mock_git = MagicMock()
        mock_git.describe.return_value = "v1.2.3"
        mock_repo.return_value.git = mock_git

        result = action.git_describe_version()
        assert result == "1.2.3"
        mock_git.describe.assert_called_once_with(
            "--abbrev=0",
            "--tags",
            "--match=v*.*.*",
            "--exclude=*/*",
            "--exclude=*-rc[0-9]*",
        )

    @patch("action.Repo")
    def test_git_describe_excludes_rc_tags(self, mock_repo: MagicMock) -> None:
        mock_git = MagicMock()
        mock_git.describe.return_value = "v1.2.3"
        mock_repo.return_value.git = mock_git

        action.git_describe_version()
        args = mock_git.describe.call_args.args
        assert "--exclude=*-rc[0-9]*" in args


class TestReadPrTitle:
    @patch("action.get_env_var")
    @patch("action.get_pr_number")
    @patch("action.github.Github")
    def test_read_pr_title_success(
        self, mock_github: MagicMock, mock_get_pr_number: MagicMock, mock_get_env_var: MagicMock
    ) -> None:
        mock_get_env_var.side_effect = lambda var: {
            "GITHUB_TOKEN": "fake_token",
            "GITHUB_REPOSITORY": "owner/repo",
        }[var]
        mock_get_pr_number.return_value = 123

        mock_pr = MagicMock()
        mock_pr.title = "[patch] Fix critical bug"
        mock_repo = MagicMock()
        mock_repo.get_pull.return_value = mock_pr
        mock_gh = MagicMock()
        mock_gh.get_repo.return_value = mock_repo
        mock_github.return_value = mock_gh

        result = action.read_pr_title()
        assert result == "[patch] Fix critical bug"
        mock_github.assert_called_once_with("fake_token")
        mock_gh.get_repo.assert_called_once_with("owner/repo")
        mock_repo.get_pull.assert_called_once_with(123)


class TestMain:
    @patch("action.get_env_var")
    def test_main_exits_on_master_branch(self, mock_get_env_var: MagicMock) -> None:
        mock_get_env_var.return_value = "master"
        with pytest.raises(SystemExit):
            action.main()

    @patch("action.get_env_var")
    @patch("action.read_project_version")
    @patch("action.read_next_version")
    def test_main_version_mismatch_exits(
        self, mock_read_next: MagicMock, mock_read_project: MagicMock, mock_get_env_var: MagicMock
    ) -> None:
        mock_get_env_var.return_value = "refs/pull/123/merge"
        mock_read_project.return_value = "1.2.3"
        mock_read_next.return_value = "1.2.4"

        with pytest.raises(SystemExit):
            action.main()

    @patch("action.get_env_var")
    @patch("action.read_project_version")
    @patch("action.read_next_version")
    @patch("builtins.print")
    def test_main_version_match_success(
        self,
        mock_print: MagicMock,
        mock_read_next: MagicMock,
        mock_read_project: MagicMock,
        mock_get_env_var: MagicMock,
    ) -> None:
        mock_get_env_var.return_value = "refs/pull/123/merge"
        mock_read_project.return_value = "1.2.4"
        mock_read_next.return_value = "1.2.4"

        action.main()
        mock_print.assert_called_with(
            "[INFO]  NEXT VERSION MATCHES pyproject.toml VERSION:", "1.2.4"
        )


class TestDie:
    def test_die_exits_with_messages(self) -> None:
        with patch("builtins.print") as mock_print:
            with pytest.raises(SystemExit) as exc_info:
                action.die(["Error message 1", "Error message 2"])

            assert exc_info.value.code == 1
            mock_print.assert_any_call("[ERROR]")
            mock_print.assert_any_call("[ERROR]  Error message 1")
            mock_print.assert_any_call("[ERROR]  Error message 2")
