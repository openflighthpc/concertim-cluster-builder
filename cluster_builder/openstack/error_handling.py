import inspect

from flask import (current_app, make_response, jsonify, request)

import keystoneauth1.exceptions.connection as ks_connection_exceptions
import keystoneauth1.exceptions.http as ks_http_exceptions
import heatclient.exc as heat_exceptions

def setup_error_handling(app):
    """
    Configure the given Flask app with error handling for openstack exceptions.
    """
    for exc in map(ks_http_exceptions.__dict__.get, ks_http_exceptions.__all__):
        if inspect.isclass(exc) and issubclass(exc, Exception):
            app.logger.debug(f"adding handler for {exc.__module__}.{exc.__qualname__}")
            app.register_error_handler(exc, _handle_keystone_http_exception)

    for exc in map(ks_connection_exceptions.__dict__.get, ks_connection_exceptions.__all__):
        if inspect.isclass(exc) and issubclass(exc, Exception):
            app.logger.debug(f"adding handler for {exc.__module__}.{exc.__qualname__}")
            app.register_error_handler(exc, _handle_keystone_connection_exception)

    for exc in map(heat_exceptions.__dict__.get, heat_exceptions.__dict__):
        if inspect.isclass(exc) and issubclass(exc, heat_exceptions.HTTPException):
            app.logger.debug(f"adding handler for {exc.__module__}.{exc.__qualname__}")
            app.register_error_handler(exc, _handle_heat_http_exception)


def _handle_keystone_http_exception(error):
    current_app.logger.debug(f"handling error {error.__class__} with _handle_keystone_http_exception")
    if isinstance(error, ks_http_exceptions.Unauthorized):
        current_app.logger.info(
            "Authorization failed. %(exception)s from %(remote_addr)s",
            {'exception': error, 'remote_addr': request.remote_addr})
    else:
        current_app.logger.info(str(error))
    title = error.__class__.__name__
    body = [{"status": str(error.http_status), "title": title, "detail": error.message}]
    return make_response(jsonify(body), error.http_status)


def _handle_keystone_connection_exception(error):
    current_app.logger.debug(f"handling error {error.__class__} with _handle_keystone_connection_exception")
    current_app.logger.info(str(error))
    title = error.__class__.__name__
    body = [{"status": "502", "title": title, "detail": error.message}]
    return make_response(jsonify(body), 502)


def _handle_heat_http_exception(error):
    current_app.logger.debug(f"handling error {error.__class__} with _handle_heat_http_exception")
    current_app.logger.info(str(error))
    original_error = error.error
    title = original_error['title']
    detail = original_error['error']['message']
    body = [{"status": str(error.code), "title": title, "detail": detail}]
    return make_response(jsonify(body), error.code)
