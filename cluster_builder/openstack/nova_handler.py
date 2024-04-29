import time

from novaclient import client

VERSION = '2'

class NovaHandler:
    def __init__(self, sess, logger):
        self.logger = logger
        self.nova = self.__get_client(sess)

    def __get_client(self, sess):
        start_time = time.time()
        while time.time() - start_time < 30:  # Try for up to 30 seconds
            try:
                nova = client.Client(VERSION, session=sess)
                self.logger.debug("Nova client connected")
                return nova
            except Exception as e:
                self.logger.error(f"Failed to create Nova client: {e}. Retrying...")
                time.sleep(1)

        raise Exception("Failed to create Nova client after multiple attempts.")


    def list_flavors(self):
        return self.nova.flavors.list()

    def list_keypairs(self):
        return self.nova.keypairs.list()

    # A limit of -1 represents no limit
    def get_limits(self):
        limits = self.nova.limits.get().to_dict()["absolute"]
        limits["remaining_ram"] = None if limits["maxTotalRAMSize"] == -1 else limits["maxTotalRAMSize"] - limits["totalRAMUsed"]
        limits["remaining_cores"] = None if limits["maxTotalCores"] == -1 else limits["maxTotalCores"] - limits["totalCoresUsed"]
        limits["remaining_instances"] = None if limits["maxTotalInstances"] == -1 else limits["maxTotalInstances"] - limits["totalInstancesUsed"]
        return limits
