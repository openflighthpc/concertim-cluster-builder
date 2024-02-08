
import jwt
import os
import json
import time
from .exceptions import MiddlewareAuthenticationError

def authenticate_headers(config, headers, logger):

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
    



