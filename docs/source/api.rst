Python API
==========

Basic Workflow
--------------
1. Initialize database:

   .. code-block:: python

      from rezplugins.command.production_resolver_lib import ProductionResolverDatabase

      with ProductionResolverDatabase(load_production=False) as db:
          db.initialize()

.. warning::
    Initializing the :class:`ProductionResolverDatabase` without `load_production=False` will allow you to edit the production database directly. This is a bad practice because we always want to make changes in a staging area, test them thoroughly, and then deploy to production when everything is validated.

2. Add packages to a context:

   .. code-block:: python

      with ProductionResolverDatabase(load_production=False) as db:
          [...]
          db.add_package(("my_project", "assets", "character"), "maya-2024", software="maya")

3. Save changes to staging:

   .. code-block:: python

      with ProductionResolverDatabase(load_production=False) as db:
          [...]
          db.save(comment="Your modifications.")

4. Deploy changes to production:

   .. code-block:: python

      with ProductionResolverDatabase(load_production=False) as db:
          [...]
          db.deploy()

Common Operations
-----------------
- **Add Package**:

  .. code-block:: python

     db.add_package(context_tuple, package_name, step=None, software=None)

- **Remove Package**:

  .. code-block:: python

     db.remove_package(context_tuple, package_name, step=None, software=None)

- **Get Package List**:

  .. code-block:: python

     packages = db.get_package_list(*context_elements)

Methods and Classes
-------------------

.. automodule:: rezplugins.command.production_resolver_lib
   :members:
