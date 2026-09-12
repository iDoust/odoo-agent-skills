#!/usr/bin/env python3
"""
Odoo Module Deprecation and Migration Scanner.

Scans Odoo modules (Python and XML files) to detect deprecated APIs, breaking
syntax changes, and version incompatibilities across Odoo 17, 18, and 19.

Zero-dependency: Uses only Python standard library.
"""

from __future__ import annotations

import argparse
import ast
import json
import os
import re
import sys
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass
class Issue:
    file: str
    line: int
    severity: str  # 'ERROR', 'WARNING', 'INFO'
    code: str
    message: str
    recommendation: str


class OdooDeprecationScanner:
    def __init__(self, target_version: str = "19"):
        self.target = target_version
        self.issues: list[Issue] = []

    def scan_path(self, root_path: Path) -> list[Issue]:
        self.issues.clear()
        if root_path.is_file():
            self._scan_file(root_path)
        elif root_path.is_dir():
            for p in sorted(root_path.rglob("*")):
                if p.is_file() and not any(part.startswith(".") for part in p.parts):
                    self._scan_file(p)
        return self.issues

    def _scan_file(self, file_path: Path):
        suffix = file_path.suffix.lower()
        if suffix == ".py":
            self._scan_python(file_path)
        elif suffix == ".xml":
            self._scan_xml(file_path)

    # -------------------------------------------------------------------------
    # Python Scanner
    # -------------------------------------------------------------------------
    def _scan_python(self, file_path: Path):
        try:
            content = file_path.read_text(encoding="utf-8")
        except Exception as e:
            self.issues.append(
                Issue(str(file_path), 0, "ERROR", "FILE_READ_ERR", f"Could not read file: {e}", "")
            )
            return

        # AST-based parsing
        try:
            tree = ast.parse(content, filename=str(file_path))
            self._check_python_ast(file_path, tree, content)
        except SyntaxError as e:
            self.issues.append(
                Issue(str(file_path), e.lineno or 0, "ERROR", "SYNTAX_ERROR", f"Python SyntaxError: {e.msg}", "Fix invalid Python syntax.")
            )

        # Line-by-line regex checks
        lines = content.splitlines()
        for idx, line in enumerate(lines, start=1):
            self._check_python_line(file_path, idx, line)

    def _check_python_ast(self, file_path: Path, tree: ast.AST, content: str):
        is_test_file = "test" in file_path.stem.lower() or "tests" in file_path.parts

        for node in ast.walk(tree):
            # 1. Method definitions
            if isinstance(node, ast.FunctionDef):
                # _name_search deprecated in v18+
                if node.name == "_name_search" and self.target in ("18", "19"):
                    self.issues.append(
                        Issue(
                            str(file_path),
                            node.lineno,
                            "WARNING",
                            "DEPRECATED_NAME_SEARCH",
                            "_name_search() is deprecated in Odoo 18+.",
                            "Override def _search_display_name(self, operator, value) instead.",
                        )
                    )
                # name_get deprecated since 16.4/17
                elif node.name == "name_get":
                    self.issues.append(
                        Issue(
                            str(file_path),
                            node.lineno,
                            "WARNING",
                            "DEPRECATED_NAME_GET",
                            "name_get() is deprecated since Odoo 16.4/17.0.",
                            "Override def _compute_display_name(self) instead.",
                        )
                    )
                # _flush_search deprecated since 17.1
                elif node.name == "_flush_search" and self.target in ("18", "19"):
                    self.issues.append(
                        Issue(
                            str(file_path),
                            node.lineno,
                            "WARNING",
                            "DEPRECATED_FLUSH_SEARCH",
                            "_flush_search() is deprecated.",
                            "Use self.env.execute_query(SQL(...)) which auto-flushes metadata.",
                        )
                    )

            # 2. Imports
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                if isinstance(node, ast.ImportFrom):
                    # from odoo.osv import expression (deprecated in 19)
                    if node.module == "odoo.osv" and self.target == "19":
                        self.issues.append(
                            Issue(
                                str(file_path),
                                node.lineno,
                                "ERROR",
                                "DEPRECATED_OSV_MODULE",
                                "odoo.osv is deprecated in Odoo 19 (emits DeprecationWarning).",
                                "Use 'from odoo.fields import Domain' and pythonic operators (&, |, ~).",
                            )
                        )
                    elif node.module == "odoo.osv.expression" and self.target == "19":
                        self.issues.append(
                            Issue(
                                str(file_path),
                                node.lineno,
                                "ERROR",
                                "DEPRECATED_OSV_EXPRESSION",
                                "odoo.osv.expression is deprecated in Odoo 19.",
                                "Use 'from odoo.fields import Domain' (Domain.AND, Domain.OR, or & / |).",
                            )
                        )

            # 3. Class Attributes
            elif isinstance(node, ast.ClassDef):
                for item in node.body:
                    if isinstance(item, ast.Assign):
                        for target in item.targets:
                            # _sql_constraints deprecated in 19
                            if isinstance(target, ast.Name) and target.id == "_sql_constraints" and self.target == "19":
                                self.issues.append(
                                    Issue(
                                        str(file_path),
                                        item.lineno,
                                        "WARNING",
                                        "DEPRECATED_SQL_CONSTRAINTS",
                                        "_sql_constraints is deprecated in Odoo 19.",
                                        "Define table constraints using models.Constraint instead.",
                                    )
                                )

            # 4. Method Calls
            elif isinstance(node, ast.Call):
                # Dangerous cr.commit() in normal code (excluding tests)
                if not is_test_file and isinstance(node.func, ast.Attribute):
                    if node.func.attr == "commit" and isinstance(node.func.value, ast.Attribute) and node.func.value.attr == "cr":
                        self.issues.append(
                            Issue(
                                str(file_path),
                                node.lineno,
                                "WARNING",
                                "DANGEROUS_CR_COMMIT",
                                "Direct self.env.cr.commit() violates Odoo coding guidelines and breaks tests.",
                                "Use with self.env.cr.savepoint() or an isolated cursor (with self.pool.cursor():).",
                            )
                        )

    def _check_python_line(self, file_path: Path, line_no: int, line: str):
        # 1. Controller routes: type='json' vs type='jsonrpc'
        if "@http.route" in line or "@route(" in line:
            if self.target == "19" and ("type='json'" in line or 'type="json"' in line):
                self.issues.append(
                    Issue(
                        str(file_path),
                        line_no,
                        "ERROR",
                        "INVALID_ROUTE_TYPE_V19",
                        "type='json' does not exist in Odoo 19.",
                        "Change route definition to type='jsonrpc'.",
                    )
                )
            elif self.target == "18" and ("type='jsonrpc'" in line or 'type="jsonrpc"' in line):
                self.issues.append(
                    Issue(
                        str(file_path),
                        line_no,
                        "ERROR",
                        "INVALID_ROUTE_TYPE_V18",
                        "type='jsonrpc' causes KeyError in Odoo 18.0 LTS dispatcher.",
                        "Use type='json' for Odoo 18.0 LTS compatibility.",
                    )
                )
            elif self.target == "17" and ("type='jsonrpc'" in line or 'type="jsonrpc"' in line):
                self.issues.append(
                    Issue(
                        str(file_path),
                        line_no,
                        "ERROR",
                        "INVALID_ROUTE_TYPE_V17",
                        "type='jsonrpc' is not supported in Odoo 17.",
                        "Use type='json'.",
                    )
                )

        # 2. Field options: group_operator vs aggregator
        if "group_operator=" in line and self.target in ("18", "19"):
            self.issues.append(
                Issue(
                    str(file_path),
                    line_no,
                    "WARNING",
                    "DEPRECATED_GROUP_OPERATOR",
                    "group_operator is deprecated since Odoo 17.2.",
                    "Replace with aggregator='sum' (or 'avg', 'min', 'max').",
                )
            )

        # 3. Storable product: detailed_type vs is_storable
        if "detailed_type" in line and self.target in ("18", "19") and not line.strip().startswith("#"):
            if any(term in line for term in ("'product'", '"product"', "detailed_type")):
                self.issues.append(
                    Issue(
                        str(file_path),
                        line_no,
                        "WARNING",
                        "REMOVED_DETAILED_TYPE",
                        "detailed_type was removed in Odoo 18+.",
                        "Use is_storable = True on product.template / product.product.",
                    )
                )

        # 4. Record accessors deprecated in 19: self._cr, self._uid, self._context
        if self.target == "19":
            for attr in ("self._cr", "record._cr", "self._uid", "record._uid", "self._context", "record._context"):
                if attr in line and not line.strip().startswith("#"):
                    replacement = attr.replace("._", ".env.")
                    self.issues.append(
                        Issue(
                            str(file_path),
                            line_no,
                            "WARNING",
                            "DEPRECATED_RECORD_ENV_ATTR",
                            f"{attr} is deprecated in Odoo 19.",
                            f"Replace with {replacement}.",
                        )
                    )

        # 5. Decorators not in v17: @api.private, @api.readonly
        if self.target == "17":
            if "@api.private" in line or "@api.readonly" in line:
                self.issues.append(
                    Issue(
                        str(file_path),
                        line_no,
                        "ERROR",
                        "UNSUPPORTED_DECORATOR_V17",
                        "@api.private and @api.readonly do not exist in Odoo 17.",
                        "Use leading underscore prefix (e.g. def _internal_calc(self):) for RPC protection in v17.",
                    )
                )

    # -------------------------------------------------------------------------
    # XML Scanner
    # -------------------------------------------------------------------------
    def _scan_xml(self, file_path: Path):
        try:
            content = file_path.read_text(encoding="utf-8")
        except Exception as e:
            self.issues.append(
                Issue(str(file_path), 0, "ERROR", "XML_READ_ERR", f"Could not read XML file: {e}", "")
            )
            return

        lines = content.splitlines()
        for idx, line in enumerate(lines, start=1):
            stripped = line.strip()
            if stripped.startswith("<!--") or stripped.startswith("-->"):
                continue

            # 1. <tree> vs <list>
            if self.target in ("18", "19"):
                if "<tree" in line and not "</tree" in line and "ir.ui.view" not in line:
                    # Check if it is a list view root tag
                    if re.search(r"<tree\b", line):
                        self.issues.append(
                            Issue(
                                str(file_path),
                                idx,
                                "ERROR",
                                "INVALID_TREE_TAG_V18_PLUS",
                                "<tree> root view tag changed to <list> in Odoo 18+.",
                                "Change <tree string='...'> to <list string='...'>.",
                            )
                        )
                if 'expr="//tree' in line or "expr='//tree" in line:
                    self.issues.append(
                        Issue(
                            str(file_path),
                            idx,
                            "ERROR",
                            "XPATH_TREE_TARGET_V18_PLUS",
                            "XPath target '//tree' will fail to match on Odoo 18+ views.",
                            "Change xpath expression to '//list'.",
                        )
                    )
            elif self.target == "17":
                if re.search(r"<list\b", line):
                    self.issues.append(
                        Issue(
                            str(file_path),
                            idx,
                            "ERROR",
                            "INVALID_LIST_TAG_V17",
                            "<list> tag does not exist in Odoo 17.",
                            "Use <tree string='...'> in Odoo 17.",
                        )
                    )

            # 2. Chatter syntax: <div class="oe_chatter"> vs <chatter/>
            if self.target == "17" and re.search(r"<chatter\b", line):
                self.issues.append(
                    Issue(
                        str(file_path),
                        idx,
                        "ERROR",
                        "UNSUPPORTED_CHATTER_TAG_V17",
                        "<chatter/> tag does not exist in Odoo 17.",
                        "Use <div class='oe_chatter'><field name='message_follower_ids'/><field name='activity_ids'/><field name='message_ids'/></div>.",
                    )
                )

            # 3. Legacy attrs / states modifiers
            if 'attrs="{' in line or "attrs='{" in line:
                self.issues.append(
                    Issue(
                        str(file_path),
                        idx,
                        "WARNING",
                        "DEPRECATED_ATTRS_SYNTAX",
                        "attrs='{...}' dictionary syntax was deprecated in Odoo 17+.",
                        "Use direct Python expressions: invisible='state == \"draft\"', readonly='...', required='...'.",
                    )
                )
            if 'states="' in line or "states='" in line:
                self.issues.append(
                    Issue(
                        str(file_path),
                        idx,
                        "WARNING",
                        "DEPRECATED_STATES_SYNTAX",
                        "states='...' attribute is deprecated in Odoo 17+.",
                        "Use invisible=\"state not in ('draft', 'confirmed')\" instead.",
                    )
                )

            # 4. Action view_mode
            if "<field name=\"view_mode\"" in line or "<field name='view_mode'" in line:
                if self.target in ("18", "19") and "tree,form" in line:
                    self.issues.append(
                        Issue(
                            str(file_path),
                            idx,
                            "INFO",
                            "CONVENTION_VIEW_MODE",
                            "In Odoo 18+, view_mode standard convention is 'list,form' rather than 'tree,form'.",
                            "Update view_mode field value to 'list,form'.",
                        )
                    )
                elif self.target == "17" and "list,form" in line:
                    self.issues.append(
                        Issue(
                            str(file_path),
                            idx,
                            "ERROR",
                            "INVALID_VIEW_MODE_V17",
                            "In Odoo 17, 'list' view_mode does not exist.",
                            "Use 'tree,form'.",
                        )
                    )


# -----------------------------------------------------------------------------
# CLI Entrypoint
# -----------------------------------------------------------------------------
def main() -> int:
    parser = argparse.ArgumentParser(
        description="Scan Odoo module code for version deprecations and breaking changes."
    )
    parser.add_argument("path", type=Path, help="Path to Odoo module directory or file to scan.")
    parser.add_argument(
        "--target",
        choices=["17", "18", "19"],
        default="19",
        help="Target Odoo version (default: 19).",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format: text or json (default: text).",
    )
    parser.add_argument(
        "--fail-on-warning",
        action="store_true",
        help="Exit with code 1 even on warnings (by default only ERROR causes exit code 1).",
    )

    args = parser.parse_args()

    scanner = OdooDeprecationScanner(target_version=args.target)
    issues = scanner.scan_path(args.path)

    error_count = sum(1 for i in issues if i.severity == "ERROR")
    warn_count = sum(1 for i in issues if i.severity == "WARNING")
    info_count = sum(1 for i in issues if i.severity == "INFO")

    if args.format == "json":
        print(json.dumps([asdict(i) for i in issues], indent=2))
    else:
        print(f"\n🔍 Odoo {args.target}.0 Deprecation Scanner Report for: {args.path}")
        print("=" * 70)
        if not issues:
            print("✅ No version deprecations or compatibility issues found.")
        else:
            for issue in issues:
                icon = "❌" if issue.severity == "ERROR" else ("⚠️ " if issue.severity == "WARNING" else "ℹ️ ")
                print(f"{icon} [{issue.severity}] {issue.code} at {issue.file}:{issue.line}")
                print(f"   Message: {issue.message}")
                if issue.recommendation:
                    print(f"   Fix:     {issue.recommendation}")
                print()

            print("=" * 70)
            print(f"Summary: {error_count} error(s), {warn_count} warning(s), {info_count} info notice(s).")

    if error_count > 0 or (args.fail_on_warning and warn_count > 0):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
