import pycurl
import json
from atf.framework.FrameworkBase import *
from atf.common.webservice.Response import Response


class WebService(FrameworkBase):
    r"""
    Base Web Service class
    A set of common return codes and methods for HTTP/1.1 definition http://www.w3.org/Protocols/rfc2616/rfc2616-sec9.html#sec9
    """

    (RESPONSE_CODE_OK) = 200
    r"""Standard response for successful HTTP requests"""
    (RESPONSE_CODE_CREATED) = 201
    r"""The request has been fulfilled and resulted in a new resource being created"""
    (RESPONSE_CODE_ACCEPTED) = 202
    r"""The request has been accepted for processing, but the processing has not been completed"""
    (RESPONSE_CODE_NO_CONTENT) = 204
    r"""The server successfully processed the request, but is not returning any content"""
    (RESPONSE_CODE_RESET_CONTENT) = 205
    r"""The server successfully processed the request, but is not returning any content"""
    (RESPONSE_CODE_PARTIAL_CONTENT) = 206
    r"""The server is delivering only part of the resource due to a range header sent by the client"""

    (RESPONSE_CODE_FOUND) = 302
    r"""This is an example of industry practice contradicting the standard"""
    (RESPONSE_CODE_NOT_MODIFIED) = 304
    r"""Indicates the resource has not been modified since last requested"""

    (RESPONSE_CODE_BAD_REQUEST) = 400
    r"""The request cannot be fulfilled due to bad syntax"""
    (RESPONSE_CODE_UNAUTHORIZED) = 401
    r"""Similar to 403 Forbidden, but specifically for use when authentication is required and has failed or has not yet been provided"""
    (RESPONSE_CODE_FORBIDEN) = 403
    r"""The request was a valid request, but the server is refusing to respond to it"""
    (RESPONSE_CODE_NOT_FOUND) = 404
    r"""The requested resource could not be found but may be available again in the future"""
    (RESPONSE_CODE_METHOD_NOT_ALLOWED) = 405
    r"""The method specified in the Request-Line is not allowed for the resource identified by the Request-URI"""
    (RESPONSE_CODE_NOT_ACCEPTABLE) = 406
    r"""The requested resource is only capable of generating content not acceptable according to the Accept headers sent in the request"""
    (RESPONSE_CODE_PROXY_AUTHENTICATION_REQUIRED) = 407
    r"""This code is similar to 401 (Unauthorized), but indicates that the client must first authenticate itself with the proxy"""
    (RESPONSE_CODE_REQUEST_TIMEOUT) = 408
    r"""The client did not produce a request within the time that the server was prepared to wait. The client MAY repeat the request without modifications at any later time"""
    (RESPONSE_CODE_CONFLICT) = 409
    r"""The request could not be completed due to a conflict with the current state of the resource"""
    (RESPONSE_CODE_GONE) = 410
    r"""The requested resource is no longer available at the server and no forwarding address is known"""
    (RESPONSE_CODE_LENGTH_REQUIRED) = 411
    r"""The server refuses to accept the request without a defined Content- Length"""
    (RESPONSE_CODE_PRECONDITION_FAILED) = 412
    r"""The precondition given in one or more of the request-header fields evaluated to false when it was tested on the server"""
    (RESPONSE_CODE_ENTITY_TOO_LARGE) = 413
    r"""The server is refusing to process a request because the request entity is larger than the server is willing or able to process"""
    (RESPONSE_CODE_URI_TOO_LONG) = 414
    r"""The server is refusing to service the request because the Request-URI is longer than the server is willing to interpret"""
    (RESPONSE_CODE_RANGE_NOT_SATISFIABLE) = 416
    r"""A server should return a response with this status code if a request included a Range request-header field, and none of the range-specifier values in this field overlap the current extent of the selected resource"""
    (RESPONSE_CODE_EXPECTATION_FAILED) = 417
    r"""The expectation given in an Expect request-header field could not be met by this server"""
    (RESPONSE_CODE_UNPROCESSABLE_ENTITY) = 422
    r"""The request was well-formed but was unable to be followed due to semantic errors"""

    (RESPONSE_CODE_INTERNAL_SERVER_ERROR) = 500
    r"""A generic error message, given when no more specific message is suitable"""
    (RESPONSE_CODE_NOT_IMPLEMENTED) = 501
    r"""The server either does not recognize the request method, or it lacks the ability to fulfill the request"""
    (RESPONSE_CODE_BAD_GATEWAY) = 502
    r"""The server was acting as a gateway or proxy and received an invalid response from the upstream server"""
    (RESPONSE_CODE_SERVICE_UNAVAILABLE) = 503
    r"""The server is currently unavailable (because it is overloaded or down for maintenance)"""
    (RESPONSE_CODE_GATEWAY_TIMEOUT) = 504
    r"""The server was acting as a gateway or proxy and did not receive a timely response from the upstream server"""

    @staticmethod
    def get(session, url, **kwargs):
        r"""
        Do generic webservice HTTP[S] GET request
        @param session:
            Current open and authorized L{Session}
        @param url:
            Request URL
        @param kwargs:
            Optional arguments for request
        @return:
            Webservice L{Response} object
        """
        return session.request('get', url=url, **kwargs)

    @staticmethod
    def put(session, url, data=None, **kwargs):
        r"""
        Do generic webservice HTTP[S] PUT request
        @param session:
            Current open and authorized L{Session}
        @param url:
            Request URL
        @param data:
            Request data
        @param kwargs:
            Optional arguments for request
        @return:
            Webservice L{Response} object
        """
        return session.request('put', url=url, data=data, **kwargs)

    @staticmethod
    def post(session, url, data=None, **kwargs):
        r"""
        Do generic webservice HTTP[S] POST request
        @param session:
            Current open and authorized L{Session}
        @param url:
            Request URL
        @param data:
            Request data
        @param kwargs:
            Optional arguments for request
        @return:
            Webservice L{Response} object
        """
        return session.request('post', url=url, data=data, **kwargs)

    @staticmethod
    def delete(session, url, **kwargs):
        r"""
        Do generic webservice HTTP[S] DELETE request
        @param session:
            Current open and authorized L{Session}
        @param url:
            Request URL
        @param kwargs:
            Optional arguments for request
        @return:
            Webservice L{Response} object
        """
        return session.request('delete', url=url, **kwargs)

    @staticmethod
    def options(session, url, **kwargs):
        r"""
        Do generic webservice HTTP[S] OPTIONS request
        @param session:
            Current open and authorized L{Session}
        @param url:
            Request URL
        @param kwargs:
            Optional arguments for request
        @return:
            Webservice L{Response} object
        """
        return session.request('options', url=url, **kwargs)

    @staticmethod
    def patch(session, url, data=None, **kwargs):
        r"""
        Do generic webservice HTTP[S] PATCH request
        @param session:
            Current open and authorized L{Session}
        @param url:
            Request URL
        @param data:
            Request data
        @param kwargs:
            Optional arguments for request
        @return:
            Webservice L{Response} object
        """
        return session.request('patch', url=url, data=data, **kwargs)

    @staticmethod
    def head(session, url, **kwargs):
        r"""
        Do generic webservice HTTP[S] HEAD request
        @param session:
            Current open and authorized L{Session}
        @param url:
            Request URL
        @param kwargs:
            Optional arguments for request
        @return:
            Webservice L{Response} object
        """
        return session.request('head', url=url, **kwargs)

    @staticmethod
    def trace(session, url, **kwargs):
        r"""
        Do generic webservice HTTP[S] TRACE request
        @param session:
            Current open and authorized L{Session}
        @param url:
            Request URL
        @param kwargs:
            Optional arguments for request
        @return:
            Webservice L{Response} object
        """
        return session.request('trace', url=url, **kwargs)

    @staticmethod
    def connect(session, url, **kwargs):
        r"""
        Do generic webservice HTTP[S] CONNECT request
        @param session:
            Current open and authorized L{Session}
        @param url:
            Request URL
        @param kwargs:
            Optional arguments for request
        @return:
            Webservice L{Response} object
        """
        return session.request('connect', url=url, **kwargs)


class PyCurlWebService(WebService):
    r"""
    WebService class wrapping pycurl
    """
    JSON_HEADERS = ['Accept: application/json', 'Content-Type: application/json']

    def __init__(self,
                 hostname,
                 port,
                 path,
                 username,
                 password,
                 protocol='http',
                 auth=pycurl.HTTPAUTH_BASIC,
                 diagLevel=logging.WARNING):

        r"""
        @param hostname:
            Target system hostname or IP address
        @param port:
            Target system port number
        @param path:
            URL path
        @param username:
            Username for webservice authentication
        @param password:
            Password for webservice authentication
        @param protocol:
            Protocol to use [HTTPS|HTTP]
        @param auth:
            Authentication mechanism
        @param diagLevel:
            What debug level to run this object in
        """

        FrameworkBase.__init__(self, diagLevel=diagLevel)
        self.hostname = hostname
        self.port = port
        self.path = path
        self.username = username
        self.password = password
        self.protocol = protocol
        self.auth = auth
        self.baseUrl = protocol.lower() + '://' + hostname + ':' + str(port) + path + '/'

    def doRequest(self, method, url, headers, timeout, data=None, encode=True, upload=False, binary=False):
        r"""
        Execute HTTP[S] request

        @param method:
            Request method [get|post|put|delete]
        @param url:
            Request url
        @param headers:
            Request headers:
        @param timeout:
            Request timeout for blocking operation
        @param data:
            Request data
        @param encode:
            Encode request data based on 'Accept' header (bool)
        @param upload:
            If true data is treated as file name to upload
        @param binary:
            If True, upload data is treated as binary
        @return:
            WebService response
        """
        curl = pycurl.Curl()
        responseBody = StringIO.StringIO()
        responseHeaders = StringIO.StringIO()
        curl.setopt(curl.URL, str(self.baseUrl + url))
        curl.setopt(pycurl.HTTPHEADER, headers)
        curl.setopt(pycurl.WRITEFUNCTION, responseBody.write)
        curl.setopt(pycurl.HEADERFUNCTION, responseHeaders.write)
        curl.setopt(pycurl.USERPWD, self.username + ":" + self.password)
        curl.setopt(pycurl.CONNECTTIMEOUT, timeout)
        curl.setopt(pycurl.HTTPAUTH, self.auth)
        #disable SSL cert verification
        curl.setopt(pycurl.SSL_VERIFYPEER, 0)
        curl.setopt(pycurl.SSL_VERIFYHOST, 0)
        curl.setopt(pycurl.VERBOSE, 1)

        if method.upper() == 'POST' or method.upper() == 'PUT':
            if method.upper() == 'POST':
                curl.setopt(pycurl.POST, 1)
            else:
                curl.setopt(pycurl.CUSTOMREQUEST, "PUT")
            if upload == True:
                curl.setopt(pycurl.UPLOAD, 1)
                if binary == True:
                    filesize = os.path.getsize(data)
                    curl.setopt(pycurl.INFILESIZE, filesize)
                    fin = open(data, 'rb')
                    curl.setopt(pycurl.READDATA, fin)
                else:
                    curl.setopt(curl.HTTPPOST, [('file', (curl.FORM_FILE, data))])
            else:
                if data != None and encode == True:
                    curl.setopt(pycurl.POSTFIELDS, json.dumps(data))
                else:
                    curl.setopt(pycurl.POSTFIELDS, '')

        if method.upper() == 'DELETE':
            curl.setopt(pycurl.CUSTOMREQUEST, "DELETE")

        curl.perform()
        status = curl.getinfo(pycurl.HTTP_CODE)
        try:
            body = json.loads(responseBody.getvalue())
        except ValueError:
            body = responseBody.getvalue()
        #format headers as list of strings
        headers = responseHeaders.getvalue().split('\r\n')
        headers = [hdr for hdr in headers if hdr != '']

        curl.close()
        responseBody.close()
        responseHeaders.close()
        response = Response()
        response.status = status
        response.data = body
        response.headers = headers
        if upload == True and binary==True:
            fin.close()
        return response

    def get(self, url, headers=JSON_HEADERS, timeout=120,):
        """
        @param url:
            Webservice url
        @param headers:
            Webservice headers
        @param timeout:
            Request timeout for blocking operation
        @return:
           WebService response
        """
        return self.doRequest('get', url, headers, timeout)

    def post(self, url, headers=JSON_HEADERS, timeout=120, data=None, encode=True, upload=False, binary=False):
        """
        @param url:
            Webservice url
        @param headers:
            Webservice headers
        @param timeout:
            Request timeout for blocking operation
        @param data:
            Webservice data payload
        @param encode:
            Encode request data based on 'Accept' header (bool)
        @param upload:
            If true data is treated as file name to upload
        @param binary:
            If True, upload data is treated as binary
        @return:
           WebService response
        """
        return self.doRequest('post', url, headers, timeout, data=data, encode=encode, upload=upload, binary=binary)

    def put(self, url, data, headers=JSON_HEADERS, timeout=120, encode=True, upload=False, binary=False):
        """
        @param url:
            Webservice url
        @param data:
            Webservice data payload
        @param headers:
            Webservice headers
        @param timeout:
            Request timeout for blocking operation
        @param encode:
            Encode request data based on 'Accept' header (bool)
        @param upload:
            If true data is treated as file name to upload
        @param binary:
            If True, upload data is treated as binary
        @return:
           WebService response

        """
        return self.doRequest('put', url, headers, timeout, data=data, encode=encode, upload=upload, binary=binary)

    def delete(self, url, headers=JSON_HEADERS, timeout=120):
        """
        @param url:
            Webservice url
        @param headers:
            Webservice headers
        @param timeout:
            Request timeout for blocking operation
            Encode request data based on 'Accept' header (bool)
        @return:
           WebService response
        """
        return self.doRequest('delete', url, headers, timeout)

    def uploadFile(self, url, path, headers=JSON_HEADERS, timeout=120):
        """
        @param url:
            Webservice url
        @param path:
            Filepath to upload
        @param headers:
            Webservice headers
        @param timeout:
            Request timeout for blocking operation
            Encode request data based on 'Accept' header (bool)
        @return:
           WebService response
        """
        curl = pycurl.Curl()
        responseBody = StringIO.StringIO()
        curl.setopt(curl.URL, str(self.baseUrl + url))
        curl.setopt(pycurl.HTTPHEADER, headers)
        curl.setopt(pycurl.WRITEFUNCTION, responseBody.write)
        curl.setopt(pycurl.USERPWD, self.username + ":" + self.password)
        curl.setopt(pycurl.CONNECTTIMEOUT, timeout)
        curl.setopt(pycurl.HTTPAUTH, self.auth)
        #disable SSL cert verification
        curl.setopt(pycurl.SSL_VERIFYPEER, 0)
        curl.setopt(pycurl.SSL_VERIFYHOST, 0)

        #curl.setopt(pycurl.VERBOSE, 1)

        #curl.setopt(pycurl.PUT, 1)
        curl.setopt(pycurl.CUSTOMREQUEST, "PUT")
        curl.setopt(pycurl.UPLOAD, 1)

        #curl.setopt(curl.HTTPPOST, [('file', (curl.FORM_FILE, path))])

        filesize = os.path.getsize(path)
        curl.setopt(pycurl.INFILESIZE, filesize)
        fin = open(path, 'rb')
        curl.setopt(pycurl.READDATA, fin)
        curl.perform()

        status = curl.getinfo(pycurl.HTTP_CODE)
        try:
            body = json.loads(responseBody.getvalue())
        except ValueError:
            body = responseBody.getvalue()

        curl.close()
        fin.close()
        responseBody.close()
        response = Response()
        response.status = status
        response.data = body
        return response
