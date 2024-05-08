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


import jwt
import os
import json
import time
from .exceptions import MiddlewareAuthenticationError

def assert_authenticated(config, headers, logger):

    headers = dict(headers)
    logger.info(f"Headers : {headers}")

    # Checking for presence of Authorization Header field
    if "Authorization" not in headers:
        logger.error(f"Authorization header not present in request")
        raise MiddlewareAuthenticationError("Authorization header not present in request")
    
    # Checking for presence of 'Bearer' keyword
    bearer_token = headers["Authorization"]
    if bearer_token[0:7] != "Bearer ":
        logger.error("Bearer token not present")
        raise MiddlewareAuthenticationError("Bearer token not present in Authorization header")

    encoded_message = bearer_token[7:]

    if 'JWT_SECRET' in config:
        secret_key = config['JWT_SECRET']
    else:
        logger.error("JWT_SECRET not set")
        raise MiddlewareAuthenticationError("JWT_SECRET not set")

    # Decrypting message
    try:
        payload = jwt.decode(encoded_message, key=secret_key, algorithms="HS256", options={"require": ["exp"]})
    
    except jwt.ExpiredSignatureError as e:
        logger.error("JWT Signature expired")
        raise MiddlewareAuthenticationError(str(e))
    
    except Exception as e:
        logger.error(f"Exception : {e}")
        raise MiddlewareAuthenticationError(str(e))

    logger.debug(f"Payload : {payload}")
    logger.info("Authentication Successful")
    



