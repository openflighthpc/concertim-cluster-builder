import json

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

