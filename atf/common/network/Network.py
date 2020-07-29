from atf.framework.FrameworkBase import *
import socket


class NetworkUtil(FrameworkBase):
    r"""
    A class to provide network utility function
    """
    (TYPE_IPV4) = "IPV4"
    (TYPE_IPV6) = "IPV6"

    @staticmethod
    def checkAddressType(ip):
        r"""
        Check if given IP address is whether IPv4 or IPv6
        @param ip:
            The IP address.
        @return:
            Return type of IP.
        """

        try:
            socket.inet_pton(socket.AF_INET, ip)
            return NetworkUtil.TYPE_IPV4
        except:
            pass

        try:
            socket.inet_pton(socket.AF_INET6, ip)
            return NetworkUtil.TYPE_IPV6
        except socket.error, failure:
            raise (FrameworkError(ip, '%s : %s' % (failure, ip)))
