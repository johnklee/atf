from base64 import b64encode
from atf.framework.FrameworkBase import *


class AuthBase(FrameworkBase):
    r"""
    Base class that all Auth mechanisms
    This is a common class for all Auth mechanisms. All auth classes should inherit from it
    and implement __call__ method that provide authentication procedure
    """
    def __call__(self, request):
        r"""        
        @param request:
            L{Request} object to authorize
        """
        raise NotImplementedError('Individual Auth classes must be implemented')
    
class HTTPDigestAuth(AuthBase):
    r"""
    HTTPDigestAuth implementation
    """
    def __init__(self):
        raise NotImplementedError('HTTPDigestAuth not implemented yet')


class HTTPBasicAuth(AuthBase):
    r"""
    BasicAuth implementation
    """
    def __init__(self, username, password):
        r"""
        BasicAuth constructor
        @param username:
            Username
        @param password:
            Password
        """
        self.username = username
        self.password = password

    def __call__(self, headers):
        r"""
        Process request and add Authorization header
        @param request:
            Request object to authorize
        @return:
            Authorized request object
        """
        headers['Authorization'] = self._basic_auth_str(self.username, self.password)
        return self

    def _basic_auth_str(self, username, password):
        r"""Returns a Basic Auth string
        @param username:
            Username to create base64 string
        @param password:
            Password to create base64 string
        """
        return 'Basic ' + b64encode(('%s:%s' % (username, password)).encode('latin1')).strip().decode('latin1')
