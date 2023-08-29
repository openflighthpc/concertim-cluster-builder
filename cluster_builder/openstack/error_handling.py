import inspect
import re

from flask import (current_app, make_response, jsonify, request)

import keystoneauth1.exceptions.connection as ks_connection_exceptions
import keystoneauth1.exceptions.http as ks_http_exceptions
import heatclient.exc as heat_exceptions
import magnumclient.exceptions as magnum_exceptions

HEAT_BAD_PARAMETER_REGEXP = re.compile("^Parameter '([^']*)' is invalid: (.*)")
MAGNUM_BAD_PARAMETER_REGEXP = re.compile("^Unable to find ([^ ]*) (.*).")

def setup_error_handling(app):
    """
    Configure the given Flask app with error handling for openstack exceptions.
    """
    app.logger.info("configuring error handlers")
    for exc in map(ks_http_exceptions.__dict__.get, ks_http_exceptions.__all__):
        if inspect.isclass(exc) and issubclass(exc, Exception):
            _register_error_handler(app, exc, _handle_keystone_http_exception)

    for exc in map(ks_connection_exceptions.__dict__.get, ks_connection_exceptions.__all__):
        if inspect.isclass(exc) and issubclass(exc, Exception):
            _register_error_handler(app, exc, _handle_keystone_connection_exception)

    for exc in map(heat_exceptions.__dict__.get, heat_exceptions.__dict__):
        if inspect.isclass(exc) and issubclass(exc, heat_exceptions.HTTPException):
            if issubclass(exc, heat_exceptions.HTTPBadRequest):
                _register_error_handler(app, exc, _handle_heat_http_bad_request)
            else:
                _register_error_handler(app, exc, _handle_heat_http_exception)

    for exc in map(magnum_exceptions.__dict__.get, magnum_exceptions.__dict__):
        if inspect.isclass(exc) and issubclass(exc, magnum_exceptions.HttpError):
            if issubclass(exc, magnum_exceptions.BadRequest):
                _register_error_handler(app, exc, _handle_magnum_http_bad_request)
            else:
                _register_error_handler(app, exc, _handle_magnum_http_exception)
    app.logger.debug("done configuring error handlers")


def _register_error_handler(app, exc, handler):
    app.logger.debug(f"{exc.__module__}.{exc.__qualname__} -> {handler.__name__}")
    app.register_error_handler(exc, handler)


def _handle_keystone_http_exception(error):
    current_app.logger.debug(f"handling error {error.__class__} with _handle_keystone_http_exception")
    if isinstance(error, ks_http_exceptions.Unauthorized):
        current_app.logger.info(
            "Authorization failed. %(exception)s from %(remote_addr)s",
            {'exception': error, 'remote_addr': request.remote_addr})
    else:
        current_app.logger.info(f"{error.__module__}.{error.__class__.__qualname__}: {error}")
    title = error.__class__.__name__
    errors = [{"status": str(error.http_status), "title": title, "detail": error.message}]
    return make_response(jsonify({"errors": errors}), error.http_status)


def _handle_keystone_connection_exception(error):
    current_app.logger.debug(f"handling error {error.__class__} with _handle_keystone_connection_exception")
    current_app.logger.info(f"{error.__module__}.{error.__class__.__qualname__}: {error}")
    title = error.__class__.__name__
    errors = [{"status": "502", "title": title, "detail": error.message}]
    return make_response(jsonify({"errors": errors}), 502)


def _handle_heat_http_exception(error):
    current_app.logger.debug(f"handling error {error.__class__} with _handle_heat_http_exception")
    current_app.logger.info(f"{error.__module__}.{error.__class__.__qualname__}: {error}")
    original_error = error.error
    title = original_error['title']
    detail = original_error['error']['message']
    errors = [{"status": str(error.code), "title": title, "detail": detail}]
    return make_response(jsonify({"errors": errors}), error.code)


def _handle_heat_http_bad_request(error):
    current_app.logger.debug(f"handling error {error.__class__} with _handle_heat_http_bad_request")
    current_app.logger.info(f"{error.__module__}.{error.__class__.__qualname__}: {error}")
    original_error = error.error
    title = original_error['title']
    detail = original_error['error']['message']
    match = HEAT_BAD_PARAMETER_REGEXP.match(detail)
    errors = [{"status": str(error.code), "title": title, "detail": detail}]
    if match is not None:
        if len(match.group(2)):
            errors[0]["detail"] = match.group(2)
        errors[0]["source"] = {"pointer": f"/cluster/parameters/{match.group(1)}"}
    return make_response(jsonify({"errors": errors}), error.code)


def _handle_magnum_http_exception(error):
    current_app.logger.debug(f"handling error {error.__class__} with _handle_magnum_http_exception")
    current_app.logger.info(f"{error.__module__}.{error.__class__.__qualname__}: {error}")
    title = error.__class__.__name__
    detail = error.details
    errors = [{"status": str(error.http_status), "title": title, "detail": detail}]
    return make_response(jsonify({"errors": errors}), error.http_status)


def _handle_magnum_http_bad_request(error):
    current_app.logger.debug(f"handling error {error.__class__} with _handle_magnum_http_bad_request")
    current_app.logger.info(f"{error.__module__}.{error.__class__.__qualname__}: {error}")
    title = error.__class__.__name__
    detail = error.details
    errors = [{"status": str(error.http_status), "title": title, "detail": detail}]
    try:
        match = MAGNUM_BAD_PARAMETER_REGEXP.match(detail)
        if match is not None:
            request_params = request.get_json()["cluster"]["parameters"]
            for param, val in request_params.items():
                if val == match.group(2):
                    errors[0]["source"] = {"pointer": f"/cluster/parameters/{param}"}
    except:
        pass
    return make_response(jsonify({"errors": errors}), error.http_status)
