"""
==============================================================================
 Copyright (C) 2024-present Alces Flight Ltd.

 This file is part of Concertim Cluster Builder.

 This program and the accompanying materials are made available under
 the terms of the Eclipse Public License 2.0 which is available at
 <https://www.eclipse.org/legal/epl-2.0>, or alternative license
 terms made available by Alces Flight Ltd - please direct inquiries
 about licensing to licensing@alces-flight.com.

 Concertim Visualisation App is distributed in the hope that it will be useful, but
 WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, EITHER EXPRESS OR
 IMPLIED INCLUDING, WITHOUT LIMITATION, ANY WARRANTIES OR CONDITIONS
 OF TITLE, NON-INFRINGEMENT, MERCHANTABILITY OR FITNESS FOR A
 PARTICULAR PURPOSE. See the Eclipse Public License 2.0 for more
 details.

 You should have received a copy of the Eclipse Public License 2.0
 along with Concertim Visualisation App. If not, see:

  https://opensource.org/licenses/EPL-2.0

 For more information on Concertim Cluster Builder, please visit:
 https://github.com/openflighthpc/concertim-cluster-builder
==============================================================================
"""

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
    test_config = {
        "TESTING": True,
        "DEBUG" : True,
        "JWT_SECRET": "TEST_SECRET",
        "LOG_LEVEL": "DEBUG",
        "LOG_FILE": None,
    }
    app = create_app(instance_path=instance_path, test_config=test_config)

    yield app

    shutil.rmtree(instance_path)


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def runner(app):
    return app.test_cli_runner()
