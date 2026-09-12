import tempfile
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))
from scan_deprecations import OdooDeprecationScanner


class ScanDeprecationsTest(unittest.TestCase):
    def test_detects_osv_expression_in_v19(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            test_py = Path(tmpdir) / "models.py"
            test_py.write_text(
                "from odoo.osv import expression\n"
                "from odoo import models\n"
                "class TestModel(models.Model):\n"
                "    _name = 'test.model'\n"
                "    _sql_constraints = [('code_uniq', 'unique(code)', 'Err')]\n"
                "    def _name_search(self, name):\n"
                "        pass\n",
                encoding="utf-8"
            )

            # Target 19 should flag osv.expression, _sql_constraints, and _name_search
            scanner_19 = OdooDeprecationScanner(target_version="19")
            issues_19 = scanner_19.scan_path(Path(tmpdir))
            codes_19 = {i.code for i in issues_19}

            self.assertIn("DEPRECATED_OSV_MODULE", codes_19)
            self.assertIn("DEPRECATED_SQL_CONSTRAINTS", codes_19)
            self.assertIn("DEPRECATED_NAME_SEARCH", codes_19)

    def test_detects_xml_tree_in_v18_and_list_in_v17(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            test_xml = Path(tmpdir) / "views.xml"
            test_xml.write_text(
                "<odoo>\n"
                "    <record id='view_tree' model='ir.ui.view'>\n"
                "        <field name='name'>test.tree</field>\n"
                "        <field name='arch' type='xml'>\n"
                "            <tree string='Test'>\n"
                "                <field name='name'/>\n"
                "            </tree>\n"
                "        </field>\n"
                "    </record>\n"
                "</odoo>\n",
                encoding="utf-8"
            )

            # Target 18 should flag <tree>
            scanner_18 = OdooDeprecationScanner(target_version="18")
            issues_18 = scanner_18.scan_path(Path(tmpdir))
            codes_18 = {i.code for i in issues_18}
            self.assertIn("INVALID_TREE_TAG_V18_PLUS", codes_18)

            # Target 17 should NOT flag <tree>
            scanner_17 = OdooDeprecationScanner(target_version="17")
            issues_17 = scanner_17.scan_path(Path(tmpdir))
            codes_17 = {i.code for i in issues_17}
            self.assertNotIn("INVALID_TREE_TAG_V18_PLUS", codes_17)

    def test_route_type_checks(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            ctrl_py = Path(tmpdir) / "controllers.py"
            ctrl_py.write_text(
                "from odoo import http\n"
                "class TestController(http.Controller):\n"
                "    @http.route('/api/test', type=\"json\", auth='public')\n"
                "    def test_endpoint(self):\n"
                "        return {'ok': True}\n",
                encoding="utf-8"
            )

            # Target 18 should allow type="json"
            scanner_18 = OdooDeprecationScanner(target_version="18")
            issues_18 = scanner_18.scan_path(Path(tmpdir))
            codes_18 = {i.code for i in issues_18}
            self.assertNotIn("INVALID_ROUTE_TYPE_V19", codes_18)
            self.assertNotIn("INVALID_ROUTE_TYPE_V18", codes_18)

            # Target 19 should flag type="json"
            scanner_19 = OdooDeprecationScanner(target_version="19")
            issues_19 = scanner_19.scan_path(Path(tmpdir))
            codes_19 = {i.code for i in issues_19}
            self.assertIn("INVALID_ROUTE_TYPE_V19", codes_19)

    def test_cr_commit_check(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            normal_py = Path(tmpdir) / "service.py"
            normal_py.write_text(
                "class BadService:\n"
                "    def do_work(self):\n"
                "        self.env.cr.commit()\n",
                encoding="utf-8"
            )
            test_py = Path(tmpdir) / "test_service.py"
            test_py.write_text(
                "class TestService:\n"
                "    def test_work(self):\n"
                "        self.env.cr.commit()\n",
                encoding="utf-8"
            )

            scanner = OdooDeprecationScanner(target_version="18")
            issues = scanner.scan_path(Path(tmpdir))
            issues_by_file = {Path(i.file).name: i.code for i in issues}

            # Normal file must warn about cr.commit()
            self.assertEqual(issues_by_file.get("service.py"), "DANGEROUS_CR_COMMIT")
            # Test file should be exempted
            self.assertNotIn("test_service.py", issues_by_file)

    def test_detailed_type_and_group_operator(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            model_py = Path(tmpdir) / "product.py"
            model_py.write_text(
                "from odoo import fields, models\n"
                "class ProductTemplate(models.Model):\n"
                "    _inherit = 'product.template'\n"
                "    detailed_type = fields.Selection(selection_add=[('custom', 'Custom')])\n"
                "    amount = fields.Float(group_operator='sum')\n",
                encoding="utf-8"
            )

            # Target 18 should flag both
            scanner_18 = OdooDeprecationScanner(target_version="18")
            issues_18 = scanner_18.scan_path(Path(tmpdir))
            codes_18 = {i.code for i in issues_18}
            self.assertIn("REMOVED_DETAILED_TYPE", codes_18)
            self.assertIn("DEPRECATED_GROUP_OPERATOR", codes_18)

    def test_xml_chatter_and_attrs(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            view_xml = Path(tmpdir) / "views.xml"
            view_xml.write_text(
                "<odoo>\n"
                "    <record id='test_view' model='ir.ui.view'>\n"
                "        <field name='name'>test.form</field>\n"
                "        <field name='arch' type='xml'>\n"
                "            <form>\n"
                "                <field name='name' attrs=\"{'invisible': [('state', '=', 'draft')]}\"/>\n"
                "                <field name='stage' states='draft,confirm'/>\n"
                "                <chatter/>\n"
                "            </form>\n"
                "        </field>\n"
                "    </record>\n"
                "</odoo>\n",
                encoding="utf-8"
            )

            # Target 17 flags <chatter/>, attrs, states
            scanner_17 = OdooDeprecationScanner(target_version="17")
            issues_17 = scanner_17.scan_path(Path(tmpdir))
            codes_17 = {i.code for i in issues_17}
            self.assertIn("UNSUPPORTED_CHATTER_TAG_V17", codes_17)
            self.assertIn("DEPRECATED_ATTRS_SYNTAX", codes_17)
            self.assertIn("DEPRECATED_STATES_SYNTAX", codes_17)

            # Target 18 accepts <chatter/>
            scanner_18 = OdooDeprecationScanner(target_version="18")
            issues_18 = scanner_18.scan_path(Path(tmpdir))
            codes_18 = {i.code for i in issues_18}
            self.assertNotIn("UNSUPPORTED_CHATTER_TAG_V17", codes_18)


if __name__ == "__main__":
    unittest.main()
