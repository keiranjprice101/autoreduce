# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Test cases for the manual job submission script
"""
import unittest
from unittest.mock import patch, Mock, MagicMock
import scripts.manual_operations.manual_submission as ms

from model.message.message import Message

from queue_processors.queue_processor.status_utils import StatusUtils
from utils.clients.connection_exception import ConnectionException
from utils.clients.django_database_client import DatabaseClient
from utils.clients.icat_client import ICATClient
from utils.clients.queue_client import QueueClient
from scripts.manual_operations.tests.test_manual_remove import create_experiment_and_instrument, make_test_run

STATUS = StatusUtils()


# pylint:disable=no-self-use,too-many-public-methods
class TestManualSubmission(unittest.TestCase):
    """
    Test manual_submission.py
    """
    def setUp(self):
        """ Creates test variables used throughout the test suite """
        self.loc_and_rb_args = [
            MagicMock(name="DatabaseClient"),
            MagicMock(name="ICATClient"), "instrument", -1, "file_ext"
        ]
        self.sub_run_args = [MagicMock(name="QueueClient"), -1, "instrument", "data_file_location", -1]
        self.valid_return = ("location", "rb")

        self.experiment, self.instrument = create_experiment_and_instrument()

        self.run1 = make_test_run(self.experiment, self.instrument, "1")
        self.run1.data_location.create(file_path='test/file/path/2.raw')

    def tearDown(self) -> None:
        self.experiment.delete()
        self.instrument.delete()
        self.run1.delete()

    def mock_database_query_result(self, side_effects):
        """ Sets the return value(s) of database queries to those provided
        :param side_effects: A list of values to return from the database query (in sequence)"""
        mock_query_result = MagicMock(name="mock_query_result")
        mock_query_result.fetchall.side_effect = side_effects
        mock_connection = MagicMock(name="mock_connection")
        mock_connection.execute.return_value = mock_query_result
        self.loc_and_rb_args[0].connect.return_value = mock_connection

    def make_query_return_object(self, return_from):
        """ Creates a MagicMock object in a format which mimics the format of
        an object returned from a query to ICAT or the auto-reduction database
        :param return_from: A string representing what type of return object
        to be mocked
        :return: The formatted MagicMock object """
        ret_obj = [MagicMock(name="Return object")]
        if return_from == "icat":
            ret_obj[0].location = self.valid_return[0]
            ret_obj[0].dataset.investigation.name = self.valid_return[1]
        elif return_from == "db_location":
            ret_obj[0].file_path = self.valid_return[0]
        elif return_from == "db_rb":
            ret_obj[0].reference_number = self.valid_return[1]
        return ret_obj

    @patch('scripts.manual_operations.manual_submission.get_location_and_rb_from_database', return_value=None)
    @patch('scripts.manual_operations.manual_submission.get_location_and_rb_from_icat')
    def test_get_checks_database_then_icat(self, mock_from_icat, mock_from_database):
        """
        Test: Data for a given run is searched for in the database before calling ICAT
        When: get_location_and_rb is called for a datafile which isn't in the database
        """
        ms.get_location_and_rb(*self.loc_and_rb_args)
        mock_from_database.assert_called_once()
        mock_from_icat.assert_called_once()

    def test_get_from_data_base_no_client(self):
        """
        Test: None is returned
        When: get_location_and_rb_from_database called with no database_client
        """
        self.assertIsNone(ms.get_location_and_rb_from_database(None, 'GEM', 123))

    @patch('model.database.access.get_reduction_run')
    def test_get_from_database_no_run(self, mock_get_run):
        """
        Test: None is returned
        When: get_location_and_rb_from_database can't find a ReductionRun record
        """
        mock_database_client = Mock()
        mock_get_run.return_value = None
        self.assertIsNone(ms.get_location_and_rb_from_database(mock_database_client, 'GEM', 123))
        mock_get_run.assert_called_once()

    def test_get_from_database(self):
        """
        Test: Data for a given run can be retrieved from the database in the expected format
        When: get_location_and_rb_from_database is called and the data is present
        in the database
        """
        db_client = DatabaseClient()
        db_client.connect()
        actual = ms.get_location_and_rb_from_database(db_client, 'ARMI', 101)
        # Values from testing database
        expected = ('test/file/path/2.raw', 1231231)
        self.assertEqual(expected, actual)

    @patch('scripts.manual_operations.manual_submission.get_icat_instrument_prefix')
    def test_get_from_icat_when_file_exists_without_zeroes(self, _):
        """
        Test: Data for a given run can be retrieved from ICAT in the expected format
        When: get_location_and_rb_from_icat is called and the data is present in ICAT
        """
        self.loc_and_rb_args[1].execute_query.return_value = self.make_query_return_object("icat")
        location_and_rb = ms.get_location_and_rb_from_icat(*self.loc_and_rb_args[1:])
        self.loc_and_rb_args[1].execute_query.assert_called_once()
        self.assertEqual(location_and_rb, self.valid_return)

    @patch('scripts.manual_operations.manual_submission.get_icat_instrument_prefix', return_value='MAR')
    def test_icat_uses_prefix_mapper(self, _):
        """
        Test: The instrument shorthand name is used
        When: querying ICAT with function get_location_and_rb_from_icat
        """
        icat_client = Mock()
        data_file = Mock()
        data_file.location = 'location'
        data_file.dataset.investigation.name = 'inv_name'
        # Add return here to ensure we do NOT try fall through cases
        # and do NOT have to deal with multiple calls to mock
        icat_client.execute_query.return_value = [data_file]
        actual_loc, actual_inv_name = ms.get_location_and_rb_from_icat(icat_client, 'MARI', '123', 'nxs')
        self.assertEqual('location', actual_loc)
        self.assertEqual('inv_name', actual_inv_name)
        icat_client.execute_query.assert_called_once_with("SELECT df FROM Datafile df WHERE"
                                                          " df.name = 'MAR00123.nxs' INCLUDE"
                                                          " df.dataset AS ds, ds.investigation")

    @patch('scripts.manual_operations.manual_submission.get_icat_instrument_prefix')
    def test_get_location_and_rb_from_icat_when_first_file_not_found(self, _):
        """
        Test: that get_location_and_rb_from_icat can handle a number of failed ICAT
        data file search attempts before it returns valid data file and check that
        expected format is then still returned.
        When: get_location_and_rb_from_icat is called and the file is initially not
        found in ICAT.
        """
        # icat returns: not found a number of times before file found
        self.loc_and_rb_args[1].execute_query.side_effect =\
            [None, None, None, self.make_query_return_object("icat")]
        # call the method to test
        location_and_rb = ms.get_location_and_rb_from_icat(*self.loc_and_rb_args[1:])
        # how many times have icat been called
        self.assertEqual(self.loc_and_rb_args[1].execute_query.call_count, 4)
        # check returned format is OK
        self.assertEqual(location_and_rb, self.valid_return)

    @patch('scripts.manual_operations.manual_submission.get_location_and_rb_from_database')
    @patch('scripts.manual_operations.manual_submission.get_location_and_rb_from_icat')
    def test_get_when_run_number_not_int(self, mock_from_icat, mock_from_database):
        """
        Test: A SystemExit is raised and neither the database nor ICAT are checked for data
        When: get_location_and_rb is called with a run_number which cannot be cast as an int
        """
        self.loc_and_rb_args[3] = "string_rb_number"
        with self.assertRaises(SystemExit):
            ms.get_location_and_rb(*self.loc_and_rb_args)
        mock_from_icat.assert_not_called()
        mock_from_database.assert_not_called()

    def test_submit_run(self):
        """
        Test: A given run is submitted to the DataReady queue
        When: submit_run is called with valid arguments
        """
        ms.submit_run(*self.sub_run_args)
        message = Message(rb_number=self.sub_run_args[1],
                          instrument=self.sub_run_args[2],
                          data=self.sub_run_args[3],
                          run_number=self.sub_run_args[4],
                          facility="ISIS",
                          started_by=-1)
        self.sub_run_args[0].send.assert_called_with('/queue/DataReady', message, priority=1)

    @patch('icat.Client')
    @patch('utils.clients.icat_client.ICATClient.connect')
    def test_icat_login_valid(self, mock_connect, _):
        """
        Test: A valid ICAT client is returned
        When: We can log in via the client
        Note: We mock the connect so it does not actual perform the connect (default pass)
        """
        actual = ms.login_icat()
        self.assertIsInstance(actual, ICATClient)
        mock_connect.assert_called_once()

    @patch('icat.Client')
    @patch('utils.clients.icat_client.ICATClient.connect')
    def test_icat_login_invalid(self, mock_connect, _):
        """
        Test: None is returned
        When: We are unable to log in via the icat client
        """
        con_exp = ConnectionException('icat')
        mock_connect.side_effect = con_exp
        self.assertIsNone(ms.login_icat())

    @patch('utils.clients.django_database_client.DatabaseClient.connect')
    def test_database_login_valid(self, _):
        """
        Test: A valid Database client is returned
        When: We can log in via the client
        Note: We mock the connect so it does not actual perform the connect (default pass)
        """
        actual = ms.login_database()
        self.assertIsInstance(actual, DatabaseClient)

    @patch('utils.clients.django_database_client.DatabaseClient.connect')
    def test_database_login_invalid(self, mock_connect):
        """
        Test: None is returned
        When: We are unable to log in via the database client
        """
        con_exp = ConnectionException('MySQL')
        mock_connect.side_effect = con_exp
        self.assertIsNone(ms.login_database())

    @patch('utils.clients.queue_client.QueueClient.connect')
    def test_queue_login_valid(self, _):
        """
        Test: A valid Queue client is returned
        When: We can log in via the queue client
        Note: We mock the connect so it does not actual perform the connect (default pass)
        """
        actual = ms.login_queue()
        self.assertIsInstance(actual, QueueClient)

    @patch('utils.clients.queue_client.QueueClient.connect')
    def test_queue_login_invalid(self, mock_connect):
        """
        Test: An exception is raised
        When: We are unable to log in via the client
        """
        con_exp = ConnectionException('Queue')
        mock_connect.side_effect = con_exp
        self.assertRaises(RuntimeError, ms.login_queue)

    def test_submit_run_no_amq(self):
        """
        Test: That there is an early return
        When: Calling submit_run with active_mq as None
        """
        self.assertIsNone(
            ms.submit_run(active_mq_client=None,
                          rb_number=None,
                          instrument=None,
                          data_file_location=None,
                          run_number=None))

    # pylint:disable=too-many-arguments
    @patch('scripts.manual_operations.manual_submission.login_icat')
    @patch('scripts.manual_operations.manual_submission.login_database')
    @patch('scripts.manual_operations.manual_submission.login_queue')
    @patch('scripts.manual_operations.manual_submission.get_location_and_rb')
    @patch('scripts.manual_operations.manual_submission.submit_run')
    @patch('scripts.manual_operations.manual_submission.get_run_range')
    def test_main_valid(self, mock_run_range, mock_submit, mock_get_loc, mock_queue, mock_database, mock_icat):
        """
        Test: The control methods are called in the correct order
        When: main is called and the environment (client settings, input, etc.) is valid
        """
        mock_run_range.return_value = range(1111, 1112)

        # Setup Mock clients
        mock_db_client = Mock()
        mock_icat_client = Mock()
        mock_queue_client = Mock()

        # Assign Mock return values
        mock_queue.return_value = mock_queue_client
        mock_database.return_value = mock_db_client
        mock_icat.return_value = mock_icat_client
        mock_get_loc.return_value = ('test/file/path', 2222)

        # Call functionality
        ms.main(instrument='TEST', first_run=1111)

        # Assert
        mock_run_range.assert_called_with(1111, last_run=None)
        mock_icat.assert_called_once()
        mock_database.assert_called_once()
        mock_queue.assert_called_once()
        mock_get_loc.assert_called_once_with(mock_db_client, mock_icat_client, 'TEST', 1111, "nxs")
        mock_submit.assert_called_once_with(mock_queue_client, 2222, 'TEST', 'test/file/path', 1111)

    @patch('scripts.manual_operations.manual_submission.login_icat')
    @patch('scripts.manual_operations.manual_submission.login_database')
    @patch('scripts.manual_operations.manual_submission.get_run_range')
    def test_main_bad_client(self, mock_get_run_range, mock_db, mock_icat):
        """
        Test: A RuntimeError is raised
        When: Neither ICAT or Database connections can be established
        """
        mock_get_run_range.return_value = range(1111, 1112)
        mock_db.return_value = None
        mock_icat.return_value = None
        self.assertRaises(RuntimeError, ms.main, 'TEST', 1111)
        mock_get_run_range.assert_called_with(1111, last_run=None)
        mock_db.asert_called_once()
        mock_icat.assert_called_once()
