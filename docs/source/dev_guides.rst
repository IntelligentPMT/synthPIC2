Developer Guides
================

We have the goal to keep improving ``synthPIC2`` and contributions are very welcome.

Compile Documentation (offline)
-------------------------------
The most current documentation is available at https://intelligentpmt.github.io/synthPIC2.

However, if you want to improve the documentation, you can compile it locally:

* Start the docker container: ::

    docker-compose run app

* Start ``sphinx-autobuild``, which will build the documentation, watch for changes and rebuild if necessary: ::

    sphinx-autobuild docs/source docs/build/html --host 0.0.0.0

* Visit http://localhost:8000/, to see the documentation.

* Refer to the `sphinx tutorial <https://www.sphinx-doc.org/en/master/tutorial/index.html>`_ for more help.

