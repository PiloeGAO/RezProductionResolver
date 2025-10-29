"""Tests for the production resolver library."""

import sqlite3

from datetime import datetime
from pathlib import Path

import pytest
from rez.exceptions import RezError
from rez.resolver import ResolverStatus

from rezplugins.command.production_resolver_lib import (
    ProductionResolverDatabase,
    HistoryEditOperation,
    HistoryEdit,
)


def test___init___production_set(
    staging_database: Path, mock_rez_config: object
) -> None:
    """Tests if we are able to initialize the production resolver variables with production only set.

    Args:
        staging_database (:class:`pathlib.Path`): The path to the staging database.
        mock_rez_config (object): Mocked rez configuration.
    """
    with ProductionResolverDatabase(load_production=False) as database:
        assert database.production_database_path == mock_rez_config.production_database
        assert database.staging_path == staging_database
        assert (
            database.history_folder_path
            == mock_rez_config.production_database.parent / "history"
        )


def test___init___production_staging_set(
    mock_rez_config_staging_customized: object,
) -> None:
    """Tests if we are able to initialize the production resolver variables with production and staging only set.

    Args:
        mock_rez_config_staging_customized (object): Mocked rez configuration.
    """
    with ProductionResolverDatabase(load_production=False) as database:
        assert (
            database.production_database_path
            == mock_rez_config_staging_customized.production_database
        )
        assert (
            database.staging_path == mock_rez_config_staging_customized.staging_database
        )
        assert (
            database.history_folder_path
            == mock_rez_config_staging_customized.production_database.parent / "history"
        )


def test___init___production_history_set(
    staging_database: Path, mock_rez_config_history_folder_customized: object
) -> None:
    """Tests if we are able to initialize the production resolver variables with production and history only set.

    Args:
        staging_database (:class:`pathlib.Path`): The path to the staging database.
        mock_rez_config_history_folder_customized (object): Mocked rez configuration.
    """
    with ProductionResolverDatabase(load_production=False) as database:
        assert (
            database.production_database_path
            == mock_rez_config_history_folder_customized.production_database
        )
        assert database.staging_path == staging_database
        assert (
            database.history_folder_path
            == mock_rez_config_history_folder_customized.history_folder
        )


def test_edits(mocker: object, mock_rez_config: object) -> None:
    """Tests if the edits are recorded during package addition/deletion.

    Args:
        mocker (object): Mocked object.
        mock_rez_config (object): Mocked rez configuration.
    """
    with ProductionResolverDatabase(load_production=False) as database:
        database.initialize()
        database.add_package([], "packageA", None, None, validate=False)
        database.add_package([], "packageB", "stepA", None, validate=False)
        database.add_package([], "packageC", None, "software", validate=False)
        database.add_package([], "packageD", "stepA", "software", validate=False)
        database.remove_package([], "packageA", validate=False)
        database.remove_package([], "packageB", "stepA", None, validate=False)
        database.remove_package([], "packageC", None, "software", validate=False)
        database.remove_package([], "packageD", "stepA", "software", validate=False)

        assert database.edits == [
            HistoryEdit(
                context=[],
                package_name="packageA",
                step=None,
                software=None,
                operation=HistoryEditOperation.INSTALL,
            ),
            HistoryEdit(
                context=[],
                package_name="packageB",
                step="stepA",
                software=None,
                operation=HistoryEditOperation.INSTALL,
            ),
            HistoryEdit(
                context=[],
                package_name="packageC",
                step=None,
                software="software",
                operation=HistoryEditOperation.INSTALL,
            ),
            HistoryEdit(
                context=[],
                package_name="packageD",
                step="stepA",
                software="software",
                operation=HistoryEditOperation.INSTALL,
            ),
            HistoryEdit(
                context=[],
                package_name="packageA",
                step=None,
                software=None,
                operation=HistoryEditOperation.UNINSTALL,
            ),
            HistoryEdit(
                context=[],
                package_name="packageB",
                step="stepA",
                software=None,
                operation=HistoryEditOperation.UNINSTALL,
            ),
            HistoryEdit(
                context=[],
                package_name="packageC",
                step=None,
                software="software",
                operation=HistoryEditOperation.UNINSTALL,
            ),
            HistoryEdit(
                context=[],
                package_name="packageD",
                step="stepA",
                software="software",
                operation=HistoryEditOperation.UNINSTALL,
            ),
        ]


def test_exists(mock_rez_config: object) -> None:
    """Tests if the database exists.

    Args:
        mock_rez_config (object): Mocked rez configuration.
    """
    with ProductionResolverDatabase(load_production=False) as database:
        assert database.exists()

    with ProductionResolverDatabase(load_production=True) as database:
        assert database.exists()


def test_initialize(staging_database: Path, mock_rez_config: object) -> None:
    """Tests the initialization of the production resolver.

    Args:
        staging_database (:class:`pathlib.Path`): The path to the staging database.
        mock_rez_config (object): Mocked rez configuration.
    """
    assert not staging_database.exists()

    with ProductionResolverDatabase(load_production=False) as database:
        database.initialize()

    assert staging_database.exists()

    connection = sqlite3.connect(staging_database.as_posix())
    cursor = connection.cursor()

    tables = {
        "context": ["context_id", "project", "category", "entity"],
        "package": ["context_id", "name", "step", "software"],
        "history": [
            "user",
            "context",
            "package_name",
            "step",
            "software",
            "operation",
            "date",
            "comment",
        ],
    }

    for table_name, columns_name in tables.items():
        assert (
            next(
                iter(
                    cursor.execute(
                        f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}';"
                    ).fetchone()
                ),
                None,
            )
            is not None
        )

        columns = [
            value[0]
            for value in cursor.execute(
                f"SELECT name FROM PRAGMA_TABLE_INFO('{table_name}');"
            ).fetchall()
        ]
        assert columns_name == columns

    assert (
        cursor.execute(
            "SELECT context_id FROM context WHERE project IS NULL AND category IS NULL AND entity IS NULL"
        ).fetchone()[0]
        == 1
    )

    with ProductionResolverDatabase(load_production=False) as database:
        assert database.exists()


@pytest.mark.freeze_time("2020-01-01")
def test_save(mocker: object, staging_database: Path, mock_rez_config: object) -> None:
    """Tests the saving of changes to the database.

    Args:
        mocker (object): Mocked object.
        staging_database (:class:`pathlib.Path`): The path to the staging database.
        mock_rez_config (object): Mocked rez configuration.
    """
    mocker.patch("getpass.getuser", return_value="user")

    production_context = [
        "project",
        "category",
        "entity",
    ]

    database_index = None

    with ProductionResolverDatabase(load_production=False) as database:
        database.initialize()

        database_index = database.cursor.execute(
            "INSERT INTO context(project, category, entity) VALUES(?, ?, ?) RETURNING context_id;",
            (production_context[0], production_context[1], production_context[2]),
        ).fetchone()[0]
        database.save()

    with ProductionResolverDatabase(load_production=False) as database:
        assert (
            database.cursor.execute(
                f"SELECT context_id FROM context WHERE project = '{production_context[0]}' AND category = '{production_context[1]}' AND entity = '{production_context[2]}';"
            ).fetchone()[0]
            == database_index
        )

    with ProductionResolverDatabase(load_production=False) as database:
        database.add_package([], "packageA", None, None, validate=False)
        database.save(store_history=False)
        assert not database.cursor.execute(
            "SELECT * FROM history ORDER BY rowid"
        ).fetchall()

        database.add_package([], "packageB", "stepA", None, validate=False)
        database.save(store_history=True)

        assert database.cursor.execute(
            "SELECT * FROM history ORDER BY rowid"
        ).fetchall() == [
            (
                "user",
                "",
                "packageB",
                "stepA",
                "",
                HistoryEditOperation.INSTALL.value,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "(1/1)",
            ),
        ]

        database.add_package([], "packageC", None, "software", validate=False)
        database.add_package([], "packageD", "stepA", "software", validate=False)
        database.save(store_history=True)

        database.save()

        assert database.cursor.execute(
            "SELECT * FROM history ORDER BY rowid"
        ).fetchall() == [
            (
                "user",
                "",
                "packageB",
                "stepA",
                "",
                HistoryEditOperation.INSTALL.value,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "(1/1)",
            ),
            (
                "user",
                "",
                "packageC",
                "",
                "software",
                HistoryEditOperation.INSTALL.value,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "(1/2)",
            ),
            (
                "user",
                "",
                "packageD",
                "stepA",
                "software",
                HistoryEditOperation.INSTALL.value,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "(2/2)",
            ),
        ]

        database.remove_package([], "packageD", "stepA", "software", validate=False)
        database.save(comment="Removing a wrong package")

        assert database.cursor.execute(
            "SELECT * FROM history ORDER BY rowid"
        ).fetchall() == [
            (
                "user",
                "",
                "packageB",
                "stepA",
                "",
                HistoryEditOperation.INSTALL.value,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "(1/1)",
            ),
            (
                "user",
                "",
                "packageC",
                "",
                "software",
                HistoryEditOperation.INSTALL.value,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "(1/2)",
            ),
            (
                "user",
                "",
                "packageD",
                "stepA",
                "software",
                HistoryEditOperation.INSTALL.value,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "(2/2)",
            ),
            (
                "user",
                "",
                "packageD",
                "stepA",
                "software",
                HistoryEditOperation.UNINSTALL.value,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Removing a wrong package(1/1)",
            ),
        ]


@pytest.mark.freeze_time("2020-01-01")
def test__compute_history_database_path():
    """Tests the computation of the history database path."""
    with ProductionResolverDatabase(load_production=False) as database:
        assert database._compute_history_database_path() == (
            database.history_folder_path
            / f"{datetime.now().strftime('%y_%m_%d_%H_%M_%S_%f')}.db"
        )


@pytest.mark.freeze_time("2020-01-01")
def test_deploy(mock_rez_config: object) -> None:
    """Tests the deployment of the database to production.

    Args:
        mock_rez_config (object): Mocked rez configuration.
    """
    with ProductionResolverDatabase(load_production=False) as database:
        database.initialize()

        database.deploy()

        assert Path(
            database.history_folder_path
            / f"{datetime.now().strftime('%y_%m_%d_%H_%M_%S_%f')}.db"
        ).exists()
        assert Path(database.production_database_path).exists()


def test_deploy_production_database(mock_rez_config: object) -> None:
    """Tests the deployment of the production database to production.

    Args:
        mock_rez_config (object): Mocked rez configuration.
    """
    with pytest.raises(RuntimeError, match="Cannot deploy a production database."):
        with ProductionResolverDatabase(load_production=True) as database:
            database.initialize()
            database.deploy()


def test_deploy_no_history(mock_rez_config_no_history: object) -> None:
    """Tests the deployment of the database to production without history.

    Args:
        mock_rez_config_no_history (object): Mocked rez configuration without history.
    """
    with ProductionResolverDatabase(load_production=False) as database:
        database.initialize()

        database.deploy()

        assert Path(database.production_database_path).exists()


def test_insert_context(mock_rez_config: object) -> None:
    """Tests the insertion of a context into the database.

    Args:
        mock_rez_config (object): Mocked rez configuration.
    """
    production_context = [
        "project",
        "category",
        "entity",
    ]

    with ProductionResolverDatabase(load_production=False) as database:
        database.initialize()
        context_id = database.insert_context(*production_context)

        assert (
            database.cursor.execute(
                f"SELECT context_id FROM context WHERE project = '{production_context[0]}' AND category = '{production_context[1]}' AND entity = '{production_context[2]}';"
            ).fetchone()[0]
            == context_id
        )


def test_get_context_row_id(mock_rez_config: object):
    """Tests the retrieval of a context row ID from the database.

    Args:
        mock_rez_config (object): Mocked rez configuration.
    """
    production_context = [
        "project",
        "category",
        "entity",
    ]

    with ProductionResolverDatabase(load_production=False) as database:
        database.initialize()
        context_id = database.insert_context(*production_context)

        assert database.get_context_row_id(*production_context) == context_id
        assert (
            database.get_context_row_id(*production_context)
            == database.cursor.execute(
                f"SELECT context_id FROM context WHERE project = '{production_context[0]}' AND category = '{production_context[1]}' AND entity = '{production_context[2]}';"
            ).fetchone()[0]
        )


@pytest.mark.parametrize(
    "package_context",
    [
        (None, None, None),
        ("project", None, None),
        ("project", "category", None),
        ("project", "category", "entity"),
    ],
)
def test_sanitize_context(
    mock_rez_config: object,
    package_context: tuple[str, str, str],
) -> None:
    """Tests the sanitization of contexts.

    Args:
        mock_rez_config (object): Mocked rez configuration.
        package_context (tuple[str | None, str | None, str | None]): The package context to sanitize.
    """
    assert (
        ProductionResolverDatabase.sanitize_context(*package_context) == package_context
    )


def test_sanitize_context_errors(mock_rez_config: object) -> None:
    """Tests the sanitization of contexts with invalid package context.

    Args:
        mock_rez_config (object): Mocked rez configuration.
    """
    with pytest.raises(
        ValueError, match="A context can only 0 to 3 production environments."
    ):
        ProductionResolverDatabase.sanitize_context(
            "project", "category", "entity", "step"
        )


def test_get_package_list_with_validation_valid(
    mocker: object, mock_rez_config: object
):
    """Tests the retrieval of a package list from the database with validation.

    Args:
        mocker (object): Mocked object.
        mock_rez_config (object): Mocked rez configuration.
    """

    mocker.patch(
        "rezplugins.command.production_resolver_lib.ProductionResolverDatabase.validate_context",
        return_value=(True, None),
    )

    with ProductionResolverDatabase(load_production=False) as database:
        database.initialize()

        # Add the context before doing any operation.
        database.insert_context()
        database.insert_context("project")
        database.insert_context("project", "category")
        database.insert_context("project", "category", "entity")

        database.add_package(
            [None, None, None], package_name="packageA", validate=False
        )
        assert database.get_package_list(None, None, None, validate=False) == (
            "packageA",
        )

        database.add_package(
            ["project", None, None], package_name="packageB", validate=False
        )
        assert database.get_package_list("project", None, None, validate=False) == (
            "packageA",
            "packageB",
        )

        database.add_package(
            ["project", "category", None], package_name="packageC", validate=False
        )
        assert database.get_package_list("project", "category", validate=False) == (
            "packageA",
            "packageB",
            "packageC",
        )

        database.add_package(
            ["project", "category", "entity"], package_name="packageD", validate=False
        )
        assert database.get_package_list(
            "project", "category", "entity", validate=False
        ) == (
            "packageA",
            "packageB",
            "packageC",
            "packageD",
        )

        database.add_package(
            [None, None, None], package_name="packageE", step="stepA", validate=False
        )
        assert database.get_package_list(
            None, None, None, step="stepA", validate=False
        ) == (
            "packageA",
            "packageE",
        )
        database.add_package(
            [None, None, None],
            package_name="packageF",
            software="softwareA",
            validate=False,
        )
        assert database.get_package_list(
            None, None, None, software="softwareA", validate=False
        ) == (
            "packageA",
            "packageF",
        )
        database.add_package(
            [None, None, None],
            package_name="packageG",
            step="stepB",
            software="softwareB",
            validate=False,
        )
        assert database.get_package_list(
            None, None, None, step="stepB", software="softwareB", validate=False
        ) == (
            "packageA",
            "packageG",
        )


def test_get_package_list_with_validation_invalid(
    mocker: object, mock_rez_config: object
):
    """Tests the retrieval of a package list from the database with validation failing.

    Args:
        mocker (object): Mocked object.
        mock_rez_config (object): Mocked rez configuration.
    """
    exception = RezError("Mocked message")
    error_message = f"Package list can't be validated: {exception}"

    mocker.patch(
        "rezplugins.command.production_resolver_lib.ProductionResolverDatabase.validate_context",
        return_value=(False, exception),
    )

    with ProductionResolverDatabase(load_production=False) as database:
        database.initialize()

        # Add the context before doing any operation.
        database.insert_context()
        database.insert_context("project")
        database.insert_context("project", "category")
        database.insert_context("project", "category", "entity")

        database.add_package(
            [None, None, None], package_name="packageA", validate=False
        )
        with pytest.raises(ValueError, match=error_message):
            _ = database.get_package_list(None, None, None, validate=True)

        database.add_package(
            ["project", None, None], package_name="packageB", validate=False
        )
        with pytest.raises(ValueError, match=error_message):
            _ = database.get_package_list("project", None, None, validate=True)

        database.add_package(
            ["project", "category", None], package_name="packageC", validate=False
        )
        with pytest.raises(ValueError, match=error_message):
            _ = database.get_package_list("project", "category", validate=True)

        database.add_package(
            ["project", "category", "entity"], package_name="packageD", validate=False
        )
        with pytest.raises(ValueError, match=error_message):
            _ = database.get_package_list(
                "project", "category", "entity", validate=True
            )

        database.add_package(
            [None, None, None], package_name="packageE", step="stepA", validate=False
        )
        with pytest.raises(ValueError, match=error_message):
            _ = database.get_package_list(None, None, None, step="stepA", validate=True)
        database.add_package(
            [None, None, None],
            package_name="packageF",
            software="softwareA",
            validate=False,
        )
        with pytest.raises(ValueError, match=error_message):
            _ = database.get_package_list(
                None, None, None, software="softwareA", validate=True
            )
        database.add_package(
            [None, None, None],
            package_name="packageG",
            step="stepB",
            software="softwareB",
            validate=False,
        )
        with pytest.raises(ValueError, match=error_message):
            _ = database.get_package_list(
                None, None, None, step="stepB", software="softwareB", validate=True
            )


def test_get_package_list_without_validation(mock_rez_config: object):
    """Tests the retrieval of a package list from the database without validation.

    Args:
        mocker (object): Mocked object.
        mock_rez_config (object): Mocked rez configuration.
    """
    with ProductionResolverDatabase(load_production=False) as database:
        database.initialize()

        # Add the context before doing any operation.
        database.insert_context()
        database.insert_context("project")
        database.insert_context("project", "category")
        database.insert_context("project", "category", "entity")

        database.add_package(
            [None, None, None], package_name="packageA", validate=False
        )
        assert database.get_package_list(None, None, None, validate=False) == (
            "packageA",
        )

        database.add_package(
            ["project", None, None], package_name="packageB", validate=False
        )
        assert database.get_package_list("project", None, None, validate=False) == (
            "packageA",
            "packageB",
        )

        database.add_package(
            ["project", "category", None], package_name="packageC", validate=False
        )
        assert database.get_package_list("project", "category", validate=False) == (
            "packageA",
            "packageB",
            "packageC",
        )

        database.add_package(
            ["project", "category", "entity"], package_name="packageD", validate=False
        )
        assert database.get_package_list(
            "project", "category", "entity", validate=False
        ) == (
            "packageA",
            "packageB",
            "packageC",
            "packageD",
        )

        database.add_package(
            [None, None, None], package_name="packageE", step="stepA", validate=False
        )
        assert database.get_package_list(
            None, None, None, step="stepA", validate=False
        ) == (
            "packageA",
            "packageE",
        )
        database.add_package(
            [None, None, None],
            package_name="packageF",
            software="softwareA",
            validate=False,
        )
        assert database.get_package_list(
            None, None, None, software="softwareA", validate=False
        ) == (
            "packageA",
            "packageF",
        )
        database.add_package(
            [None, None, None],
            package_name="packageG",
            step="stepB",
            software="softwareB",
            validate=False,
        )
        assert database.get_package_list(
            None, None, None, step="stepB", software="softwareB", validate=False
        ) == (
            "packageA",
            "packageG",
        )


def test_validate_context_valid(mocker: object) -> None:
    """Tests the validation of a context.

    Args:
        mocker (object): Mocked object.
    """

    class ResolvedContext:
        def __init__(self, packages):
            self.packages = packages

        def validate(self):
            return True

        @property
        def status(self):
            return ResolverStatus.solved

    mocker.patch("rez.resolved_context.ResolvedContext", side_effect=ResolvedContext)
    assert ProductionResolverDatabase.validate_context("python") == (True, None)


def test_validate_context_invalid(mocker: object) -> None:
    """Tests the invalidation of a context.

    Args:
        mocker (object): Mocked object.
    """
    exception = RezError("Mocked message")

    class ResolvedContext:
        def __init__(self, packages):
            self.packages = packages

        def validate(self):
            raise exception

    mocker.patch("rez.resolved_context.ResolvedContext", side_effect=ResolvedContext)

    assert ProductionResolverDatabase.validate_context("anotherTool") == (
        False,
        exception,
    )


@pytest.mark.parametrize(
    "package_name,package_context,package_step,package_software",
    [
        ("packageA", (None, None, None), None, None),
        ("packageB", (None, None, None), "stepA", None),
        ("packageC", (None, None, None), None, "softwareA"),
        ("packageD", (None, None, None), "stepA", "softwareB"),
        ("packageE", ("project", None, None), None, None),
        ("packageF", ("project", None, None), None, None),
        ("packageG", ("project", None, None), "stepA", None),
        ("packageH", ("project", None, None), None, "softwareA"),
        ("packageI", ("project", None, None), "stepA", "softwareB"),
        ("packageJ", ("project", "category", None), None, None),
        ("packageK", ("project", "category", None), None, None),
        ("packageL", ("project", "category", None), "stepA", None),
        ("packageM", ("project", "category", None), None, "softwareA"),
        ("packageN", ("project", "category", None), "stepA", "softwareB"),
        ("packageO", ("project", "category", "entity"), None, None),
        ("packageP", ("project", "category", "entity"), "stepA", None),
        ("packageQ", ("project", "category", "entity"), None, "softwareA"),
        ("packageR", ("project", "category", "entity"), "stepA", "softwareB"),
    ],
)
@pytest.mark.freeze_time("2020-01-01")
def test_add_package(
    mocker: object,
    mock_rez_config: object,
    package_name: str,
    package_context: tuple[str, str, str],
    package_step: str,
    package_software: str,
) -> None:
    """Tests the addition of a package for a combination of situations.

    Warning:
        Validation is disabled.

    Args:
        mocker (object): Mocked object.
        mock_rez_config (object): Mocked rez configuration.
        package_name (str): Package name.
        package_context (tuple): Package context.
        package_step (str): Package step.
        package_software (str): Package software.
    """
    mocker.patch("getpass.getuser", return_value="user")

    with ProductionResolverDatabase(load_production=False) as database:
        database.initialize()

        package_id = database.add_package(
            package_context,
            package_name,
            step=package_step,
            software=package_software,
            validate=False,
        )

        # Get the context id to make sure a context is created if necessary.
        assert database.cursor.execute(
            "SELECT context_id FROM context WHERE project {project} AND category {category} AND entity {entity};".format(
                project=(
                    f"= '{package_context[0]}'" if package_context[0] else "IS NULL"
                ),
                category=(
                    f"= '{package_context[1]}'" if package_context[1] else "IS NULL"
                ),
                entity=(
                    f"= '{package_context[2]}'" if package_context[2] else "IS NULL"
                ),
            )
        ).fetchone()[0]

        assert (
            package_name,
            package_step,
            package_software,
        ) == database.cursor.execute(
            f"SELECT name, step, software FROM package WHERE rowid = '{package_id}';"
        ).fetchone()

        database.save()

        assert database.cursor.execute(
            "SELECT * FROM history ORDER BY rowid DESC LIMIT 1"
        ).fetchall()[0] == (
            "user",
            ",".join([context for context in package_context if context]),
            package_name,
            package_step or "",
            package_software or "",
            HistoryEditOperation.INSTALL.value,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "(1/1)",
        )


def test_add_package_with_validation_valid(
    mocker: object, mock_rez_config: object
) -> None:
    """Tests the addition of a package with validation.

    Args:
        mocker (object): Mocked object.
        mock_rez_config (object): Mocked rez configuration.
    """
    package_name = "anotherTool"

    mocker.patch(
        "rezplugins.command.production_resolver_lib.ProductionResolverDatabase.validate_context",
        return_value=(True, None),
    )

    with ProductionResolverDatabase(load_production=False) as database:
        database.initialize()

        package_id = database.add_package(
            [None, None, None],
            package_name,
            step=None,
            software=None,
            validate=True,
        )
        assert (
            package_name,
            None,
            None,
        ) == database.cursor.execute(
            f"SELECT name, step, software FROM package WHERE rowid = '{package_id}';"
        ).fetchone()


def test_add_package_errors(mocker: object, mock_rez_config: object) -> None:
    """Tests the addition of a package with invalid validation.

    Args:
        mocker (object): Mocked object.
        mock_rez_config (object): Mocked rez configuration.
    """
    package_name = "anotherTool"
    exception = RezError("Mocked message")

    mocker.patch(
        "rezplugins.command.production_resolver_lib.ProductionResolverDatabase.validate_context",
        return_value=(False, exception),
    )

    with pytest.raises(RezError):
        with ProductionResolverDatabase(load_production=False) as database:
            database.initialize()

            database.add_package(
                [None, None, None],
                package_name,
                step=None,
                software=None,
                validate=True,
            )


@pytest.mark.parametrize(
    "package_name,package_context,package_step,package_software",
    [
        ("packageA", (None, None, None), None, None),
        ("packageB", (None, None, None), "stepA", None),
        ("packageC", (None, None, None), None, "softwareA"),
        ("packageD", (None, None, None), "stepA", "softwareB"),
        ("packageE", ("project", None, None), None, None),
        ("packageF", ("project", None, None), None, None),
        ("packageG", ("project", None, None), "stepA", None),
        ("packageH", ("project", None, None), None, "softwareA"),
        ("packageI", ("project", None, None), "stepA", "softwareB"),
        ("packageJ", ("project", "category", None), None, None),
        ("packageK", ("project", "category", None), None, None),
        ("packageL", ("project", "category", None), "stepA", None),
        ("packageM", ("project", "category", None), None, "softwareA"),
        ("packageN", ("project", "category", None), "stepA", "softwareB"),
        ("packageO", ("project", "category", "entity"), None, None),
        ("packageP", ("project", "category", "entity"), "stepA", None),
        ("packageQ", ("project", "category", "entity"), None, "softwareA"),
        ("packageR", ("project", "category", "entity"), "stepA", "softwareB"),
    ],
)
@pytest.mark.freeze_time("2020-01-01")
def test_remove_package(
    mocker: object,
    mock_rez_config: object,
    package_name: str,
    package_context: tuple[str, str, str],
    package_step: str,
    package_software: str,
) -> None:
    """Tests the removal of a package for a combination of situations.

    Warning:
        Validation is disabled.

    Args:
        mocker (object): Mocked object.
        mock_rez_config (object): Mocked rez configuration.
        package_name (str): Package name.
        package_context (tuple): Package context.
        package_step (str): Package step.
        package_software (str): Package software.

    """
    mocker.patch("getpass.getuser", return_value="user")

    with ProductionResolverDatabase(load_production=False) as database:
        database.initialize()

        package_id = database.add_package(
            package_context,
            package_name,
            step=package_step,
            software=package_software,
            validate=False,
        )

        # Get the context id to make sure a context is created if not.
        context_id = database.cursor.execute(
            "SELECT context_id FROM context WHERE project {project} AND category {category} AND entity {entity};".format(
                project=(
                    f"= '{package_context[0]}'" if package_context[0] else "IS NULL"
                ),
                category=(
                    f"= '{package_context[1]}'" if package_context[1] else "IS NULL"
                ),
                entity=(
                    f"= '{package_context[2]}'" if package_context[2] else "IS NULL"
                ),
            )
        ).fetchone()[0]

        assert (
            context_id,
            package_name,
            package_step,
            package_software,
        ) == database.cursor.execute(
            f"SELECT context_id, name, step, software FROM package WHERE rowid = '{package_id}';"
        ).fetchone()

        database.remove_package(
            package_context,
            package_name,
            step=package_step,
            software=package_software,
            validate=False,
        )
        assert not database.cursor.execute(
            f"SELECT name, step, software FROM package WHERE rowid = '{package_id}';"
        ).fetchone()

        database.save()

        assert database.cursor.execute(
            "SELECT * FROM history ORDER BY rowid DESC LIMIT 1"
        ).fetchall()[0] == (
            "user",
            ",".join([context for context in package_context if context]),
            package_name,
            package_step or "",
            package_software or "",
            HistoryEditOperation.UNINSTALL.value,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "(2/2)",
        )


def test_remove_package_with_validation_valid(
    mocker: object, mock_rez_config: object
) -> None:
    """Tests the removal of a package with validation.

    Args:
        mocker (object): Mocked object.
        mock_rez_config (object): Mocked rez configuration.
    """
    package_name = "anotherTool"

    mocker.patch(
        "rezplugins.command.production_resolver_lib.ProductionResolverDatabase.validate_context",
        return_value=(True, None),
    )

    with ProductionResolverDatabase(load_production=False) as database:
        database.initialize()

        package_id = database.add_package(
            [None, None, None],
            package_name,
            step=None,
            software=None,
            validate=False,
        )
        assert (
            package_name,
            None,
            None,
        ) == database.cursor.execute(
            f"SELECT name, step, software FROM package WHERE rowid = '{package_id}';"
        ).fetchone()

        database.remove_package(
            (None, None, None),
            package_name,
            step=None,
            software=None,
            validate=True,
        )
        assert not database.cursor.execute(
            f"SELECT name, step, software FROM package WHERE rowid = '{package_id}';"
        ).fetchone()


def test_remove_package_errors(mocker: object, mock_rez_config: object) -> None:
    """Tests the removal of a package with an invalid package.

    Args:
        mocker (object): Mocked object.
        mock_rez_config (object): Mocked rez configuration.
    """

    with ProductionResolverDatabase(load_production=False) as database:
        database.initialize()

        invalid_context = ("unknownProject", None, None)
        with pytest.raises(
            ValueError,
            match=f"Context '{','.join([context for context in invalid_context if context])}' doesn't exist.",
        ):
            database.remove_package(invalid_context, "packageA", validate=False)

        with pytest.raises(
            ValueError, match="Package 'invalidPackage' doesn't exists."
        ):
            database.remove_package((None, None, None), "invalidPackage", validate=True)

    package_name = "anotherTool"
    exception = RezError("Mocked message")

    mocker.patch(
        "rezplugins.command.production_resolver_lib.ProductionResolverDatabase.validate_context",
        return_value=(False, exception),
    )

    with pytest.raises(RezError):
        with ProductionResolverDatabase(load_production=False) as database:
            database.initialize()

            database.add_package(
                [None, None, None],
                package_name,
                step=None,
                software=None,
                validate=False,
            )

            database.remove_package(
                (None, None, None),
                package_name,
                step=None,
                software=None,
                validate=True,
            )
