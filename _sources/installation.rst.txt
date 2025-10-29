Installation
============

Prerequisites
-------------
Before installing and using this plugin, you must first setup Rez according to the official documentation:
https://rez.readthedocs.io/en/stable/installation.html

The plugin requires Rez 3.3.0 or higher.

Project Setup
-------------
Clone this repository to your local machine.

Plugin Configuration
--------------------
To make the plugin discoverable by Rez, add the following line to your rezconfig.py file:

.. code-block:: python

   plugin_path = [
       "/path/to/the/installation/RezProductionResolver/src",
   ]

Replace ``/path/to/the/installation/RezProductionResolver`` with the actual path to the plugin directory in your project.

Development
-----------
1. Clone this repository to your local machine
2. Run tests :

   .. code-block:: bash

      pip install -e .[tests]
      cd src
      pytest ../tests

3. Build the documentation :

   .. code-block:: bash

      pip install -e .[docs]
      cd docs
      make html

.. note::
   We are currently only testing the main core library since testing the commands requires a more complex rez setup. Testing the commands would be ideal to ensure consistency and stability, this is planned but no development started yet. Feel free to open a pullrequest and contribute to the project.