from dataclasses import asdict, dataclass
import datetime
import glob
import os
import yaml

from flask import (abort)

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
    heat_template_url: str
    magnum_cluster_template: str
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
                    cls.logger.error(f'Failed to load cluster type definition: {id} {exc}')
                    return None
                else:
                    cluster_type = cls(
                            id=id,
                            title=template.get("title", ""),
                            description=template.get("description", id),
                            parameters=template.get("parameters", []),
                            kind=template.get("kind"),
                            heat_template_url=template.get("heat_template_url"),
                            magnum_cluster_template=template.get("magnum_cluster_template"),
                            last_modified=datetime.datetime.fromtimestamp(os.path.getmtime(file))
                            )
                    return cluster_type
        except FileNotFoundError as exc:
            cls.logger.error(f'Failed to load cluster type definition: {id}:{file} FileNotFoundError')
            return None


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


    def template_path(self):
        return os.path.join(self.hot_templates_dir, self.heat_template_url)


    def asdict(self, attributes=None):
        if attributes is None:
            return asdict(self)
        else:
            return {k: v for k, v in asdict(self).items() if k in attributes}
