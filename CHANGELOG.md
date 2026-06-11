# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.1] - 2026-06-11

### Fixed

- Documented index-file link format now wraps link destinations in CommonMark
  angle brackets (`<...>`), so generated index links with spaces and
  parentheses in file names (`{Label} ({Model}).md`) resolve correctly instead
  of being truncated at the literal `)`.
