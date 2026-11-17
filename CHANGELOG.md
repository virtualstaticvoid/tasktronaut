# Changelog

All notable changes to this project will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased] - YYYY-MM-DD

### Added

### Changed

### Deprecated

### Removed

### Fixed

### Security

## [0.5.0](https://github.com/virtualstaticvoid/tasktronaut/compare/v0.4.0...v0.5.0) - 2026-11-17

### Added

* `tasktronaut.backends.rq.RqQueue` queue class, and `JobScopedReadyJobRegistryMixin` for custom queue classes
  (e.g. `django-rq`'s `DjangoRQ`), which hand off ready dependent jobs via `JobScopedReadyJobRegistry`

### Fixed

* steps of a process could wait up to ten minutes (until RQ worker maintenance) before being enqueued, because
  RQ 3.0 aborts the hand-off of a ready dependent job whenever any other worker concurrently readies or enqueues
  a dependent job on the same queue; workers should use `RqQueue` (e.g. `rq worker --queue-class
  tasktronaut.backends.rq.RqQueue`) as their queue class

## [0.4.0](https://github.com/virtualstaticvoid/tasktronaut/compare/v0.3.0...v0.4.0) - 2026-11-16

### Added

* `rq` optional dependency extra (`pip install tasktronaut[rq]`), as already described in the documentation

### Changed

* require `rq>=3.0.0` (and `django-rq>=4.2.0` for development)

### Fixed

* jobs which completed successfully could be left in RQ's started job registry, and later marked as failed
  with `AbandonedJobError`, when RQ < 3.0 retried the success handling transaction after a `WatchError`

## [0.3.0](https://github.com/virtualstaticvoid/tasktronaut/compare/v0.2.0...v0.3.0) - 2025-11-12

### Added

* `context` argument to the `around_task` hook method
* `tasktronaut.__version__` attribute
* library documentation, including getting started guide, user guide and API reference
* greeting example process

### Removed

* **breaking**: `ProcessDefinition.create_process` is no longer a public method;
  use `ProcessDefinition.build()` to create a process instead

### Fixed

* task functions without a `context` parameter failed when executed

## [0.2.0](https://github.com/virtualstaticvoid/tasktronaut/compare/v0.1.0...v0.2.0) - 2025-11-07

### Changed

* move source to `src` directory
* initial documentation

## [0.1.0](https://github.com/virtualstaticvoid/tasktronaut/compare/v0.0.0...v0.1.0) - 2025-11-07

### Added

Initial release
