######################################################################################################################
# Copyright (C) 2017 - 2020 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
Functions for exporting data into a Spine database using entity names as references.

:author: M. Marin (KTH)
:date:   1.4.2020
"""

from .parameter_value import from_database


def export_data(
    db_map,
    object_class_ids=None,
    relationship_class_ids=None,
    parameter_value_list_ids=None,
    object_parameter_ids=None,
    relationship_parameter_ids=None,
    object_ids=None,
    relationship_ids=None,
    object_parameter_value_ids=None,
    relationship_parameter_value_ids=None,
    alternative_ids=None,
    scenario_ids=None,
    scenario_alternative_ids=None
):
    """
    Exports data from given database into a dictionary that can be splatted into keyword arguments for ``import_data``.

    Args:
        db_map (DiffDatabaseMapping): The db to pull stuff from.
        object_class_ids (Iterable, optional): A collection of ids to pick from the database table
        relationship_class_ids (Iterable, optional): A collection of ids to pick from the database table
        parameter_value_list_ids (Iterable, optional): A collection of ids to pick from the database table
        object_parameter_ids (Iterable, optional): A collection of ids to pick from the database table
        relationship_parameter_ids (Iterable, optional): A collection of ids to pick from the database table
        object_ids (Iterable, optional): A collection of ids to pick from the database table
        relationship_ids (Iterable, optional): A collection of ids to pick from the database table
        object_parameter_value_ids (Iterable, optional): A collection of ids to pick from the database table
        relationship_parameter_value_ids (Iterable, optional): A collection of ids to pick from the database table
        alternative_ids (Iterable, optional): A collection of ids to pick from the database table
        scenario_ids (Iterable, optional): A collection of ids to pick from the database table
        scenario_alternative_ids (Iterable, optional): A collection of ids to pick from the database table

    Returns:
        dict: exported data
    """
    data = {
        "object_classes": export_object_classes(db_map, object_class_ids),
        "relationship_classes": export_relationship_classes(db_map, relationship_class_ids),
        "parameter_value_lists": export_parameter_value_lists(db_map, parameter_value_list_ids),
        "object_parameters": export_object_parameters(db_map, object_parameter_ids),
        "relationship_parameters": export_relationship_parameters(db_map, relationship_parameter_ids),
        "objects": export_objects(db_map, object_ids),
        "relationships": export_relationships(db_map, relationship_ids),
        "object_parameter_values": export_object_parameter_values(db_map, object_parameter_value_ids),
        "relationship_parameter_values": export_relationship_parameter_values(db_map, relationship_parameter_value_ids),
        "alternatives": export_alternatives(db_map, alternative_ids),
        "scenarios": export_scenarios(db_map, scenario_ids),
        "scenario_alternatives": export_scenario_alternatives(db_map, scenario_alternative_ids),
    }
    return {key: value for key, value in data.items() if value}


def export_object_classes(db_map, ids):
    sq = db_map.object_class_sq
    return sorted((x.name, x.description, x.display_icon) for x in db_map.query(sq).filter(db_map.in_(sq.c.id, ids)))


def export_objects(db_map, ids):
    sq = db_map.ext_object_sq
    return sorted((x.class_name, x.name, x.description) for x in db_map.query(sq).filter(db_map.in_(sq.c.id, ids)))


def export_relationship_classes(db_map, ids):
    sq = db_map.wide_relationship_class_sq
    return sorted(
        (x.name, x.object_class_name_list.split(","), x.description)
        for x in db_map.query(sq).filter(db_map.in_(sq.c.id, ids))
    )


def export_parameter_value_lists(db_map, ids):
    sq = db_map.wide_parameter_value_list_sq
    return sorted(
        (x.name, [from_database(value) for value in x.value_list.split(";")])
        for x in db_map.query(sq).filter(db_map.in_(sq.c.id, ids))
    )


def export_object_parameters(db_map, ids):
    sq = db_map.object_parameter_definition_sq
    return sorted(
        (x.object_class_name, x.parameter_name, from_database(x.default_value), x.value_list_name, x.description)
        for x in db_map.query(sq).filter(db_map.in_(sq.c.id, ids))
    )


def export_relationship_parameters(db_map, ids):
    sq = db_map.relationship_parameter_definition_sq
    return sorted(
        (x.relationship_class_name, x.parameter_name, from_database(x.default_value), x.value_list_name, x.description)
        for x in db_map.query(sq).filter(db_map.in_(sq.c.id, ids))
    )


def export_relationships(db_map, ids):
    sq = db_map.wide_relationship_sq
    return sorted(
        (x.class_name, x.object_name_list.split(",")) for x in db_map.query(sq).filter(db_map.in_(sq.c.id, ids))
    )


def export_object_parameter_values(db_map, ids):
    sq = db_map.object_parameter_value_sq
    return sorted(
        (x.object_class_name, x.object_name, x.parameter_name, from_database(x.value))
        for x in db_map.query(sq).filter(db_map.in_(sq.c.id, ids))
    )


def export_relationship_parameter_values(db_map, ids):
    sq = db_map.relationship_parameter_value_sq
    return sorted(
        (x.relationship_class_name, x.object_name_list.split(","), x.parameter_name, from_database(x.value))
        for x in db_map.query(sq).filter(db_map.in_(sq.c.id, ids))
    )


def export_alternatives(db_map, ids):
    """
    Exports alternatives from database.

    The format is what :func:`import_alternatives` accepts as its input.

    Args:
        db_map (spinedb_api.DatabaseMapping or spinedb_api.DiffDatabaseMapping): a database map
        ids (Iterable, optional): ids of the alternatives to export

    Returns:
        Iterable: tuples of two elements: name of alternative and description
    """
    sq = db_map.alternative_sq
    return sorted((x.name, x.description) for x in db_map.query(sq).filter(db_map.in_(sq.c.id, ids)))


def export_scenarios(db_map, ids):
    """
    Exports scenarios from database.

    The format is what :func:`import_scenarios` accepts as its input.

    Args:
        db_map (spinedb_api.DatabaseMapping or spinedb_api.DiffDatabaseMapping): a database map
        ids (Iterable, optional): ids of the scenarios to export

    Returns:
        Iterable: tuples of two elements: name of scenario and description
    """
    sq = db_map.scenario_sq
    return sorted((x.name, x.description) for x in db_map.query(sq).filter(db_map.in_(sq.c.id, ids)))


def export_scenario_alternatives(db_map, ids):
    """
    Exports scenario alternatives from database.

    The format is what :func:`import_scenario_alternatives` accepts as its input.

    Args:
        db_map (spinedb_api.DatabaseMapping or spinedb_api.DiffDatabaseMapping): a database map
        ids (Iterable, optional): ids of the scenario alternatives to export

    Returns:
        Iterable: tuples of two elements: name of scenario and list containing tuples of alternative names and ranks
    """
    items = dict()
    alternatives = {a.id: a.name for a in db_map.query(db_map.alternative_sq)}
    scenarios = {s.id: s.name for s in db_map.query(db_map.scenario_sq)}
    sq = db_map.scenario_alternative_sq
    for scenario_alternative in db_map.query(sq).filter(db_map.in_(sq.c.id, ids)):
        alternative = alternatives[scenario_alternative.alternative_id]
        scenario = scenarios[scenario_alternative.scenario_id]
        rank = scenario_alternative.rank
        items.setdefault(scenario, list()).append((alternative, rank))
    return sorted(items.items())
