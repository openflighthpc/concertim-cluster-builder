
import jwt
import os
import json
import time


def authenticate_headers(config, headers, logger):

    headers = dict(headers)
    logger.info(f"Headers : {headers}")

    # Checking for presence of Authorization Header field
    if "Authorization" not in headers:
        return False, "Authorization header not present in request"
    
    # Checking for presence of 'Bearer' keyword
    bearer_token = headers["Authorization"]
    if bearer_token[0:7] != "Bearer ":
        logger.error("Bearer token not present")
        return False, "Bearer token not present in Authorization header"

    encoded_message = bearer_token[7:]

    if 'JWT_SECRET' in config:
        secret_key = config['JWT_SECRET']
    else:
        logger.error("JWT_SECRET not set")
        return False, "JWT_SECRET not set"

    #Decrypting message
    try:
        payload = jwt.decode(encoded_message, key=secret_key, algorithms="HS256", options={"require": ["exp"]})
    except jwt.ExpiredSignatureError:
        logger.error("JWT Signature expired")
        return False, "JWT Signature expired"
    except Exception as e:
        logger.error(f"Exception : {e}")
        return False, "JWT decoding failed"

    logger.info(f"Payload : {payload}")
    logger.info("Authentication Successful")
    
    return True, "SUCCCESS"




