import pytest
import shutil
import sys
import tempfile

# Mess with import path to allow importing our code.  There must be a better
# way to do this, but I don't know what that is at the moment.
import os
root = os.path.dirname(os.path.dirname(__file__))
sys.path.append(root)

from cluster_builder import create_app

@pytest.fixture()
def app():
    instance_path = tempfile.mkdtemp()
    print(f"instance_path set to {instance_path}", file=sys.stderr)
    app = create_app(instance_path=instance_path)
    app.config.update({
        "TESTING": True,
        "DEBUG" : True,
        "JWT_SECRET": "TEST_SECRET"
        })

    yield app

    shutil.rmtree(instance_path)


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def runner(app):
    return app.test_cli_runner()
