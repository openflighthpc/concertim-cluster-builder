from dataclasses import dataclass
import glob
import os
import yaml

@dataclass
class ClusterType:
    # Class variables configured in configure method.
    types_dir = None
    logger = None

    # Instance variables used by dataclass decorator.
    id: str
    title: str
    description: str
    parameters: dict

    @classmethod
    def configure(cls, types_dir, logger):
        cls.types_dir = types_dir
        cls.logger = logger

    @classmethod
    def all(cls):
        """
        Return list of cluster types.
        """
        types = []

        for file in glob.glob(os.path.join(cls.types_dir, "*.yaml")):
            id = os.path.splitext(os.path.basename(file))[0]
            with open(file, 'r') as stream:
                try:
                    template = yaml.safe_load(stream)
                except yaml.YAMLError as exc:
                    cls.logger.error(f'failed to load cluster type definition: {id} {exc}')
                else:
                    cluster_type = cls(
                            id=id,
                            title=template.get("title", ""),
                            description=template.get("description", id),
                            parameters=template.get("parameters", [])
                            )
                    types.append(cluster_type)

        return types
