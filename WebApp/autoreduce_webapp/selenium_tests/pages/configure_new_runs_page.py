# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #

from django.urls import reverse
from selenium.webdriver.remote.webelement import WebElement

from selenium_tests.pages.component_mixins.footer_mixin import FooterMixin
from selenium_tests.pages.component_mixins.navbar_mixin import NavbarMixin
from selenium_tests.pages.component_mixins.tour_mixin import TourMixin
from selenium_tests.pages.component_mixins.rerun_form_mixin import RerunFormMixin
from selenium_tests.pages.page import Page


class ConfigureNewRunsPage(Page, RerunFormMixin, NavbarMixin, FooterMixin, TourMixin):
    """
    Page model class for run summary page
    """
    def __init__(self, driver, instrument, run_start=None, run_end=None, experiment_reference=None):
        super().__init__(driver)
        self.instrument = instrument
        self._run_start_number = run_start
        self._run_end_number = run_end
        self._experiment_reference = experiment_reference

    def url_path(self) -> str:
        """
        Return the current URL of the page.
        :return: (str) the url path
        """
        kwargs = {
            "instrument": self.instrument,
        }
        if self._experiment_reference:
            kwargs["experiment_reference"] = self._experiment_reference
            return reverse("instrument:variables_by_experiment", kwargs=kwargs)
        else:
            if self._run_start_number:
                kwargs["start"] = self._run_start_number

            if self._run_end_number:
                kwargs["end"] = self._run_end_number

            return reverse("instrument:variables", kwargs=kwargs)

    @property
    def run_start(self) -> WebElement:
        return self.driver.find_element_by_id("run_start")

    @property
    def run_start_val(self) -> WebElement:
        return self.driver.find_element_by_id("run_start").get_attribute("value")

    @run_start.setter
    def run_start(self, value):
        self._set_field(self.run_start, value)

    @property
    def run_end(self) -> WebElement:
        return self.driver.find_element_by_id("run_end")

    @property
    def run_end_val(self) -> WebElement:
        return self.driver.find_element_by_id("run_end").get_attribute("value")

    @run_end.setter
    def run_end(self, value):
        self._set_field(self.run_end, value)

    @property
    def experiment_reference_number(self) -> WebElement:
        return self.driver.find_element_by_id("experiment_reference_number")

    @property
    def experiment_reference_number_val(self) -> WebElement:
        return self.driver.find_element_by_id("experiment_reference_number").get_attribute("value")

    @experiment_reference_number.setter
    def experiment_reference_number(self, value):
        self._set_field(self.experiment_reference_number, value)

    @property
    def range_or_experiment_toggle(self) -> WebElement:
        return self.driver.find_element_by_id("variable-range-toggle")

    @property
    def reset_to_current_values(self) -> WebElement:
        """
        Finds and returns the "Reset to values in the current reduce_vars script" button
        """
        return self.driver.find_element_by_id("currentScript")

    @property
    def replace_confirm(self) -> WebElement:
        return self.driver.find_element_by_id("replace_confirm")
