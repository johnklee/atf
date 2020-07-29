from atf.framework.FrameworkBase import *


class Response(FrameworkBase):
    r"""
    Webservices response object. 
    It is a container for all webservice L{Response} attributes.
    """

    def __init__(self):
        r"""
        Response object constructor and attributes initialization. 
        Class attributes:
            - data:     Webservice response data
            - headers:  Webservice response headers
            - url:      Webservice response URL
            - status:   Webservice response status code
            - request:  Webservice initial L{Request}
            - msg:      Webservice message
        """
        self.data = None
        self.headers = None
        self.url = None
        self.status = None
        self.request = None
        self.msg = None

    def getHeader(self, name, default=None):
        r"""
        Return a header value

        @param name:
            Header name
        @param default:
            default value to return if name not present
        @return:
            Header value, or default if not present
        """
        if name in self.headers:
            return self.headers[name].strip()
        else:
            return default

    def __repr__(self):
        r"""
        Prints out the L{Response} object
        """
        return "%s(%r)" % (self.__class__, self.__dict__)
