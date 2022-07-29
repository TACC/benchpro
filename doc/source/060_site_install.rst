=================
Site Installation
=================

The BenchPRO site package is available from the benchpro-site_ repo.
You should setup the backend result collection database for your site before proceeding with this installation.

.. _benchpro-site: https://github.com/TACC/benchpro-site

Clone the repo

.. code-block::

   git clone https://github.com/TACC/benchpro-site
   cd benchpro-site

Setup your site specific settings in :code:`site.sh`. 

Run the installation script with

.. code-block::

   ./install [ssh-key]

You will be prompted to provide the database user's private key generated in the datase installation process. Alternatively you can provide it on the command line as the first argument to the install script.



