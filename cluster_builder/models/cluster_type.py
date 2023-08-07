from dataclasses import asdict, dataclass
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
        "type": "object",
        "properties": {
            "title": { "type": "string" },
            "description": { "type": "string" },
            "kind": {
                "type": "string",
                "enum": ["heat", "magnum"]
                },
            "parameters": {
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
                    "properties": { "heat_template_url": { "type": "string" } },
                    "required": ["heat_template_url"],
                    },
                },
            {
                "if": {
                    "properties": { "kind": { "const": "magnum" } },
                    "required": ["kind"]
                    },
                "then": {
                    "properties": { "magnum_cluster_template": { "type": "string" } },
                    "required": ["magnum_cluster_template"],
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
                    template = yaml.safe_load(stream)
                except yaml.YAMLError as exc:
                    cls.logger.error(f'Loading {id} failed: {exc}')
                    return None
                else:
                    try:
                        cls._validate(template)
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
                                "title": template.get("title", ""),
                                "description": template.get("description", id),
                                "parameters": template.get("parameters", []),
                                "kind": template.get("kind"),
                                "last_modified": datetime.datetime.fromtimestamp(os.path.getmtime(file))
                                }
                        if template["kind"] == "heat":
                            fields["upstream_template"] = template.get("heat_template_url")
                        elif template["kind"] == "magnum":
                            fields["upstream_template"] = template.get("magnum_cluster_template")
                        cluster_type = cls(**fields)
                        return cluster_type
        except FileNotFoundError as exc:
            cls.logger.error(f'Loading {id} failed: FileNotFoundError: {file}')
            return None


    @classmethod
    def _validate(cls, template):
        jsonschema.validate(instance=template, schema=SCHEMA)
        if template.get("kind") == "heat":
            # Attempt to load the HOT.  This will catch some possible issues with
            # the template, such as it not being found at that path, not being
            # valid YAML and some schema issues too.
            try:
                hot_template_path = cls._hot_template_path(template.get("heat_template_url"))
                _files, hot_template = template_utils.get_template_contents(hot_template_path)
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
                for resource in hot_template["resources"].values():
                    if resource["type"] == "OS::Neutron::Router":
                        found_router = True
                    if resource["type"] == "OS::Neutron::Net":
                        found_network = True
                if not found_router or not found_network:
                    raise NetworkNotFoundError()

    @classmethod
    def _hot_template_path(cls, relative_path):
        return os.path.join(cls.hot_templates_dir, relative_path)


    @staticmethod
    def merge_parameters(cluster_type, given_answers):
        """
        Return the given answers merged with the defaults for the cluster
        type's parameters.  The given answers take precedence.
        """
        merged_parameters = {}
        for name, parameter in cluster_type.parameters.items():
            given_answer = given_answers is not None and given_answers.get(name)
            if given_answer is not None:
                merged_parameters[name] = given_answer
            else:
                merged_parameters[name] = parameter.get("default")
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
