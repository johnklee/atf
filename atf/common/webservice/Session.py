from atf.framework.FrameworkBase import *
from atf.common.webservice.Request import Request
from atf.common.webservice.Auth import AuthBase


class Session(FrameworkBase):
    r"""
    Webservices session object
    """
    def __init__(self, username, password, auth=None, diagLevel=logging.WARNING):
        r"""
        Session constructor

        @param username:
            Username to create session
        @param password:
            Password to create session
        @param auth:
            Authentication class
        @param diagLevel:
            Logger lever
        """
        FrameworkBase.__init__(self, diagLevel=diagLevel)

        # Authenticate with specified authentication mechanism
        self.__auth = None
        if auth:
            if issubclass(auth, AuthBase):
                self.__auth = auth(username, password)
            else:
                raise FrameworkError("auth should be a subclass of AuthBase")

    def request(self, method, url, headers=None, data=None, params=None, retries=False, timeout=None):
        r"""
        Execute HTTP[S] request

        @param method:
            Request method [get|post|put|delete|options|head|trace|connect]
        @param url:
            Request url
        @param headers:
            Request headers:
        @param data:
            Request data
        @param params:
            Request parameters to add to URL
        @param retries:
            Configure the number of retries to allow before raising a :class:`~urllib3.exceptions.MaxRetryError` exception.
            Pass None to retry until you receive a response. 
            Pass a L{urllib3.util.retry.Retry} object for fine-grained control over different types of retries.
            Pass an integer number to retry connection errors that many times, but no other types of errors. 
            Pass zero to never retry.
            Pass `False`, then retries are disabled and any exception is raised immediately. Also, instead of raising a MaxRetryError on redirects,
            the redirect response will be returned.
        @param timeout:
            Request timeout for blocking operation
        @rtype:
            L{Response} object
        @return:
            Request response object
        """
        # all methods are upper case
        method = method.upper()

        # create request object
        request = Request(method=method,
                          url=url,
                          headers=headers,
                          data=data,
                          auth=self.__auth,
                          params=params,
                          retries=retries,
                          timeout=timeout,
                          diagLevel=self.logger.getEffectiveLevel())
        # send request
        return request.send()
