Plugin Configuration
====================

In your `rezconfig.py`, you can customize these settings:

.. code-block:: python

   plugins = {
      "command": {
            "production_resolver": {
                  "production_database": "~/packages/package_list.sqlite3",
                  "staging_database": "~/packages/staging.sqlite3",
                  "history_folder": "~/packages/backups",
                  "keep_history": "true"
            }
      }
   }


Database Configuration
----------------------
The plugin uses a SQLite-based database system with three key locations:

1. **Production Database Path**

   - Default location:
      Determined by `rez.config.plugins.command.production_resolver.production_database`
   - Can be customized in your Rez configuration
   - Used for storing finalized package context configurations

2. **Staging Database Path**

   - Auto-generated as: `{production_database}/staging.{production_database}`
   - Can be customized in your Rez configuration:
      Determined by `rez.config.plugins.command.production_resolver.staging_database`
   - Used for temporary modifications before deployment

3. **Backup Folder Path**

   - Auto-generated as: `{production_database}/history`
   - Can be customized in your Rez configuration:
      Determined by `rez.config.plugins.command.production_resolver.history_folder`
   - Stores timestamped backups when history preservation is enabled

History Configuration
---------------------
The plugin provides optional history tracking with these configuration options:

1. **History Preservation**

   - Controlled by: `rez.config.plugins.command.production_resolver.keep_history`
   - When enabled (default):

     - Creates timestamped backups before deployment
     - Backup format: `YY_MM_DD_HH_MM_SS_ffff.db`
     - Stored in the history folder
   - When disabled:

     - No backups are created
     - Deploy directly overwrites production database

2. **History Retention**

   - Not directly controlled by the plugin
   - Manual cleanup required for the history folder
   - Recommended to implement retention policies based on your workflow

Path Resolution Example
-----------------------
Given a production database path of `/project/configs/packages.db`, the plugin will:

- Use staging database: `/project/configs/staging.packages.db`
- Store history in: `/project/configs/history/`
- Create backups like: `/project/configs/history/25_10_28_14_30_00_000000.db`

