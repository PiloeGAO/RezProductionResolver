Getting started
===============

Manage Commands
----------------

The plugin provides a `rez manage` command for managing production package configurations. Here's the typical workflow:

1. **Initialize database**
2. **Modify package configurations**
3. **Save your changes into staging**
4. **Deploy changes to production**

.. image:: _static/workflow_diagram.svg
   :alt: Staging and Deployment Workflow


Database initialization (`\-init/\-\-initialize`)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Initialize the staging database with the necessary tables.

.. code-block:: bash

    rez manage --initialize

.. important::
    We not do any checks, you must use this command with care since you can break your staging database.

Install Packages (`\-i/\-\-install`)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Installs the `maya-2024` package for Maya software in the "character" asset context of "my_project".

.. code-block:: bash

    rez manage --install maya-2024 --software maya my_project assets character


Uninstall Packages (`\-ui/\-\-uninstall`)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Removes the `houdini-19` package from the studio-level lighting context.

.. code-block:: bash

   rez manage --uninstall houdini-19 --step lighting

.. important::
   The `uninstall` operation is *always* performed before installs.

List Installed Packages (`\-ls/\-\-list`)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Lists all Blender modeling packages in the "project" context of "my_game".

.. code-block:: bash

   rez manage --list --step modeling --software blender my_game project

Deploy Changes (`\-\-deploy`)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Deploys staging changes to production (requires confirmation unless using `\-f/\-\-force` flag).

.. code-block:: bash

   rez manage --deploy

Validation
^^^^^^^^^^
All package operations include automatic validation using Rez's resolver. If conflicts are found, operations will fail with detailed error messages unless the `\-f/\-\-force` flag is used.

Staging and Deployment
^^^^^^^^^^^^^^^^^^^^^^
Changes are applied to a staging database first. Use `\-\-deploy` to promote changes to production. When history preservation is enabled (default), previous production states are archived with timestamps.

.. note::
   *Staging* is a temporary workspace for testing changes before applying them to *production*.

Advanced Options
^^^^^^^^^^^^^^^^
- **Force operations**: Use `\-f/\-\-force` flag to bypass confirmation prompts and rez validation
- **Filter by step**: `\-s/\-\-step [step]` (e.g. modeling, lighting)
- **Filter by software**: `\-sw/\-\-software [software]` (e.g. maya, blender)

Example with multiple operations:

Installs Python 3.9 and uninstalls Python 3.8 in the project context without confirmation.

.. code-block:: bash

   rez manage --install python-3.9 --uninstall python-3.8 --force my_project

Resolve Commands
----------------

The `rez resolve` command:

- Queries the database for the current package configuration
- Builds a Rez `ResolvedContext` for validation and execution
- Supports two execution modes:

  - **Terminal mode** (no software specified): Opens an environment shell with all packages
  - **Software mode** (software name): Executes the specified software's default command

- Does not modify any database state

To start a software:

.. code-block:: bash

   rez resolve my_project --software blender

.. tip::
   The software name is used in the command execution, the executable must be in `$PATH` or set as an alias.

To start a new rez resolved terminal:

.. code-block:: bash

   rez resolve my_project

Advanced Options
^^^^^^^^^^^^^^^^
- **Filter by step**: `\-s/\-\-step [step]` (e.g. modeling, lighting)
- **Filter by software**: `\-sw/\-\-software [software]` (e.g. maya, blender)
- **Use the staging database**: `\-stg/\-\-staging`
