from datetime import datetime
import json
import pytest

from .utils import (write_cluster_definition, write_hot)

def test_invalid_definitions_result_in_404__missing_hot(client, app):
    # This cluster definition is broken as its heat template doesn't get
    # written.
    broken_definition = {
            "title": "broken-heat",
            "description": "fake",
            "kind": "heat",
            "heat_template_url": "does-not-exist.yaml",
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
def test_last_modified_for_heat_template_is_latest_of_either_definition_or_hot(client, app, definition_last_modified, hot_last_modified, expected_last_modified):
    definition = {
            "title": "test-heat",
            "description": "test-description",
            "kind": "heat",
            "heat_template_url": "test-hot.yaml",
            }
    hot = {
            "heat_template_version": "2021-04-16",
            "resources": {
                "router": { "type": "OS::Neutron::Router" },
                "network": { "type": "OS::Neutron::Net" },
                }
            }

    write_cluster_definition(app, definition, "test", last_modified=definition_last_modified)
    write_hot(app, hot, "test-hot.yaml", last_modified=hot_last_modified)
    response = client.get("/cluster-types/test")
    data = json.loads(response.data)
    assert data["id"] == "test"
    timeformat = "%a, %d %b %Y %T GMT"
    assert data["last_modified"] == datetime.fromisoformat(expected_last_modified).strftime(timeformat)
