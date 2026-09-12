# Changelog

## Unreleased

### Added

- Universal Odoo Agent Skills for Odoo 17, 18, and 19.
- Development, debugging, review, security, testing, and upgrade workflows.
- Optional Doodba indexing, read-only Odoo querying, and output optimization
  skills.
- Shared ORM, views, OWL, security, performance, migration, integration, and
  module references.
- Community and Enterprise source matrix for supported versions.
- Dependency-free core structure validation.
- Deprecation scanner CLI (`scripts/scan_deprecations.py`) with AST and regex
  analysis for Python and XML files targeting Odoo 17, 18, and 19.
- OCA community standards and `openupgradelib` migration guide
  (`references/operations/oca-guidelines.md`).
- Community Edition solutions for Enterprise features
  (`references/modules/community-enterprise-solutions.md`): Financial Reports,
  Barcode Scanning, Multi-tier Approvals, Digital Signatures, and DMS.
- Cross-references from migration, upgrade, review, and development skills to
  the deprecation scanner, OCA guidelines, and CE solutions guide.
- Comprehensive README with full reference index, project structure, and
  quick-start instructions.
- Dedicated directory index hubs: `references/operations/README.md`,
  `references/integrations/README.md`, and `references/versions/README.md`.
- Complete bidirectional cross-referencing across all operation references,
  integration patterns, and version delta documents.
- Expanded `odoo-development`, `odoo-debug`, `odoo-security`, and `odoo-upgrade`
  skill manifests with complete reference coverage.

### Changed

- Moved reusable Odoo knowledge out of the legacy plugin tree.
- Moved reusable Doodba, query, and token-optimization capabilities into
  universal skills.
- Removed the root `.claude-plugin` marketplace coupling and archived the
  remaining Claude-only wrappers outside the active repository.
- Converted absolute `file:///` links in `references/orm/` to portable
  relative markdown links.
- Expanded module references README to list all 20 domain and pattern files.

### Removed

- Unsupported-only Odoo 14–16 material from universal paths.
- Pairwise version dispatchers and vendor-specific Odoo workflow commands from
  the core.
