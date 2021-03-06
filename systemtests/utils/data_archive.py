# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
from pathlib import Path
from shutil import rmtree
from typing import List

from queue_processors.queue_processor.settings import SCRIPTS_DIRECTORY, CYCLE_DIRECTORY, ARCHIVE_ROOT


class DataArchive:
    """
    Class for the local data-archive used in the end to end tests.
    """
    def __init__(self, instruments: List[str], start_year: int, end_year: int):
        self.instruments = instruments
        self.start_year = start_year
        self.end_year = end_year

    def create(self) -> None:
        """
        Create the data-archive structure as required by the end to end tests
        """
        for instrument in self.instruments:
            self._create_cycle_path(instrument)
            self._create_script_directory(instrument)

    def add_reduction_script(self, instrument: str, script_text: str) -> None:
        """
        Given an instrument and a script text, create a reduce.py file in that instruments folder matching the given
        script text
        :param instrument: (str) the instrument for the reduce.py
        :param script_text: (str) the content for the reduce.py
        """
        location = Path(SCRIPTS_DIRECTORY % instrument, "reduce.py")
        self._create_file_at_location(location, script_text)

    def add_reduce_vars_script(self, instrument: str, script_text: str):
        """
        Given an instrument and script_text, create the reduce_vars.py file for that instrument with the given script
        text
        :param instrument: (str) the instrument for the reduce_vars.py
        :param script_text: (str) the content of the reduce_vars.py
        """
        location = Path(SCRIPTS_DIRECTORY % instrument, "reduce_vars.py")
        self._create_file_at_location(location, script_text)

    @staticmethod
    def add_data_file(instrument: str, datafile_name: str, year: int, cycle_num: int) -> str:
        """
        Given an instrument, datafile name, year and cycle number. Create a datafile in the appropriate place within
        the data-archive
        :param instrument: (str) The instrument of the datafile
        :param datafile_name: (str) The name of the datafile
        :param year: (int) The year of the run in the format yy where xxyy is the full year
        :param cycle_num: (int) The cycle number for that year
        :return: (str) The string path of the datafile created.
        """
        location = Path(CYCLE_DIRECTORY % (instrument, f"{year}_{cycle_num}"))
        location.mkdir(parents=True)
        datafile = Path(location, datafile_name)
        datafile.touch()
        return str(datafile)

    def _create_cycle_path(self, instrument: str) -> None:
        for year in range(self.start_year, self.end_year):
            for cycle_number in range(1, 6):
                Path(CYCLE_DIRECTORY % (instrument, f"{year}_{cycle_number}")).mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _create_script_directory(instrument: str) -> None:
        Path(SCRIPTS_DIRECTORY % instrument).mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _create_file_at_location(location: Path, file_text: str) -> None:
        with open(location, "w+") as fle:
            fle.write(file_text)

    @staticmethod
    def delete() -> None:
        """
        Remove the created data-archive from disk.
        """
        rmtree(ARCHIVE_ROOT)
