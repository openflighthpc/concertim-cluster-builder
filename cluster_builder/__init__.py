import os
from logging.config import dictConfig

from flask import (Flask, make_response, jsonify)
from jsonschema import ValidationError

def create_app(test_config=None):
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
    app = Flask(__name__, instance_relative_config=True)
    # app.config.from_mapping()

    if test_config is None:
        app.config.from_pyfile('config.py', silent=True)
    else:
        app.config.from_mapping(test_config)

    try:
        os.makedirs(app.instance_path)
        os.makedirs(os.path.join(app.instance_path, "cluster-types-enabled"))
        os.makedirs(os.path.join(app.instance_path, "cluster-types-available"))
    except OSError:
        pass

    from . import cluster_types
    app.register_blueprint(cluster_types.bp)
    
    from . import clusters
    app.register_blueprint(clusters.bp)
    
    @app.errorhandler(400)
    def bad_request(error):
        if isinstance(error.description, ValidationError):
            jsonschema_error = error.description
            title = "JSON schema error"
            source = {"pointer": "/{}".format("/".join(jsonschema_error.absolute_path))}
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

    return app
