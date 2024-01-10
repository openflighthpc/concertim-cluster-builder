# Local Imports
from .utils.service_logger import create_logger
# endpoints file containing info on all Middleware endpoints
from .utils.endpoints import ENDPOINTS
from .utils.exceptions import MiddlewareItemConflict, MissingRequiredArgs, MissingRequiredField

# Py Packages
import sys
import json
# Disable insecure warnings  
import requests
requests.packages.urllib3.disable_warnings() 

class MiddlewareService(object):
    def __init__(self, config_obj, logger):
        self._CONFIG = config_obj
        #self._LOG_FILE = log_file
        #self.__LOGGER = create_logger(__name__, self._LOG_FILE, self._CONFIG['log_level'])
        logger.error(f"{self._CONFIG}")
        self.__LOGGER = logger
        self._URL = self._CONFIG['middleware']['middleware_url']
        self.__retry_count = 0
        self.__AUTH_TOKEN = self.__get_auth_token()
    
    def __get_auth_token(self):
        
        return "DUMMYTOKEN"
        """ login = self._CONFIG['concertim']['concertim_username']
        password = self._CONFIG['concertim']['concertim_password']
        variables_dict = {'login': login, 'password': password}
        token = self._api_call('post', 'LOGIN_AUTH', variables_dict)
        return token """
    
    # Return a dict of available endpoints and the call/data needed
    def list_available_endpoints(self):
        return ENDPOINTS

    def get_credits(self, variables_dict):
        response = self._api_call('post', 'GET_CREDITS', variables_dict=variables_dict)
        return response
    
   
    # Generic method for handling Concertim API calls.
    def _api_call(self, method, endpoint_name, variables_dict={}, endpoint_var=''):
        """
        Generic method for handling Concertim API calls.
        ACCEPTS:
            method - the REST call to make (get,post,patch,etc)
            endpoint_name - the endpoint name correspoinding to the ENDPOINTS dictionary
                            (CREATE_DEVICE, DELETE_DEVICE, UPDATE_DEVICE, etc)
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
        if endpoint_name != 'LOGIN_AUTH' and self.__AUTH_TOKEN is not None:
            headers["Authorization"] = self.__AUTH_TOKEN
        elif endpoint_name == 'LOGIN_AUTH':
            self.__LOGGER.debug("Getting Concertim Auth Token")
        elif self.__AUTH_TOKEN is None:
            e = MissingRequiredArgs("No Authentication Token provided")
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

        # Handle response status codes
        if response.status_code in [200, 201]:
            # Send the token if it is the login endpoint, else return the response.json
            if endpoint_name == 'LOGIN_AUTH':
                return response.headers.get("Authorization")
            self.__retry_count = 0
            return response.json()
        elif response.status_code == 422:
            ''' 
            +++ TEMP FIX
            '''
            for k,v in response.json().items():
                if "blank" in str(v):
                    e = MissingRequiredField(f"Required value missing - {response.json()}")
                    self.__LOGGER.warning(f"{type(e).__name__} - {e}")
                    raise e
            ''' 
            --- TEMP FIX
            '''
            e = MiddlewareItemConflict(f"The item you are trying to add already exists - {response.json()}")
            self.__LOGGER.warning(f"{type(e).__name__} - {e}")
            raise e
        #elif response.status_code == NUM:
        #    e = MissingRequiredField(f"Required value missing - {response.json()}")
        #    self.__LOGGER.warning(f"{type(e).__name__} - {e}")
        #    raise e
        elif response.status_code in [401,403,405,407,408]:
            if self.__retry_count == 0:
                self.__LOGGER.warning(f"API call failed due to one of the following codes '[401,403,405,407,408]' - retrying once")
                self.__retry(method, endpoint_name, variables_dict=variables_dict, endpoint_var=endpoint_var)
            else:
                self.__LOGGER.error('Unhandled REST request error.')
                self.__retry_count = 0
                response.raise_for_status()
        else:
            self.__LOGGER.error('Unhandled REST request error.')
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
                    if key in casting:
                        data_dict[key] = casting[key](value.format(**variables_dict))
                    elif value.replace('{','').replace('}','') not in variables_dict and endpoint_name in ['UPDATE_DEVICE','UPDATE_RACK','UPDATE_TEMPLATE', 'UPDATE_USER']:
                        continue
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
            e = MissingRequiredArgs(missing_vars)
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

