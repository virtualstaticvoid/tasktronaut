Getting Started with Tasktronaut
=================================

Welcome to Tasktronaut!

This guide will help you install the library, set up your first process, and run it successfully.

Installation
------------

Prerequisites
~~~~~~~~~~~~~

Tasktronaut requires:

- Python 3.7 or higher
- pip (Python package manager)

Installing from PyPI
~~~~~~~~~~~~~~~~~~~~

The easiest way to install Tasktronaut is using pip:

.. code-block:: bash

    pip install tasktronaut[rq]

For a specific version:

.. code-block:: bash

    pip install tasktronaut[rq]==0.3.0

Installing with Optional Dependencies
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Tasktronaut may offer optional extras for extended functionality. Install them as follows:

.. code-block:: bash

    pip install tasktronaut[dev]
    pip install tasktronaut[docs]

Installing from Source
~~~~~~~~~~~~~~~~~~~~~~

To install the development version from the repository:

.. code-block:: bash

    git clone https://github.com/virtualstaticvoid/tasktronaut.git
    cd tasktronaut
    uv sync

Verifying Your Installation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Verify the installation was successful by importing Tasktronaut in a Python shell:

.. code-block:: python

    >>> import tasktronaut
    >>> print(tasktronaut.__version__)
    x.x.x

If you see the version number without errors, you're ready to go!


Your First Process
------------------

Creating a Simple Process
~~~~~~~~~~~~~~~~~~~~~~~~~~

Let's create a basic process with three sequential tasks. Create a file called ``my_first_process.py``:

.. code-block:: python

    from tasktronaut import ProcessDefinition, Builder

    class GreetingProcess(ProcessDefinition):
        """A simple process that greets the user."""

        def define_process(self, builder: Builder):
            builder.task(self.say_hello)
            builder.task(self.say_name)
            builder.task(self.say_goodbye)

        def say_hello(self):
            print("Hello!")

        def say_name(self, name: str = "World", **kwargs):
            print(f"Nice to meet you, {name}.")

        def say_goodbye(self):
            print("Goodbye!")
