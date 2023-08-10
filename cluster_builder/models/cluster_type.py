from dataclasses import asdict, dataclass, field
import datetime
import glob
import os
import yaml
import urllib

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
            },
        "type": "object",
        "properties": {
            "title": { "type": "string" },
            "description": { "type": "string" },
            "kind": {
                "type": "string",
                "enum": ["heat", "magnum"]
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
                        "parameters": {"$ref": "/schemas/parameters"}
                        },
                    "required": ["magnum_cluster_template", "parameters"],
                    },
                }
            ]
        }

class NetworkNotFoundError(RuntimeError):
    pass

class HotNotFoundError(FileNotFoundError):
    pass


@dataclass
class ClusterType:
    # Class variables configured in configure method.
    hot_templates_dir = None
    logger = None
    types_dir = None

    # Instance variables used by dataclass decorator.
    id: str
    title: str
    description: str
    parameters: dict
    kind: str
    upstream_template: str
    last_modified: str
    hardcoded_parameters: dict = field(default_factory=dict)

    @classmethod
    def configure(cls, hot_templates_dir, types_dir, logger):
        cls.hot_templates_dir = hot_templates_dir
        cls.types_dir = types_dir
        cls.logger = logger

    @classmethod
    def all(cls):
        """
        Return list of cluster types.
        """
        cls.logger.info(f"Retrieving all cluster types")
        types = []

        for file in glob.glob(os.path.join(cls.types_dir, "*.yaml")):
            id = os.path.splitext(os.path.basename(file))[0]
            cluster_type = cls._load(id, file)
            if cluster_type is not None:
                types.append(cluster_type)

        return types

    @classmethod
    def find(cls, id):
        """
        Return the specified cluster type or abort with a 404.
        """
        file = os.path.join(cls.types_dir, f"{id}.yaml")
        cls.logger.info(f"Finding cluster type: {id}:{file}")
        cluster_type = cls._load(id, file)
        if cluster_type is None:
            abort(404, f"Unknown cluster type: {id}")
        else:
            return cluster_type


    @classmethod
    def _load(cls, id, file):
        try:
            with open(file, 'r') as stream:
                try:
                    definition = yaml.safe_load(stream)
                except yaml.YAMLError as exc:
                    cls.logger.error(f'Loading {id} failed: {exc}')
                    return None
                else:
                    try:
                        cls._validate(definition)
                    except HotNotFoundError as exc:
                        cls.logger.error(f'Loading {id} failed: HotNotFoundError: {exc}')
                    except NetworkNotFoundError as exc:
                        cls.logger.error(f'Loading {id} failed: network or router resource not found')
                        cls.logger.debug(f'Loading {id} failed: HOT templates are expected to define a private network. It appears that this template does not.')
                    except jsonschema.ValidationError as exc:
                        error_message = best_match([exc]).message
                        cls.logger.error(f'Loading {id} failed: {error_message}')
                        cls.logger.debug(f'Loading {id} failed: {exc}')
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
                            hot_template = cls._hot_template_contents(fields["upstream_template"])
                            fields["hardcoded_parameters"] = definition.get("hardcoded_parameters", {})
                            fields["parameters"] = cls.extract_parameters(hot_template, fields["hardcoded_parameters"])
                        elif definition["kind"] == "magnum":
                            fields["upstream_template"] = definition.get("magnum_cluster_template")
                            fields["parameters"] = definition.get("parameters", {})
                        cluster_type = cls(**fields)
                        return cluster_type
        except FileNotFoundError as exc:
            cls.logger.error(f'Loading {id} failed: FileNotFoundError: {file}')
            return None


    @classmethod
    def _validate(cls, definition):
        jsonschema.validate(instance=definition, schema=SCHEMA)
        if definition.get("kind") == "heat":
            # Attempt to load the HOT.  This will catch some possible issues with
            # the template, such as it not being found at that path, not being
            # valid YAML and some schema issues too.
            try:
                hot_template = cls._hot_template_contents(definition.get("heat_template_url"))
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

    @classmethod
    def _hot_template_path(cls, relative_path):
        return os.path.join(cls.hot_templates_dir, relative_path)


    @classmethod
    def _hot_template_contents(cls, relative_path):
        hot_template_path = cls._hot_template_path(relative_path)
        _files, hot_template = template_utils.get_template_contents(hot_template_path)
        return hot_template


    @staticmethod
    def extract_parameters(hot_template, hardcoded_parameters):
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


    @staticmethod
    def merge_parameters(cluster_type, given_answers):
        """
        Return the parameters to be sent to the cloud service.

        The value for each parameter can come from (in order of precedence):

        1. Hardcoded parameters in the cluster type definition.
        2. User given answer.
        3. Default set in either the cluster type definition or the HOT
        template.
        """
        merged_parameters = {}
        for name, parameter in cluster_type.parameters.items():
            given_answer = given_answers is not None and given_answers.get(name)
            if given_answer is not None:
                merged_parameters[name] = given_answer
            else:
                merged_parameters[name] = parameter.get("default")
        for name, value in cluster_type.hardcoded_parameters.items():
            merged_parameters[name] = value
        return merged_parameters


    def assert_parameters_present(self, answers):
        """
        Asserts that all parameters defined in the cluster type either have a
        default or are present in answers.
        """
        missing = []
        for name, parameter in self.parameters.items():
            if parameter.get("default") is not None:
                continue
            if answers is not None and answers.get(name) is not None:
                continue
            missing.append(name)
        if len(missing) > 0:
            abort(400, "Missing parameters: {}".format(", ".join(missing)))


    def hot_template_path(self):
        return self._hot_template_path(self.upstream_template)


    def asdict(self, attributes=None):
        if attributes is None:
            return asdict(self)
        else:
            return {k: v for k, v in asdict(self).items() if k in attributes}
