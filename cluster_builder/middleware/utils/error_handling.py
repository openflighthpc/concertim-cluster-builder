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


from .exceptions import MIDDLEWARE_EXCEPTIONS
from flask import (current_app, make_response, jsonify, request)
import traceback 

def setup_middleware_error_handling(app):

    app.logger.info("Configuring Middleware error handlers")

    for exc in MIDDLEWARE_EXCEPTIONS:
        _register_error_handler(app, exc, MiddlewareErrorHandler)
    
    app.logger.debug("Done configuring Middleware error handlers")

def _register_error_handler(app, exc, handler):
    app.logger.debug(f"{exc.__module__}.{exc.__qualname__} -> {handler.__name__}")
    app.register_error_handler(exc, handler())


class BaseErrorHandler:
    """
    Base class for handling Middleware errors.  All errors should be returned as
    a JSON response using the JSON:API error format
    (https://jsonapi.org/format/#errors).

    It also provides a mechanism for additional processing of the error.  For
    example, we might want to change the HTTP status to one that is more
    suitable or consistent.
    """
    def __init__(self):
        pass

    def __call__(self, error):
        error_class_name = f"{error.__module__}.{error.__class__.__qualname__}"
        current_app.logger.debug(f"handling {error_class_name} with {self.__class__.__name__}")
        current_app.logger.info(f"{error_class_name}: {error.__dict__}")
        current_app.logger.debug(traceback.format_exc())
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


class MiddlewareErrorHandler(BaseErrorHandler):
    pass
