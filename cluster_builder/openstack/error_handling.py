import inspect
import re

from flask import (current_app, make_response, jsonify, request)

import keystoneauth1.exceptions.connection as ks_connection_exceptions
import keystoneauth1.exceptions.http as ks_http_exceptions
import heatclient.exc as heat_exceptions
import magnumclient.exceptions as magnum_exceptions
import saharaclient.api.base as sahara_exceptions

def setup_error_handling(app):
    """
    Configure the given Flask app with error handling for openstack exceptions.
    """
    app.logger.info("configuring error handlers")
    for exc in map(ks_http_exceptions.__dict__.get, ks_http_exceptions.__all__):
        if inspect.isclass(exc) and issubclass(exc, Exception):
            _register_error_handler(app, exc, KeystoneHttpErrorHandler)

    for exc in map(ks_connection_exceptions.__dict__.get, ks_connection_exceptions.__all__):
        if inspect.isclass(exc) and issubclass(exc, Exception):
            _register_error_handler(app, exc, KeystoneConnectionErrorHandler)

    for exc in map(heat_exceptions.__dict__.get, heat_exceptions.__dict__):
        if inspect.isclass(exc) and issubclass(exc, heat_exceptions.HTTPException):
            if issubclass(exc, heat_exceptions.HTTPBadRequest):
                _register_error_handler(app, exc, HeatHttpBadRequestHandler)
            else:
                _register_error_handler(app, exc, HeatHttpErrorHandler)

    for exc in map(magnum_exceptions.__dict__.get, magnum_exceptions.__dict__):
        if inspect.isclass(exc) and issubclass(exc, magnum_exceptions.HttpError):
            if issubclass(exc, magnum_exceptions.BadRequest):
                _register_error_handler(app, exc, MagnumHttpBadRequestHandler)
            elif issubclass(exc, magnum_exceptions.NotFound):
                _register_error_handler(app, exc, MagnumHttpNotFoundHandler)
            else:
                _register_error_handler(app, exc, MagnumHttpErrorHandler)

    for exc in map(sahara_exceptions.__dict__.get, sahara_exceptions.__dict__):
        if inspect.isclass(exc) and issubclass(exc, Exception):
            _register_error_handler(app, exc, SaharaHttpErrorHandler)

    app.logger.debug("done configuring error handlers")


def _register_error_handler(app, exc, handler):
    app.logger.debug(f"{exc.__module__}.{exc.__qualname__} -> {handler.__name__}")
    app.register_error_handler(exc, handler())


class BaseErrorHandler:
    """
    Base class for handling openstack errors.  All errors should be returned as
    a JSON response using the JSON:API error format
    (https://jsonapi.org/format/#errors).

    The various openstack APIs cannot agree on how to encode errors.  Some
    store the HTTP status on the attribute `http_status` others use `code`
    others use `error_code`.  Similar for the error details or message. This
    class and its subclasses provide a common mechanism for handling these
    differences.

    It also provides a mechanism for additional processing of the error.  For
    example, we might want to change the HTTP status to one that is more
    suitable or consistent.
    """
    def __init__(self):
        pass

    def __call__(self, error):
        error_class_name = f"{error.__module__}.{error.__class__.__qualname__}"
        current_app.logger.debug(f"handling {error_class_name} with {self.__class__.__name__}")
        current_app.logger.info(f"{error_class_name}: {error}")
        errors = self.errors(error)
        try:
            status = int(errors[0]["status"], 10)
        except (ValueError, TypeError):
            status = self.status(error)
        return make_response(jsonify({"errors": errors}), status)

    def status(self, error):
        return error.http_status

    def title(self, error):
        return error.__class__.__name__

    def detail(self, error):
        return error.message

    def errors(self, error):
        return [{"status": str(self.status(error)), "title": self.title(error), "detail": self.detail(error)}]


class KeystoneHttpErrorHandler(BaseErrorHandler):
    pass

class KeystoneConnectionErrorHandler(BaseErrorHandler):
    def status(self, error):
        return 502

class HeatHttpErrorHandler(BaseErrorHandler):
    def status(self, error):
        return error.code

    def title(self, error):
        return error.error['title']

    def detail(self, error):
        return error.error['error']['message']

class HeatHttpBadRequestHandler(HeatHttpErrorHandler):
    BAD_PARAMETER_REGEXP = re.compile("^Parameter '([^']*)' is invalid: (.*)")

    def errors(self, error):
        errors = super().errors(error)
        match = self.BAD_PARAMETER_REGEXP.match(errors[0]["detail"])
        if match is not None:
            if len(match.group(2)):
                errors[0]["detail"] = match.group(2)
            errors[0]["source"] = {"pointer": f"/cluster/parameters/{match.group(1)}"}
        return errors

class MagnumHttpErrorHandler(BaseErrorHandler):
    def detail(self, error):
        return error.details

class MagnumHttpBadRequestHandler(MagnumHttpErrorHandler):
    BAD_PARAMETER_REGEXP = re.compile("^Unable to find ([^ ]*) (.*).")

    def errors(self, error):
        errors = super().errors(error)
        match = self.BAD_PARAMETER_REGEXP.match(errors[0]["detail"])
        if match is not None:
            request_params = request.get_json()["cluster"]["parameters"]
            for param, val in request_params.items():
                if val == match.group(2):
                    errors[0]["source"] = {"pointer": f"/cluster/parameters/{param}"}
        return errors

class MagnumHttpNotFoundHandler(MagnumHttpErrorHandler):
    def errors(self, error):
        errors = super().errors(error)
        match = MagnumHttpBadRequestHandler.BAD_PARAMETER_REGEXP.match(errors[0]["detail"])
        if match is not None:
            # Magnum couldn't find some resource that was specified in the
            # parameters.  This is more accurately reported as a Bad Request
            # than Not Found.
            response_status = 400
            errors[0]["title"] = "Bad Request"
            errors[0]["status"] = str(response_status)
            request_params = request.get_json()["cluster"]["parameters"]
            for param, val in request_params.items():
                if val == match.group(2):
                    errors[0]["source"] = {"pointer": f"/cluster/parameters/{param}"}
        return errors

class SaharaHttpErrorHandler(BaseErrorHandler):
    NOT_FOUND_REGEXP = re.compile("^([^ ]*) (.*) not found")
    INVALID_FORMAT_REGEXP = re.compile("^([^:]*): '([^']*)' is not a '[^']*'")

    def status(self, error):
        return error.error_code

    def title(self, error):
        return error.error_name

    def detail(self, error):
        return error.error_message

    def errors(self, error):
        errors = super().errors(error)
        match = self.NOT_FOUND_REGEXP.match(errors[0]["detail"])
        if match is None:
            match = self.INVALID_FORMAT_REGEXP.match(errors[0]["detail"])
        if match is not None:
            errors[0]["title"] = "Bad Request"
            errors[0]["detail"] = match.group(0)
            errors[0]["status"] = "400"
            request_params = request.get_json()["cluster"]["parameters"]
            for param, val in request_params.items():
                if val == match.group(2):
                    errors[0]["source"] = {"pointer": f"/cluster/parameters/{param}"}
        return errors
