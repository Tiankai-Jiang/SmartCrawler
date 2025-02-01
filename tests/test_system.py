import unittest
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from crawler import process_company
from llms import get_llm

class TestSystem(unittest.TestCase):

    def setUp(self):
        # Prepare environment
        self.test_url = "https://www.nvfund.com/portfolio/amphista"
        self.output_file = "test_output.csv"
        self.llm_provider = get_llm('openai')

        # Clean up any existing output file
        if os.path.exists(self.output_file):
            os.remove(self.output_file)

    def tearDown(self):
        # Cleanup after tests
        if os.path.exists(self.output_file):
            os.remove(self.output_file)

    def test_full_workflow(self):
        """
        Test the entire pipeline from fetching HTML to saving data in CSV.
        """
        process_company(self.test_url, self.llm_provider, self.output_file)

        # Verify that output CSV was created
        self.assertTrue(os.path.exists(self.output_file))

        # Verify the CSV content
        with open(self.output_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
            self.assertGreater(len(lines), 1)  # Header + at least one row

            header = lines[0].strip().split(",")
            data_row = lines[1].strip().split(",")

            # Basic sanity checks
            self.assertIn("name", header)
            self.assertIn("url", header)
            self.assertIn("Amphista Therapeutics", lines[1])

if __name__ == "__main__":
    unittest.main()