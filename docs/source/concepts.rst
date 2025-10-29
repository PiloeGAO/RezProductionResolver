Concepts
========

Context Management
------------------
Contexts follow a hierarchical structure: `[project] [category] [entity]`

Examples:

- Studio-level: ``rez manage ...``
- Project-level: ``rez manage ... my_project``
- Category-level: ``rez manage ... my_project assets``
- Entity-level: ``rez manage ... my_project assets character``

.. image:: _static/context_hierarchy_diagram.svg
   :alt: Context hierarchy diagram

Production Resolver Architecture
--------------------------------
This plugin provides a database-driven approach to manage Rez package contexts. Key components include:

- **Context Management**: Hierarchical organization of packages through project, category, and entity levels
- **Database Operations**: SQLite-based storage for context configurations
- **Validation System**: Automatic validation of package combinations using Rez's resolver
- **Deployment Workflow**: Staging and deployment system with optional history preservation

Database Structure
------------------
The plugin maintains three main tables:

1. **context**: Stores context definitions (project, category, entity)
2. **package**: Maps packages to contexts with optional step/software metadata
3. **history**: Tracks changes with user comments and timestamps

Key Features
------------
- Context-aware package management
- Multi-level inheritance (studio → project → category → entity)
- Step/software specific package associations
- Automatic validation of package combinations
- History tracking with optional backups