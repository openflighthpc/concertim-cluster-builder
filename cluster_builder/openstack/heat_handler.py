import time
import yaml
import secrets

from heatclient.client import Client as HeatClient

from ..models import utils as model_utils

class Cluster:
    def __init__(self, id, name):
        self.id = id
        self.name = name


class HeatHandler:
    def __init__(self, sess, logger):
        self.logger = logger
        self.client = self.__get_client(sess)


    def __get_client(self, sess):
        start_time = time.time()
        while time.time() - start_time < 30:  # Try for up to 30 seconds
            try:
                client = HeatClient(version='1', session=sess)
                self.logger.debug("Heat client connected")
                return client
            except Exception as e:
                self.logger.error(f"Failed to create Heat client: {e}. Retrying...")
                time.sleep(1)

        raise Exception("Failed to create Heat client after multiple attempts.")


    def create_cluster(self, cluster_data, cluster_type):
        self.logger.info(f"Creating cluster {cluster_data['name']} from {cluster_data['cluster_type_id']}")
        # Allow errors to be propagated.  They will be caught and handled in
        # either `openstack.error_handling.py` or `__init__.py`.
        parameters = model_utils.merge_parameters(cluster_type, cluster_data.get("parameters"))
        self.logger.debug(f"parameters: {parameters}")
        stack_name = "{}--{}".format(cluster_data["name"], secrets.token_urlsafe(16))
        response = self.client.stacks.create(
                stack_name=stack_name,
                template=self._template_stream(cluster_type, cluster_data.get("selections")),
                parameters=parameters
                )
        return Cluster(id=response["stack"]["id"], name=stack_name)


    def _template_stream(self, cluster_type, selections):
        merged_resources = {}
        merged_outputs = {}
        merged_conditions = {}
        heat_template_versions = []

        self.logger.info(f"Building HEAT template for {cluster_type.id}: optional selections={selections}")
        for component in cluster_type.components:
            is_selected = selections.get(component.name, False)
            if component.is_optional and not is_selected:
                self.logger.info(f"skipping deselected component {component.name}")
                continue
            self.logger.info(f"including {'selected optional' if component.is_optional else 'mandatory'} component {component.name}")
            heat_template_versions.append(component.heat_template_version)

            for resource in component.resources:
                if resource in merged_resources:
                    raise RuntimeError(f"no good! duplicate resource identifiers {resource}")
            merged_resources.update(component.resources)

            for output in component.outputs:
                if output in merged_outputs:
                    raise RuntimeError(f"no good! duplicate output identifiers {output}")
            merged_outputs.update(component.outputs)

            for condition in component.conditions:
                if condition in merged_conditions:
                    raise RuntimeError(f"no good! duplicate condition identifiers {condition}")
            merged_conditions.update(component.conditions)

        if len(list(set(heat_template_versions))) > 1:
            raise RuntimeError(f"no good! incompatible heat template versions {heat_template_versions}")

        template = {
            "heat_template_version": heat_template_versions[0],
            "parameters": cluster_type.parameters_file.parameters,
            "resources": merged_resources,
            "conditions": merged_conditions,
            "outputs": merged_outputs,
        }

        return yaml.safe_dump(template)
