# Change Log
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/)
and this project adheres to [Semantic Versioning](http://semver.org/).

## [1.0.0] - 2026-07-04
### Changed
- Ported to helga 2.x / Python 3: replaced MongoDB (pymongo) with PostgreSQL
  via `helga.db.get_connection()`.
- Replaced `requests` dependency with stdlib `urllib.request`.
- Replaced `bson.son.SON` with plain SQL ORDER BY.
- Implemented `redact()` (was a no-op): content inside `[]` is now logged as
  `[REDACTED]`.
- Updated CHANGELOG format.

## [0.2.0] - 2017-08-03
### Added
- search command with dpaste output

## [0.1.0] - 2016-11-06
### Added
- logs messages into redis
