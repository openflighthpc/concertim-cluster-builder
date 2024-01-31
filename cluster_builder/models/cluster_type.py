from dataclasses import asdict, dataclass, field

from flask import (abort)

from .cluster_type_factory import ClusterTypeFactory

@dataclass
class ClusterType:
    # Class variables configured in configure method.
    logger = None

    # Instance variables used by dataclass decorator.
    id: str
    title: str
    description: str
    parameters: dict
    kind: str
    upstream_template: str
    last_modified: str
    hardcoded_parameters: dict = field(default_factory=dict)
    # XXX Do I need this?
    required_parameters: list = field(default_factory=list)

    @classmethod
    def configure(cls, hot_templates_dir, types_dir, logger):
        cls.factory = ClusterTypeFactory(cls, hot_templates_dir, types_dir, logger)
        cls.logger = logger


    @classmethod
    def all(cls):
        """
        Return list of cluster types.
        """
        return cls.factory.all()


    @classmethod
    def find(cls, id):
        """
        Return the specified cluster type or abort with a 404.
        """
        return cls.factory.find(id)


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
        return self.factory.hot_template_path(self.upstream_template)


    def asdict(self, attributes=None):
        if attributes is None:
            return asdict(self)
        else:
            return {k: v for k, v in asdict(self).items() if k in attributes}
