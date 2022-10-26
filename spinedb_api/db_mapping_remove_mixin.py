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

"""Provides :class:`.DiffDatabaseMappingRemoveMixin`.

:author: Manuel Marin (KTH)
:date:   11.8.2018
"""

from sqlalchemy.exc import DBAPIError
from .exception import SpineDBAPIError

# TODO: improve docstrings


class DatabaseMappingRemoveMixin:
    """Provides the :meth:`remove_items` method to stage ``REMOVE`` operations over a Spine db."""

    # pylint: disable=redefined-builtin
    def cascade_remove_items(self, cache=None, **kwargs):
        """Removes items by id in cascade.

        Args:
            **kwargs: keyword is table name, argument is list of ids to remove
        """
        cascading_ids = self.cascading_ids(cache=cache, **kwargs)
        self.remove_items(**cascading_ids)

    def remove_items(self, **kwargs):
        """Removes items by id, *not in cascade*.

        Args:
            **kwargs: keyword is table name, argument is list of ids to remove
        """
        for tablename, ids in kwargs.items():
            table_id = self.table_ids.get(tablename, "id")
            table = self._metadata.tables[tablename]
            delete = table.delete().where(self.in_(getattr(table.c, table_id), ids))
            try:
                self.connection.execute(delete)
            except DBAPIError as e:
                msg = f"DBAPIError while removing {tablename} items: {e.orig.args}"
                raise SpineDBAPIError(msg) from e
            else:
                self.make_commit_id()

    # pylint: disable=redefined-builtin
    def cascading_ids(self, cache=None, **kwargs):
        """Returns cascading ids.

        Keyword args:
            cache (dict, optional)
            **kwargs: set of ids keyed by table name to be removed

        Returns:
            cascading_ids (dict): cascading ids keyed by table name
        """
        if cache is None:
            forced_table_names = None
            if "entity_metadata" in kwargs or "parameter_value_metadata" in kwargs or "metadata" in kwargs:
                forced_table_names = {"entity_metadata", "parameter_value_metadata"}
            cache = self.make_cache(set(kwargs), only_descendants=True, forced_table_names=forced_table_names)
        ids = {}
        self._merge(ids, self._object_class_cascading_ids(kwargs.get("object_class", set()), cache))
        self._merge(ids, self._object_cascading_ids(kwargs.get("object", set()), cache))
        self._merge(ids, self._relationship_class_cascading_ids(kwargs.get("relationship_class", set()), cache))
        self._merge(ids, self._relationship_cascading_ids(kwargs.get("relationship", set()), cache))
        self._merge(ids, self._entity_group_cascading_ids(kwargs.get("entity_group", set()), cache))
        self._merge(ids, self._parameter_definition_cascading_ids(kwargs.get("parameter_definition", set()), cache))
        self._merge(ids, self._parameter_value_cascading_ids(kwargs.get("parameter_value", set()), cache))
        self._merge(ids, self._parameter_value_list_cascading_ids(kwargs.get("parameter_value_list", set()), cache))
        self._merge(ids, self._list_value_cascading_ids(kwargs.get("list_value", set()), cache))
        self._merge(ids, self._alternative_cascading_ids(kwargs.get("alternative", set()), cache))
        self._merge(ids, self._scenario_cascading_ids(kwargs.get("scenario", set()), cache))
        self._merge(ids, self._scenario_alternatives_cascading_ids(kwargs.get("scenario_alternative", set()), cache))
        self._merge(ids, self._feature_cascading_ids(kwargs.get("feature", set()), cache))
        self._merge(ids, self._tool_cascading_ids(kwargs.get("tool", set()), cache))
        self._merge(ids, self._tool_feature_cascading_ids(kwargs.get("tool_feature", set()), cache))
        self._merge(ids, self._tool_feature_method_cascading_ids(kwargs.get("tool_feature_method", set()), cache))
        self._merge(ids, self._metadata_cascading_ids(kwargs.get("metadata", set()), cache))
        self._merge(ids, self._entity_metadata_cascading_ids(kwargs.get("entity_metadata", set()), cache))
        self._merge(
            ids, self._parameter_value_metadata_cascading_ids(kwargs.get("parameter_value_metadata", set()), cache)
        )
        return {key: value for key, value in ids.items() if value}

    @staticmethod
    def _merge(left, right):
        for tablename, ids in right.items():
            left.setdefault(tablename, set()).update(ids)

    def _alternative_cascading_ids(self, ids, cache):
        """Returns alternative cascading ids."""
        cascading_ids = {"alternative": set(ids)}
        parameter_values = [x for x in cache.get("parameter_value", {}).values() if x.alternative_id in ids]
        scenario_alternatives = [x for x in cache.get("scenario_alternative", {}).values() if x.alternative_id in ids]
        self._merge(cascading_ids, self._parameter_value_cascading_ids({x.id for x in parameter_values}, cache))
        self._merge(
            cascading_ids, self._scenario_alternatives_cascading_ids({x.id for x in scenario_alternatives}, cache)
        )
        return cascading_ids

    def _scenario_cascading_ids(self, ids, cache):
        cascading_ids = {"scenario": set(ids)}
        scenario_alternatives = [x for x in cache.get("scenario_alternative", {}).values() if x.scenario_id in ids]
        self._merge(
            cascading_ids, self._scenario_alternatives_cascading_ids({x.id for x in scenario_alternatives}, cache)
        )
        return cascading_ids

    def _object_class_cascading_ids(self, ids, cache):
        """Returns object class cascading ids."""
        cascading_ids = {"entity_class": set(ids), "object_class": set(ids)}
        objects = [x for x in cache.get("object", {}).values() if x.class_id in ids]
        relationship_classes = (
            x
            for x in cache.get("relationship_class", {}).values()
            if {int(id_) for id_ in x.object_class_id_list.split(",")}.intersection(ids)
        )
        paramerer_definitions = [x for x in cache.get("parameter_definition", {}).values() if x.entity_class_id in ids]
        self._merge(cascading_ids, self._object_cascading_ids({x.id for x in objects}, cache))
        self._merge(cascading_ids, self._relationship_class_cascading_ids({x.id for x in relationship_classes}, cache))
        self._merge(
            cascading_ids, self._parameter_definition_cascading_ids({x.id for x in paramerer_definitions}, cache)
        )
        return cascading_ids

    def _object_cascading_ids(self, ids, cache):
        """Returns object cascading ids."""
        cascading_ids = {"entity": set(ids), "object": set(ids)}
        relationships = (
            x
            for x in cache.get("relationship", {}).values()
            if {int(id_) for id_ in x.object_id_list.split(",")}.intersection(ids)
        )
        parameter_values = [x for x in cache.get("parameter_value", {}).values() if x.entity_id in ids]
        groups = [x for x in cache.get("entity_group", {}).values() if {x.group_id, x.member_id}.intersection(ids)]
        entity_metadata_ids = {x.id for x in cache.get("entity_metadata", {}).values() if x.entity_id in ids}
        self._merge(cascading_ids, self._relationship_cascading_ids({x.id for x in relationships}, cache))
        self._merge(cascading_ids, self._parameter_value_cascading_ids({x.id for x in parameter_values}, cache))
        self._merge(cascading_ids, self._entity_group_cascading_ids({x.id for x in groups}, cache))
        self._merge(cascading_ids, self._entity_metadata_cascading_ids(entity_metadata_ids, cache))
        return cascading_ids

    def _relationship_class_cascading_ids(self, ids, cache):
        """Returns relationship class cascading ids."""
        cascading_ids = {
            "relationship_class": set(ids),
            "relationship_entity_class": set(ids),
            "entity_class": set(ids),
        }
        relationships = [x for x in cache.get("relationship", {}).values() if x.class_id in ids]
        paramerer_definitions = [x for x in cache.get("parameter_definition", {}).values() if x.entity_class_id in ids]
        self._merge(cascading_ids, self._relationship_cascading_ids({x.id for x in relationships}, cache))
        self._merge(
            cascading_ids, self._parameter_definition_cascading_ids({x.id for x in paramerer_definitions}, cache)
        )
        return cascading_ids

    def _relationship_cascading_ids(self, ids, cache):
        """Returns relationship cascading ids."""
        cascading_ids = {"relationship": set(ids), "entity": set(ids), "relationship_entity": set(ids)}
        parameter_values = [x for x in cache.get("parameter_value", {}).values() if x.entity_id in ids]
        groups = [x for x in cache.get("entity_group", {}).values() if {x.group_id, x.member_id}.intersection(ids)]
        entity_metadata_ids = {x.id for x in cache.get("entity_metadata", {}).values() if x.entity_id in ids}
        self._merge(cascading_ids, self._parameter_value_cascading_ids({x.id for x in parameter_values}, cache))
        self._merge(cascading_ids, self._entity_group_cascading_ids({x.id for x in groups}, cache))
        self._merge(cascading_ids, self._entity_metadata_cascading_ids(entity_metadata_ids, cache))
        return cascading_ids

    def _entity_group_cascading_ids(self, ids, cache):  # pylint: disable=no-self-use
        """Returns entity group cascading ids."""
        return {"entity_group": set(ids)}

    def _parameter_definition_cascading_ids(self, ids, cache):
        """Returns parameter definition cascading ids."""
        cascading_ids = {"parameter_definition": set(ids)}
        parameter_values = [x for x in cache.get("parameter_value", {}).values() if x.parameter_id in ids]
        features = [x for x in cache.get("feature", {}).values() if x.parameter_definition_id in ids]
        self._merge(cascading_ids, self._parameter_value_cascading_ids({x.id for x in parameter_values}, cache))
        self._merge(cascading_ids, self._feature_cascading_ids({x.id for x in features}, cache))
        return cascading_ids

    def _parameter_value_cascading_ids(self, ids, cache):  # pylint: disable=no-self-use
        """Returns parameter value cascading ids."""
        cascading_ids = {"parameter_value": set(ids)}
        value_metadata_ids = {
            x.id for x in cache.get("parameter_value_metadata", {}).values() if x.parameter_value_id in ids
        }
        self._merge(cascading_ids, self._parameter_value_metadata_cascading_ids(value_metadata_ids, cache))
        return cascading_ids

    def _parameter_value_list_cascading_ids(self, ids, cache):  # pylint: disable=no-self-use
        """Returns parameter value list cascading ids and adds them to the given dictionaries."""
        cascading_ids = {"parameter_value_list": set(ids)}
        features = [x for x in cache.get("feature", {}).values() if x.parameter_value_list_id in ids]
        self._merge(cascading_ids, self._feature_cascading_ids({x.id for x in features}, cache))
        return cascading_ids

    def _list_value_cascading_ids(self, ids, cache):  # pylint: disable=no-self-use
        """Returns parameter value list value cascading ids."""
        return {"list_value": set(ids)}

    def _scenario_alternatives_cascading_ids(self, ids, cache):
        return {"scenario_alternative": set(ids)}

    def _feature_cascading_ids(self, ids, cache):
        cascading_ids = {"feature": set(ids)}
        tool_features = [x for x in cache.get("tool_feature", {}).values() if x.feature_id in ids]
        self._merge(cascading_ids, self._tool_feature_cascading_ids({x.id for x in tool_features}, cache))
        return cascading_ids

    def _tool_cascading_ids(self, ids, cache):
        cascading_ids = {"tool": set(ids)}
        tool_features = [x for x in cache.get("tool_feature", {}).values() if x.tool_id in ids]
        self._merge(cascading_ids, self._tool_feature_cascading_ids({x.id for x in tool_features}, cache))
        return cascading_ids

    def _tool_feature_cascading_ids(self, ids, cache):
        cascading_ids = {"tool_feature": set(ids)}
        tool_feature_methods = [x for x in cache.get("tool_feature_method", {}).values() if x.tool_feature_id in ids]
        self._merge(cascading_ids, self._tool_feature_method_cascading_ids({x.id for x in tool_feature_methods}, cache))
        return cascading_ids

    def _tool_feature_method_cascading_ids(self, ids, cache):
        return {"tool_feature_method": set(ids)}

    def _metadata_cascading_ids(self, ids, cache):
        cascading_ids = {"metadata": set(ids)}
        entity_metadata = {
            "entity_metadata": {x.id for x in cache.get("entity_metadata", {}).values() if x.metadata_id in ids}
        }
        self._merge(cascading_ids, entity_metadata)
        value_metadata = {
            "parameter_value_metadata": {
                x.id for x in cache.get("parameter_value_metadata", {}).values() if x.metadata_id in ids
            }
        }
        self._merge(cascading_ids, value_metadata)
        return cascading_ids

    def _non_referenced_metadata_ids(self, ids, metadata_table_name, cache):
        metadata_id_counts = self._metadata_usage_counts(cache)
        cascading_ids = {}
        metadata = cache.get(metadata_table_name, {})
        for id_ in ids:
            metadata_id_counts[metadata[id_].metadata_id] -= 1
        zero_count_metadata_ids = {id_ for id_, count in metadata_id_counts.items() if count == 0}
        self._merge(cascading_ids, {"metadata": zero_count_metadata_ids})
        return cascading_ids

    def _entity_metadata_cascading_ids(self, ids, cache):
        cascading_ids = {"entity_metadata": set(ids)}
        cascading_ids.update(self._non_referenced_metadata_ids(ids, "entity_metadata", cache))
        return cascading_ids

    def _parameter_value_metadata_cascading_ids(self, ids, cache):
        cascading_ids = {"parameter_value_metadata": set(ids)}
        cascading_ids.update(self._non_referenced_metadata_ids(ids, "parameter_value_metadata", cache))
        return cascading_ids
