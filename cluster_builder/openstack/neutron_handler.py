from dataclasses import dataclass
import time

from neutronclient.v2_0 import client

@dataclass
class Network:
    id: str
    name: str
    external: bool

class NeutronHandler:
    def __init__(self, sess, logger):
        self.logger = logger
        self.neutron = self.__get_client(sess)

    def __get_client(self, sess):
        start_time = time.time()
        while time.time() - start_time < 30:  # Try for up to 30 seconds
            try:
                neutron = client.Client(session=sess)
                self.logger.debug("Neutron client connected")
                return neutron
            except Exception as e:
                self.logger.error(f"Failed to create Neutron client: {e}. Retrying...")
                time.sleep(1)

        raise Exception("Failed to create Neutron client after multiple attempts.")


    def list_networks(self):
        networks = []
        for network in self.neutron.list_networks()["networks"]:
            kwargs = {"id": network["id"], "name": network["name"], "external": network["router:external"]}
            networks.append(Network(**kwargs))
        return networks
