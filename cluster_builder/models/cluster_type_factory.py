import datetime
import os
import urllib

from heatclient.common import template_utils
from heatclient import exc as heatclientExceptions
from jsonschema.exceptions import (best_match)
import jsonschema

from .cluster_type import (BaseClusterType, SaharaClusterType, MagnumClusterType, HeatClusterType, Component)

SCHEMA_DEFS = {
    "$defs": {
        "parameters": {
            "$id": "/schemas/parameters",
            "type": "object",
            "patternProperties": {
                "^.*$": {
                    "type": "object",
                    "properties": {
                        "type": {
                            "type": "string",
                            "enum": ["string", "number", "json", "comma_delimited_list", "boolean"]
                        },
                        "label": { "type": "string" },
                        "description": { "type": "string" },
                        "default": {},
                        "hidden": { "type": "boolean" },
                        "constraints": {
                            "type": "array",
                            # "items": {
                            #     "type": "object",
                            #     "properties": {},
                            #     "additionalProperties": False
                            #     }
                        },
                        "immutable": { "type": "boolean" },
                        "tags": {}
                    },
                    "additionalProperties": False,
                    "required": ["type"]
                }
            },
            "additionalProperties": False
        },
        "parameter_groups": {
            "$id": "/schemas/parameter_groups",
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "label": { "type": "string" },
                    "description": { "type": "string" },
                    "parameters": {
                        "type": "array",
                        "items": { "type": "string" }
                    }
                }
            }
        }
    }
}


class BaseClusterTypeFactory:
    """
    BaseClusterTypeFactory is the base class for cluster type factories.  A
    cluster type factory continues the job of loading a cluster type started by
    ClusterTypeRepo.  Any differences between the different cluster type kinds
    are handled by the child classes.
    """

    # Class variables overridden by subclasses.
    klass = BaseClusterType
    SCHEMA = {}

    def __init__(self, logger):
        self.logger = logger


    def load(self, id, path, definition):
        if not self._validate(id, path, definition):
            return None
        fields = self._extract_fields(id, path, definition)
        cluster_type = self.klass(**fields)
        return cluster_type


    def _validate(self, id, path, definition):
        try:
            jsonschema.validate(instance=definition, schema=self.SCHEMA)
        except jsonschema.ValidationError as exc:
            error_message = best_match([exc]).message
            self.logger.error(f'Loading {id}:{path} failed: {error_message}')
            self.logger.debug(f'Loading {id}:{path} failed: {exc}')
            return False
        else:
            return True


    def _extract_fields(self, id, path, definition):
        fields = {
            "id": id,
            "path": path,
            "title": definition["title"],
            "description": definition["description"],
            "kind": definition["kind"],
            "parameter_groups": definition.get("parameter_groups", []),
            "last_modified": datetime.datetime.fromtimestamp(os.path.getmtime(path)),
            "order": definition.get("order"),
            "logo_url": definition.get("logo_url"),
        }
        return fields


class MagnumClusterTypeFactory(BaseClusterTypeFactory):
    """
    Loads magnum-based cluster type definitions from disk; validates them and
    creates ClusterType objects.
    """

    klass = MagnumClusterType

    SCHEMA = {
        "$defs": SCHEMA_DEFS,
        "type": "object",
        "properties": {
            "title": { "type": "string" },
            "description": { "type": "string" },
            "kind": {
                "type": "string",
                "enum": ["magnum"]
            },
            "magnum_cluster_template": { "type": "string" },
            "parameters": {"$ref": "/schemas/parameters"},
            "parameter_groups": {"$ref": "/schemas/parameter_groups"},
            "order": { "type": "number" },
            "logo_url": { "type": "string" },
        },
        "required": ["title", "description", "kind", "parameters", "magnum_cluster_template", "order", "logo_url"],
    }

    def _extract_fields(self, id, path, definition):
        fields = super()._extract_fields(id, path, definition)
        fields["upstream_template"] = definition.get("magnum_cluster_template")
        fields["parameters"] = definition.get("parameters", {})
        return fields


class SaharaClusterTypeFactory(BaseClusterTypeFactory):
    """
    Loads sahara-based cluster type definitions from disk; validates them and
    creates ClusterType objects.
    """

    klass = SaharaClusterType

    SCHEMA = {
        "$defs": SCHEMA_DEFS,
        "type": "object",
        "properties": {
            "title": { "type": "string" },
            "description": { "type": "string" },
            "kind": {
                "type": "string",
                "enum": ["sahara"]
            },
            "sahara_cluster_template": { "type": "string" },
            "parameters": {"$ref": "/schemas/parameters"},
            "parameter_groups": {"$ref": "/schemas/parameter_groups"},
            "order": { "type": "number" },
            "logo_url": { "type": "string" },
        },
        "required": ["title", "description", "kind", "parameters", "sahara_cluster_template", "order", "logo_url"],
    }

    def _extract_fields(self, id, path, definition):
        fields = super()._extract_fields(id, path, definition)
        fields["upstream_template"] = definition.get("sahara_cluster_template")
        fields["parameters"] = definition.get("parameters", {})
        return fields


class HeatClusterTypeFactory(BaseClusterTypeFactory):
    """
    Loads heat-based cluster type definitions from disk; validates them and
    creates ClusterType objects.
    """

    klass = HeatClusterType

    SCHEMA = {
        "$defs": SCHEMA_DEFS,
        "type": "object",
        "properties": {
            "title": { "type": "string" },
            "description": { "type": "string" },
            "kind": {
                "type": "string",
                "enum": ["heat"]
            },
            "hardcoded_parameters": {
                "type": "object",
                "patternProperties": {
                    "^.*$": {
                        "type": ["string", "number", "boolean"],
                    }
                },
                "additionalProperties": False
            },
            "parameter_groups": {"$ref": "/schemas/parameter_groups"},
            "components": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "optional": {"type": "boolean"},
                    },
                    "required": ["name"],
                }
            },
            "order": { "type": "number" },
            "logo_url": { "type": "string" },
        },
        "required": ["title", "description", "kind", "components", "order", "logo_url"],
        "additionalProperties": False,
    }

    def load(self, id, path, definition):
        if not self._validate(id, path, definition):
            return None
        base_dir = os.path.dirname(path)
        components = self._load_components(base_dir, definition.get("components"))
        if components is None:
            return None
        if not self._validate_network_present(components):
            return None

        fields = self._extract_fields(id, path, definition, components)
        cluster_type = self.klass(**fields)
        return cluster_type


    def _load_components(self, base_dir, component_defs):
        components_dir = os.path.join(base_dir, "components")
        components = []
        for c in component_defs:
            path = c["name"]
            if not os.path.isabs(path):
                path = os.path.join(components_dir, f'{path}.yaml')
            component = ComponentLoader(self.logger).load(path, optional=c.get("optional", False))
            if component is None:
                # If any component fails to load, the entire cluster type is
                # invalid.  Return None to indicate this, the logs will have
                # details of why.
                return None
            else:
                components.append(component)
        return components


    def _validate_network_present(self, components):
        # Check that at least one of the component's HOT includes a network and
        # router in its resources. We require that all clusters are created on
        # their own network not the public network.  The presence of
        # OS::Neutron::{Router,Net} is the heuristic we use for this.
        found_router = False
        found_network = False
        for component in components:
            _, hot_template = template_utils.get_template_contents(component.path, fetch_child=True)
            for resource in hot_template.get("resources", {}).values():
                if resource["type"] == "OS::Neutron::Router":
                    found_router = True
                if resource["type"] == "OS::Neutron::Net":
                    found_network = True
            if found_router and found_network:
                break
        if not found_router or not found_network:
            self.logger.error(f'Loading {id} failed: network or router resource not found')
            self.logger.debug(f'Loading {id} failed: heat-based cluster types are expected to define a private network. It appears that this cluster type does not.')
            return False

        # If we get here, the template is valid.
        return True


    def _extract_fields(self, id, path, definition, components):
        fields = super()._extract_fields(id, path, definition)
        fields["hardcoded_parameters"] = definition.get("hardcoded_parameters", {})
        fields["components"] = components

        for component in components:
            if component.last_modified > fields["last_modified"]:
                fields["last_modified"] = component.last_modified

        return fields


class ComponentLoader:
    SCHEMA = {
        "$defs": SCHEMA_DEFS,
        "type": "object",
        "properties": {
            "heat_template_version": {"type": "string"},
            "parameters": {"$ref": "/schemas/parameters"},
            "resources": {"type": "object"},
            "conditions": {"type": "object"},
            "outputs": {"type": "object"},
        },
        "additionalProperties": False,
    }

    def __init__(self, logger):
        self.logger = logger


    def load(self, path, optional=False):
        try:
            _, hot_template = template_utils.get_template_contents(path, fetch_child=True)
            jsonschema.validate(instance=hot_template, schema=self.SCHEMA)
        except heatclientExceptions.CommandError as exc:
            self.logger.error(f'Loading {path} failed: {exc}')
            return None
        except urllib.error.URLError as exc:
            self.logger.error(f'Loading failed: component not found: {path}')
            return None
        except jsonschema.ValidationError as exc:
            error_message = best_match([exc]).message
            self.logger.error(f'Loading component from {path} failed: {error_message}')
            self.logger.debug(f'Loading component from {path} failed: {exc}')
            return None

        return Component(
            path=path,
            heat_template_version=hot_template.get("heat_template_version"),
            parameters=hot_template.get("parameters", {}),
            resources=hot_template.get("resources", {}),
            conditions=hot_template.get("conditions", {}),
            outputs=hot_template.get("outputs", {}),
            last_modified=datetime.datetime.fromtimestamp(os.path.getmtime(path)),
            is_optional=optional,
            name=os.path.splitext(os.path.basename(path))[0],
        )
