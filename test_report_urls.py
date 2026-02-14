#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
TEST: Verify all url_for calls in the reports index page.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(__file__))
from app import create_app

class TestReportURLs(unittest.TestCase):
    def setUp(self):
        """Set up test application."""
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['SERVER_NAME'] = 'localhost:5000'
        self.client = self.app.test_client()

    def test_report_index_urls(self):
        """Test that all url_for calls on the reports index page are valid."""
        with self.app.app_context():
            from flask import url_for

            endpoints = [
                'reports.employees',
                'reports.attendance',
                'reports.payroll_sheet',
                'reports.loans',
                'reports.detailed_salary_index',
                'reports.permanent_loans',
                'reports.audit_trail'
            ]

            for endpoint in endpoints:
                try:
                    url = url_for(endpoint)
                    print(f"[OK] Successfully generated URL for '{endpoint}': {url}")
                except Exception as e:
                    self.fail(f"Failed to build URL for endpoint '{endpoint}'. Error: {e}")

if __name__ == '__main__':
    print("=" * 80)
    print("REPORTS PAGE URL VERIFICATION TEST")
    print("=" * 80)
    unittest.main()
