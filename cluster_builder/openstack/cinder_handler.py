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
                self.logger.debug("Cinder client connected")
                return nova
            except Exception as e:
                self.logger.error(f"Failed to create Cinder client: {e}. Retrying...")
                time.sleep(1)

        raise Exception("Failed to create Cinder client after multiple attempts.")


    # A limit of -1 represents no limit
    def get_limits(self):
        grouped_limits = {}
        limits = self.cinder.limits.get().to_dict()["absolute"]
        grouped_limits["volume_disk"] = {
            "total_allowed": limits["maxTotalVolumeGigabytes"], "used": limits["totalGigabytesUsed"], "units": "GB"
        }
        grouped_limits["volume_disk"]["remaining"] = None if limits["maxTotalVolumeGigabytes"] == -1 else limits["maxTotalVolumeGigabytes"] - limits["totalGigabytesUsed"]

        grouped_limits["volumes"] = {
            "total_allowed": limits["maxTotalVolumes"], "used": limits["totalVolumesUsed"], "units": ""
        }
        grouped_limits["volumes"]["remaining"] = None if limits["maxTotalVolumes"] == -1 else limits["maxTotalVolumes"] - limits["totalVolumesUsed"]

        return grouped_limits
