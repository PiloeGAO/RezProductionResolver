"""Production Resolver Library.

This module provides a `ProductionResolverDatabase` class to manage SQLite-based
package context configurations for Rez production environments. It supports
context-aware package management, validation, and deployment workflows.
"""

import dataclasses
import os
import sqlite3
import getpass

from copy import copy
from datetime import datetime
from enum import IntEnum
from pathlib import Path
from typing import Self


def get_rez_config():
    """Gets the production resolver configuration.

    Returns:
        :class:`rez.utils.data_utils.RO_AttrDictWrapper`: The production resolver configuration.
    """
    from rez.config import config

    # Validate that the config contains the expected plugin path
    if not hasattr(config.plugins.command, "production_resolver"):
        raise ValueError("Rez configuration missing production_resolver plugin.")

    return config.plugins.command.production_resolver


class HistoryEditOperation(IntEnum):
    """Enumeration of possible operations for history edits.

    This enum defines the types of operations that can be recorded in the
    production resolver's history. Each value corresponds to a specific
    action performed on a package context.

    Attributes:
        INSTALL (int): Represents an installation operation (value 1).
        UNINSTALL (int): Represents an uninstallation operation (value 2).

    Example:
        >>> HistoryEditOperation.INSTALL
        <HistoryEditOperation.INSTALL: 1>
    """

    INSTALL = 1
    UNINSTALL = 2


@dataclasses.dataclass
class HistoryEdit:
    """Data container for recording history edits in the production resolver.

    This class captures metadata about changes made to package contexts,
    including the operation type (install/uninstall), associated package,
    and contextual information.

    Attributes:
        context (tuple[str | None, str | None, str | None]):
            Production context tuple (project, category, entity).
            May contain None values for unset levels.
        package_name (str | None): Name of the package being modified.
        step (str | None): Pipeline step associated with the operation.
        software (str | None): Software context for the operation.
        operation (:class:`HistoryEditOperation`):
            Type of operation (INSTALL/UNINSTALL). Defaults to INSTALL.

    Example:
        >>> HistoryEdit(
        ...     context=("project", "assets", "character"),
        ...     package_name="maya-2024",
        ...     operation=HistoryEditOperation.INSTALL
        ... )
        HistoryEdit(context=('project', 'assets', 'character'), package_name='maya-2024', step=None, software=None, operation=<HistoryEditOperation.INSTALL: 1>)
    """

    context: tuple[str | None, str | None, str | None] = ()
    package_name: str | None = None
    step: str | None = None
    software: str | None = None
    operation: HistoryEditOperation = HistoryEditOperation.INSTALL


class ProductionResolverDatabase:
    """The Production Resolver database manager.

    Example:
        You can access and edit the database through this class using a context manager:

        .. code-block:: python

            with ProductionResolverDatabase() as db:
                db.initialize()
                db.insert_context("project", "category", "entity")
                db.add_package(("project", "category", "entity"), "packageA")
                db.save()
                db.deploy()

    Args:
        load_production (bool, optional): Whether or not to load the production database. Defaults to True.

    Attributes:
        production_database_path (:class:`pathlib.Path`): The path to the production database.
        staging_path (:class:`pathlib.Path`): The path to the staging database.
        history_folder_path (:class:`pathlib.Path`): The path to the backup folder.

    """

    def __init__(self, load_production=True):
        """Initializes the production resolver database manager."""
        self.__settings = get_rez_config()
        self.__load_production = load_production
        self.__edits = None

        self.production_database_path = Path(self.__settings.production_database)
        self.staging_path = (
            Path(self.__settings.get("staging_database", ""))
            if self.__settings.get("staging_database", None)
            else (
                self.production_database_path.parent
                / f"staging.{os.path.split(self.production_database_path)[1]}"
            )
        )
        self.history_folder_path = (
            Path(self.__settings.get("history_folder", ""))
            if self.__settings.get("history_folder", None)
            else self.production_database_path.parent / "history"
        )

        self.connection = None
        self.cursor = None

    def __enter__(self) -> Self:
        """
        Enters the context manager.

        Returns:
            :class:`ProductionResolverDatabase`: The production resolver database manager.
        """
        if self.__load_production:
            self.connection = sqlite3.connect(self.production_database_path)
        else:
            self.connection = sqlite3.connect(self.staging_path)
        self.cursor = self.connection.cursor()

        self.__edits = []
        return self

    def __exit__(self, *_) -> None:
        """Exits the context manager."""
        self.connection.close()
        self.connection = None
        self.cursor = None
        self.__edits = None

    @property
    def edits(self) -> list[HistoryEdit]:
        """list[:class:`HistoryEdit`]: Returns the edits from the database not saved."""
        return self.__edits

    def exists(self) -> bool:
        """Check if the database exists.

        Returns:
            bool: True if the database exists.
        """
        if self.__load_production:
            return self.production_database_path.exists()
        else:
            return self.staging_path.exists()

    def initialize(self) -> None:
        """Creates all the necessary tables for the production resolver.

        Note:
            This method should only be called once, as it initializes the
            database with default values.
        """
        # Create the tables.
        self.cursor.execute(
            "CREATE TABLE IF NOT EXISTS context(context_id INTEGER PRIMARY KEY AUTOINCREMENT, project TEXT, category TEXT, entity TEXT)"
        )
        self.cursor.execute(
            "CREATE TABLE IF NOT EXISTS package(context_id INTEGER, name TEXT, step TEXT, software TEXT, FOREIGN KEY(context_id) REFERENCES context(context_id))"
        )
        self.cursor.execute(
            "CREATE TABLE IF NOT EXISTS history(user TEXT, context TEXT, package_name TEXT, step TEXT, software TEXT, operation INT, date TIMESTAMP, comment TEXT)"
        )

        # Setup initial values.
        self.cursor.execute(
            "INSERT INTO context(project, category, entity) VALUES (NULL, NULL, NULL)"
        )

        self.save()

    def save(self, store_history=True, comment="") -> None:
        """Commits the current database transaction.

        Args:
            store_history (bool, optional): Whether or not to store the history database. Defaults to True.
            comment (str, optional): A comment to add in the history table. Defaults to "".

        Note:
            This method should be called after any changes to the database.
        """
        if store_history:
            for index, edit_data in enumerate(self.__edits):
                edits = (
                    getpass.getuser(),
                    ",".join(
                        [
                            context_name
                            for context_name in edit_data.context
                            if context_name
                        ]
                    ),
                    edit_data.package_name,
                    edit_data.step or "",
                    edit_data.software or "",
                    edit_data.operation.value,
                    datetime.now(),
                    comment + f"({index+1}/{len(self.__edits)})",
                )
                self.cursor.execute(
                    "INSERT INTO history(user, context, package_name, step, software, operation, date, comment) VALUES (?, ?, ?, ?, ?, ?, ?, ?);",
                    edits,
                )

        self.__edits = []
        self.connection.commit()

    def _compute_history_database_path(self) -> Path:
        """Compute the path to the history database.

        Returns:
            :class:`pathlib.Path`: Path to the history database.
        """
        path = (
            self.history_folder_path
            / f"{datetime.now().strftime('%y_%m_%d_%H_%M_%S_%f')}.db"
        )
        return path

    def deploy(self) -> None:
        """Deploys the current database to production, optionally creating a backup of the existing production database.

        If the 'keep_history' configuration is enabled, a timestamped backup of the production database is created. The current database connection is then copied to the production database.

        Note:
            Backup files are saved in the :attr:`history_folder_path` directory with filenames formatted as ``YY_MM_DD_HH_MM_SS_ffff.db`` where ``ffff`` represents microseconds.

        Raises:
            RuntimeError: If the currently edited database is a production database.
            :class:`sqlite3.OperationalError`: If an error occurs during database operations.
        """
        if self.__load_production:
            raise RuntimeError("Cannot deploy a production database.")

        if bool(get_rez_config().keep_history):
            if not os.path.exists(self.history_folder_path):
                os.makedirs(self.history_folder_path, exist_ok=True)

            db_backup_path = self._compute_history_database_path().as_posix()

            with sqlite3.connect(self.production_database_path) as production_db:
                with sqlite3.connect(db_backup_path) as backup_db:
                    production_db.backup(backup_db)

        with sqlite3.connect(self.production_database_path) as production_db:
            self.connection.backup(production_db)

    def insert_context(self, *contexts: str) -> int | None:
        """Insert a context into the database.

        Args:
            *contexts (str): The context to add to the database.

        Returns:
            int | None: Index of the inserted context.
        """
        production_context = self.sanitize_context(*contexts)

        return self.cursor.execute(
            "INSERT INTO context(project, category, entity) VALUES(?, ?, ?) RETURNING context_id;",
            (production_context[0], production_context[1], production_context[2]),
        ).fetchone()[0]

    def get_context_row_id(self, *contexts: str) -> int | None:
        """Gets the row ID of a context in the database.

        Args:
            *contexts (str): The context to retrieve.

        Returns:
            int | None: The row ID of the context.
        """
        production_context = self.sanitize_context(*contexts)

        # Build conditions dynamically with placeholders
        conditions = []
        params = []

        if production_context[0] is not None:
            conditions.append("project = ?")
            params.append(production_context[0])
        else:
            conditions.append("project IS NULL")

        if production_context[1] is not None:
            conditions.append("category = ?")
            params.append(production_context[1])
        else:
            conditions.append("category IS NULL")

        if production_context[2] is not None:
            conditions.append("entity = ?")
            params.append(production_context[2])
        else:
            conditions.append("entity IS NULL")

        query = "SELECT context_id FROM context WHERE " + " AND ".join(conditions)
        result = self.cursor.execute(query, params).fetchall()
        return next(iter(result), (None,))[0]

    @staticmethod
    def sanitize_context(*contexts: str) -> tuple[str | None, str | None, str | None]:
        """Converts an arbitrary number of context string to a production context tuple.

        Example:
            >>> sanitize_context("studio", "project")
            ("studio", "project", None)

        Args:
            *contexts (str): List of context IDs.

        Raises:
            ValueError: A context can only have up to 3 context levels.

        Returns:
            tuple[str | None, str | None, str | None]: Production context tuple."""
        if len(contexts) > 3:
            raise ValueError("A context can only 0 to 3 production environments.")

        production_context = []
        production_context.extend(contexts)
        production_context = production_context + [
            None for _ in range(3 - len(production_context))
        ]
        return tuple(production_context)

    def get_package_list(
        self, *contexts: str, step=None, software=None, validate=True
    ) -> tuple[str]:
        """Gets the package list of a context.

        Notes:
            - We apply packages ontop of another by keeping the search order (studio, project, category and entity).

        Args:
            *contexts (str): The contexts to retrieve.
            step (str, optional): The step of the packages. Defaults to None.
            software (str, optional): The software of the packages. Defaults to None.
            validate (bool, optional): Whether to validate the packages. Defaults to True.

        Returns:
            tuple: The package list of the context.
        """
        production_context = self.sanitize_context(*contexts)

        # Do a query on each production level to get context indexes : studio, project, category and entity.
        context_row_ids = [
            self.get_context_row_id(None, None, None),
            self.get_context_row_id(production_context[0], None, None),
            self.get_context_row_id(production_context[0], production_context[1], None),
            self.get_context_row_id(
                production_context[0], production_context[1], production_context[2]
            ),
        ]

        context_row_ids = list(
            dict.fromkeys(
                [value for value in context_row_ids if value]
            )  # Remove duplicates but keep the order in the context stack.
        )

        packages = []

        # Define all the combinations of step/software queries ontop of simple context fetch.
        lookup_steps = {
            "AND step IS NULL AND software IS NULL": [],
        }

        if step:
            lookup_steps["AND step = ? AND software IS NULL"] = [str(step)]
        if software:
            lookup_steps["AND step IS NULL AND software = ?"] = [str(software)]
        if step and software:
            lookup_steps["AND step = ? AND software  = ?"] = [
                str(step),
                str(software),
            ]

        for context_id in context_row_ids:
            base_attributes = [context_id]
            for lookup_step, lookup_attributes in lookup_steps.items():
                query_attributes = copy(base_attributes)
                query_attributes.extend(lookup_attributes)

                query_result = self.cursor.execute(
                    f"SELECT name from package WHERE context_id = ? {lookup_step};",
                    query_attributes,
                )

                packages.extend(
                    [pck[0] for pck in query_result.fetchall()] if query_result else []
                )

        if validate:
            validation_status, message = self.validate_context(*packages)
            if not validation_status:
                raise ValueError(f"Package list can't be validated: {message}")

        return tuple(dict.fromkeys(packages))

    @staticmethod
    def validate_context(*packages: str) -> tuple[bool, Exception]:
        """Validates the production context.

        Args:
            *packages (str): The packages to validate.

        Returns:
            tuple[bool, :class:`rez.exceptions.RezError`]: A boolean indicating whether the validation was successful and an optional exception.
        """
        from rez.exceptions import RezError
        from rez.resolved_context import ResolvedContext
        from rez.resolver import ResolverStatus

        try:
            rez_context = ResolvedContext(packages)
            rez_context.validate()
            return (rez_context.status == ResolverStatus.solved, None)
        except RezError as rez_error:
            return (False, rez_error)

    def add_package(
        self,
        contexts: tuple[str | None, str | None, str | None],
        package_name: str,
        step: str = None,
        software: str = None,
        validate: bool = True,
    ) -> int:
        """Adds a package to the database under the specified context.

        The package is inserted into the 'package' table with the given
        context ID, step, and software. If validation is enabled, it ensures
        the package is valid using Rez's ResolvedContext.

        Args:
            contexts (tuple[str | None, str | None, str | None]): The production context tuple.
            package_name (str): The name of the package to add.
            step (str, optional): The step this package is associated with.
            software (str, optional): The software this package is associated with.
            validate (bool, optional): Whether to validate the package using Rez.
                Defaults to True.

        Raises:
            ValueError: If the package fails validation or if the context does not exist.

        Returns:
            int: Index of the added package.
        """
        if validate:
            all_packages = list(
                self.get_package_list(
                    *contexts,
                    step=step,
                    software=software,
                    validate=False,  # We don't validate since the validation will be performed later in the process.
                )
            )
            all_packages.append(package_name)
            validation_status, message = self.validate_context(*all_packages)
            if not validation_status:
                raise message

        context_id = self.get_context_row_id(*contexts)
        if not context_id:
            context_id = self.insert_context(*contexts)

        self.cursor.execute(
            "INSERT INTO package (context_id, name, step, software) VALUES (?, ?, ?, ?);",
            (context_id, package_name, step, software),
        )

        self.__edits.append(
            HistoryEdit(
                contexts,
                package_name,
                step,
                software,
                HistoryEditOperation.INSTALL,
            )
        )

        return self.cursor.lastrowid

    def remove_package(
        self,
        contexts: tuple[str | None, str | None, str | None],
        package_name: str,
        step: str = None,
        software: str = None,
        validate: bool = True,
    ) -> None:
        """Removes a package from the database under the specified context.

        The package is removed from the 'package' table with the given
        context ID, step, and software. If validation is enabled, it ensures
        the package is valid using Rez's ResolvedContext.

        Args:
            contexts (tuple[str | None, str | None, str | None]): The production context tuple.
            package_name (str): The name of the package to remove.
            step (str, optional): The step this package is associated with.
            software (str, optional): The software this package is associated with.
            validate (bool, optional): Whether to validate the package using Rez.
                Defaults to True.

        Raises:
            ValueError: If the package fails validation or if the context does not exist or if the package does not exist.
        """

        context_id = self.get_context_row_id(*contexts)
        if not context_id:
            raise ValueError(
                f"Context '{','.join([context for context in contexts if context])}' doesn't exist."
            )

        query = "SELECT rowid FROM package WHERE name = ? AND context_id = ? "
        query_attributes = [package_name, context_id]

        if step is not None:
            query += "AND step = ? "
            query_attributes.append(step)
        else:
            query += "AND step IS NULL "

        if software is not None:
            query += "AND software = ? "
            query_attributes.append(software)
        else:
            query += "AND software IS NULL "

        query += ";"

        package_row_id = next(
            iter(
                self.cursor.execute(
                    query,
                    query_attributes,
                ).fetchall()
            ),
            (None,),
        )[0]
        if not package_row_id:
            raise ValueError(f"Package '{package_name}' doesn't exists.")

        if validate:
            all_packages = list(
                self.get_package_list(
                    *contexts,
                    step=step,
                    software=software,
                    validate=False,  # We don't validate since the validation will be performed later in the process.
                )
            )
            all_packages.remove(package_name)
            validation_status, message = self.validate_context(*all_packages)
            if not validation_status:
                raise message

        self.cursor.execute(f"DELETE FROM package WHERE rowid = ?;", (package_row_id,))

        self.__edits.append(
            HistoryEdit(
                contexts,
                package_name,
                step,
                software,
                HistoryEditOperation.UNINSTALL,
            )
        )
