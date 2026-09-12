# Odoo debugging reference

Classify the failure before choosing a fix:

- server traceback or RPC error: read the complete Python traceback and locate
  the first project-owned frame;
- module installation or upgrade: validate manifest order, dependencies, XML,
  access data, and registry loading;
- XML parsing or view validation: inspect the inherited architecture and the
  target version's view schema;
- access error: trace model access, record rules, user groups, companies, and
  elevated access;
- frontend or OWL error: inspect the browser console, asset bundle, registry,
  service, component lifecycle, and RPC response;
- database or performance error: inspect the query, indexes, flush state,
  transaction boundary, and query count.

Always separate the transport symptom from the root exception. Inspect all
callers of a shared method before adding a guard, and leave one focused
reproduction or regression test behind.
