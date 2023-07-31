import time
import yaml
import secrets

from heatclient.client import Client as HeatClient
from heatclient.common import template_utils

from ..models import ClusterType

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
        response = None
        # Allow errors to be propagated.  They will be caught and handled in
        # either `openstack.error_handling.py` or `__init__.py`.
        parameters = ClusterType.merge_parameters(cluster_type, cluster_data.get("parameters"))
        self.logger.debug(f"parameters: {parameters}")
        stack_name = "{}--{}".format(cluster_data["name"], secrets.token_urlsafe(16))
        response = self.client.stacks.create(
                stack_name=stack_name,
                template=self._template_stream(cluster_type),
                parameters=parameters
                )
        return Cluster(id=response["stack"]["id"], name=stack_name)


    def _template_stream(self, cluster_type):
        _files, template = template_utils.get_template_contents(cluster_type.template_path())
        return yaml.safe_dump(template)
