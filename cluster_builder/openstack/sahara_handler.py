import time
import secrets

from saharaclient.client import Client
from saharaclient.osc import utils

from ..models import utils as model_utils

class Cluster:
    def __init__(self, id, name):
        self.id = id
        self.name = name


class SaharaHandler:
    def __init__(self, sess, logger):
        self.logger = logger
        self.client = self.__get_client(sess)

    def __get_client(self, sess):
        start_time = time.time()
        while time.time() - start_time < 30:  # Try for up to 30 seconds
            try:
                client = Client(version='1.1', session=sess)
                self.logger.debug("Sahara client connected")
                return client
            except Exception as e:
                self.logger.error(f"Failed to create Sahara client: {e}. Retrying...")
                time.sleep(1)

        raise Exception("Failed to create Sahara client after multiple attempts.")

    def create_cluster(self, cluster_data, cluster_type, project_limits, flavors):
        # Allow errors to be propagated.  They will be caught and handled in
        # either `openstack.error_handling.py` or `__init__.py`.
        cluster_name = "{}-{}".format(cluster_data["name"], secrets.token_urlsafe(4)[0:4])
        self.logger.info(f"Creating cluster {cluster_name} from {cluster_data['cluster_type_id']}")
        args = self._build_args(cluster_data, cluster_type, cluster_name)
        self.logger.debug(f"args: {args}")
        sahara_cluster = self.client.clusters.create(**args)
        return Cluster(id=sahara_cluster.id, name=sahara_cluster.name)

    def _build_args(self, cluster_data, cluster_type, cluster_name):
        self.logger.debug(f"getting sahara cluster template {cluster_type.upstream_template}")
        parameters = model_utils.merge_parameters(cluster_type, cluster_data.get("parameters"))
        sct = utils.get_resource(self.client.cluster_templates, cluster_type.upstream_template)
        self.logger.debug(f"getting image_id for {parameters.get('image', None)}")
        try:
            image_name = parameters.pop("image")
            image_id = utils.get_resource_id(self.client.images, image_name)
        except Exception as ex:
            # The error message returned by openstack is "No matches found."
            # Nothing else is provided to help identify that it is the image
            # that hasn't been found, so we modify the exception here.
            ex.error_message = f"image {image_name} not found"
            raise ex

        # XXX Ideally, we would map from a network name to a network id here.
        # Unfortunately, I don't know how to do that right now. The code below
        # would work if `network_client` were an instance of
        # `python-novaclient:novaclient.v2.networks.NeutronManager`, but I'm
        # not sure how to correctly create one of those.
        #
        # Instead, we require the network id to be passed as a parameter.
        #
        #   try:
        #       network_id = network_client.find_network(parameters.pop("network"), ignore_missing=False).id
        #   except KeyError:
        #       network_id = None
        try:
            network_id = parameters.pop("network_id")
        except KeyError:
            network_id = None

        args = dict(
            name=cluster_name,
            plugin_name=sct.plugin_name,
            cluster_template_id=sct.id,
            default_image_id=image_id,
            net_id=network_id,
            user_keypair_id=parameters.pop("user_keypair"),
            )
        if hasattr(sct, 'plugin_version'):
            args["plugin_version"] = sct.plugin_version
        else:
            args["hadoop_version"] = sct.hadoop_version
        return {**args, **parameters}


    def list_plugins(self):
        return self.client.plugins.list()


    def list_images(self):
        return self.client.images.list()


    def list_cluster_templates(self):
        return self.client.cluster_templates.list()
