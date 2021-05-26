######################################################################################################################
# Copyright (C) 2017-2021 Spine project consortium
# This file is part of Spine Database API.
# Spine Database API is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser
# General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your
# option) any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
Tests for the parameter_value module.

:authors: A. Soininen (VTT)
:date:   7.6.2019
"""

from datetime import datetime
import json
import unittest
import dateutil.parser
from dateutil.relativedelta import relativedelta
import numpy as np
import numpy.testing
from spinedb_api.parameter_value import (
    convert_containers_to_maps,
    convert_leaf_maps_to_specialized_containers,
    convert_map_to_table,
    duration_to_relativedelta,
    relativedelta_to_duration,
    from_database,
    to_database,
    Array,
    DateTime,
    Duration,
    IndexedNumberArray,
    Map,
    TimePattern,
    TimeSeriesFixedResolution,
    TimeSeriesVariableResolution,
)


class TestParameterValue(unittest.TestCase):
    """Test for the free functions and classes in parameter_value."""

    def test_duration_to_relativedelta_seconds(self):
        delta = duration_to_relativedelta("7s")
        self.assertEqual(delta, relativedelta(seconds=7))
        delta = duration_to_relativedelta("1 second")
        self.assertEqual(delta, relativedelta(seconds=1))
        delta = duration_to_relativedelta("7 seconds")
        self.assertEqual(delta, relativedelta(seconds=7))
        delta = duration_to_relativedelta("99 seconds")
        self.assertEqual(delta, relativedelta(minutes=1, seconds=39))

    def test_relativedelta_to_duration_seconds(self):
        delta = duration_to_relativedelta("7s")
        duration = relativedelta_to_duration(delta)
        self.assertEqual(duration, "7s")
        delta = duration_to_relativedelta("9999999s")
        duration = relativedelta_to_duration(delta)
        self.assertEqual(duration, "9999999s")

    def test_duration_to_relativedelta_minutes(self):
        delta = duration_to_relativedelta("7m")
        self.assertEqual(delta, relativedelta(minutes=7))
        delta = duration_to_relativedelta("1 minute")
        self.assertEqual(delta, relativedelta(minutes=1))
        delta = duration_to_relativedelta("7 minutes")
        self.assertEqual(delta, relativedelta(minutes=7))

    def test_relativedelta_to_duration_minutes(self):
        delta = duration_to_relativedelta("7m")
        duration = relativedelta_to_duration(delta)
        self.assertEqual(duration, "7m")
        delta = duration_to_relativedelta("999999m")
        duration = relativedelta_to_duration(delta)
        self.assertEqual(duration, "999999m")

    def test_duration_to_relativedelta_hours(self):
        delta = duration_to_relativedelta("7h")
        self.assertEqual(delta, relativedelta(hours=7))
        delta = duration_to_relativedelta("1 hour")
        self.assertEqual(delta, relativedelta(hours=1))
        delta = duration_to_relativedelta("7 hours")
        self.assertEqual(delta, relativedelta(hours=7))

    def test_relativedelta_to_duration_hours(self):
        delta = duration_to_relativedelta("7h")
        duration = relativedelta_to_duration(delta)
        self.assertEqual(duration, "7h")
        delta = duration_to_relativedelta("99999h")
        duration = relativedelta_to_duration(delta)
        self.assertEqual(duration, "99999h")

    def test_duration_to_relativedelta_days(self):
        delta = duration_to_relativedelta("7D")
        self.assertEqual(delta, relativedelta(days=7))
        delta = duration_to_relativedelta("1 day")
        self.assertEqual(delta, relativedelta(days=1))
        delta = duration_to_relativedelta("7 days")
        self.assertEqual(delta, relativedelta(days=7))

    def test_relativedelta_to_duration_days(self):
        delta = duration_to_relativedelta("7D")
        duration = relativedelta_to_duration(delta)
        self.assertEqual(duration, "7D")
        delta = duration_to_relativedelta("9999D")
        duration = relativedelta_to_duration(delta)
        self.assertEqual(duration, "9999D")

    def test_duration_to_relativedelta_months(self):
        delta = duration_to_relativedelta("7M")
        self.assertEqual(delta, relativedelta(months=7))
        delta = duration_to_relativedelta("1 month")
        self.assertEqual(delta, relativedelta(months=1))
        delta = duration_to_relativedelta("7 months")
        self.assertEqual(delta, relativedelta(months=7))

    def test_relativedelta_to_duration_months(self):
        delta = duration_to_relativedelta("7M")
        duration = relativedelta_to_duration(delta)
        self.assertEqual(duration, "7M")
        delta = duration_to_relativedelta("99M")
        duration = relativedelta_to_duration(delta)
        self.assertEqual(duration, "99M")

    def test_duration_to_relativedelta_years(self):
        delta = duration_to_relativedelta("7Y")
        self.assertEqual(delta, relativedelta(years=7))
        delta = duration_to_relativedelta("7Y")
        self.assertEqual(delta, relativedelta(years=7))
        delta = duration_to_relativedelta("1 year")
        self.assertEqual(delta, relativedelta(years=1))
        delta = duration_to_relativedelta("7 years")
        self.assertEqual(delta, relativedelta(years=7))

    def test_relativedelta_to_duration_years(self):
        delta = duration_to_relativedelta("7Y")
        duration = relativedelta_to_duration(delta)
        self.assertEqual(duration, "7Y")

    def test_from_database_plain_number(self):
        database_value = "23.0"
        value = from_database(database_value, value_type=None)
        self.assertTrue(isinstance(value, float))
        self.assertEqual(value, 23.0)

    def test_to_database_plain_number(self):
        value = 23.0
        database_value, value_type = to_database(value)
        value_as_float = json.loads(database_value)
        self.assertEqual(value_as_float, value)
        self.assertIsNone(value_type)

    def test_to_database_DateTime(self):
        value = DateTime(datetime(year=2019, month=6, day=26, hour=12, minute=50, second=13))
        database_value, value_type = to_database(value)
        value_as_dict = json.loads(database_value)
        self.assertEqual(value_as_dict, {"type": "date_time", "data": "2019-06-26T12:50:13"})
        self.assertEqual(value_type, "date_time")

    def test_from_database_DateTime(self):
        database_value = '{"type": "date_time", "data": "2019-06-01T22:15:00+01:00"}'
        value = from_database(database_value, value_type="date_time")
        self.assertEqual(value.value, dateutil.parser.parse("2019-06-01T22:15:00+01:00"))

    def test_DateTime_to_database(self):
        value = DateTime(datetime(year=2019, month=6, day=26, hour=10, minute=50, second=34))
        database_value, value_type = value.to_database()
        value_dict = json.loads(database_value)
        self.assertEqual(value_dict, {"type": "date_time", "data": "2019-06-26T10:50:34"})
        self.assertEqual(value_type, "date_time")

    def test_from_database_Duration(self):
        database_value = '{"type": "duration", "data": "4 seconds"}'
        value = from_database(database_value, value_type="duration")
        self.assertEqual(value.value, relativedelta(seconds=4))

    def test_from_database_Duration_default_units(self):
        database_value = '{"type": "duration", "data": 23}'
        value = from_database(database_value, value_type="duration")
        self.assertEqual(value.value, relativedelta(minutes=23))

    def test_from_database_Duration_legacy_list_format_converted_to_Array(self):
        database_value = '{"type": "duration", "data": ["1 hour", "1h", 60, "2 hours"]}'
        value = from_database(database_value, value_type="duration")
        expected = Array([Duration("1h"), Duration("1h"), Duration("1h"), Duration("2h")])
        self.assertEqual(value, expected)

    def test_Duration_to_database(self):
        value = Duration(duration_to_relativedelta("8 years"))
        database_value, value_type = value.to_database()
        value_as_dict = json.loads(database_value)
        self.assertEqual(value_as_dict, {"type": "duration", "data": "8Y"})
        self.assertEqual(value_type, "duration")

    def test_from_database_TimePattern(self):
        database_value = """
        {
          "type": "time_pattern",
          "data": {
            "m1-4,m9-12": 300,
            "m5-8": 221.5
          }
        }
        """
        value = from_database(database_value, value_type="time_pattern")
        self.assertEqual(len(value), 2)
        self.assertEqual(value.indexes, ["m1-4,m9-12", "m5-8"])
        numpy.testing.assert_equal(value.values, numpy.array([300.0, 221.5]))

    def test_TimePattern_to_database(self):
        value = TimePattern(["m1-4,m9-12", "m5-8"], numpy.array([300.0, 221.5]))
        database_value, value_type = value.to_database()
        value_as_dict = json.loads(database_value)
        self.assertEqual(value_as_dict, {"type": "time_pattern", "data": {"m1-4,m9-12": 300.0, "m5-8": 221.5}})
        self.assertEqual(value_type, "time_pattern")

    def test_TimePattern_to_database_with_integer_values(self):
        value = TimePattern(["m1-4,m9-12", "m5-8"], [300, 221])
        database_value, value_type = value.to_database()
        value_as_dict = json.loads(database_value)
        self.assertEqual(value_as_dict, {"type": "time_pattern", "data": {"m1-4,m9-12": 300.0, "m5-8": 221.0}})
        self.assertEqual(value_type, "time_pattern")

    def test_TimePattern_index_length_is_not_limited(self):
        value = TimePattern(["m1-4", "m5-12"], [300, 221])
        value.indexes[0] = "m1,m3,m5,m7,m9,m11"
        value.indexes[1] = "m2,m4,m6,m8,m10,m12"
        self.assertEqual(list(value.indexes), ["m1,m3,m5,m7,m9,m11", "m2,m4,m6,m8,m10,m12"])

    def test_from_database_TimeSeriesVariableResolution_as_dictionary(self):
        releases = """{
                          "type": "time_series",
                          "data": {
                              "1977-05-25": 4,
                              "1980-05-21": 5,
                              "1983-05-25": 6
                          }
                      }"""
        time_series = from_database(releases, value_type="time_series")
        self.assertEqual(
            time_series.indexes,
            numpy.array(
                [numpy.datetime64("1977-05-25"), numpy.datetime64("1980-05-21"), numpy.datetime64("1983-05-25")],
                dtype="datetime64[D]",
            ),
        )
        self.assertEqual(len(time_series), 3)
        self.assertTrue(isinstance(time_series.values, numpy.ndarray))
        numpy.testing.assert_equal(time_series.values, numpy.array([4, 5, 6]))

    def test_from_database_TimeSeriesVariableResolution_as_two_column_array(self):
        releases = """{
                          "type": "time_series",
                          "data": [
                              ["1977-05-25", 4],
                              ["1980-05-21", 5],
                              ["1983-05-25", 6]
                          ]
                      }"""
        time_series = from_database(releases, value_type="time_series")
        self.assertEqual(
            time_series.indexes,
            numpy.array(
                [numpy.datetime64("1977-05-25"), numpy.datetime64("1980-05-21"), numpy.datetime64("1983-05-25")],
                dtype="datetime64[D]",
            ),
        )
        self.assertEqual(len(time_series), 3)
        self.assertTrue(isinstance(time_series.values, numpy.ndarray))
        numpy.testing.assert_equal(time_series.values, numpy.array([4, 5, 6]))

    def test_from_database_TimeSeriesFixedResolution_default_repeat(self):
        database_value = """{
                                   "type": "time_series",
                                   "index": {
                                       "ignore_year": true
                                   },
                                   "data": [["2019-07-02T10:00:00", 7.0],
                                            ["2019-07-02T10:00:01", 4.0]]
                               }"""
        time_series = from_database(database_value, value_type="time_series")
        self.assertTrue(time_series.ignore_year)
        self.assertFalse(time_series.repeat)

    def test_TimeSeriesVariableResolution_to_database(self):
        dates = numpy.array(["1999-05-19", "2002-05-16", "2005-05-19"], dtype="datetime64[D]")
        episodes = numpy.array([1, 2, 3], dtype=float)
        value = TimeSeriesVariableResolution(dates, episodes, False, False)
        db_value, value_type = value.to_database()
        releases = json.loads(db_value)
        self.assertEqual(releases, {"type": "time_series", "data": {"1999-05-19": 1, "2002-05-16": 2, "2005-05-19": 3}})
        self.assertEqual(value_type, "time_series")

    def test_TimeSeriesVariableResolution_to_database_with_ignore_year_and_repeat(self):
        dates = numpy.array(["1999-05-19", "2002-05-16", "2005-05-19"], dtype="datetime64[D]")
        episodes = numpy.array([1, 2, 3], dtype=float)
        value = TimeSeriesVariableResolution(dates, episodes, True, True)
        db_value, value_type = value.to_database()
        releases = json.loads(db_value)
        self.assertEqual(
            releases,
            {
                "type": "time_series",
                "data": {"1999-05-19": 1, "2002-05-16": 2, "2005-05-19": 3},
                "index": {"ignore_year": True, "repeat": True},
            },
        )
        self.assertEqual(value_type, "time_series")

    def test_from_database_TimeSeriesFixedResolution(self):
        days_of_our_lives = """{
                                   "type": "time_series",
                                   "index": {
                                       "start": "2019-03-23",
                                       "resolution": "1 day",
                                       "ignore_year": false,
                                       "repeat": false
                                   },
                                   "data": [7.0, 5.0, 8.1]
                               }"""
        time_series = from_database(days_of_our_lives, value_type="time_series")
        self.assertEqual(len(time_series), 3)
        self.assertEqual(
            time_series.indexes,
            numpy.array(
                [numpy.datetime64("2019-03-23"), numpy.datetime64("2019-03-24"), numpy.datetime64("2019-03-25")],
                dtype="datetime64[s]",
            ),
        )
        self.assertTrue(isinstance(time_series.values, numpy.ndarray))
        numpy.testing.assert_equal(time_series.values, numpy.array([7.0, 5.0, 8.1]))
        self.assertEqual(time_series.start, dateutil.parser.parse("2019-03-23"))
        self.assertEqual(len(time_series.resolution), 1)
        self.assertEqual(time_series.resolution[0], relativedelta(days=1))
        self.assertFalse(time_series.ignore_year)
        self.assertFalse(time_series.repeat)

    def test_from_database_TimeSeriesFixedResolution_no_index(self):
        database_value = """{
                                "type": "time_series",
                                "data": [1, 2, 3, 4, 5, 8]
                            }
        """
        time_series = from_database(database_value, value_type="time_series")
        self.assertEqual(len(time_series), 6)
        self.assertEqual(
            time_series.indexes,
            numpy.array(
                [
                    numpy.datetime64("0001-01-01T00:00:00"),
                    numpy.datetime64("0001-01-01T01:00:00"),
                    numpy.datetime64("0001-01-01T02:00:00"),
                    numpy.datetime64("0001-01-01T03:00:00"),
                    numpy.datetime64("0001-01-01T04:00:00"),
                    numpy.datetime64("0001-01-01T05:00:00"),
                ],
                dtype="datetime64[s]",
            ),
        )
        numpy.testing.assert_equal(time_series.values, numpy.array([1.0, 2.0, 3.0, 4.0, 5.0, 8.0]))
        self.assertEqual(time_series.start, dateutil.parser.parse("0001-01-01T00:00:00"))
        self.assertEqual(len(time_series.resolution), 1)
        self.assertEqual(time_series.resolution[0], relativedelta(hours=1))
        self.assertTrue(time_series.ignore_year)
        self.assertTrue(time_series.repeat)

    def test_from_database_TimeSeriesFixedResolution_resolution_list(self):
        database_value = """{
                                "type": "time_series",
                                "index": {
                                    "start": "2019-01-31",
                                    "resolution": ["1 day", "1M"],
                                    "ignore_year": false,
                                    "repeat": false
                                },
                                "data": [7.0, 5.0, 8.1, -4.1]
                            }"""
        time_series = from_database(database_value, value_type="time_series")
        self.assertEqual(len(time_series), 4)
        self.assertEqual(
            time_series.indexes,
            numpy.array(
                [
                    numpy.datetime64("2019-01-31"),
                    numpy.datetime64("2019-02-01"),
                    numpy.datetime64("2019-03-01"),
                    numpy.datetime64("2019-03-02"),
                ],
                dtype="datetime64[s]",
            ),
        )
        numpy.testing.assert_equal(time_series.values, numpy.array([7.0, 5.0, 8.1, -4.1]))
        self.assertEqual(time_series.start, dateutil.parser.parse("2019-01-31"))
        self.assertEqual(len(time_series.resolution), 2)
        self.assertEqual(time_series.resolution, [relativedelta(days=1), relativedelta(months=1)])
        self.assertFalse(time_series.ignore_year)
        self.assertFalse(time_series.repeat)

    def test_from_database_TimeSeriesFixedResolution_default_resolution_is_1hour(self):
        database_value = """{
                                   "type": "time_series",
                                   "index": {
                                       "start": "2019-03-23",
                                       "ignore_year": false,
                                       "repeat": false
                                   },
                                   "data": [7.0, 5.0, 8.1]
                               }"""
        time_series = from_database(database_value, value_type="time_series")
        self.assertEqual(len(time_series), 3)
        self.assertEqual(len(time_series.resolution), 1)
        self.assertEqual(time_series.resolution[0], relativedelta(hours=1))

    def test_from_database_TimeSeriesFixedResolution_default_resolution_unit_is_minutes(self):
        database_value = """{
                                   "type": "time_series",
                                   "index": {
                                       "start": "2019-03-23",
                                       "resolution": 30
                                   },
                                   "data": [7.0, 5.0, 8.1]
                               }"""
        time_series = from_database(database_value, value_type="time_series")
        self.assertEqual(len(time_series), 3)
        self.assertEqual(len(time_series.resolution), 1)
        self.assertEqual(time_series.resolution[0], relativedelta(minutes=30))
        database_value = """{
                                   "type": "time_series",
                                   "index": {
                                       "start": "2019-03-23",
                                       "resolution": [30, 45]
                                   },
                                   "data": [7.0, 5.0, 8.1]
                               }"""
        time_series = from_database(database_value, value_type="time_series")
        self.assertEqual(len(time_series), 3)
        self.assertEqual(len(time_series.resolution), 2)
        self.assertEqual(time_series.resolution[0], relativedelta(minutes=30))
        self.assertEqual(time_series.resolution[1], relativedelta(minutes=45))

    def test_from_database_TimeSeriesFixedResolution_default_ignore_year(self):
        # Should be false if start is given
        database_value = """{
                                   "type": "time_series",
                                   "index": {
                                       "start": "2019-03-23",
                                       "resolution": "1 day",
                                       "repeat": false
                                   },
                                   "data": [7.0, 5.0, 8.1]
                               }"""
        time_series = from_database(database_value, value_type="time_series")
        self.assertFalse(time_series.ignore_year)
        # Should be true if start is omitted
        database_value = """{
                                   "type": "time_series",
                                   "index": {
                                       "resolution": "1 day",
                                       "repeat": false
                                   },
                                   "data": [7.0, 5.0, 8.1]
                               }"""
        time_series = from_database(database_value, value_type="time_series")
        self.assertTrue(time_series.ignore_year)

    def test_TimeSeriesFixedResolution_to_database(self):
        values = numpy.array([3, 2, 4], dtype=float)
        resolution = [duration_to_relativedelta("1 months")]
        start = datetime(year=2007, month=6, day=1)
        value = TimeSeriesFixedResolution(start, resolution, values, True, True)
        db_value, value_type = value.to_database()
        releases = json.loads(db_value)
        self.assertEqual(
            releases,
            {
                "type": "time_series",
                "index": {"start": "2007-06-01 00:00:00", "resolution": "1M", "ignore_year": True, "repeat": True},
                "data": [3, 2, 4],
            },
        )
        self.assertEqual(value_type, "time_series")

    def test_TimeSeriesFixedResolution_resolution_list_to_database(self):
        start = datetime(year=2007, month=1, day=1)
        resolutions = ["1 month", "1 year"]
        resolutions = [duration_to_relativedelta(r) for r in resolutions]
        values = numpy.array([3.0, 2.0, 4.0])
        value = TimeSeriesFixedResolution(start, resolutions, values, True, True)
        db_value, value_type = value.to_database()
        releases = json.loads(db_value)
        self.assertEqual(
            releases,
            {
                "type": "time_series",
                "index": {
                    "start": "2007-01-01 00:00:00",
                    "resolution": ["1M", "1Y"],
                    "ignore_year": True,
                    "repeat": True,
                },
                "data": [3.0, 2.0, 4.0],
            },
        )
        self.assertEqual(value_type, "time_series")

    def test_TimeSeriesFixedResolution_init_conversions(self):
        series = TimeSeriesFixedResolution("2019-01-03T00:30:33", "1D", [3.0, 2.0, 1.0], False, False)
        self.assertTrue(isinstance(series.start, datetime))
        self.assertTrue(isinstance(series.resolution, list))
        for element in series.resolution:
            self.assertTrue(isinstance(element, relativedelta))
        self.assertTrue(isinstance(series.values, numpy.ndarray))
        series = TimeSeriesFixedResolution("2019-01-03T00:30:33", ["2h", "4h"], [3.0, 2.0, 1.0], False, False)
        self.assertTrue(isinstance(series.resolution, list))
        for element in series.resolution:
            self.assertTrue(isinstance(element, relativedelta))

    def test_TimeSeriesVariableResolution_init_conversion(self):
        series = TimeSeriesVariableResolution(["2008-07-08T03:00", "2008-08-08T13:30"], [3.3, 4.4], True, True)
        self.assertTrue(isinstance(series.indexes, np.ndarray))
        for index in series.indexes:
            self.assertTrue(isinstance(index, np.datetime64))
        self.assertTrue(isinstance(series.values, np.ndarray))

    def test_from_database_Map_dictionary_format(self):
        database_value = '{"type":"map", "index_type":"str", "data":{"a": 1.1, "b": 2.2}}'
        value = from_database(database_value, value_type="map")
        self.assertIsInstance(value, Map)
        self.assertEqual(value.indexes, ["a", "b"])
        self.assertEqual(value.values, [1.1, 2.2])

    def test_from_database_Map_two_column_array_format(self):
        database_value = '{"type":"map", "index_type":"float", "data":[[1.1, "a"], [2.2, "b"]]}'
        value = from_database(database_value, value_type="map")
        self.assertIsInstance(value, Map)
        self.assertEqual(value.indexes, [1.1, 2.2])
        self.assertEqual(value.values, ["a", "b"])

    def test_from_database_Map_nested_maps(self):
        database_value = '''
        {
            "type": "map",
             "index_type": "duration",
              "data":[["1 hour", {"type": "map",
                                  "index_type": "date_time",
                                  "data": {"2020-01-01T12:00": {"type":"duration", "data":"3 hours"}}}]]
        }'''
        value = from_database(database_value, value_type="map")
        self.assertEqual(value.indexes, [Duration("1 hour")])
        nested_map = value.values[0]
        self.assertIsInstance(nested_map, Map)
        self.assertEqual(nested_map.indexes, [DateTime("2020-01-01T12:00")])
        self.assertEqual(nested_map.values, [Duration("3 hours")])

    def test_from_database_Map_with_TimeSeries_values(self):
        database_value = '''
        {
            "type": "map",
             "index_type": "duration",
              "data":[["1 hour", {"type": "time_series",
                                  "data": [["2020-01-01T12:00", -3.0], ["2020-01-02T12:00", -9.3]]
                                 }
                     ]]
        }'''
        value = from_database(database_value, value_type="map")
        self.assertEqual(value.indexes, [Duration("1 hour")])
        self.assertEqual(
            value.values,
            [TimeSeriesVariableResolution(["2020-01-01T12:00", "2020-01-02T12:00"], [-3.0, -9.3], False, False)],
        )

    def test_from_database_Map_with_Array_values(self):
        database_value = '''
        {
            "type": "map",
             "index_type": "duration",
              "data":[["1 hour", {"type": "array", "data": [-3.0, -9.3]}]]
        }'''
        value = from_database(database_value, value_type="map")
        self.assertEqual(value.indexes, [Duration("1 hour")])
        self.assertEqual(value.values, [Array([-3.0, -9.3])])

    def test_from_database_Map_with_TimePattern_values(self):
        database_value = '''
        {
            "type": "map",
             "index_type": "float",
              "data":[["2.3", {"type": "time_pattern", "data": {"1m,2m": -9.3, "3-12m": -3.9}}]]
        }'''
        value = from_database(database_value, value_type="map")
        self.assertEqual(value.indexes, [2.3])
        self.assertEqual(value.values, [TimePattern(["1m,2m", "3-12m"], [-9.3, -3.9])])

    def test_Map_to_database(self):
        map_value = Map(["a", "b"], [1.1, 2.2])
        db_value, value_type = to_database(map_value)
        raw = json.loads(db_value)
        self.assertEqual(raw, {"type": "map", "index_type": "str", "data": [["a", 1.1], ["b", 2.2]]})
        self.assertEqual(value_type, "map")

    def test_Map_to_database_with_TimeSeries_values(self):
        time_series1 = TimeSeriesVariableResolution(["2020-01-01T12:00", "2020-01-02T12:00"], [2.3, 4.5], False, False)
        time_series2 = TimeSeriesVariableResolution(
            ["2020-01-01T12:00", "2020-01-02T12:00"], [-4.5, -2.3], False, False
        )
        map_value = Map(["a", "b"], [time_series1, time_series2])
        db_value, value_type = to_database(map_value)
        raw = json.loads(db_value)
        expected = {
            "type": "map",
            "index_type": "str",
            "data": [
                ["a", {"type": "time_series", "data": {"2020-01-01T12:00:00": 2.3, "2020-01-02T12:00:00": 4.5}}],
                ["b", {"type": "time_series", "data": {"2020-01-01T12:00:00": -4.5, "2020-01-02T12:00:00": -2.3}}],
            ],
        }
        self.assertEqual(raw, expected)
        self.assertEqual(value_type, "map")

    def test_Map_to_database_nested_maps(self):
        nested_map = Map([Duration("2 months")], [Duration("5 days")])
        map_value = Map([DateTime("2020-01-01T13:00")], [nested_map])
        db_value, value_type = to_database(map_value)
        raw = json.loads(db_value)
        self.assertEqual(
            raw,
            {
                "type": "map",
                "index_type": "date_time",
                "data": [
                    [
                        "2020-01-01T13:00:00",
                        {"type": "map", "index_type": "duration", "data": [["2M", {"type": "duration", "data": "5D"}]]},
                    ]
                ],
            },
        )
        self.assertEqual(value_type, "map")

    def test_Array_of_floats_to_database(self):
        array = Array([-1.1, -2.2, -3.3])
        db_value, value_type = to_database(array)
        raw = json.loads(db_value)
        self.assertEqual(raw, {"type": "array", "value_type": "float", "data": [-1.1, -2.2, -3.3]})
        self.assertEqual(value_type, "array")

    def test_Array_of_strings_to_database(self):
        array = Array(["a", "b"])
        db_value, value_type = to_database(array)
        raw = json.loads(db_value)
        self.assertEqual(raw, {"type": "array", "value_type": "str", "data": ["a", "b"]})
        self.assertEqual(value_type, "array")

    def test_Array_of_DateTimes_to_database(self):
        array = Array([DateTime("2020-01-01T13:00")])
        db_value, value_type = to_database(array)
        raw = json.loads(db_value)
        self.assertEqual(raw, {"type": "array", "value_type": "date_time", "data": ["2020-01-01T13:00:00"]})
        self.assertEqual(value_type, "array")

    def test_Array_of_Durations_to_database(self):
        array = Array([Duration("4 months")])
        db_value, value_type = to_database(array)
        raw = json.loads(db_value)
        self.assertEqual(raw, {"type": "array", "value_type": "duration", "data": ["4M"]})
        self.assertEqual(value_type, "array")

    def test_Array_of_floats_from_database(self):
        database_value = """{
            "type": "array",
            "value_type": "float",
            "data": [1.2, 2.3]
        }"""
        array = from_database(database_value, value_type="array")
        self.assertEqual(array.values, [1.2, 2.3])
        self.assertEqual(array.indexes, [0, 1])

    def test_Array_of_default_value_type_from_database(self):
        database_value = """{
            "type": "array",
            "data": [1.2, 2.3]
        }"""
        array = from_database(database_value, value_type="array")
        self.assertEqual(array.values, [1.2, 2.3])
        self.assertEqual(array.indexes, [0, 1])

    def test_Array_of_strings_from_database(self):
        database_value = """{
            "type": "array",
            "value_type": "str",
            "data": ["A", "B"]
        }"""
        array = from_database(database_value, value_type="array")
        self.assertEqual(array.values, ["A", "B"])
        self.assertEqual(array.indexes, [0, 1])

    def test_Array_of_DateTimes_from_database(self):
        database_value = """{
            "type": "array",
            "value_type": "date_time",
            "data": ["2020-03-25T10:34:00"]
        }"""
        array = from_database(database_value, value_type="array")
        self.assertEqual(array.values, [DateTime("2020-03-25T10:34:00")])
        self.assertEqual(array.indexes, [0])

    def test_Array_of_Durations_from_database(self):
        database_value = """{
            "type": "array",
            "value_type": "duration",
            "data": ["2 years", "7 seconds"]
        }"""
        array = from_database(database_value, value_type="array")
        self.assertEqual(array.values, [Duration("2 years"), Duration("7s")])
        self.assertEqual(array.indexes, [0, 1])

    def test_DateTime_copy_construction(self):
        date_time = DateTime("2019-07-03T09:09:09")
        copied = DateTime(date_time)
        self.assertEqual(copied, date_time)

    def test_Duration_copy_construction(self):
        duration = Duration("3 minutes")
        copied = Duration(duration)
        self.assertEqual(copied, duration)

    def test_DateTime_equality(self):
        date_time = DateTime(dateutil.parser.parse("2019-07-03T09:09:09"))
        self.assertEqual(date_time, date_time)
        equal_date_time = DateTime(dateutil.parser.parse("2019-07-03T09:09:09"))
        self.assertEqual(date_time, equal_date_time)
        inequal_date_time = DateTime(dateutil.parser.parse("2018-07-03T09:09:09"))
        self.assertNotEqual(date_time, inequal_date_time)

    def test_Duration_equality(self):
        duration = Duration(duration_to_relativedelta("3 minutes"))
        self.assertEqual(duration, duration)
        equal_duration = Duration(duration_to_relativedelta("3m"))
        self.assertEqual(duration, equal_duration)
        inequal_duration = Duration(duration_to_relativedelta("3 seconds"))
        self.assertNotEqual(duration, inequal_duration)

    def test_Map_equality(self):
        map_value = Map(["a"], [-2.3])
        self.assertEqual(map_value, Map(["a"], [-2.3]))
        nested_map = Map(["a"], [-2.3])
        map_value = Map(["A"], [nested_map])
        self.assertEqual(map_value, Map(["A"], [Map(["a"], [-2.3])]))

    def test_TimePattern_equality(self):
        pattern = TimePattern(["1d", "2-7d"], np.array([-2.3, -5.0]))
        self.assertEqual(pattern, pattern)
        equal_pattern = TimePattern(["1d", "2-7d"], np.array([-2.3, -5.0]))
        self.assertEqual(pattern, equal_pattern)
        inequal_pattern = TimePattern(["1-3m", "4-12m"], np.array([-5.0, 23.0]))
        self.assertNotEqual(pattern, inequal_pattern)

    def test_TimeSeriesFixedResolution_equality(self):
        series = TimeSeriesFixedResolution("2019-01-03T00:30:33", "1D", [3.0, 2.0, 1.0], False, False)
        self.assertEqual(series, series)
        equal_series = TimeSeriesFixedResolution("2019-01-03T00:30:33", "1D", [3.0, 2.0, 1.0], False, False)
        self.assertEqual(series, equal_series)
        inequal_series = TimeSeriesFixedResolution("2019-01-03T00:30:33", "1D", [3.0, 2.0, 1.0], True, False)
        self.assertNotEqual(series, inequal_series)

    def test_TimeSeriesVariableResolution_equality(self):
        series = TimeSeriesVariableResolution(["2000-01-01T00:00", "2001-01-01T00:00"], [4.2, 2.4], True, True)
        self.assertEqual(series, series)
        equal_series = TimeSeriesVariableResolution(["2000-01-01T00:00", "2001-01-01T00:00"], [4.2, 2.4], True, True)
        self.assertEqual(series, equal_series)
        inequal_series = TimeSeriesVariableResolution(["2000-01-01T00:00", "2002-01-01T00:00"], [4.2, 2.4], False, True)
        self.assertNotEqual(series, inequal_series)

    def test_IndexedValue_constructor_converts_values_to_floats(self):
        value = IndexedNumberArray([4, -9, 11])
        self.assertEqual(value.values.dtype, np.dtype(float))
        numpy.testing.assert_equal(value.values, numpy.array([4.0, -9.0, 11.0]))
        value = IndexedNumberArray(numpy.array([16, -251, 99]))
        self.assertEqual(value.values.dtype, np.dtype(float))
        numpy.testing.assert_equal(value.values, numpy.array([16.0, -251.0, 99.0]))

    def test_Map_is_nested(self):
        map_value = Map(["a"], [-2.3])
        self.assertFalse(map_value.is_nested())
        nested_map = Map(["a"], [-2.3])
        map_value = Map(["A"], [nested_map])
        self.assertTrue(map_value.is_nested())

    def test_convert_leaf_maps_to_specialized_containers_non_nested_map(self):
        map_value = Map([DateTime("2000-01-01T00:00"), DateTime("2000-01-02T00:00")], [-3.2, -2.3])
        converted = convert_leaf_maps_to_specialized_containers(map_value)
        self.assertEqual(
            converted,
            TimeSeriesVariableResolution(["2000-01-01T00:00", "2000-01-02T00:00"], [-3.2, -2.3], False, False),
        )

    def test_convert_leaf_maps_to_specialized_containers_no_conversion(self):
        map_value = Map(["a", "b"], [-3.2, -2.3])
        converted = convert_leaf_maps_to_specialized_containers(map_value)
        self.assertEqual(converted, map_value)

    def test_convert_leaf_maps_to_specialized_containers_nested_map(self):
        nested1 = Map(["a", "b"], [-3.2, -2.3])
        nested2 = Map([DateTime("2000-01-01T00:00"), DateTime("2000-01-02T00:00")], [-3.2, -2.3])
        map_value = Map([1.0, 2.0, 3.0], [nested1, nested2, 4.4])
        converted = convert_leaf_maps_to_specialized_containers(map_value)
        time_series = TimeSeriesVariableResolution(["2000-01-01T00:00", "2000-01-02T00:00"], [-3.2, -2.3], False, False)
        expected = Map([1.0, 2.0, 3.0], [nested1, time_series, 4.4])
        self.assertEqual(converted, expected)

    def test_convert_non_nested_map_to_table(self):
        map_ = Map(["a", "b"], [-3.2, -2.3])
        table = convert_map_to_table(map_)
        self.assertEqual(table, [["a", -3.2], ["b", -2.3]])

    def test_convert_nested_map_to_table(self):
        map1 = Map(["a", "b"], [-3.2, -2.3])
        map2 = Map(["c", "d"], [3.2, 2.3])
        nested_map = Map(["A", "B"], [map1, map2])
        table = convert_map_to_table(nested_map)
        self.assertEqual(table, [["A", "a", -3.2], ["A", "b", -2.3], ["B", "c", 3.2], ["B", "d", 2.3]])

    def test_convert_uneven_nested_map_to_table(self):
        map1 = Map(["a", "b"], [-3.2, -2.3])
        nested_map = Map(["A", "B"], [map1, 42.0])
        table = convert_map_to_table(nested_map, False)
        self.assertEqual(table, [["A", "a", -3.2], ["A", "b", -2.3], ["B", 42.0]])

    def test_convert_nested_map_to_table_with_padding(self):
        map1 = Map(["a", "b"], [-3.2, -2.3])
        nested_map = Map(["A", "B"], [map1, 42.0])
        table = convert_map_to_table(nested_map, True)
        self.assertEqual(table, [["A", "a", -3.2], ["A", "b", -2.3], ["B", 42.0, None]])

    def test_convert_containers_to_maps_empty_map(self):
        self.assertEqual(convert_containers_to_maps(Map([], [], str)), Map([], [], str))

    def test_convert_containers_to_maps_time_series(self):
        time_series = TimeSeriesVariableResolution(["2020-11-27T12:55", "2020-11-27T13:00"], [2.5, 2.3], False, False)
        map_ = convert_containers_to_maps(time_series)
        self.assertEqual(map_, Map([DateTime("2020-11-27T12:55"), DateTime("2020-11-27T13:00")], [2.5, 2.3]))

    def test_convert_containers_to_maps_map_with_time_series(self):
        time_series = TimeSeriesVariableResolution(["2020-11-27T12:55", "2020-11-27T13:00"], [2.5, 2.3], False, False)
        map_ = Map(["a", "b"], [-1.1, time_series])
        converted = convert_containers_to_maps(map_)
        expected = Map(
            ["a", "b"], [-1.1, Map([DateTime("2020-11-27T12:55"), DateTime("2020-11-27T13:00")], [2.5, 2.3])]
        )
        self.assertEqual(converted, expected)

    def convert_map_to_dict(self):
        map1 = Map(["a", "b"], [-3.2, -2.3])
        map2 = Map(["c", "d"], [3.2, 2.3])
        nested_map = Map(["A", "B"], [map1, map2])
        self.assertEqual(nested_map, {"A": {"a": -3.2, "b": -2.3}, "B": {"c": 3.2, "d": 2.3}})


if __name__ == "__main__":
    unittest.main()
