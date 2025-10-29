Rez Production Resolver documentation
=====================================

A `Rez <https://github.com/AcademySoftwareFoundation/rez/>`__ plugin for managing production environments through staged changes, tailored for animation/VFX workflows where stability is critical.

.. image:: https://github.com/PiloeGAO/RezProductionResolver/actions/workflows/ci-tests.yml/badge.svg
   :target: https://github.com/PiloeGAO/RezProductionResolver/actions/workflows/ci-tests.yml
   :alt: CI Tests Status

.. image:: https://github.com/PiloeGAO/RezProductionResolver/actions/workflows/coverage.yml/badge.svg
   :target: https://github.com/PiloeGAO/RezProductionResolver/actions/workflows/coverage.yml
   :alt: Test Coverage

.. image:: https://github.com/PiloeGAO/RezProductionResolver/actions/workflows/docs-deploy.yml/badge.svg
   :target: https://github.com/PiloeGAO/RezProductionResolver/actions/workflows/docs-deploy.yml
   :alt: Docs Deployment

Key Features
^^^^^^^^^^^^
- SQLite-backed environment storage
- Context-aware package stacking (studio → project → category → entity)
- Automatic validation during install/uninstall
- Optional history backups on deploy

Package Management Workflow
^^^^^^^^^^^^^^^^^^^^^^^^^^^
- Stage changes with rez manage --install/uninstall
- Resolve with `rez resolve --staging` (builds Rez context from staging)
- Deploy to production when validated

Start rez contexts in specific contexts
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Launches software using the configurations:

.. code-block:: bash

   rez resolve <my_project> <my_category> <my_entity> blender -s lighting

List all the packages used in a particular context:

.. code-block:: bash

   rez manage <my_project> <my_category> <my_entity> --step modeling --software blender --list


Why Use This?
^^^^^^^^^^^^^
- Maintains pipeline stability for animation/VFX workflows with staged validation
- Prevents production environment breakage during testing
- Ensures validation occurs before packages are added or removed
- Isolates development changes from live pipelines

Quickstart
^^^^^^^^^^
Get started with the plugin using these simple steps:

1. Initialize the staging database:

   .. code-block:: bash

      rez manage --initialize

2. Install a package for a specific context:

   .. code-block:: bash

      rez manage --install maya-2024 --software maya my_project assets character

3. Test your staging changes:

   .. code-block:: bash

      rez resolve my_project assets character --software maya --staging

4. Deploy changes to production:

   .. code-block:: bash

      rez manage --deploy

5. Run your favorite software without any fears:

   .. code-block:: bash

      rez resolve my_project assets character --software maya


.. toctree::
   :maxdepth: 2
   :caption: General
   :hidden:

   installation
   getting_started
   concepts

.. toctree::
   :maxdepth: 2
   :caption: Reference
   :hidden:

   plugin_configuration
   api
