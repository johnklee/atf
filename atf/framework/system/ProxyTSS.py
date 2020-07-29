import logging

from ProxySystem import *
from atf.framework.SystemConfig import *


class TSSConfig (SystemConfig):
    r"""
    This class is used to encapsulate all information required to configure,
    start and control a TSS instance.
    """

    def __init__(self, systemConfig=None, deviceConfig=None):
        SystemConfig.__init__(self, systemConfig=systemConfig, 
                              deviceConfig=deviceConfig)


class ProxyTSS (ProxySystem):
    r"""
    The ProxyTSS class extends the ProxySystem interface to include methods
    that must be implemented by all proxies supporting Test System Support 
    services. Examples of these would include web server hosts that make 
    up part of a test suites environment.
    """

    ###
    # Class error definitions
    ### 
    # Unknown device type configured to run system on.
    (ERR_UNSUPPORTED_PACKAGE_TYPE)  = FrameworkError.ERR_TSS 

    def __init__(self, tssConfig = None, diagLevel=logging.ERROR):
        r"""
        Save config and diagnostics output details

        @param tssConfig:
            A pre-constructed SystemConfig object
            
        @param diagLevel:
            What debug level to run this object in.
                
        @return:  
            None.                
        """
        ProxySystem.__init__(self, tssConfig, diagLevel)
        
        self.services = {}
        """TSS services dictionary"""
        
    def setDNS(self, dnsIp):
        r"""
        Set the DNS server of the TSS being proxied.
        
        @param dnsIp:
            The IP address of the DNS server to be set.
        """
        raise (NotImplementedError())
    
    def setDefaultGateway(self, gwIp):
        r"""
        Set the default gateway of the TSS being proxied.
        
        @param gwIp:
            The IP address of the default gateway to be set.
        """
        raise (NotImplementedError())
    
    def enableForwarding(self, inInterface, outInterface):
        r"""
        Enable forwarding of the TSS being proxied.
        
        @param inInterface:
            The ingress interface from which traffic is to be forwarded. 
        
        @param outInterface:
            The egress interface over which traffic is to be forwarded.
        """
        raise (NotImplementedError())
    
    def setStaticIp(self, interface, ip):
        r"""
        Set a static IP address for a nominated interface on the Linux TSS being proxied.
        
        @param interface:
            The interface that the static IP is to be associated with.
            
        @param ip:
            The IP address that is to be statically assigned to the nominated interface.
        """
        raise (NotImplementedError())
