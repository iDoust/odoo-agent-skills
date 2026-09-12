# Upstream and migration notes

## Source

- Original repository: https://github.com/letzdoo/claude-marketplace
- Fork: https://github.com/iDoust/odoo-agent-skills
- Original license: MIT
- Primary imported component: `plugins/odoo-development`

The original project is a Claude Code marketplace containing Odoo development,
Doodba, query, and token-optimization plugins. This fork extracts the reusable
Odoo knowledge into standard, vendor-neutral Agent Skills.

## Direction of this fork

The universal core officially supports:

- Odoo 17
- Odoo 18
- Odoo 19

The core is organized around workflow instructions in `skills/` and reusable
knowledge in `references/`. It is intended to work with Agent Skills-compatible
coding agents without requiring a particular vendor CLI, command system,
subagent mechanism, hook, or plugin marketplace.

## Major differences

- Odoo 17–19 focus
- Vendor-neutral core
- Standard Agent Skills entry point at `skills/odoo-development/SKILL.md`
- Shared knowledge separated from workflow instructions
- Version deltas separated from shared guidance
- Reusable Doodba, query, and output-optimization capabilities moved into
  universal skills
- Claude-specific marketplace wrappers removed from the active repository
- Legacy Odoo material is not automatically loaded by the universal core
- Codex-compatible and other Agent Skills-compatible use is supported by the
  core layout, without a required CLI adapter

## Migration status

The migration is complete for the universal Odoo 17–19 core:

- the old root marketplace and `plugins/odoo-development` tree are no longer
  part of the canonical layout;
- reusable ORM, view, OWL, security, testing, operations, integration,
  migration, performance, and module knowledge lives under `references/`;
- development, debugging, review, security, testing, and upgrade workflows
  live under `skills/`;
- Community and Enterprise source locations were checked for Odoo 17, 18, and
  19 and recorded in `references/versions/source-matrix.md`; and
- a dependency-free validator checks required skills, links, frontmatter, and
  vendor-neutral core content.

The root `.claude-plugin` directory was deliberately removed. The remaining
Claude marketplace wrapper has been archived outside the repository after its
reusable capabilities were moved into universal skills. No adapter is required
for the active core.

The local Odoo 17, 18, and 19 checkouts expose version metadata and source
trees, but their `.git` directories do not contain usable repository metadata;
therefore this project records source paths and manifest inventories rather
than claiming local branch or remote state.

## Knowledge migration rules

When moving upstream material:

1. Keep generic Odoo 17–19 knowledge in shared references.
2. Keep meaningful version differences in `references/versions/`.
3. Preserve migration guidance only when it helps a supported upgrade path.
4. Remove unsupported-only material after checking that it is not reusable.
5. Remove vendor invocation language from universal paths.
6. Verify version-specific claims against the target Odoo source and official
   documentation before treating them as requirements.

## Attribution

The MIT license and required copyright notice in [LICENSE](LICENSE) are
preserved. New files in the universal core are part of this fork and retain
the repository license.
