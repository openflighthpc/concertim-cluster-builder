from logging.config import dictConfig
import json
import os

from flask import (Flask, make_response, jsonify)
from jsonschema import ValidationError
from jsonschema.exceptions import (best_match)
from werkzeug.exceptions import HTTPException

def create_app(instance_path=None, test_config=None):
    # dictConfig({
    #     'version': 1,
    #     'formatters': {'default': {
    #         'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
    #     }},
    #     'handlers': {'wsgi': {
    #         'class': 'logging.StreamHandler',
    #         'stream': 'ext://flask.logging.wsgi_errors_stream',
    #         'formatter': 'default'
    #     }},
    #     'root': {
    #         'level': 'INFO',
    #         'handlers': ['wsgi']
    #     }
    # })
    app = Flask(__name__, instance_relative_config=True, instance_path=instance_path)
    # app.config.from_mapping()

    if test_config is None:
        app.config.from_pyfile('config.py', silent=True)
    else:
        app.config.from_mapping(test_config)

    os.makedirs(app.instance_path, exist_ok=True)
    os.makedirs(os.path.join(app.instance_path, "cluster-types-enabled"), exist_ok=True)
    os.makedirs(os.path.join(app.instance_path, "cluster-types-available"), exist_ok=True)
    os.makedirs(os.path.join(app.instance_path, "hot"), exist_ok=True)

    from .models import ClusterType
    ClusterType.configure(
            hot_templates_dir=os.path.join(app.instance_path, "hot"),
            types_dir=os.path.join(app.instance_path, "cluster-types-enabled"),
            logger=app.logger,
            )

    from . import cluster_types
    app.register_blueprint(cluster_types.bp)
    
    from . import clusters
    app.register_blueprint(clusters.bp)

    from .openstack.error_handling import setup_error_handling
    setup_error_handling(app)

    @app.errorhandler(400)
    def bad_request(error):
        if isinstance(error.description, ValidationError):
            jsonschema_error = error.description
            title = "JSON schema error"
            source = {"pointer": "/{}".format("/".join(jsonschema_error.absolute_path))}
            if jsonschema_error.validator == 'oneOf':
                additional = best_match(jsonschema_error.context).message
                detail = "{}: the best matched error is: {}".format(jsonschema_error.message, additional)
            else:
                detail = jsonschema_error.message
            errors = [{"status": f"{error.code}", "title": title, "detail": detail, "source": source}]
            app.logger.debug(f'jsonschema validation error: {errors}')
            return make_response(jsonify({'errors': errors}), error.code)

        # handle other "Bad Request"-errors
        title = error.name
        errors = [{"status": f"{error.code}", "title": title}]
        if hasattr(error, 'description'):
            errors[0]["detail"] = str(error.description)
        app.logger.debug(f'bad request: {errors}')
        return make_response(jsonify({'errors': errors}), error.code)

    @app.errorhandler(404)
    def not_found(error):
        errors = [ { "status": f"{error.code}", "title": error.name } ]
        if hasattr(error, 'description'):
            errors[0]["detail"] = str(error.description)
        return make_response(jsonify({"errors": errors}), error.code)


    @app.errorhandler(HTTPException)
    def handle_exception(error):
        """Return JSON instead of HTML for HTTP errors."""
        response = error.get_response()
        response.data = json.dumps({
            "errors": [{
                "status": str(error.code),
                "title": error.name,
                "description": error.description,
                }]
        })
        response.content_type = "application/json"
        return response

    return app
