# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2019 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #

"""
The purpose of this package is for performing MySQL queries to monitor system state
performance and health. This file retrieves and cleans cycle data for
use in MySQL queries.
"""

# Dependencies
# Web-scraping dependencies
import os
import logging
import requests
import lxml.html as lh
import pandas as pd
import re


class TableWebScraper:
    """
    Web-scrapes beam cycle data from https://www.isis.stfc.ac.uk/Pages/Beam-Status.aspx
    for MySQL system checks. This URl can be changed at the bottom of the script
    """

    def __init__(self, url, local_data=None):
        self.url = url
        if local_data is None:
            # By default, a local copy of cycle data is stored in the current working directory
            self.local_data = "cycle_dates.csv"
        else:
            # Allows for a custom location to be set for a local CSV copy of cycle data
            self.local_data = local_data

    def save_to_csv(self, data):
        """ Create local copy of dataframe as .csv to read when web page is not accessible"""
        data.to_csv(r'{}'.format(self.local_data), encoding='utf-8')
        return data

    @staticmethod
    def read_csv(local_data):
        """Reads csv into a pandas data frame """
        if os.path.isfile("{}".format(local_data)):
            # Directory exists
            data = pd.read_csv("{}".format(local_data), index_col=0, encoding='utf8')
            return data
        else:
            # Directory doesn't exist
            logging.error("No file named {} found".format(local_data))

    # -/////////////////////////////////////// Web scraping //////////////////////////////////-#

    def create_table(self):
        """Private function to format data scraped ready to be placed into a pandas data frame"""

        def _create_header_cols(elements, column):
            # For each row, store each first element (header) and an empty list col
            index = 0
            for text in elements[0]:
                index += 1
                name = text.text_content()
                column.append((name, []))

        def _populate_table(elements, col):
            """Populate  table with web scraped data"""

            # Data is stored on the second row onwards
            for j in range(1, len(elements)):
                # tr_elem is our j'th row
                tr_elem = elements[j]

                # If row is not of size 5, the //tr data is not from table we expect
                if len(tr_elem) != 5:
                    break

                # Iterate through each element of the row
                index = 0
                for t in tr_elem.iterchildren():
                    data = t.text_content()
                    # Append data to empty list of index column
                    col[index][1].append(data)
                    index += 1

        def _datatable_constructor(col):
            """Construct data frame from list of columns"""
            dictionary = {title: column for (title, column) in col}
            data = pd.DataFrame(dictionary)
            self.save_to_csv(data)
            return data

        def _web_scrape(url):
            """Web scrape URL input"""
            col = []  # empty list to store list of columns
            response = requests.get(url)
            doc = lh.fromstring(response.content)  # Store the contents of the website under doc
            tr_elements = doc.xpath('//tr')  # Parse data stored between <tr>..</tr> of HTML
            _create_header_cols(tr_elements, col)
            _populate_table(tr_elements, col)
            data = _datatable_constructor(col)
            return data

        def _check_connection(url):
            """Web scrape if URL can be pinged else retrieve local copy made"""
            request = requests.get('{}'.format(url))
            if request.status_code == 200:
                data = _web_scrape(url)
                logging.info('Connection to URL established')
            else:
                data = TableWebScraper.read_csv(self.local_data)
                logging.info('URL currently not available')

            return data

        data = _check_connection(website)
        return data


# #-/////////////////////////////////// Data cleaning /////////////////////////////////////-#
class DataClean:

    def __init__(self, df):
        self.df = df

    def normalise(self):
        """Contains a range of private methods for normalising dataframe"""

        # Encode in ascii and decode utf-8 to remove zero width spaces
        for i in list(self.df):
            self.df[i] = (self.df[i].str.encode('ascii', 'ignore')).str.decode("utf-8")

        # Drop all rows containing empty strings
        self.df = self.df[self.df.loc[:] != ''].dropna()

        # Remove references of "Add to calender" from Cycle Column
        self.df.Cycle = [x.strip('Add to calendar') for x in self.df.Cycle]

        # Format Start and End columns to comma separated values for MySQL date queries
        cycle_period = ['Start', 'End']
        for index in cycle_period:
            self.df[index] = DataClean.date_formatter(self.df, index)

        return self.df

    @staticmethod
    def month_str_to_int(string):
        """Dictionary to compare month name with numeric equivalent"""
        month_compare = {'jan': '1', 'feb': '2', 'mar': '3', 'apr': '4',
                         'may': '5', 'jun': '6', 'jul': '7', 'aug': '8',
                         'sep': '9', 'oct': '10', 'nov': '11', 'dec': '12'}

        # strip string length to 3 letters and make lower case for key comparison in month_compare
        string = string.strip()[:3].lower()

        # Return comparison if month is recognised as key in month_compare
        try:
            return month_compare[string]
        except ValueError:
            # Month is not recognised as key in month_compare
            print("{} is not a month".format(string))

    # Re-format date in Start and End columns to separate days, months and year by a , and space
    @staticmethod
    def date_formatter(df, index):
        """ Format Start and End columns to comma separated values for MySQL date queries"""
        new_col = []
        for i in df[index]:
            month = ''.join(re.findall("\D", i))
            numerical = re.findall("\d", i)
            if len(numerical) == 6:
                day = '{}{}'.format(numerical.pop(0), numerical.pop(0))
            else:
                day = numerical.pop(0)
            year = ''.join(numerical)
            converted_row = '{}-{}-{}'.format(year.strip(),
                                              DataClean.month_str_to_int((month.strip())),
                                              day.strip())
            new_col.append(converted_row)
        return new_col


# Set url to scrape from, put inside pandas table and clean data frame ready for queries
website = 'https://www.isis.stfc.ac.uk/Pages/Beam-Status.aspx'
# Normalise is kept separate in case table no longer needs to be normalised.
data_frame = DataClean(TableWebScraper(website).create_table()).normalise()
