import time

from magnumclient.client import Client

from ..models import ClusterType

class Cluster:
    def __init__(self, id, name):
        self.id = id
        self.name = name

class MagnumHandler:
    def __init__(self, sess, logger):
        self.logger = logger
        self.client = self.__get_client(sess)


    def __get_client(self, sess):
        start_time = time.time()
        while time.time() - start_time < 30:  # Try for up to 30 seconds
            try:
                client = Client(version='1', session=sess)
                self.logger.debug("Magnum client connected")
                return client
            except Exception as e:
                self.logger.error(f"Failed to create Magnum client: {e}. Retrying...")
                time.sleep(1)

        raise Exception("Failed to create Magnum client after multiple attempts.")

    def create_cluster(self, cluster_data, cluster_type):
        self.logger.info(f"Creating cluster {cluster_data['name']} from {cluster_data['cluster_type_id']}")
        # Allow errors to be propagated.  They will be caught and handled in
        # either `openstack.error_handling.py` or `__init__.py`.
        cluster_name = cluster_data["name"]
        self.logger.debug(f"getting cluster template {cluster_type.upstream_template}")
        magnum_cluster_template = self.client.cluster_templates.get(cluster_type.upstream_template)
        parameters = ClusterType.merge_parameters(cluster_type, cluster_data.get("parameters"))
        self.logger.debug(f"parameters: {parameters}")
        magnum_cluster = self.client.clusters.create(
                name=cluster_name,
                cluster_template_id=magnum_cluster_template.uuid,
                **parameters
                )
        return Cluster(id=magnum_cluster.uuid, name=cluster_name)
    
    def get_cluster(self, cluster_id):
        self.logger.info(f"Getting cluster info for {cluster_id}")

        response = self.client.clusters.get(cluster_id)
        return response
    
    def check_cluster_running(self, cluster_id):
        cluster = self.get_cluster(cluster_id)

        if cluster.status == 'CREATE_COMPLETE':
            return True
        
        return False
