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

# Endpoints file containing info on all Middleware endpoints
from .utils.endpoints import ENDPOINTS
from .utils.exceptions import MiddlewareItemConflict, MiddlewareMissingRequiredArgs, MiddlewareServiceError

# Py Packages
import sys
import json
import jwt
import time
import os
# Disable insecure warnings  
import requests
requests.packages.urllib3.disable_warnings() 

class MiddlewareService(object):
    def __init__(self, config_obj, logger, middleware_url):
        self._CONFIG = config_obj    
        self.__LOGGER = logger
        self._URL = middleware_url
        self.__retry_count = 0
        self.__AUTH_TOKEN = self.__get_auth_token()
    
    def __get_auth_token(self):

        if 'JWT_SECRET' not in self._CONFIG:
            self.__LOGGER.error("JWT_SECRET not set")
            return None
    
        secret_key = self._CONFIG['JWT_SECRET']

        # Encoding payload      
        try:
            encoded_jwt = jwt.encode({"exp": int(time.time() + 60)}, secret_key , algorithm="HS256")
            return "Bearer " + encoded_jwt
        
        except Exception as e:
            self.__LOGGER.error("JWT Encoding failed")
            
        return None

    # Return a dict of available endpoints and the call/data needed
    def list_available_endpoints(self):
        return ENDPOINTS

    def get_credits(self, variables_dict):

        self.__LOGGER.info("*** Calling get_credits Middleware API ***")
        
        try:
            response = self._api_call('post', 'GET_CREDITS', variables_dict=variables_dict)        
            self.__LOGGER.info("*** Finished get_credits Middleware API ***")
            self.__LOGGER.debug(f"{response}")
            return response['credits']
        
        except Exception as e:
            self.__LOGGER.error("*** get_credits Middleware API failed ***")
            raise MiddlewareServiceError(str(e))
        
    
    def create_order(self, variables_dict):

        self.__LOGGER.info(" *** Calling create_order Middleware API ***")

        try:
            response = self._api_call('post', 'CREATE_ORDER', variables_dict=variables_dict)
            self.__LOGGER.info("*** Finished create_order Middleware API ***")
            self.__LOGGER.debug(f"{response}")

            return response['order']
        
        except Exception as e:
            self.__LOGGER.error("*** create_order Middleware API failed ***")
            raise MiddlewareServiceError(str(e))
    
    def delete_order(self, variables_dict):

        self.__LOGGER.info(" *** Calling delete_order Middleware API ***")

        try:
            self._api_call('post', 'DELETE_ORDER', variables_dict=variables_dict)
            self.__LOGGER.info("*** Finished delete_order Middleware API ***")
            
        except Exception as e:
            self.__LOGGER.error("*** delete_order Middleware API failed ***")
            raise MiddlewareServiceError(str(e))

    def add_order_tag(self, variables_dict):

        self.__LOGGER.info(" *** Calling add_order_tag Middleware API ***")

        try:
            response = self._api_call('post', 'ADD_ORDER_TAG', variables_dict=variables_dict)
            self.__LOGGER.info("*** Finished add_order_tag Middleware API ***")
            self.__LOGGER.debug(f"{response}")
            return response
    
        except Exception as e:
            self.__LOGGER.error("*** add_order_tag Middleware API failed ***")
            raise MiddlewareServiceError(str(e))

    # Generic method for handling Concertim API calls.
    def _api_call(self, method, endpoint_name, variables_dict={}, endpoint_var=''):
        """
        Generic method for handling Concertim API calls.
        ACCEPTS:
            method - the REST call to make (get,post,patch,etc)
            endpoint_name - the endpoint name correspoinding to the ENDPOINTS dictionary
                            (GET_CREDITS, CREATE_ORDER, DELETE_ORDER, ADD_ORDER_TAG, etc)
            *variables_dict - the dictionary containing all needed variables to make the API call
            *endpoint_var - this is the ID or NAME of a device/template/rack that needs to be filled in the URL string
        
        Will return the JSON response, or raise an exception based on the status code
        
        """
        endpoint = ENDPOINTS[method.upper()]['endpoints'][endpoint_name]
        headers = ENDPOINTS[method.upper()]['headers']
        # Handle endpoint formatting
        if endpoint_var:
            url = self._URL + endpoint['endpoint'].format(endpoint_var)
        else:
            url = self._URL + endpoint['endpoint']

        # Handle if it is LOGIN_AUTH
        if self.__AUTH_TOKEN is not None:
            headers["Authorization"] = self.__AUTH_TOKEN
        else:
            e = MiddlewareMissingRequiredArgs("No Authentication Token provided")
            self.__LOGGER.error(f"{type(e).__name__} - {e}")
            raise e

        # Handle if there is a 'data' dump needed
        if variables_dict:
            self.__check_required_vars(variables_dict, endpoint)
            data_dict = self.__get_data(variables_dict, endpoint['data'], endpoint_name)
            data = json.dumps(data_dict)
            self.__LOGGER.debug(f"Data to send: {data}")
            # Don't log user/pass in plain text
            if endpoint_name == 'LOGIN_AUTH':
                self.__LOGGER.debug(f"API CALL ({method}) - {url}")
            else:
                self.__LOGGER.debug(f"API CALL ({method}) - {url} : data [{data}]")

            response = getattr(requests, method.lower())(url, headers=headers, data=data, verify=False)
        else:
            self.__LOGGER.debug(f"API CALL ({method}) - {url}")
            response = getattr(requests, method.lower())(url, headers=headers, verify=False)

        self.__LOGGER.debug(f"API Response : {response.__dict__}")

        # Handle response status codes
        if response.status_code in [200, 201]:
            self.__retry_count = 0
            return response.json()
        
        elif response.status_code == 204:
            self.__retry_count = 0
            return 
        
        elif response.status_code == 422:
            e = MiddlewareItemConflict(f"The item you are trying to add already exists - {response}")
            self.__LOGGER.warning(f"{type(e).__name__} - {e}")
            raise e

        elif response.status_code in [401,403,405,407,408]:
            if self.__retry_count == 0:
                self.__LOGGER.warning(f"API call failed due to one of the following codes '[401,403,405,407,408]' - retrying once")
                self.__retry(method, endpoint_name, variables_dict=variables_dict, endpoint_var=endpoint_var)
            else:
                self.__LOGGER.error(f"REST request failed : {response.__dict__}")
                self.__retry_count = 0
                response.raise_for_status()

        else:
            self.__LOGGER.error(f"REST request failed : {response.__dict__}")
            response.raise_for_status()
            

    # Return the given data template from ENDPOINTS with all var filled in from variables_dict
    # Uses recursion to traverse through the dict
    # If the endpoint name is an UPDATE_* call, remove empty key,val pairs before returning
    def __get_data(self, variables_dict, data_template, endpoint_name):
        try:
            data_dict = {}
            casting = {'value': float, 'ttl': int}
            for key, value in data_template.items():
                if isinstance(value, dict):
                    data_dict[key] = self.__get_data(variables_dict, value, endpoint_name)
                    if key == 'metadata' and not data_dict['metadata']:
                        del data_dict['metadata']
                else:
                    data_dict[key] = value.format(**variables_dict)
            
            return data_dict
        
        except Exception as e:
            self.__LOGGER.error(f"Failed to fill data template from ENDPOINTS {endpoint_name} - template:{data_template} - variables:{variables_dict}")
            self.__LOGGER.error(f"{type(e).__name__} - {e} - {sys.exc_info()[2].tb_frame.f_code.co_filename} - {sys.exc_info()[2].tb_lineno}")
            raise e
        
    # Return Ture if all necessary vars are present, otherwise raise an err
    def __check_required_vars(self, variables_dict, endpoint):
        missing_vars = [var for var in endpoint['required_vars'] if var not in variables_dict]
        if missing_vars:
            e = MiddlewareMissingRequiredArgs(missing_vars)
            self.__LOGGER.error(f"{type(e).__name__} - {e}")
            raise e
        return True

    def __retry(self, *args, **kwargs):
        self.__LOGGER.debug(f"Retrying API call after re-authenticating")
        self.__retry_count += 1
        self.__AUTH_TOKEN = self.__get_auth_token()
        self.__LOGGER.debug(f"Retry count : {self.__retry_count}")
        self._api_call(*args, **kwargs)

    def disconnect(self):
        self.__LOGGER.info("Disconnecting Middleware Services")
        self.__AUTH_TOKEN = None
        self._URL = None

