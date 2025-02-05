######################################################################################################################
# Copyright (C) 2017-2022 Spine project consortium
# This file is part of Spine Database API.
# Spine Database API is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser
# General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your
# option) any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
Contains unit tests for JSONConnector.

:author: A. Soininen (VTT)
:date:   30.12.2021
"""
import pickle
import unittest
from spinedb_api.spine_io.importers.json_reader import JSONConnector


class TestJSONConnector(unittest.TestCase):
    def test_connector_is_picklable(self):
        reader = JSONConnector(None)
        pickled = pickle.dumps(reader)
        self.assertTrue(pickled)


if __name__ == '__main__':
    unittest.main()
