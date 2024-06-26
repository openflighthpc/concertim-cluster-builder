from logging.config import dictConfig
import json
import os
import pathlib
import ruamel.yaml
import sys
import traceback

from flask import (Flask, make_response, jsonify)
from jsonschema import ValidationError
from jsonschema.exceptions import (best_match)
from werkzeug.exceptions import HTTPException

yaml = ruamel.yaml.YAML(typ="safe", pure=True)

def default_config(app):
    return {
        'LOG_LEVEL': 'info',
        'LOG_FILE': os.path.join(app.root_path, '..', 'log', 'cluster-builder.log'),
    }


def load_config(path):
    try:
        return yaml.load(path)
    except FileNotFoundError as exc:
        print(f"Fatal error parsing config file: {str(exc)}", file=sys.stderr)
        sys.exit(1)
    except (ruamel.yaml.parser.ParserError, ruamel.yaml.scanner.ScannerError) as exc:
        print(f"Fatal error parsing config file: {path}: {str(exc)}", file=sys.stderr)
        sys.exit(1)


def configure_logging(app):
    config = {
        'version': 1,
        'formatters': {
            'default': {
                'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
            }
        },
        'handlers': {
            'wsgi': {
                'class': 'logging.StreamHandler',
                'stream': 'ext://flask.logging.wsgi_errors_stream',
                'formatter': 'default'
            },
        },
        'root': {
            'level': app.config['LOG_LEVEL'].upper(),
            'handlers': []
        }
    }
    log_file = app.config['LOG_FILE']
    if log_file is not None:
        config['handlers']['file'] = {
            'class': 'logging.FileHandler',
            'filename': log_file,
            'formatter': 'default'
        }
        config['root']['handlers'].append('file')
    if log_file is None or sys.stdout.isatty():
        config['root']['handlers'].append('wsgi')
    dictConfig(config)


def create_app(instance_path=None, test_config=None):
    app = Flask(__name__, instance_relative_config=True, instance_path=instance_path)
    if test_config is None:
        app.config.from_mapping(default_config(app))
        config_file = pathlib.Path(os.getenv('CONFIG_FILE', './config/config.yaml'))
        config = load_config(config_file)
        app.config.from_mapping(config)
    else:
        app.config.from_mapping(test_config)
    configure_logging(app)

    if 'JWT_SECRET' not in app.config:
        if 'JWT_SECRET' in os.environ:
            app.config['JWT_SECRET'] = os.environ['JWT_SECRET']
        else:
            app.logger.error("JWT_SECRET not set")

    os.makedirs(app.instance_path, exist_ok=True)
    os.makedirs(os.path.join(app.instance_path, "cluster-types-enabled"), exist_ok=True)
    os.makedirs(os.path.join(app.instance_path, "cluster-types-available"), exist_ok=True)

    from .models import ClusterTypeRepo
    ClusterTypeRepo.configure(
        types_dir=os.path.join(app.instance_path, "cluster-types-enabled"),
        logger=app.logger,
    )

    from . import cluster_types
    app.register_blueprint(cluster_types.bp)
    
    from . import clusters
    app.register_blueprint(clusters.bp)

    from . import cloud_assets
    app.register_blueprint(cloud_assets.bp)

    from .openstack.error_handling import setup_error_handling
    setup_error_handling(app)

    from .middleware.utils.error_handling import setup_middleware_error_handling
    setup_middleware_error_handling(app)
    
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
    def handle_http_exception(error):
        #Return JSON instead of HTML for HTTP errors.
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


    @app.errorhandler(Exception)
    def handle_exception(error):
        """Return JSON instead of HTML for all errors."""
        app.logger.exception(error)
        title = "500 Server Error"
        detail = "{}: {}".format(type(error).__name__, error)
        body = [{"status": 500, "title": title, "detail": detail}]
        if app.debug:
            meta = {"traceback": traceback.format_tb(error.__traceback__)}
            body[0]["meta"] = meta
        return make_response(jsonify({"errors": body}), 500)
    
    # Filtering sensitive JWT_SECRET info
    filtered_config = app.config.copy()
    if 'JWT_SECRET' in filtered_config:
        filtered_config['JWT_SECRET'] = '[FILTERED]'
    app.logger.debug(f"App config : \n{filtered_config}")

    return app
