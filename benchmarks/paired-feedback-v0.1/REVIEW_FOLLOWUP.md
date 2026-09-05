# Validation follow-up for the factual-lineage candidate

Review follow-up: eight additional validation tests bring the current total to
80 methods (zero skipped, zero expected failures). All pass with and without
Python `-O`; runtime validation in the bridge/report/probe/exporter is now
unconditional. Checkout credential persistence is disabled, output HTML suffixes
are checked before writing, pass counts exclude skipped/expected-failure tests,
and fingerprint paths use POSIX separators. Automated code review is not an
independent scientific replication; no efficacy claim has changed.
