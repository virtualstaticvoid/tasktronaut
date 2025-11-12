User Guide
==========

Introduction
------------

Tasktronaut is a Python library for defining and executing processes composed of individual tasks.

It provides a declarative API for organizing tasks into complex workflows with support for sequential
execution, concurrent execution, conditional logic, iteration, and nested sub-processes.

Getting Started
---------------

Basic Process Definition
~~~~~~~~~~~~~~~~~~~~~~~~

To create a process, subclass ``ProcessDefinition`` and implement the ``define_process`` method:

.. code-block:: python

    from tasktronaut import ProcessDefinition, Builder

    class MyProcess(ProcessDefinition):
        def define_process(self, builder: Builder):
            builder.task(self.step_one)
            builder.task(self.step_two)
            builder.task(self.step_three)

        def step_one(self):
            print("Executing step one")

        def step_two(self):
            print("Executing step two")

        def step_three(self):
            print("Executing step three")

The ``builder`` object is used to add tasks and structure your process flow.


Tasks
-----

Defining Tasks
~~~~~~~~~~~~~~

Tasks are methods that perform work within a process. There are several ways to define tasks:

**Simple Methods:**

Any method can be used as a task:

.. code-block:: python

    def my_task(self, *args, **kwargs):
        # Task implementation
        pass

**Context-Aware Methods:**

Methods can receive a ``Context`` object to access execution information:

.. code-block:: python

    from tasktronaut import Context

    def my_task(self, context: Context, **kwargs):
        # Access runtime information via context
        pass

**Task Decorator:**

Use the ``@task`` decorator to add metadata like descriptions:

.. code-block:: python

    from tasktronaut import task

    @task(description="Processes data input")
    def my_task(self, *args, **kwargs):
        pass

    @task()
    def another_task(self):
        pass

    @task
    def simple_task(self):
        pass


Execution Modes
---------------

Sequential Execution
~~~~~~~~~~~~~~~~~~~~

By default, tasks execute one after another in the order they are defined. Set the execution mode explicitly:

.. code-block:: python

    from tasktronaut import ExecutionMode, ProcessDefinition

    class SequentialProcess(ProcessDefinition):
        process_execution_mode = ExecutionMode.SEQUENTIAL

        def define_process(self, builder: Builder):
            builder.task(self.task_a)
            builder.task(self.task_b)
            builder.task(self.task_c)

Tasks execute in order: task_a, then task_b, then task_c.

Concurrent Execution
~~~~~~~~~~~~~~~~~~~~

Execute multiple tasks in parallel:

.. code-block:: python

    class ConcurrentProcess(ProcessDefinition):
        process_execution_mode = ExecutionMode.CONCURRENT

        def define_process(self, builder: Builder):
            builder.task(self.task_a)
            builder.task(self.task_b)
            builder.task(self.task_c)

All three tasks may execute simultaneously.


Process Structure
-----------------

Sequential and Concurrent Blocks
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Group tasks into sequential or concurrent sections within a larger process:

.. code-block:: python

    class MixedProcess(ProcessDefinition):
        def define_process(self, builder: Builder):
            builder.task(self.setup)

            # Run these tasks sequentially
            with builder.sequential() as b:
                b.task(self.step_one)
                b.task(self.step_two)

            # Run these tasks concurrently
            with builder.concurrent() as b:
                b.task(self.parallel_task_a)
                b.task(self.parallel_task_b)

            builder.task(self.cleanup)

This allows fine-grained control over execution flow within a single process.


Input Arguments
---------------

Defining Expected Arguments
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Specify the input arguments your process accepts with type hints:

.. code-block:: python

    import datetime
    from typing import List, Optional

    class ProcessWithArguments(ProcessDefinition):
        def define_process(self, builder: Builder):
            builder.expected_arguments(
                name=str,
                count=int,
                date=datetime.date,
                tags=List[str],
                description=Optional[str],
                data=None,  # Any type accepted
            )
            builder.task(self.process_data)

        def process_data(self, name: str, count: int, **kwargs):
            pass

These arguments are passed to your tasks and can be accessed via keyword arguments or through the Context object.


Conditional Logic
-----------------

Using Options
~~~~~~~~~~~~~

Include or exclude tasks based on boolean options:

.. code-block:: python

    class ConditionalProcess(ProcessDefinition):
        def define_process(self, builder: Builder):
            if builder.option("enable_validation", False):
                builder.task(self.validate_input)

            builder.task(self.process)

            if builder.option("enable_logging", True):
                builder.task(self.log_results)

The first argument is the option name, and the second is the default value. Tasks are only added if the option is True.


Iteration
---------

The Each Pattern
~~~~~~~~~~~~~~~~

Iterate over a collection and execute tasks for each item:

.. code-block:: python

    from typing import Iterator

    class IterativeProcess(ProcessDefinition):
        def items(self, files: List[str], **_) -> Iterator[dict]:
            for file in files:
                yield {"filename": file}

        def define_process(self, builder: Builder):
            for iteration in builder.each(self.items):
                iteration.task(self.process_file)

        def process_file(self, filename: str, **kwargs):
            print(f"Processing {filename}")

The ``items`` method is a generator that yields dictionaries of arguments for each iteration.

**With Descriptions:**

Optionally provide descriptions for each iteration:

.. code-block:: python

    class IterativeProcessWithDescriptions(ProcessDefinition):
        def items(self, files: List[str], **_) -> Iterator[Tuple[dict, str]]:
            for file in files:
                yield ({"filename": file}, f"Processing {file}")

        def define_process(self, builder: Builder):
            for iteration in builder.each(self.items):
                iteration.task(self.process_file)


Transformation
--------------

The Transform Pattern
~~~~~~~~~~~~~~~~~~~~~

Transform input arguments before executing tasks:

.. code-block:: python

    class TransformingProcess(ProcessDefinition):
        def transform_input(self, raw_data: str, **_) -> dict:
            return {
                "processed_data": raw_data.upper(),
            }

        def define_process(self, builder: Builder):
            with builder.transform(self.transform_input) as transformed:
                transformed.task(self.process)

        def process(self, processed_data: str, **kwargs):
            pass

The transform method receives the input arguments and returns a dictionary of transformed arguments.

**With Descriptions:**

Include descriptions for transformed sections:

.. code-block:: python

    class TransformingProcessWithDescription(ProcessDefinition):
        def transform_input(self, item_id: int, **_) -> Tuple[dict, str]:
            return (
                {"processed_id": item_id * 2},
                f"Processing item {item_id}",
            )

        def define_process(self, builder: Builder):
            with builder.transform(self.transform_input) as transformed:
                transformed.task(self.process)


Sub-Processes
-------------

Nesting Processes
~~~~~~~~~~~~~~~~~

Include another ``ProcessDefinition`` as a sub-process:

.. code-block:: python

    class ValidationProcess(ProcessDefinition):
        def define_process(self, builder: Builder):
            builder.task(self.check_schema)
            builder.task(self.check_constraints)

    class MainProcess(ProcessDefinition):
        def define_process(self, builder: Builder):
            builder.task(self.load_data)
            builder.sub_process(ValidationProcess)
            builder.task(self.save_data)

Sub-processes allow you to compose larger workflows from smaller, reusable process definitions.


Advanced Patterns
-----------------

Combining Multiple Patterns
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Complex workflows can combine multiple patterns:

.. code-block:: python

    class ComplexProcess(ProcessDefinition):
        def get_batches(self, items: List[str], **_) -> Iterator[Tuple[dict, str]]:
            for i in range(0, len(items), 10):
                batch = items[i:i+10]
                yield ({"batch": batch}, f"Batch {i//10}")

        def define_process(self, builder: Builder):
            builder.task(self.setup)

            for batch_iter in builder.each(self.get_batches):
                with batch_iter.transform(self.prepare_batch) as prepared:
                    with prepared.concurrent() as b:
                        b.task(self.process_item_a)
                        b.task(self.process_item_b)

            builder.task(self.finalize)

This process iterates over batches, transforms them, and then processes items concurrently within each batch.


Best Practices
--------------

- **Keep tasks focused**: Each task should have a single responsibility.
- **Use descriptions**: Add task descriptions for clarity and debugging.
- **Handle exceptions**: Include error handling within task methods.
- **Leverage context**: Use the Context object to access execution metadata when needed.
- **Organize related tasks**: Use sub-processes to organize large workflows into logical units.
- **Document arguments**: Clearly define expected arguments in ``expected_arguments()``.
- **Use type hints**: Include type hints for better IDE support and documentation.
