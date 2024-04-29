import time

from cinderclient import client

VERSION = '3'

class CinderHandler:
    def __init__(self, sess, logger):
        self.logger = logger
        self.cinder = self.__get_client(sess)

    def __get_client(self, sess):
        start_time = time.time()
        while time.time() - start_time < 30:  # Try for up to 30 seconds
            try:
                nova = client.Client(VERSION, session=sess)
                self.logger.debug("Nova client connected")
                return nova
            except Exception as e:
                self.logger.error(f"Failed to create Cinder client: {e}. Retrying...")
                time.sleep(1)

        raise Exception("Failed to create Cinder client after multiple attempts.")


    # A limit of -1 represents no limit
    def get_limits(self):
        limits = self.cinder.limits.get().to_dict()["absolute"]
        limits["remaining_disk"] = None if limits["maxTotalVolumeGigabytes"] == -1 else  limits["maxTotalVolumeGigabytes"] - limits["totalGigabytesUsed"]
        limits["remaining_volumes"] = None if limits["maxTotalVolumes"] == -1 else limits["maxTotalVolumes"] - limits["totalVolumesUsed"]
        return limits
