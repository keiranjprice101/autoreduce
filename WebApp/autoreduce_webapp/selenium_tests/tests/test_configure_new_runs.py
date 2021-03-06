# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #

from django.urls import reverse

from selenium_tests.tests.base_tests import NavbarTestMixin, BaseTestCase, FooterTestMixin
from selenium_tests.pages.configure_new_runs_page import ConfigureNewRunsPage

from systemtests.utils.data_archive import DataArchive


class TestConfigureNewRunsPage(NavbarTestMixin, BaseTestCase, FooterTestMixin):

    fixtures = BaseTestCase.fixtures + ["two_runs"]

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.instrument_name = "TestInstrument"
        cls.data_archive = DataArchive([cls.instrument_name], 21, 21)
        cls.data_archive.create()
        cls.data_archive.add_reduction_script(cls.instrument_name, """print('some text')""")
        cls.data_archive.add_reduce_vars_script(cls.instrument_name,
                                                """standard_vars={"variable1":"test_variable_value_123"}""")
        cls.instrument_name = "TestInstrument"

    @classmethod
    def tearDownClass(cls) -> None:
        cls.data_archive.delete()
        super().tearDownClass()

    def setUp(self) -> None:
        super().setUp()
        self.page = ConfigureNewRunsPage(self.driver, self.instrument_name)
        self.page.launch()

    def test_reset_values_does_reset_the_values(self):
        """Test that the button to reset the variables to the values from the reduce_vars script works"""
        self.page.variable1_field = "the new value in the field"
        self.page.reset_to_current_values.click()

        # need to re-query the driver because resetting replaces the elements
        var_field = self.page.variable1_field
        assert var_field.get_attribute("value") == "test_variable_value_123"

    def test_back_to_instruments_goes_back(self):
        """
        Test: Clicking back goes back to the instrument
        """
        back = self.page.cancel_button
        assert back.is_displayed()
        assert back.text == "Cancel"
        back.click()
        assert reverse("runs:list", kwargs={"instrument": self.instrument_name}) in self.driver.current_url
