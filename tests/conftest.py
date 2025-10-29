import os

from pathlib import Path

from pytest import fixture
from rez.utils.data_utils import AttrDictWrapper


@fixture
def rez_config() -> AttrDictWrapper:
    config = AttrDictWrapper()
    config.production_database = None
    config.staging_database = None
    config.history_folder = None
    config.keep_history = True
    return config


@fixture
def temporary_database(tmp_path: Path) -> Path:
    return tmp_path / "production.db"


@fixture
def mock_rez_config(
    mocker: object,
    tmp_path: Path,
    rez_config: AttrDictWrapper,
    temporary_database: Path,
) -> None:
    config = rez_config.copy()
    config.production_database = temporary_database

    mocker.patch(
        "rezplugins.command.production_resolver_lib.get_rez_config",
        return_value=config,
    )
    return config


@fixture
def mock_rez_config_staging_customized(
    mocker: object,
    tmp_path: Path,
    rez_config: AttrDictWrapper,
    temporary_database: Path,
) -> None:
    config = rez_config.copy()
    config.production_database = temporary_database
    config.staging_database = tmp_path / "another_staging.db"

    mocker.patch(
        "rezplugins.command.production_resolver_lib.get_rez_config",
        return_value=config,
    )
    return config


@fixture
def mock_rez_config_history_folder_customized(
    mocker: object,
    tmp_path: Path,
    rez_config: AttrDictWrapper,
    temporary_database: Path,
) -> None:
    config = rez_config.copy()
    config.production_database = temporary_database
    config.history_folder = tmp_path / "backup_old_databases"

    mocker.patch(
        "rezplugins.command.production_resolver_lib.get_rez_config",
        return_value=config,
    )
    return config


@fixture
def mock_rez_config_no_history(
    mocker: object, rez_config: AttrDictWrapper, temporary_database: Path
) -> None:
    config = rez_config.copy()
    config.production_database = temporary_database
    config.keep_history = False

    mocker.patch(
        "rezplugins.command.production_resolver_lib.get_rez_config",
        return_value=config,
    )
    return config


@fixture
def staging_database(temporary_database: Path) -> Path:
    return (
        Path(os.path.dirname(temporary_database))
        / f"staging.{os.path.split(temporary_database)[1]}"
    )
