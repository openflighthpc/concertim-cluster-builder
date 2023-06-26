import time
import yaml

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


    def list_stacks(self):
        self.logger.debug(f"Fetching all stacks")
        return self.client.stacks.list()


    def create_cluster(self, cluster_data, cluster_type):
        self.logger.info(f"Creating cluster {cluster_data['name']} from {cluster_data['cluster_type_id']}")
        response = None
        try:
            stack_name = "{}-{}".format(cluster_data["name"], cluster_type.id)
            response = self.client.stacks.create(
                    stack_name=stack_name,
                    template=self._template_stream(cluster_type),
                    parameters=ClusterType.merge_parameters(cluster_type, cluster_data.get("parameters"))
                    )
        except Exception as e:
            self.logger.exception(e)
            raise
        else:
            return Cluster(id=response["stack"]["id"], name=stack_name)


    def _template_stream(self, cluster_type):
        _files, template = template_utils.get_template_contents(cluster_type.template_path())
        return yaml.safe_dump(template)
