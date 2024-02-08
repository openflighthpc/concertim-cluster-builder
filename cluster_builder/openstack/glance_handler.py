import time

from glanceclient import client

VERSION = '2'

class GlanceHandler:
    def __init__(self, sess, logger):
        self.logger = logger
        self.glance = self.__get_client(sess)

    def __get_client(self, sess):
        start_time = time.time()
        while time.time() - start_time < 30:  # Try for up to 30 seconds
            try:
                glance = client.Client(VERSION, session=sess)
                self.logger.debug("Glance client connected")
                return glance
            except Exception as e:
                self.logger.error(f"Failed to create Glance client: {e}. Retrying...")
                time.sleep(1)

        raise Exception("Failed to create Glance client after multiple attempts.")


    def list_images(self):
        return self.glance.images.list()

