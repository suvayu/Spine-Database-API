######################################################################################################################
# Copyright (C) 2017 - 2019 Spine project consortium
# This file is part of Spine Database API.
# Spine Database API is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser
# General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your
# option) any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""Provides :class:`.DiffDatabaseMappingAddMixin`.

:author: Manuel Marin (KTH)
:date:   11.8.2018
"""
# TODO: improve docstrings

from datetime import datetime
from sqlalchemy import func, Column, Integer, String, null
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import DBAPIError
from .exception import SpineDBAPIError
from .helpers import get_relationship_entity_class_items, get_relationship_entity_items, get_parameter_value_list_items


class DiffDatabaseMappingAddMixin:
    """Provides methods to stage ``INSERT`` operations over a Spine db.
    """

    class NextId(declarative_base()):
        __tablename__ = "next_id"

        user = Column(String(155), primary_key=True)
        date = Column(String(155), primary_key=True)
        entity_id = Column(Integer, server_default=null())
        entity_class_id = Column(Integer, server_default=null())
        entity_group_id = Column(Integer, server_default=null())
        parameter_definition_id = Column(Integer, server_default=null())
        parameter_value_id = Column(Integer, server_default=null())
        parameter_tag_id = Column(Integer, server_default=null())
        parameter_value_list_id = Column(Integer, server_default=null())
        parameter_definition_tag_id = Column(Integer, server_default=null())
        alternative_id = Column(Integer, server_default=null())
        scenario_id = Column(Integer, server_default=null())
        scenario_alternative_id = Column(Integer, server_default=null())
        tool_id = Column(Integer, server_default=null())
        feature_id = Column(Integer, server_default=null())
        tool_feature_id = Column(Integer, server_default=null())
        tool_feature_method_id = Column(Integer, server_default=null())
        metadata_id = Column(Integer, server_default=null())
        parameter_value_metadata_id = Column(Integer, server_default=null())
        entity_metadata_id = Column(Integer, server_default=null())

    def __init__(self, *args, **kwargs):
        """Initialize class."""
        super().__init__(*args, **kwargs)
        self.NextId.__table__.create(self.connection, checkfirst=True)

    def _next_id_row(self):
        """Returns the next_id row."""
        next_id = self.query(self.NextId).one_or_none()
        if next_id:
            next_id.user = self.username
            next_id.date = datetime.utcnow()
        else:
            next_id = self.NextId(user=self.username, date=datetime.utcnow())
            self.session.add(next_id)
        try:
            # TODO: This flush is supposed to lock the record, so no one can steal our ids.... does it work?
            self.session.flush()
        except DBAPIError as e:
            # TODO: Find a way to try this again, or wait till unlocked
            # Maybe listen for an event?
            self.session.rollback()
            raise SpineDBAPIError("Unable to get next id: {}".format(e.orig.args))
        return self.query(self.NextId).one_or_none()

    def _next_id(self, tablename, next_id_candidate=None):
        classname = {
            "object_class": "EntityClass",
            "object": "Entity",
            "relationship_class": "EntityClass",
            "relationship": "Entity",
            "entity_group": "EntityGroup",
            "parameter_definition": "ParameterDefinition",
            "parameter_value": "ParameterValue",
            "parameter_tag": "ParameterTag",
            "parameter_definition_tag": "ParameterDefinitionTag",
            "parameter_value_list": "ParameterValueList",
            "alternative": "Alternative",
            "scenario": "Scenario",
            "scenario_alternative": "ScenarioAlternative",
            "tool": "Tool",
            "feature": "Feature",
            "tool_feature": "ToolFeature",
            "tool_feature_method": "ToolFeatureMethod",
            "metadata": "Metadata",
            "parameter_value_metadata": "ParameterValueMetadata",
            "entity_metadata": "EntityMetadata",
        }[tablename]
        class_ = getattr(self, classname)
        max_id = self.query(func.max(class_.id)).scalar()
        next_id = max_id + 1 if max_id else 1
        if next_id_candidate is None:
            return next_id
        return max(next_id_candidate, next_id)

    def _items_and_ids(self, tablename, *items):
        if not items:
            return [], set()
        fieldname = {
            "object_class": "entity_class_id",
            "object": "entity_id",
            "relationship_class": "entity_class_id",
            "relationship": "entity_id",
            "entity_group": "entity_group_id",
            "parameter_definition": "parameter_definition_id",
            "parameter_value": "parameter_value_id",
            "parameter_tag": "parameter_tag_id",
            "parameter_value_list": "parameter_value_list_id",
            "parameter_definition_tag": "parameter_definition_tag_id",
            "alternative": "alternative_id",
            "scenario": "scenario_id",
            "scenario_alternative": "scenario_alternative_id",
            "tool": "tool_id",
            "feature": "feature_id",
            "tool_feature": "tool_feature_id",
            "tool_feature_method": "tool_feature_method_id",
            "metadata": "metadata_id",
            "parameter_value_metadata": "parameter_value_metadata_id",
            "entity_metadata": "entity_metadata_id",
        }[tablename]
        next_id_row = self._next_id_row()
        next_id = getattr(next_id_row, fieldname)
        next_id = self._next_id(tablename, next_id)
        ids = list(range(next_id, next_id + len(items)))
        items_to_add = list()
        append_item = items_to_add.append
        for id_, item in zip(ids, items):
            item["id"] = id_
            append_item(item)
        next_id = ids[-1] + 1
        setattr(next_id_row, fieldname, next_id)
        return items_to_add, set(ids)

    def add_features(self, *items, strict=False, return_dups=False):
        """Stage features items for insertion.

        :param Iterable items: One or more Python :class:`dict` objects representing the items to be inserted.
        :param bool strict: Whether or not the method should raise :exc:`~.exception.SpineIntegrityError`
            if the insertion of one of the items violates an integrity constraint.
        :param bool return_dups: Whether or not already existing and duplicated entries should also be returned.

        :returns:
            - **new_items** -- A list of items succesfully staged for insertion.
            - **intgr_error_log** -- A list of :exc:`~.exception.SpineIntegrityError` instances corresponding
              to found violations.
        """
        checked_items, intgr_error_log = self.check_features_for_insert(*items, strict=strict)
        ids = self._add_features(*checked_items)
        if return_dups:
            ids.update(set(x.id for x in intgr_error_log if x.id))
        return ids, intgr_error_log

    def _add_features(self, *items):
        """Add object classes to database without checking integrity.

        Args:
            items (iter): list of dictionaries which correspond to the instances to add
            strict (bool): if True SpineIntegrityError are raised. Otherwise
                they are catched and returned as a log

        Returns:
            ids (set): added instances' ids
        """
        items_to_add, ids = self._items_and_ids("feature", *items)
        self._do_add_features(*items_to_add)
        self.added_item_id["feature"].update(ids)
        return ids

    def _do_add_features(self, *items_to_add):
        try:
            self.session.bulk_insert_mappings(self.DiffFeature, items_to_add)
            self.session.commit()
        except DBAPIError as e:
            self.session.rollback()
            msg = "DBAPIError while inserting features: {}".format(e.orig.args)
            raise SpineDBAPIError(msg)

    def readd_features(self, *items):
        """Add known features to database.
        """
        self._do_add_features(*items)
        ids = set(x["id"] for x in items)
        self.added_item_id["feature"].update(ids)
        return ids, []

    def add_tools(self, *items, strict=False, return_dups=False):
        """Stage tools items for insertion.

        :param Iterable items: One or more Python :class:`dict` objects representing the items to be inserted.
        :param bool strict: Whether or not the method should raise :exc:`~.exception.SpineIntegrityError`
            if the insertion of one of the items violates an integrity constraint.
        :param bool return_dups: Whether or not already existing and duplicated entries should also be returned.

        :returns:
            - **new_items** -- A list of items succesfully staged for insertion.
            - **intgr_error_log** -- A list of :exc:`~.exception.SpineIntegrityError` instances corresponding
              to found violations.
        """
        checked_items, intgr_error_log = self.check_tools_for_insert(*items, strict=strict)
        ids = self._add_tools(*checked_items)
        if return_dups:
            ids.update(set(x.id for x in intgr_error_log if x.id))
        return ids, intgr_error_log

    def _add_tools(self, *items):
        """Add tools to database without checking integrity.

        Args:
            items (iter): list of dictionaries which correspond to the instances to add
            strict (bool): if True SpineIntegrityError are raised. Otherwise
                they are catched and returned as a log

        Returns:
            ids (set): added instances' ids
        """
        items_to_add, ids = self._items_and_ids("tool", *items)
        self._do_add_tools(*items_to_add)
        self.added_item_id["tool"].update(ids)
        return ids

    def _do_add_tools(self, *items_to_add):
        try:
            self.session.bulk_insert_mappings(self.DiffTool, items_to_add)
            self.session.commit()
        except DBAPIError as e:
            self.session.rollback()
            msg = "DBAPIError while inserting tools: {}".format(e.orig.args)
            raise SpineDBAPIError(msg)

    def readd_tools(self, *items):
        """Add known tools to database.
        """
        self._do_add_tools(*items)
        ids = set(x["id"] for x in items)
        self.added_item_id["tool"].update(ids)
        return ids, []

    def add_tool_features(self, *items, strict=False, return_dups=False):
        """Stage tool feature items for insertion.

        :param Iterable items: One or more Python :class:`dict` objects representing the items to be inserted.
        :param bool strict: Whether or not the method should raise :exc:`~.exception.SpineIntegrityError`
            if the insertion of one of the items violates an integrity constraint.
        :param bool return_dups: Whether or not already existing and duplicated entries should also be returned.

        :returns:
            - **new_items** -- A list of items succesfully staged for insertion.
            - **intgr_error_log** -- A list of :exc:`~.exception.SpineIntegrityError` instances corresponding
              to found violations.
        """
        checked_items, intgr_error_log = self.check_tool_features_for_insert(*items, strict=strict)
        ids = self._add_tool_features(*checked_items)
        if return_dups:
            ids.update(set(x.id for x in intgr_error_log if x.id))
        return ids, intgr_error_log

    def _add_tool_features(self, *items):
        """Add tool features to database without checking integrity.

        Args:
            items (iter): list of dictionaries which correspond to the instances to add
            strict (bool): if True SpineIntegrityError are raised. Otherwise
                they are catched and returned as a log

        Returns:
            ids (set): added instances' ids
        """
        items_to_add, ids = self._items_and_ids("tool_feature", *items)
        self._do_add_tool_features(*items_to_add)
        self.added_item_id["tool_feature"].update(ids)
        return ids

    def _do_add_tool_features(self, *items_to_add):
        try:
            self.session.bulk_insert_mappings(self.DiffToolFeature, items_to_add)
            self.session.commit()
        except DBAPIError as e:
            self.session.rollback()
            msg = "DBAPIError while inserting tool features: {}".format(e.orig.args)
            raise SpineDBAPIError(msg)

    def readd_tool_features(self, *items):
        """Add known tool-features to database.
        """
        self._do_add_tool_features(*items)
        ids = set(x["id"] for x in items)
        self.added_item_id["tool_feature"].update(ids)
        return ids, []

    def add_tool_feature_methods(self, *items, strict=False, return_dups=False):
        """Stage tool feature method items for insertion.

        :param Iterable items: One or more Python :class:`dict` objects representing the items to be inserted.
        :param bool strict: Whether or not the method should raise :exc:`~.exception.SpineIntegrityError`
            if the insertion of one of the items violates an integrity constraint.
        :param bool return_dups: Whether or not already existing and duplicated entries should also be returned.

        :returns:
            - **new_items** -- A list of items succesfully staged for insertion.
            - **intgr_error_log** -- A list of :exc:`~.exception.SpineIntegrityError` instances corresponding
              to found violations.
        """
        checked_items, intgr_error_log = self.check_tool_feature_methods_for_insert(*items, strict=strict)
        ids = self._add_tool_feature_methods(*checked_items)
        if return_dups:
            ids.update(set(x.id for x in intgr_error_log if x.id))
        return ids, intgr_error_log

    def _add_tool_feature_methods(self, *items):
        """Add tool feature method items to database without checking integrity.

        Args:
            items (iter): list of dictionaries which correspond to the instances to add
            strict (bool): if True SpineIntegrityError are raised. Otherwise
                they are catched and returned as a log

        Returns:
            ids (set): added instances' ids
        """
        items_to_add, ids = self._items_and_ids("tool_feature_method", *items)
        self._do_add_tool_feature_methods(*items_to_add)
        self.added_item_id["tool_feature_method"].update(ids)
        return ids

    def _do_add_tool_feature_methods(self, *items_to_add):
        try:
            self.session.bulk_insert_mappings(self.DiffToolFeatureMethod, items_to_add)
            self.session.commit()
        except DBAPIError as e:
            self.session.rollback()
            msg = "DBAPIError while inserting tool feature methods: {}".format(e.orig.args)
            raise SpineDBAPIError(msg)

    def readd_tool_feature_methods(self, *items):
        """Add known tool feature methods to database.
        """
        self._do_add_tool_feature_methods(*items)
        ids = set(x["id"] for x in items)
        self.added_item_id["tool_feature_method"].update(ids)
        return ids, []

    def add_alternatives(self, *items, strict=False, return_dups=False):
        """Stage alternatives for insertion.

        :param Iterable items: One or more Python :class:`dict` objects representing the items to be inserted.
        :param bool strict: Whether or not the method should raise :exc:`~.exception.SpineIntegrityError`
            if the insertion of one of the items violates an integrity constraint.
        :param bool return_dups: Whether or not already existing and duplicated entries should also be returned.

        :returns:
            - **new_items** -- A list of items succesfully staged for insertion.
            - **intgr_error_log** -- A list of :exc:`~.exception.SpineIntegrityError` instances corresponding
              to found violations.
        """
        checked_items, intgr_error_log = self.check_alternatives_for_insert(*items, strict=strict)
        ids = self._add_alternatives(*checked_items)
        if return_dups:
            ids.update(set(x.id for x in intgr_error_log if x.id))
        return ids, intgr_error_log

    def _add_alternatives(self, *items):
        """Add alternatives to database without checking integrity.

        Args:
            items (iter): list of dictionaries which correspond to the instances to add
            strict (bool): if True SpineIntegrityError are raised. Otherwise
                they are catched and returned as a log

        Returns:
            ids (set): added instances' ids
        """
        items_to_add, ids = self._items_and_ids("alternative", *items)
        self._do_add_alternatives(*items_to_add)
        self.added_item_id["alternative"].update(ids)
        return ids

    def _do_add_alternatives(self, *items_to_add):
        try:
            self.session.bulk_insert_mappings(self.DiffAlternative, items_to_add)
            self.session.commit()
        except DBAPIError as e:
            self.session.rollback()
            msg = "DBAPIError while inserting alternatives: {}".format(e.orig.args)
            raise SpineDBAPIError(msg)

    def readd_alternatives(self, *items):
        """Add known alternatives to database.
        """
        self._do_add_alternatives(*items)
        ids = set(x["id"] for x in items)
        self.added_item_id["alternative"].update(ids)
        return ids, []

    def add_scenarios(self, *items, strict=False, return_dups=False):
        """Stage scenarios for insertion.

        :param Iterable items: One or more Python :class:`dict` objects representing the items to be inserted.
        :param bool strict: Whether or not the method should raise :exc:`~.exception.SpineIntegrityError`
            if the insertion of one of the items violates an integrity constraint.
        :param bool return_dups: Whether or not already existing and duplicated entries should also be returned.

        :returns:
            - **new_items** -- A list of items succesfully staged for insertion.
            - **intgr_error_log** -- A list of :exc:`~.exception.SpineIntegrityError` instances corresponding
              to found violations.
        """
        checked_items, intgr_error_log = self.check_scenarios_for_insert(*items, strict=strict)
        ids = self._add_scenarios(*checked_items)
        if return_dups:
            ids.update(set(x.id for x in intgr_error_log if x.id))
        return ids, intgr_error_log

    def _add_scenarios(self, *items):
        """Add scenarios to database without checking integrity.

        Args:
            items (iter): list of dictionaries which correspond to the instances to add
            strict (bool): if True SpineIntegrityError are raised. Otherwise
                they are catched and returned as a log

        Returns:
            ids (set): added instances' ids
        """
        items_to_add, ids = self._items_and_ids("scenario", *items)
        self._do_add_scenarios(*items_to_add)
        self.added_item_id["scenario"].update(ids)
        return ids

    def _do_add_scenarios(self, *items_to_add):
        try:
            self.session.bulk_insert_mappings(self.DiffScenario, items_to_add)
            self.session.commit()
        except DBAPIError as e:
            self.session.rollback()
            msg = "DBAPIError while inserting scenarios: {}".format(e.orig.args)
            raise SpineDBAPIError(msg)

    def readd_scenarios(self, *items):
        """Add known scenarios to database.
        """
        self._do_add_scenarios(*items)
        ids = set(x["id"] for x in items)
        self.added_item_id["scenario"].update(ids)
        return ids, []

    def add_scenario_alternatives(self, *items, strict=False, return_dups=False):
        """Stage scenario alternative items for insertion.

        :param Iterable items: One or more Python :class:`dict` objects representing the items to be inserted.
        :param bool strict: Whether or not the method should raise :exc:`~.exception.SpineIntegrityError`
            if the insertion of one of the items violates an integrity constraint.
        :param bool return_dups: Whether or not already existing and duplicated entries should also be returned.

        :returns:
            - **new_items** -- A list of items succesfully staged for insertion.
            - **intgr_error_log** -- A list of :exc:`~.exception.SpineIntegrityError` instances corresponding
              to found violations.
        """
        checked_items, intgr_error_log = self.check_scenario_alternatives_for_insert(*items, strict=strict)
        ids = self._add_scenario_alternatives(*checked_items)
        if return_dups:
            ids.update(set(x.id for x in intgr_error_log if x.id))
        return ids, intgr_error_log

    def _add_scenario_alternatives(self, *items):
        """Add scenario alternative items to database without checking integrity.

        Args:
            items (iter): list of dictionaries which correspond to the instances to add
            strict (bool): if True SpineIntegrityError are raised. Otherwise
                they are catched and returned as a log

        Returns:
            ids (set): added instances' ids
        """
        items_to_add, ids = self._items_and_ids("scenario_alternative", *items)
        self._do_add_scenario_alternatives(*items_to_add)
        self.added_item_id["scenario_alternative"].update(ids)
        return ids

    def _do_add_scenario_alternatives(self, *items_to_add):
        try:
            self.session.bulk_insert_mappings(self.DiffScenarioAlternative, items_to_add)
            self.session.commit()
        except DBAPIError as e:
            self.session.rollback()
            msg = "DBAPIError while inserting scenario alternatives: {}".format(e.orig.args)
            raise SpineDBAPIError(msg)

    def readd_scenario_alternatives(self, *items):
        """Add known scenario-alternatives to database.
        """
        self._do_add_scenario_alternatives(*items)
        ids = set(x["id"] for x in items)
        self.added_item_id["scenario_alternative"].update(ids)
        return ids, []

    def add_object_classes(self, *items, strict=False, return_dups=False):
        """Stage object class items for insertion.

        :param Iterable items: One or more Python :class:`dict` objects representing the items to be inserted.
        :param bool strict: Whether or not the method should raise :exc:`~.exception.SpineIntegrityError`
            if the insertion of one of the items violates an integrity constraint.
        :param bool return_dups: Whether or not already existing and duplicated entries should also be returned.

        :returns:
            - **new_items** -- A list of items successfully staged for insertion.
            - **intgr_error_log** -- A list of :exc:`~.exception.SpineIntegrityError` instances corresponding
              to found violations.
        """
        checked_items, intgr_error_log = self.check_object_classes_for_insert(*items, strict=strict)
        ids = self._add_object_classes(*checked_items)
        if return_dups:
            ids.update(set(x.id for x in intgr_error_log if x.id))
        return ids, intgr_error_log

    def _add_object_classes(self, *items):
        """Add object classes to database without checking integrity.

        Args:
            items (iter): list of dictionaries which correspond to the instances to add
            strict (bool): if True SpineIntegrityError are raised. Otherwise
                they are catched and returned as a log

        Returns:
            ids (set): added instances' ids
        """
        items_to_add, ids = self._items_and_ids("object_class", *items)
        self._do_add_object_classes(*items_to_add)
        self.added_item_id["entity_class"].update(ids)
        self.added_item_id["object_class"].update(ids)
        return ids

    def _do_add_object_classes(self, *items_to_add):
        oc_to_add = list()
        for item in items_to_add:
            item["type_id"] = self.object_class_type
            oc_to_add.append({"entity_class_id": item["id"], "type_id": self.object_class_type})
        try:
            self.session.bulk_insert_mappings(self.DiffEntityClass, items_to_add)
            self.session.bulk_insert_mappings(self.DiffObjectClass, oc_to_add)
            self.session.commit()
        except DBAPIError as e:
            self.session.rollback()
            msg = "DBAPIError while inserting object classes: {}".format(e.orig.args)
            raise SpineDBAPIError(msg)

    def readd_object_classes(self, *items):
        """Add known object classes to database.
        """
        self._do_add_object_classes(*items)
        ids = set(x["id"] for x in items)
        self.added_item_id["entity_class"].update(ids)
        self.added_item_id["object_class"].update(ids)
        return ids, []

    def add_objects(self, *items, strict=False, return_dups=False):
        """Stage object items for insertion.

        :param Iterable items: One or more Python :class:`dict` objects representing the items to be inserted.
        :param bool strict: Whether or not the method should raise :exc:`~.exception.SpineIntegrityError`
            if the insertion of one of the items violates an integrity constraint.
        :param bool return_dups: Whether or not already existing and duplicated entries should also be returned.

        :returns:
            - **new_items** -- A list of items succesfully staged for insertion.
            - **intgr_error_log** -- A list of :exc:`~.exception.SpineIntegrityError` instances corresponding
              to found violations.
        """
        checked_items, intgr_error_log = self.check_objects_for_insert(*items, strict=strict)
        ids = self._add_objects(*checked_items)
        if return_dups:
            ids.update(set(x.id for x in intgr_error_log if x.id))
        return ids, intgr_error_log

    def _add_objects(self, *items):
        """Add objects to database without checking integrity.

        Args:
            items (iter): list of dictionaries which correspond to the instances to add

        Returns:
            ids (set): added instances' ids
        """
        items_to_add, ids = self._items_and_ids("object", *items)
        self._do_add_objects(*items_to_add)
        self.added_item_id["entity"].update(ids)
        self.added_item_id["object"].update(ids)
        return ids

    def _do_add_objects(self, *items_to_add):
        objects_to_add = list()
        for item in items_to_add:
            item["type_id"] = self.object_entity_type
            objects_to_add.append({"entity_id": item["id"], "type_id": item["type_id"]})
        try:
            self.session.bulk_insert_mappings(self.DiffEntity, items_to_add)
            self.session.bulk_insert_mappings(self.DiffObject, objects_to_add)
            self.session.commit()
        except DBAPIError as e:
            self.session.rollback()
            msg = "DBAPIError while inserting objects: {}".format(e.orig.args)
            raise SpineDBAPIError(msg)

    def readd_objects(self, *items):
        """Add known objects to database.
        """
        self._do_add_objects(*items)
        ids = set(x["id"] for x in items)
        self.added_item_id["entity"].update(ids)
        self.added_item_id["object"].update(ids)
        return ids, []

    def add_wide_relationship_classes(self, *wide_items, strict=False, return_dups=False):
        """Stage relationship class items for insertion.

        :param Iterable items: One or more Python :class:`dict` objects representing the items to be inserted.
        :param bool strict: Whether or not the method should raise :exc:`~.exception.SpineIntegrityError`
            if the insertion of one of the items violates an integrity constraint.
        :param bool return_dups: Whether or not already existing and duplicated entries should also be returned.

        :returns:
            - **new_items** -- A list of items succesfully staged for insertion.
            - **intgr_error_log** -- A list of :exc:`~.exception.SpineIntegrityError` instances corresponding
              to found violations.
        """
        checked_wide_items, intgr_error_log = self.check_wide_relationship_classes_for_insert(
            *wide_items, strict=strict
        )
        ids = self._add_wide_relationship_classes(*checked_wide_items)
        if return_dups:
            ids.update(set(x.id for x in intgr_error_log if x.id))
        return ids, intgr_error_log

    def _add_wide_relationship_classes(self, *wide_items):
        """Add relationship classes to database without checking integrity.

        Args:
            wide_items (iter): list of dictionaries which correspond to the instances to add
            strict (bool): if True SpineIntegrityError are raised. Otherwise
                they are catched and returned as a log

        Returns:
            ids (set): added instances' ids
        """
        wide_items_to_add, ids = self._items_and_ids("relationship_class", *wide_items)
        self._do_add_wide_relationship_classes(*wide_items_to_add)
        self.added_item_id["entity_class"].update(ids)
        self.added_item_id["relationship_class"].update(ids)
        self.added_item_id["relationship_entity_class"].update(ids)
        return ids

    def _do_add_wide_relationship_classes(self, *wide_items_to_add):
        rel_ent_clss_to_add = list()
        rel_clss_to_add = list()
        for wide_item in wide_items_to_add:
            wide_item["type_id"] = self.relationship_class_type
            rel_clss_to_add.append({"entity_class_id": wide_item["id"], "type_id": self.relationship_class_type})
            rel_ent_clss_to_add += get_relationship_entity_class_items(wide_item, self.object_class_type)
        try:
            self.session.bulk_insert_mappings(self.DiffEntityClass, wide_items_to_add)
            self.session.bulk_insert_mappings(self.DiffRelationshipClass, rel_clss_to_add)
            self.session.bulk_insert_mappings(self.DiffRelationshipEntityClass, rel_ent_clss_to_add)
            self.session.commit()
        except DBAPIError as e:
            self.session.rollback()
            msg = "DBAPIError while inserting relationship classes: {}".format(e.orig.args)
            raise SpineDBAPIError(msg)

    def readd_wide_relationship_classes(self, *items):
        """Add known relationship classes to database.
        """
        self._do_add_wide_relationship_classes(*items)
        ids = set(x["id"] for x in items)
        self.added_item_id["entity_class"].update(ids)
        self.added_item_id["relationship_class"].update(ids)
        self.added_item_id["relationship_entity_class"].update(ids)
        return ids, []

    def add_wide_relationships(self, *wide_items, strict=False, return_dups=False):
        """Stage relationship items for insertion.

        :param Iterable items: One or more Python :class:`dict` objects representing the items to be inserted.
        :param bool strict: Whether or not the method should raise :exc:`~.exception.SpineIntegrityError`
            if the insertion of one of the items violates an integrity constraint.
        :param bool return_dups: Whether or not already existing and duplicated entries should also be returned.

        :returns:
            - **new_items** -- A list of items succesfully staged for insertion.
            - **intgr_error_log** -- A list of :exc:`~.exception.SpineIntegrityError` instances corresponding
              to found violations.
        """
        checked_wide_items, intgr_error_log = self.check_wide_relationships_for_insert(*wide_items, strict=strict)
        ids = self._add_wide_relationships(*checked_wide_items)
        if return_dups:
            ids.update(set(x.id for x in intgr_error_log if x.id))
        return ids, intgr_error_log

    def _add_wide_relationships(self, *wide_items):
        """Add relationships to database without checking integrity.

        Args:
            wide_items (iter): list of dictionaries which correspond to the instances to add

        Returns:
            ids (set): added instances' ids
        """
        wide_items_to_add, ids = self._items_and_ids("relationship", *wide_items)
        self._do_add_wide_relationships(*wide_items_to_add)
        self.added_item_id["entity"].update(ids)
        self.added_item_id["relationship"].update(ids)
        self.added_item_id["relationship_entity"].update(ids)
        return ids

    def _do_add_wide_relationships(self, *wide_items_to_add):
        rel_ent_to_add = list()
        rel_to_add = list()
        for wide_item in wide_items_to_add:
            wide_item["type_id"] = self.relationship_entity_type
            rel_to_add.append(
                {
                    "entity_id": wide_item["id"],
                    "entity_class_id": wide_item["class_id"],
                    "type_id": self.relationship_entity_type,
                }
            )
            rel_ent_to_add += get_relationship_entity_items(
                wide_item, self.relationship_entity_type, self.object_entity_type
            )
        try:
            self.session.bulk_insert_mappings(self.DiffEntity, wide_items_to_add)
            self.session.bulk_insert_mappings(self.DiffRelationship, rel_to_add)
            self.session.bulk_insert_mappings(self.DiffRelationshipEntity, rel_ent_to_add)
            self.session.commit()
        except DBAPIError as e:
            self.session.rollback()
            msg = "DBAPIError while inserting relationships: {}".format(e.orig.args)
            raise SpineDBAPIError(msg)

    def readd_wide_relationships(self, *items):
        """Add known relationships to database.
        """
        self._do_add_wide_relationships(*items)
        ids = set(x["id"] for x in items)
        self.added_item_id["entity"].update(ids)
        self.added_item_id["relationship"].update(ids)
        self.added_item_id["relationship_entity"].update(ids)
        return ids, []

    def add_entity_groups(self, *items, strict=False, return_dups=False):
        """Stage group object items for insertion.

        :param Iterable items: One or more Python :class:`dict` objects representing the items to be inserted.
        :param bool strict: Whether or not the method should raise :exc:`~.exception.SpineIntegrityError`
            if the insertion of one of the items violates an integrity constraint.
        :param bool return_dups: Whether or not already existing and duplicated entries should also be returned.

        :returns:
            - **new_items** -- A list of items succesfully staged for insertion.
            - **intgr_error_log** -- A list of :exc:`~.exception.SpineIntegrityError` instances corresponding
              to found violations.
        """
        checked_items, intgr_error_log = self.check_entity_groups_for_insert(*items, strict=strict)
        ids = self._add_entity_groups(*checked_items)
        if return_dups:
            ids.update(set(x.id for x in intgr_error_log if x.id))
        return ids, intgr_error_log

    def _add_entity_groups(self, *items):
        """Add group objects to database without checking integrity.

        Args:
            items (iter): list of dictionaries which correspond to the instances to add

        Returns:
            ids (set): added instances' ids
        """
        items_to_add, ids = self._items_and_ids("entity_group", *items)
        self._do_add_entity_groups(*items_to_add)
        self.added_item_id["entity_group"].update(ids)
        return ids

    def _do_add_entity_groups(self, *items):
        try:
            self.session.bulk_insert_mappings(self.DiffEntityGroup, items)
            self.session.commit()
        except DBAPIError as e:
            self.session.rollback()
            msg = "DBAPIError while inserting entity groups: {}".format(e.orig.args)
            raise SpineDBAPIError(msg)

    def readd_entity_groups(self, *items):
        """Add known group objects to the database.

        Args:
            items (iter): list of dictionaries which correspond to the instances to add

        Returns:
            ids (set): added instances' ids
        """
        self._do_add_entity_groups(*items)
        ids = set(x["id"] for x in items)
        self.added_item_id["entity_group"].update(ids)
        return ids, []

    def add_parameter_definitions(self, *items, strict=False, return_dups=False):
        """Stage parameter definition items for insertion.

        :param Iterable items: One or more Python :class:`dict` objects representing the items to be inserted.
        :param bool strict: Whether or not the method should raise :exc:`~.exception.SpineIntegrityError`
            if the insertion of one of the items violates an integrity constraint.
        :param bool return_dups: Whether or not already existing and duplicated entries should also be returned.

        :returns:
            - **new_items** -- A list of items succesfully staged for insertion.
            - **intgr_error_log** -- A list of :exc:`~.exception.SpineIntegrityError` instances corresponding
              to found violations.
        """
        checked_items, intgr_error_log = self.check_parameter_definitions_for_insert(*items, strict=strict)
        ids = self._add_parameter_definitions(*checked_items)
        if return_dups:
            ids.update(set(x.id for x in intgr_error_log if x.id))
        return ids, intgr_error_log

    def _add_parameter_definitions(self, *items):
        """Add parameters to database without checking integrity.

        Args:
            items (iter): list of dictionaries which correspond to the instances to add

        Returns:
            ids (set): added instances' ids
        """
        items_to_add, ids = self._items_and_ids("parameter_definition", *items)
        self._do_add_parameter_definitions(*items_to_add)
        self.added_item_id["parameter_definition"].update(ids)
        return ids

    def _do_add_parameter_definitions(self, *items_to_add):
        for item in items_to_add:
            item["entity_class_id"] = (
                item.pop("object_class_id", None)
                or item.pop("relationship_class_id", None)
                or item.get("entity_class_id")
            )
        try:
            self.session.bulk_insert_mappings(self.DiffParameterDefinition, items_to_add)
            self.session.commit()
        except DBAPIError as e:
            self.session.rollback()
            msg = "DBAPIError while inserting parameters: {}".format(e.orig.args)
            raise SpineDBAPIError(msg)

    def readd_parameter_definitions(self, *items):
        """Add known parameter definitions to database.
        """
        self._do_add_parameter_definitions(*items)
        ids = set(x["id"] for x in items)
        self.added_item_id["parameter_definition"].update(ids)
        return ids, []

    def add_parameter_values(self, *items, strict=False, return_dups=False):
        """Stage parameter values items for insertion.

        :param Iterable items: One or more Python :class:`dict` objects representing the items to be inserted.
        :param bool strict: Whether or not the method should raise :exc:`~.exception.SpineIntegrityError`
            if the insertion of one of the items violates an integrity constraint.
        :param bool return_dups: Whether or not already existing and duplicated entries should also be returned.

        :returns:
            - **new_items** -- A list of items succesfully staged for insertion.
            - **intgr_error_log** -- A list of :exc:`~.exception.SpineIntegrityError` instances corresponding
              to found violations.
        """
        checked_items, intgr_error_log = self.check_parameter_values_for_insert(*items, strict=strict)
        ids = self._add_parameter_values(*checked_items)
        if return_dups:
            ids.update(set(x.id for x in intgr_error_log if x.id))
        return ids, intgr_error_log

    def add_checked_parameter_values(self, *checked_items):
        ids = self._add_parameter_values(*checked_items)
        return ids, []

    def _add_parameter_values(self, *items):
        """Add parameter values to database without checking integrity.

        Returns:
            ids (set): added instances' ids
        """
        items_to_add, ids = self._items_and_ids("parameter_value", *items)
        self._do_add_parameter_values(*items_to_add)
        self.added_item_id["parameter_value"].update(ids)
        return ids

    def _do_add_parameter_values(self, *items_to_add):
        for item in items_to_add:
            item["entity_id"] = (
                item.pop("object_id", None) or item.pop("relationship_id", None) or item.get("entity_id")
            )
            item["entity_class_id"] = (
                item.pop("object_class_id", None)
                or item.pop("relationship_class_id", None)
                or item.get("entity_class_id")
            )
        try:
            self.session.bulk_insert_mappings(self.DiffParameterValue, items_to_add)
            self.session.commit()
        except DBAPIError as e:
            self.session.rollback()
            msg = "DBAPIError while inserting parameter values: {}".format(e.orig.args)
            raise SpineDBAPIError(msg)

    def readd_parameter_values(self, *items):
        """Add known parameter values to database.
        """
        self._do_add_parameter_values(*items)
        ids = set(x["id"] for x in items)
        self.added_item_id["parameter_value"].update(ids)
        return ids, []

    def add_parameter_tags(self, *items, strict=False, return_dups=False):
        """Stage parameter tag items for insertion.

        :param Iterable items: One or more Python :class:`dict` objects representing the items to be inserted.
        :param bool strict: Whether or not the method should raise :exc:`~.exception.SpineIntegrityError`
            if the insertion of one of the items violates an integrity constraint.
        :param bool return_dups: Whether or not already existing and duplicated entries should also be returned.

        :returns:
            - **new_items** -- A list of items succesfully staged for insertion.
            - **intgr_error_log** -- A list of :exc:`~.exception.SpineIntegrityError` instances corresponding
              to found violations.
        """
        checked_items, intgr_error_log = self.check_parameter_tags_for_insert(*items, strict=strict)
        ids = self._add_parameter_tags(*checked_items)
        if return_dups:
            ids.update(set(x.id for x in intgr_error_log if x.id))
        return ids, intgr_error_log

    def _add_parameter_tags(self, *items):
        """Add parameter tags to database without checking integrity.

        Returns:
            ids (set): added instances' ids
        """
        items_to_add, ids = self._items_and_ids("parameter_tag", *items)
        self._do_add_parameter_tags(*items_to_add)
        self.added_item_id["parameter_tag"].update(ids)
        return ids

    def _do_add_parameter_tags(self, *items_to_add):
        try:
            self.session.bulk_insert_mappings(self.DiffParameterTag, items_to_add)
            self.session.commit()
        except DBAPIError as e:
            self.session.rollback()
            msg = "DBAPIError while inserting parameter tags: {}".format(e.orig.args)
            raise SpineDBAPIError(msg)

    def readd_parameter_tags(self, *items):
        """Add known parameter tags to database.
        """
        self._do_add_parameter_tags(*items)
        ids = set(x["id"] for x in items)
        self.added_item_id["parameter_tag"].update(ids)
        return ids, []

    def add_parameter_definition_tags(self, *items, strict=False, return_dups=False):
        """Stage parameter definition tag items for insertion.

        :param Iterable items: One or more Python :class:`dict` objects representing the items to be inserted.
        :param bool strict: Whether or not the method should raise :exc:`~.exception.SpineIntegrityError`
            if the insertion of one of the items violates an integrity constraint.
        :param bool return_dups: Whether or not already existing and duplicated entries should also be returned.

        :returns:
            - **new_items** -- A list of items succesfully staged for insertion.
            - **intgr_error_log** -- A list of :exc:`~.exception.SpineIntegrityError` instances corresponding
              to found violations.
        """
        checked_items, intgr_error_log = self.check_parameter_definition_tags_for_insert(*items, strict=strict)
        ids = self._add_parameter_definition_tags(*checked_items)
        if return_dups:
            ids.update(set(x.id for x in intgr_error_log if x.id))
        return ids, intgr_error_log

    def _add_parameter_definition_tags(self, *items):
        items_to_add, ids = self._items_and_ids("parameter_definition_tag", *items)
        self._do_add_parameter_definition_tags(*items_to_add)
        self.added_item_id["parameter_definition_tag"].update(ids)
        return ids

    def _do_add_parameter_definition_tags(self, *items_to_add):
        """Add parameter definition tags to database without checking integrity.

        Returns:
            ids (set): added instances' ids
        """
        try:
            self.session.bulk_insert_mappings(self.DiffParameterDefinitionTag, items_to_add)
            self.session.commit()
        except DBAPIError as e:
            self.session.rollback()
            msg = "DBAPIError while inserting parameter definition tags: {}".format(e.orig.args)
            raise SpineDBAPIError(msg)

    def readd_parameter_definition_tags(self, *items):
        """Add known parameter definition tags to database.
        """
        self._do_add_parameter_definition_tags(*items)
        ids = set(x["id"] for x in items)
        self.added_item_id["parameter_definition_tag"].update(ids)
        return ids, []

    def add_wide_parameter_value_lists(self, *wide_items, strict=False, return_dups=False):
        """Stage parameter value-list items for insertion.

        :param Iterable items: One or more Python :class:`dict` objects representing the items to be inserted.
        :param bool strict: Whether or not the method should raise :exc:`~.exception.SpineIntegrityError`
            if the insertion of one of the items violates an integrity constraint.
        :param bool return_dups: Whether or not already existing and duplicated entries should also be returned.

        :returns:
            - **new_items** -- A list of items succesfully staged for insertion.
            - **intgr_error_log** -- A list of :exc:`~.exception.SpineIntegrityError` instances corresponding
              to found violations.
        """
        checked_wide_items, intgr_error_log = self.check_wide_parameter_value_lists_for_insert(
            *wide_items, strict=strict
        )
        ids = self._add_wide_parameter_value_lists(*checked_wide_items)
        if return_dups:
            ids.update(set(x.id for x in intgr_error_log if x.id))
        return ids, intgr_error_log

    def _add_wide_parameter_value_lists(self, *wide_items):
        """Add wide parameter value_lists to database without checking integrity.

        Returns:
            ids (set): added instances' ids
        """
        wide_items_to_add, ids = self._items_and_ids("parameter_value_list", *wide_items)
        self._do_add_wide_parameter_value_lists(*wide_items_to_add)
        self.added_item_id["parameter_value_list"].update(ids)
        return ids

    def _do_add_wide_parameter_value_lists(self, *wide_items_to_add):
        items_to_add = list()
        for wide_item in wide_items_to_add:
            items_to_add += get_parameter_value_list_items(wide_item)
        try:
            self.session.bulk_insert_mappings(self.DiffParameterValueList, items_to_add)
            self.session.commit()
        except DBAPIError as e:
            self.session.rollback()
            msg = "DBAPIError while inserting parameter value lists: {}".format(e.orig.args)
            raise SpineDBAPIError(msg)

    def readd_wide_parameter_value_lists(self, *wide_items):
        """Add known parameter value lists to database.
        """
        self._do_add_wide_parameter_value_lists(*wide_items)
        ids = set(x["id"] for x in wide_items)
        self.added_item_id["parameter_value_list"].update(ids)
        return ids, []

    def _add_metadata(self, *items):
        """Add metadata items to database without checking integrity.

        Args:
            items (iter): list of dictionaries which correspond to the instances to add
            strict (bool): if True SpineIntegrityError are raised. Otherwise
                they are catched and returned as a log

        Returns:
            ids (set): added instances' ids
        """
        items_to_add, ids = self._items_and_ids("metadata", *items)
        self._do_add_metadata(*items_to_add)
        self.added_item_id["metadata"].update(ids)
        return ids

    def _do_add_metadata(self, *items_to_add):
        try:
            self.session.bulk_insert_mappings(self.DiffMetadata, items_to_add)
            self.session.commit()
        except DBAPIError as e:
            self.session.rollback()
            msg = "DBAPIError while inserting metadata: {}".format(e.orig.args)
            raise SpineDBAPIError(msg)

    def _add_parameter_value_metadata(self, *items):
        """Add parameter value metadata items to database without checking integrity.

        Args:
            items (iter): list of dictionaries which correspond to the instances to add
            strict (bool): if True SpineIntegrityError are raised. Otherwise
                they are catched and returned as a log

        Returns:
            ids (set): added instances' ids
        """
        items_to_add, ids = self._items_and_ids("parameter_value_metadata", *items)
        self._do_add_parameter_value_metadata(*items_to_add)
        self.added_item_id["parameter_value_metadata"].update(ids)
        return ids

    def _do_add_parameter_value_metadata(self, *items_to_add):
        try:
            self.session.bulk_insert_mappings(self.DiffParameterValueMetadata, items_to_add)
            self.session.commit()
        except DBAPIError as e:
            self.session.rollback()
            msg = "DBAPIError while inserting parameter value metadata: {}".format(e.orig.args)
            raise SpineDBAPIError(msg)

    def _add_entity_metadata(self, *items):
        """Add entity metadata items to database without checking integrity.

        Args:
            items (iter): list of dictionaries which correspond to the instances to add
            strict (bool): if True SpineIntegrityError are raised. Otherwise
                they are catched and returned as a log

        Returns:
            ids (set): added instances' ids
        """
        items_to_add, ids = self._items_and_ids("entity_metadata", *items)
        self._do_add_entity_metadata(*items_to_add)
        self.added_item_id["entity_metadata"].update(ids)
        return ids

    def _do_add_entity_metadata(self, *items_to_add):
        try:
            self.session.bulk_insert_mappings(self.DiffEntityMetadata, items_to_add)
            self.session.commit()
        except DBAPIError as e:
            self.session.rollback()
            msg = "DBAPIError while inserting entity metadata: {}".format(e.orig.args)
            raise SpineDBAPIError(msg)

    def add_object_class(self, **kwargs):
        """Stage an object class item for insertion.

        :raises SpineIntegrityError: if the insertion of the item violates an integrity constraint.

        :returns:
            - **new_item** -- The item succesfully staged for insertion.

        :rtype: :class:`~sqlalchemy.util.KeyedTuple`
        """
        sq = self.object_class_sq
        ids, _ = self.add_object_classes(kwargs, strict=True)
        return self.query(sq).filter(sq.c.id.in_(ids)).one_or_none()

    def add_object(self, **kwargs):
        """Stage an object item for insertion.

        :raises SpineIntegrityError: if the insertion of the item violates an integrity constraint.

        :returns:
            - **new_item** -- The item succesfully staged for insertion.

        :rtype: :class:`~sqlalchemy.util.KeyedTuple`
        """
        sq = self.object_sq
        ids, _ = self.add_objects(kwargs, strict=True)
        return self.query(sq).filter(sq.c.id.in_(ids)).one_or_none()

    def add_wide_relationship_class(self, **kwargs):
        """Stage a relationship class item for insertion.

        :raises SpineIntegrityError: if the insertion of the item violates an integrity constraint.

        :returns:
            - **new_item** -- The item succesfully staged for insertion.

        :rtype: :class:`~sqlalchemy.util.KeyedTuple`
        """
        sq = self.wide_relationship_class_sq
        ids, _ = self.add_wide_relationship_classes(kwargs, strict=True)
        return self.query(sq).filter(sq.c.id.in_(ids)).one_or_none()

    def add_wide_relationship(self, **kwargs):
        """Stage a relationship item for insertion.

        :raises SpineIntegrityError: if the insertion of the item violates an integrity constraint.

        :returns:
            - **new_item** -- The item succesfully staged for insertion.

        :rtype: :class:`~sqlalchemy.util.KeyedTuple`
        """
        sq = self.wide_relationship_sq
        ids, _ = self.add_wide_relationships(kwargs, strict=True)
        return self.query(sq).filter(sq.c.id.in_(ids)).one_or_none()

    def add_parameter_definition(self, **kwargs):
        """Stage a parameter definition item for insertion.

        :raises SpineIntegrityError: if the insertion of the item violates an integrity constraint.

        :returns:
            - **new_item** -- The item succesfully staged for insertion.

        :rtype: :class:`~sqlalchemy.util.KeyedTuple`
        """
        sq = self.parameter_definition_sq
        ids, _ = self.add_parameter_definitions(kwargs, strict=True)
        return self.query(sq).filter(sq.c.id.in_(ids)).one_or_none()

    def add_parameter_value(self, **kwargs):
        """Stage a parameter value item for insertion.

        :raises SpineIntegrityError: if the insertion of the item violates an integrity constraint.

        :returns:
            - **new_item** -- The item succesfully staged for insertion.

        :rtype: :class:`~sqlalchemy.util.KeyedTuple`
        """
        sq = self.parameter_value_sq
        ids, _ = self.add_parameter_values(kwargs, strict=True)
        return self.query(sq).filter(sq.c.id.in_(ids)).one_or_none()

    def get_or_add_object_class(self, **kwargs):
        """Stage an object class item for insertion if it doesn't already exists in the db.

        :returns:
            - **item** -- The item succesfully staged for insertion or already existing.

        :rtype: :class:`~sqlalchemy.util.KeyedTuple`
        """
        sq = self.object_class_sq
        ids, _ = self.add_object_classes(kwargs, return_dups=True)
        return self.query(sq).filter(sq.c.id.in_(ids)).one_or_none()

    def get_or_add_object(self, **kwargs):
        """Stage an object item for insertion if it doesn't already exists in the db.

        :returns:
            - **item** -- The item succesfully staged for insertion or already existing.

        :rtype: :class:`~sqlalchemy.util.KeyedTuple`
        """
        sq = self.object_sq
        ids, _ = self.add_objects(kwargs, return_dups=True)
        return self.query(sq).filter(sq.c.id.in_(ids)).one_or_none()

    def get_or_add_parameter_definition(self, **kwargs):
        """Stage a parameter definition item for insertion if it doesn't already exists in the db.

        :returns:
            - **item** -- The item succesfully staged for insertion or already existing.

        :rtype: :class:`~sqlalchemy.util.KeyedTuple`
        """
        sq = self.parameter_definition_sq
        ids, _ = self.add_parameter_definitions(kwargs, return_dups=True)
        return self.query(sq).filter(sq.c.id.in_(ids)).one_or_none()
