import datetime
import glob
import os
import urllib
import yaml

from flask import (abort)
from heatclient.common import template_utils
from jsonschema.exceptions import (best_match)
import jsonschema

# JSON Schema definition for cluster type definitions.
SCHEMA = {
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
                                #     "additionalProperties": false
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
        },
        "type": "object",
        "properties": {
            "title": { "type": "string" },
            "description": { "type": "string" },
            "kind": {
                "type": "string",
                "enum": ["heat", "magnum", "sahara"]
                }
            },
        "required": ["title", "description", "kind"],
        "allOf": [
            {
                "if": {
                    "properties": { "kind": { "const": "heat" } },
                    "required": ["kind"]
                    },
                "then": {
                    "properties": {
                        "hardcoded_parameters": {
                            "type": "object",
                            "patternProperties": {
                                "^.*$": {
                                    "type": "string",
                                    }
                                },
                            "additionalProperties": False
                            },
                        "heat_template_url": { "type": "string" },
                        "parameters": False
                        },
                    "required": ["heat_template_url"],
                    },
                },
            {
                "if": {
                    "properties": { "kind": { "const": "magnum" } },
                    "required": ["kind"]
                    },
                "then": {
                    "properties": {
                        "magnum_cluster_template": { "type": "string" },
                        "parameters": {"$ref": "/schemas/parameters"},
                        "parameter_groups": {"$ref": "/schemas/parameter_groups"}
                        },
                    "required": ["magnum_cluster_template", "parameters"],
                    },
                },
            {
                "if": {
                    "properties": { "kind": { "const": "sahara" } },
                    "required": ["kind"]
                    },
                "then": {
                    "properties": {
                        "sahara_cluster_template": { "type": "string" },
                        "parameters": {"$ref": "/schemas/parameters"},
                        "parameter_groups": {"$ref": "/schemas/parameter_groups"}
                        },
                    "required": ["sahara_cluster_template", "parameters"],
                    },
                }
            ]
        }


class NetworkNotFoundError(RuntimeError):
    pass

class HotNotFoundError(FileNotFoundError):
    pass


class ClusterTypeFactory:
    """
    Loads cluster type definitions from disk; validates them and creates
    ClusterType objects.
    """

    # Class variables configured in configure method.
    hot_templates_dir = None
    logger = None
    types_dir = None

    def __init__(self, klass, hot_templates_dir, types_dir, logger):
        self.klass = klass
        self.hot_templates_dir = hot_templates_dir
        self.types_dir = types_dir
        self.logger = logger


    def all(self):
        """
        Return list of valid cluster types.
        """
        self.logger.info(f"Retrieving all cluster types")
        types = []

        for file in glob.glob(os.path.join(self.types_dir, "*.yaml")):
            id = os.path.splitext(os.path.basename(file))[0]
            cluster_type = self._load(id, file)
            if cluster_type is not None:
                types.append(cluster_type)

        return types


    def find(self, id):
        """
        Return the specified cluster type or abort with a 404.
        """
        file = os.path.join(self.types_dir, f"{id}.yaml")
        self.logger.info(f"Finding cluster type: {id}:{file}")
        cluster_type = self._load(id, file)
        if cluster_type is None:
            abort(404, f"Unknown cluster type: {id}")
        else:
            return cluster_type


    def hot_template_path(self, relative_path):
        return os.path.join(self.hot_templates_dir, relative_path)


    def _load(self, id, file):
        try:
            with open(file, 'r') as stream:
                try:
                    definition = yaml.safe_load(stream)
                except yaml.YAMLError as exc:
                    self.logger.error(f'Loading {id} failed: {exc}')
                    return None
                else:
                    try:
                        self._validate(definition)
                    except HotNotFoundError as exc:
                        self.logger.error(f'Loading {id} failed: HotNotFoundError: {exc}')
                    except NetworkNotFoundError as exc:
                        self.logger.error(f'Loading {id} failed: network or router resource not found')
                        self.logger.debug(f'Loading {id} failed: HOT templates are expected to define a private network. It appears that this template does not.')
                    except jsonschema.ValidationError as exc:
                        error_message = best_match([exc]).message
                        self.logger.error(f'Loading {id} failed: {error_message}')
                        self.logger.debug(f'Loading {id} failed: {exc}')
                        return None
                    else:
                        fields = {
                                "id": id,
                                "title": definition["title"],
                                "description": definition["description"],
                                "kind": definition["kind"],
                                "last_modified": datetime.datetime.fromtimestamp(os.path.getmtime(file))
                                }
                        if definition["kind"] == "heat":
                            fields["upstream_template"] = definition["heat_template_url"]
                            # For heat-based cluster definitions, the
                            # parameters are loaded from the HOT template.
                            hot_template = self._hot_template_contents(fields["upstream_template"])
                            fields["hardcoded_parameters"] = definition.get("hardcoded_parameters", {})
                            fields["parameters"] = self._extract_parameters(hot_template, fields["hardcoded_parameters"])
                            fields["parameter_groups"] = hot_template.get("parameter_groups", [])
                            # Update the last_modified date if the HOT has been
                            # modified more recently.
                            hot_template_path = self.hot_template_path(definition.get("heat_template_url"))
                            hot_last_modified = datetime.datetime.fromtimestamp(os.path.getmtime(hot_template_path))
                            if hot_last_modified > fields["last_modified"]:
                                fields["last_modified"] = hot_last_modified
                        elif definition["kind"] == "magnum":
                            fields["upstream_template"] = definition.get("magnum_cluster_template")
                            fields["parameters"] = definition.get("parameters", {})
                            fields["parameter_groups"] = definition.get("parameter_groups", {})
                        elif definition["kind"] == "sahara":
                            fields["upstream_template"] = definition.get("sahara_cluster_template")
                            fields["parameters"] = definition.get("parameters", {})
                            fields["parameter_groups"] = definition.get("parameter_groups", {})
                        cluster_type = self.klass(**fields)
                        return cluster_type
        except FileNotFoundError as exc:
            self.logger.error(f'Loading {id} failed: FileNotFoundError: {file}')
            return None


    def _validate(self, definition):
        jsonschema.validate(instance=definition, schema=SCHEMA)
        if definition.get("kind") == "heat":
            # Attempt to load the HOT.  This will catch some possible issues with
            # the template, such as it not being found at that path, not being
            # valid YAML and some schema issues too.
            try:
                hot_template = self._hot_template_contents(definition.get("heat_template_url"))
            except urllib.error.URLError as exc:
                filename = None
                try:
                    filename = exc.args[0].filename
                except:
                    pass
                raise HotNotFoundError(filename) from exc
            else:
                # Check that the HOT includes a network and router in its
                # resources. We require that all clusters are created on their
                # own network not the public network.  The presence of
                # OS::Neutron::{Router,Net} is the heuristic we use for this.
                found_router = False
                found_network = False
                for resource in hot_template.get("resources", {}).values():
                    if resource["type"] == "OS::Neutron::Router":
                        found_router = True
                    if resource["type"] == "OS::Neutron::Net":
                        found_network = True
                if not found_router or not found_network:
                    raise NetworkNotFoundError()


    def _hot_template_contents(self, relative_path):
        hot_template_path = self.hot_template_path(relative_path)
        _files, hot_template = template_utils.get_template_contents(hot_template_path)
        return hot_template


    def _extract_parameters(self, hot_template, hardcoded_parameters):
        if hardcoded_parameters is None:
            return hot_template.get("parameters", {})
        else:
            params = {}
            hardcoded_names = hardcoded_parameters.keys()
            for key, value in hot_template.get("parameters", {}).items():
                if key in hardcoded_names:
                    # Hardcoded params are not displayed to the user.  The
                    # hardcoded value will be provided to OpenStack exactly as
                    # provided in the cluster definition.
                    pass
                else:
                    params[key] = value
            return params
