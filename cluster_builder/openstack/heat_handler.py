import time

from heatclient.client import Client as HeatClient

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


    def create_cluster(self, cluster_data):
        self.logger.debug(f"creating cluster {cluster_data['name']}")
        stack = None
        try:
            stacks = self.list_stacks()
            stack = next(stacks)
        except Exception as e:
            self.logger.debug(e)
            raise
        else:
            if stack is None:
                self.logger.debug(f"faking cluster creation failure")
                return None
            else:
                self.logger.debug(f"fake created cluster {stack.id}")
                return Cluster(id=stack.id, name=stack.stack_name)
