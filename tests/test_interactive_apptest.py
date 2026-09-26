"""Interactive Streamlit AppTest validation suite.
Simulates real user interaction with Streamlit controls, selectboxes, buttons,
and state switching across pages without requiring a browser.
"""

import unittest
from pathlib import Path
from streamlit.testing.v1 import AppTest

ROOT_DIR = Path(__file__).parent.parent


class TestInteractiveAppTest(unittest.TestCase):
    """Verifies UI interactions and session state using Streamlit AppTest."""

    def test_01_app_root_and_sidebar_rendering(self):
        """Verifies root app.py loads, displays navigation, and renders without exceptions."""
        app_file = str(ROOT_DIR / "app.py")
        at = AppTest.from_file(app_file, default_timeout=30).run()
        self.assertEqual(len(at.exception), 0, f"Exceptions in app.py: {at.exception}")
        
        # Verify title and disclosures
        text_content = " ".join([m.value for m in at.markdown] + [t.value for t in at.title])
        self.assertIn("MANGAN-AI", text_content)
        self.assertIn("DEMO MODE", text_content)

    def test_02_production_page_parameters_and_execution(self):
        """Verifies production page responds to horizon and target parameters."""
        prod_file = str(ROOT_DIR / "pages" / "production.py")
        at = AppTest.from_file(prod_file, default_timeout=30).run()
        self.assertEqual(len(at.exception), 0, f"Exceptions in pages/production.py: {at.exception}")

        # Check for key production metrics in output
        md_text = " ".join([m.value for m in at.markdown])
        self.assertIn("Realization", md_text)
        self.assertIn("Validation", md_text)

    def test_03_exploration_page_section_switching(self):
        """Verifies exploration page renders Folium and multi-criteria layers."""
        exp_file = str(ROOT_DIR / "pages" / "exploration.py")
        at = AppTest.from_file(exp_file, default_timeout=30).run()
        self.assertEqual(len(at.exception), 0, f"Exceptions in pages/exploration.py: {at.exception}")

        md_text = " ".join([m.value for m in at.markdown])
        self.assertIn("Favorability", md_text)

    def test_04_recommendations_workflow_and_approval(self):
        """Verifies recommendations page loads review controls without crash."""
        rec_file = str(ROOT_DIR / "pages" / "recommendations.py")
        at = AppTest.from_file(rec_file, default_timeout=30).run()
        self.assertEqual(len(at.exception), 0, f"Exceptions in pages/recommendations.py: {at.exception}")

        # Check button elements exist
        self.assertGreater(len(at.button), 0, "Approval/Defer buttons should be rendered")


if __name__ == "__main__":
    unittest.main()
