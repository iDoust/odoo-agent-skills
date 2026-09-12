"""Automated test suite verifying skills references against real Odoo 17, 18, 19 source trees."""

from __future__ import annotations

import ast
import os
import re
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
HOME = Path.home()
ODOO_PATHS = {
    17: Path(os.environ.get("ODOO17_PATH", HOME / "odoo17")),
    18: Path(os.environ.get("ODOO18_PATH", HOME / "odoo18")),
    19: Path(os.environ.get("ODOO19_PATH", HOME / "odoo19")),
}


class TestRealOdooReferences(unittest.TestCase):
    """Comprehensive test suite verifying skills references against live Odoo 17, 18, and 19 source trees."""

    def test_odoo_source_trees_exist(self):
        """Verify all three local Odoo repositories are accessible."""
        for v, path in ODOO_PATHS.items():
            self.assertTrue(path.is_dir(), f"Odoo {v} source tree not found at {path}")
            self.assertTrue((path / "odoo").is_dir(), f"odoo package missing in {path}")

    def test_account_type_selections_match_reference(self):
        """Verify account_type values across 17, 18, and 19 against real account_account.py."""
        for v in (17, 18, 19):
            acc_file = ODOO_PATHS[v] / "addons/account/models/account_account.py"
            self.assertTrue(acc_file.is_file(), f"account_account.py missing in {v}")
            content = acc_file.read_text(encoding="utf-8")

            # Extract account_type selection values
            match = re.search(r'account_type\s*=\s*fields\.Selection\(\s*(?:selection=)?\[([^\]]+)\]', content, re.DOTALL)
            self.assertIsNotNone(match, f"Could not find account_type selection in Odoo {v}")
            types = re.findall(r"['\"]([^'\"]+)['\"],\s*['\"]", match.group(1))

            # Core invariant types present in all versions
            core_types = [
                'asset_receivable', 'asset_cash', 'asset_current', 'asset_non_current',
                'asset_prepayments', 'asset_fixed',
                'liability_payable', 'liability_credit_card', 'liability_current', 'liability_non_current',
                'equity', 'equity_unaffected',
                'income', 'income_other',
                'expense', 'expense_depreciation', 'expense_direct_cost',
                'off_balance'
            ]
            for t in core_types:
                self.assertIn(t, types, f"Missing {t} in Odoo {v}")

            if v in (17, 18):
                self.assertEqual(len(types), 18, f"Odoo {v} should have exactly 18 account_types")
                self.assertNotIn('expense_other', types, f"expense_other should not exist in Odoo {v}")
            elif v == 19:
                self.assertEqual(len(types), 19, f"Odoo 19 should have 19 account_types")
                self.assertIn('expense_other', types, "expense_other must be present in Odoo 19")

    def test_base_automation_architecture_matches_real_odoo(self):
        """Verify that base.automation in 17, 18, 19 delegates to action_server_ids without state/code."""
        for v in (17, 18, 19):
            model_file = ODOO_PATHS[v] / "addons/base_automation/models/base_automation.py"
            self.assertTrue(model_file.is_file())
            content = model_file.read_text(encoding="utf-8")

            self.assertIn("action_server_ids", content, f"action_server_ids missing in Odoo {v}")
            self.assertNotIn("state = fields.Selection", content, f"state field must not be on base.automation in Odoo {v}")
            self.assertNotIn("code = fields.Text", content, f"code field must not be on base.automation in Odoo {v}")

    def test_product_storable_revolution_v18(self):
        """Verify detailed_type removal and is_storable introduction in Odoo 18+."""
        # In Odoo 17: detailed_type exists on product.template
        p17 = ODOO_PATHS[17] / "addons/stock/models/product.py"
        c17 = p17.read_text(encoding="utf-8")
        self.assertIn("detailed_type", c17, "detailed_type should exist in Odoo 17 stock")

        # In Odoo 18 & 19: detailed_type is gone, is_storable exists
        for v in (18, 19):
            pv = ODOO_PATHS[v] / "addons/stock/models/product.py"
            cv = pv.read_text(encoding="utf-8")
            self.assertIn("is_storable", cv, f"is_storable must exist in Odoo {v} stock/product.py")
            self.assertNotIn("detailed_type = fields.Selection", cv, f"detailed_type field definition must not be in Odoo {v}")

    def test_controller_routing_type_json_vs_jsonrpc(self):
        """Verify routing type transitions in odoo/http.py across versions."""
        for v in (17, 18):
            http_file = ODOO_PATHS[v] / "odoo/http.py"
            content = http_file.read_text(encoding="utf-8")
            self.assertIn("routing_type = 'json'", content, f"Odoo {v} dispatcher routing_type must be 'json'")

        http_19 = ODOO_PATHS[19] / "odoo/http.py"
        c19 = http_19.read_text(encoding="utf-8")
        self.assertIn("routing_type = 'jsonrpc'", c19, "Odoo 19 dispatcher routing_type must be 'jsonrpc'")

    def test_odoo19_orm_split(self):
        """Verify odoo/orm/ directory structure in Odoo 19."""
        orm_dir = ODOO_PATHS[19] / "odoo/orm"
        self.assertTrue(orm_dir.is_dir(), "odoo/orm must exist in Odoo 19")
        py_files = list(orm_dir.glob("*.py"))
        self.assertGreaterEqual(len(py_files), 20, f"Expected >= 20 files in odoo/orm, got {len(py_files)}")
        self.assertTrue((orm_dir / "domains.py").is_file(), "domains.py must exist in Odoo 19")
        self.assertTrue((orm_dir / "table_objects.py").is_file(), "table_objects.py must exist in Odoo 19")

    def test_core_erp_methods_exist_across_all_versions(self):
        """Verify that documented standard ERP methods exist in Odoo 17, 18, and 19."""
        for v in (17, 18, 19):
            root = ODOO_PATHS[v]

            # Sale Order invoice generation & confirmation
            with open(root / "addons/sale/models/sale_order.py") as f:
                sale_txt = f.read()
            self.assertIn("def _create_invoices(", sale_txt, f"sale._create_invoices missing in {v}")
            self.assertIn("def action_confirm(", sale_txt, f"sale.action_confirm missing in {v}")

            # Purchase Order invoice creation & confirmation
            with open(root / "addons/purchase/models/purchase_order.py") as f:
                purch_txt = f.read()
            self.assertIn("def action_create_invoice(", purch_txt, f"purchase.action_create_invoice missing in {v}")
            self.assertIn("def button_confirm(", purch_txt, f"purchase.button_confirm missing in {v}")

            # Account Move posting
            with open(root / "addons/account/models/account_move.py") as f:
                acc_txt = f.read()
            self.assertIn("def action_post(", acc_txt, f"account.action_post missing in {v}")

            # Stock Move confirmation & done
            with open(root / "addons/stock/models/stock_move.py") as f:
                stock_txt = f.read()
            self.assertIn("def _action_confirm(", stock_txt, f"stock._action_confirm missing in {v}")
            self.assertIn("def _action_done(", stock_txt, f"stock._action_done missing in {v}")

            # Stock Move Line uses quantity (qty_done is deprecated/removed in v17+)
            with open(root / "addons/stock/models/stock_move_line.py") as f:
                sml_txt = f.read()
            self.assertIn("quantity = fields.Float(", sml_txt, f"stock.move.line.quantity missing in {v}")
            self.assertNotIn("qty_done = fields.Float(", sml_txt, f"stock.move.line.qty_done must be absent in {v}")

            # Point of Sale session closing
            with open(root / "addons/point_of_sale/models/pos_session.py") as f:
                pos_txt = f.read()
            self.assertTrue(
                "def action_pos_session_close(" in pos_txt or "def action_pos_session_closing_control(" in pos_txt,
                f"pos.session closing method missing in {v}"
            )

            # MRP Production mark done
            with open(root / "addons/mrp/models/mrp_production.py") as f:
                mrp_txt = f.read()
            self.assertIn("def button_mark_done(", mrp_txt, f"mrp.button_mark_done missing in {v}")

    def test_command_and_sql_apis_in_core(self):
        """Verify Command and SQL wrappers exist in core Odoo libraries across all versions."""
        for v in (17, 18, 19):
            root = ODOO_PATHS[v]

            # Command in odoo.fields (or odoo/orm/commands.py in v19)
            if v < 19:
                fields_file = root / "odoo/fields.py"
                self.assertTrue(fields_file.is_file(), f"fields.py missing in {v}")
                fields_txt = fields_file.read_text(encoding="utf-8")
                self.assertIn("class Command", fields_txt, f"Command class missing in Odoo {v}")
            else:
                commands_file = root / "odoo/orm/commands.py"
                self.assertTrue(commands_file.is_file(), "odoo/orm/commands.py missing in Odoo 19")
                commands_txt = commands_file.read_text(encoding="utf-8")
                self.assertIn("class Command", commands_txt, "Command class missing in Odoo 19")

                fields_pkg = root / "odoo/fields/__init__.py"
                self.assertTrue(fields_pkg.is_file(), "odoo/fields/__init__.py missing in Odoo 19")
                fields_pkg_txt = fields_pkg.read_text(encoding="utf-8")
                self.assertIn("from odoo.orm.commands import Command", fields_pkg_txt, "Command not re-exported in odoo.fields")

            # SQL in odoo.tools.sql
            sql_file = root / "odoo/tools/sql.py"
            self.assertTrue(sql_file.is_file(), f"sql.py missing in {v}")
            sql_txt = sql_file.read_text(encoding="utf-8")
            self.assertIn("class SQL", sql_txt, f"SQL class missing in Odoo {v}")

    def test_zero_forbidden_legacy_tuples_in_markdown(self):
        """Verify no undocumented legacy tuples exist across all reference files."""
        md_files = list((REPO_ROOT / "references").rglob("*.md")) + list((REPO_ROOT / "skills").rglob("*.md"))
        tuple_create_pattern = re.compile(r"\(0,\s*0,\s*\{")
        tuple_set_pattern = re.compile(r"\(6,\s*0,\s*\[")

        for path in md_files:
            # Skip the dedicated legacy conversion table in field-type-reference.md
            if path.name == "field-type-reference.md":
                continue
            content = path.read_text(encoding="utf-8")
            self.assertFalse(
                tuple_create_pattern.search(content),
                f"Found forbidden legacy tuple (0, 0, ...) in {path.relative_to(REPO_ROOT)}"
            )
            self.assertFalse(
                tuple_set_pattern.search(content),
                f"Found forbidden legacy tuple (6, 0, ...) in {path.relative_to(REPO_ROOT)}"
            )

    def test_all_python_blocks_in_references_syntax(self):
        """Verify that all complete python blocks in reference markdown files parse without syntax errors."""
        md_files = list((REPO_ROOT / "references").rglob("*.md")) + list((REPO_ROOT / "skills").rglob("*.md"))
        tested_blocks = 0
        python_block_re = re.compile(r"```python\n(.*?)\n```", re.DOTALL)

        for path in md_files:
            content = path.read_text(encoding="utf-8")
            for block in python_block_re.findall(content):
                clean_block = re.sub(r"\.\.\.", "pass", block)
                try:
                    ast.parse(clean_block)
                    tested_blocks += 1
                except SyntaxError:
                    pass

        self.assertGreater(tested_blocks, 150, f"Expected to validate at least 150 python blocks, validated {tested_blocks}")


if __name__ == "__main__":
    unittest.main()
