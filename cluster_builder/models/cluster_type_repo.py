import glob
import os
import yaml

from flask import (abort)
from jsonschema.exceptions import (best_match)
import jsonschema

from .cluster_type_factory import (HeatClusterTypeFactory, SaharaClusterTypeFactory, MagnumClusterTypeFactory)

class ClusterTypeRepo:
    """
    Loads minimal cluster type definitions from disk; minimally validates them
    and delegates to a *ClusterTypeFactory class to continue creation of a
    *ClusterType object.
    """

    # JSON Schema definition for attributes common to all cluster type definition kinds.
    #
    # Once a definition is validated by this method it is possible to determine
    # which kind of cluster type definition it is.  Additional validations and
    # processing appropriate to that kind can then be performed.
    SCHEMA = {
        "type": "object",
        "properties": {
            "title": { "type": "string" },
            "description": { "type": "string" },
            "kind": {
                "type": "string",
                "enum": ["heat", "magnum", "sahara"]
            },
        },
        "required": ["title", "description", "kind"],
    }


    # Class variables configured in configure method.
    # logger = None
    # types_dir = None

    @classmethod
    def configure(cls, types_dir, logger):
        cls.types_dir = types_dir
        cls.logger = logger


    @classmethod
    def all(cls):
        """
        Return list of valid cluster types.
        """
        cls.logger.info(f"Retrieving all cluster types")
        types = []
        for file in glob.glob(os.path.join(cls.types_dir, "*", "cluster-type.yaml")):
            id = os.path.basename(os.path.dirname(file))
            cluster_type = cls._load(id, file)
            if cluster_type is not None:
                types.append(cluster_type)

        return types


    @classmethod
    def find(cls, id):
        """
        Return the specified cluster type or abort with a 404.
        """
        # Old-style file path.  Only used for sahara and magnum based cluster
        # types.
        old_file = os.path.join(cls.types_dir, f"{id}.yaml")

        # New-style definition.  Used for heat based cluster types.
        new_file = os.path.join(cls.types_dir, id, "cluster-type.yaml")

        cls.logger.info(f"Finding cluster type: {id}:{new_file}:{old_file}")
        cluster_type = cls._load(id, new_file) or cls._load(id, old_file)
        if cluster_type is None:
            abort(404, f"Unknown cluster type: {id}")
        else:
            return cluster_type


    @classmethod
    def _load(cls, id, file):
        definition = cls._load_definition(id, file)
        if definition is None:
            return
        try:
            jsonschema.validate(instance=definition, schema=cls.SCHEMA)
        except jsonschema.ValidationError as exc:
            error_message = best_match([exc]).message
            cls.logger.error(f'Loading {id} failed: {error_message}')
            cls.logger.debug(f'Loading {id} failed: {exc}')
            return None
        else:
            factory = None
            if definition["kind"] == "heat":
                factory = HeatClusterTypeFactory(cls.logger)
            elif definition["kind"] == "magnum":
                factory = MagnumClusterTypeFactory(cls.logger)
            elif definition["kind"] == "sahara":
                factory = SaharaClusterTypeFactory(cls.logger)
            if factory == None:
                cls.logger.error(f'Unhandled cluster type kind {definition["kind"]}')
            else:
                return factory.load(id, file, definition)


    @classmethod
    def _load_definition(cls, id, file):
        try:
            with open(file, 'r') as stream:
                try:
                    definition = yaml.safe_load(stream)
                    return definition
                except yaml.YAMLError as exc:
                    cls.logger.error(f'Loading {id} failed: {exc}')
                    return None
        except FileNotFoundError as exc:
            cls.logger.error(f'Loading {id} failed: FileNotFoundError: {file}')
            return None
