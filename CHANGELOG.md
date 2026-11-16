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
