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

from datetime import datetime
import json
import pytest

from .utils import (write_cluster_definition, write_hot_component)

def test_invalid_definitions_result_in_404__missing_hot(client, app):
    # This cluster definition is broken as its heat template doesn't get
    # written.
    broken_definition = {
        "title": "broken-heat",
        "description": "fake",
        "kind": "heat",
        "components": "should be a list",
    }
    write_cluster_definition(app, broken_definition, "broken")
    response = client.get("/cluster-types/broken")
    assert response.status_code == 404
    data = json.loads(response.data)
    assert "errors" in data.keys()
    assert len(data["errors"]) == 1
    error = data["errors"][0]
    assert error["title"] == "Not Found"
    assert error["status"] == "404"


@pytest.mark.parametrize("last_modified", [
    "2023-01-01T12:00:00",
    "2023-08-01T12:00:00",
    "2023-08-14T12:30:59",
    ])
def test_last_modified_for_magnum_definition_is_definition_last_modified(client, app, last_modified):
    definition = {
        "title": "test-magnum",
        "description": "test-description",
        "parameters": {},
        "kind": "magnum",
        "magnum_cluster_template": "test-template",
        "order": 123,
        "logo_url": "/images/foo.svg",
    }
    write_cluster_definition(app, definition, "test", last_modified=last_modified)
    response = client.get("/cluster-types/test")
    data = json.loads(response.data)
    assert data["id"] == "test"
    timeformat = "%a, %d %b %Y %T GMT"
    assert data["last_modified"] == datetime.fromisoformat(last_modified).strftime(timeformat)


@pytest.mark.parametrize("definition_last_modified,hot_last_modified,expected_last_modified", [
    ("2023-08-14T12:00:00", "2023-08-14T12:00:00", "2023-08-14T12:00:00"),
    ("2023-08-14T12:30:00", "2023-08-14T12:00:00", "2023-08-14T12:30:00"),
    ("2023-08-01T12:00:00", "2023-08-14T12:00:00", "2023-08-14T12:00:00"),
    ])
def test_last_modified_for_heat_template(client, app, definition_last_modified, hot_last_modified, expected_last_modified):
    """
    Last modified for heat backed cluster types is the latest of their constituent files
    """
    definition = {
        "title": "test-heat",
        "description": "test-description",
        "kind": "heat",
        "components": [{"name": "test-hot"}],
        "parameter_groups": [],
        "order": 123,
        "logo_url": "/images/foo.svg",
    }
    hot = {
        "heat_template_version": "2021-04-16",
        "parameters": {},
        "resources": {
            "router": { "type": "OS::Neutron::Router" },
            "network": { "type": "OS::Neutron::Net" },
        }
    }

    write_cluster_definition(app, definition, "test", last_modified=definition_last_modified)
    write_hot_component(app, hot, "test", "test-hot", last_modified=hot_last_modified)
    response = client.get("/cluster-types/test")
    data = json.loads(response.data)
    app.logger.info(f'data: {data}')
    assert data["id"] == "test"
    timeformat = "%a, %d %b %Y %T GMT"
    assert data["last_modified"] == datetime.fromisoformat(expected_last_modified).strftime(timeformat)
