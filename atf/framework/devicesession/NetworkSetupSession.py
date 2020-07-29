import pexpect
#import pcs
import logging

from atf.framework.FrameworkBase import *
from DeviceSession import *

class NetworkSetupSessionConfig(DeviceSessionConfig):
    r"""
    Encapsulate basic information allowing for the connection and 
    control of a session to a network setup device.
    """
    def __init__(self, 
                 ip=None, 
                 port=None,
                 username=None, 
                 password=None, 
                 connectionType=DeviceSessionConfig.TELNET_SESSION,
                 deviceName=None,
                 netPortID=None):
        r"""
        Save the network specifications
         
        @param ip:
            The hostname or IP address of the device whose session is to be 
            created.
            
        @param port:
            The port number associated with the device session to be created.
        
        @param username:
            The username to be used for the device session creation.
        
        @param password:
            The password to be used for the device session creation.
        
        @param connectionType:
            The type of the session to be created. Can be one of:
                - L{DeviceSessionConfig.TELNET_SESSION}
                - L{DeviceSessionConfig.SSH_SESSION}
                 
        @param deviceName:
            The name associated with the device. This is typically used as 
            a part of the console prompt.
                 
        @param netPortID:
            The ID for the port that will be operated on in the course of 
            setting up the network session.
        """
        DeviceSessionConfig.__init__(self, ip, port, username, password, 
                                     connectionType)
        self.deviceName = deviceName
        """The name associated with the network setup device."""
        self.netPortID = netPortID
        """The ID for the port that is to be operated on for the network 
        device session."""

class NetworkSetupSession(DeviceSession):
    r"""
    The NetworkSetup hierarchy abstracts the actions of connection 
    and control of a session to a network setup device. 
    Common actions provided by this hierarchy are:
        - setVLAN: Set the vlan of the configured port
        - resetVLAN: Reset the vlan of the configured port to the
            default management VLAN (1)
    """
    
    def __init__(self,  deviceSessionConfig=None, diagLevel=logging.WARNING):
        r"""
        Set up diagnostics output and save the network config into a 
        one way dictionary from target device IF name to local connection 
        point.

        @param deviceSessionConfig:
            A pre-constructed L{DeviceSessionConfig} object
                 
        @param diagLevel:
            What debug level to run this object in.    
        """
        DeviceSession.__init__(self, 
                               deviceSessionConfig=deviceSessionConfig, 
                               diagLevel=diagLevel)
        self.state = DeviceSession.STATE_INITIALISED
        """The state of the network setup device session."""
       
    def setVlan(self, vlanID='2'):
        r"""
        Set the VLAN ID for the configured port associated with this session

        @param vlanID:
            The VLAN ID to associated with the configured port.
            
        @return:
            None, exceptions raised must be derived from L{FrameworkError}
        """      
        # Verify the state of the device session before attempting VLAN changes
        if (self.tty == None or self.state != DeviceSession.STATE_CONNECTED):
            raise (FrameworkError(DeviceSession.ERR_INVALID_SESSION_STATE, 
                                  'Invalid session for VLAN operations'))
        
        # Check that a password has been provided
        if (self.config.netPortID == None):
            raise (FrameworkError(DeviceSession.ERR_FAILED_SESSION_OPERATION,
                                  'NSS port has not been configured'))
                                          
    def resetVlan(self):
        r"""
        Set the VLAN ID for the configured port associates with this session
        to the default VLAN management ID (typically 1)

        @return:
            None, exceptions raised must be derived from L{FrameworkError}
        """      
        raise (NotImplementedError()) 
    
###
# Factory Functions
###    
def getNetworkSetupSession(type=None, 
                           deviceSessionConfig=None, 
                           diagLevel=logging.WARNING):
    r"""
    This function returns a L{NetworkSetupSession} associated with the 
    supplied type. 
    
    @param type:
        The type of the L{NetworkSetupSession} class derivative that is to be 
        returned.
        
    @param deviceSessionConfig:
        A pre-constructed L{DeviceSessionConfig} object
        
    @param diagLevel:
        What debug level to run this object in.    
        
    @return:
        None, exceptions raised must be derived from L{FrameworkError}
    """ 
    import atf.framework.SystemConfig as SystemConfig
    if (type == SystemConfig.SystemConfig.NSD_TYPE_CISCOIOS):
        import CiscoIOSNSS
        return CiscoIOSNSS.CiscoIOSNSS(deviceSessionConfig, diagLevel)
    elif (type == SystemConfig.SystemConfig.NSD_TYPE_CISCOCATOS):
        import CiscoCatOSNSS
        return CiscoCatOSNSS.CiscoCatOSNSS(deviceSessionConfig, diagLevel)
    else:
        return None
