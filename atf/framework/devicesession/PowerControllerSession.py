import pexpect
#import pcs
import logging

from atf.framework.FrameworkBase import *
from DeviceSession import *

class PowerControllerSessionConfig(DeviceSessionConfig):
    r"""
    Encapsulate basic information allowing for the connection and 
    control of a session to a power controller
    """
    def __init__(self, 
                 ip=None, 
                 port=None,
                 username=None, 
                 password=None, 
                 connectionType=DeviceSessionConfig.TELNET_SESSION,
                 powerPort=None):
        r"""
        Save the network specifications.
         
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
                
        @param powerPort:
            The port number that will be operated on in the course of 
            power management
        """
        DeviceSessionConfig.__init__(self, ip, port, username, password, 
                                     connectionType)
        self.powerPort = powerPort
        """The power port associated with the session"""
        
class PowerControllerSession(DeviceSession):
    r"""
    The PowerController hierarchy abstracts the actions of connection 
    and control of a session to a power controller device. 
    Common actions provided by this hierarchy are:
        - powerOn: Power on a device connected to the configured port of the
            power controller session
        - powerOff: Power off a device connected to the configured port of the
            power controller session
        - powerCycle: Power cycle a device connected to the configured port of the
            power controller session
    """
    ###
    # Class error definitions
    ###
    (ERR_INVALID_POWER_STATE) = FrameworkError.ERR_POWER    
    """An invalid power state for the current operation"""
    (ERR_NO_SESSION)          = FrameworkError.ERR_POWER + 1    
    """No session is available for the current operation"""
    
    ###
    # Class general definitions
    ###
    # Define valid states that a PCS can be in.
    (STATE_UNKNOWN)     = 0
    """Undetermined power port state."""
    (STATE_INITIALISED) = 1
    """Power port state initialised."""
    (STATE_POWERON)     = 2
    """Power port state on."""
    (STATE_POWEROFF)    = 3
    """Power port state off."""
    
    
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
        self.powerState = PowerControllerSession.STATE_UNKNOWN
        
    def powerOn(self) :
        r"""
        Execute a power on of the configured port via the device session 

        @return:
            None, exceptions raised must be derived from L{FrameworkError}
        """
        if (self.state != DeviceSession.STATE_CONNECTED):
            raise (FrameworkError(PowerControllerSession.ERR_NO_SESSION,
                      'No power controller session connected to perform power on'))
        if (self.powerState != PowerControllerSession.STATE_POWEROFF and
            self.powerState != PowerControllerSession.STATE_INITIALISED):
            raise (FrameworkError(PowerControllerSession.ERR_INVALID_POWER_STATE,
                      'Invalid power state for power on: %s' % self.powerState))
                   
        # Check that a password has been provided
        if (self.config.powerPort == None):
            raise (FrameworkError(DeviceSession.ERR_FAILED_SESSION_OPERATION,
                                 'PCS power port has not been configured for power on')) 
                                 
    def powerOff(self):
        r"""
        Execute a power off of the configured port via the device session 

        @return:
            None, exceptions raised must be derived from L{FrameworkError}
        """      
        if (self.state != DeviceSession.STATE_CONNECTED):
            raise (FrameworkError(PowerControllerSession.ERR_NO_SESSION,
                      'No power controller session connected to perform power off'))
        if (self.powerState != PowerControllerSession.STATE_POWERON):
            raise (FrameworkError(PowerControllerSession.ERR_INVALID_POWER_STATE,
                      'Invalid power state for power off: %s' % self.powerState))
   
        # Check that a password has been provided
        if (self.config.powerPort == None):
            raise (FrameworkError(DeviceSession.ERR_FAILED_SESSION_OPERATION,
                                 'PCS power port has not been configured for power off'))
    
    def powerCycle(self):
        r"""
        Execute a power cycle of the configured port via the device session 

        @return:
            None, exceptions raised must be derived from L{FrameworkError}
        """      
        if (self.state != DeviceSession.STATE_CONNECTED):
            raise (FrameworkError(PowerControllerSession.ERR_NO_SESSION,
                      'No power controller session connected to perform power cycle'))

        # Check that a password has been provided
        if (self.config.powerPort == None):
            raise (FrameworkError(DeviceSession.ERR_FAILED_SESSION_OPERATION,
                                 'PCS power port has not been configured for power cycle'))
        
    
###
# Factory Functions
###    
def getPowerControllerSession(type=None, 
                              deviceSessionConfig=None, 
                              diagLevel=logging.WARNING):
    r"""
    This function returns a L{PowerControllerSession} associated with the 
    supplied type. 
    
    @param type:
        The type of the L{PowerControllerSession} class derivative that is 
        to be returned.
        
    @param deviceSessionConfig:
        A pre-constructed L{DeviceSessionConfig} object
        
    @param diagLevel:
        What debug level to run this object in.    
        
    @return:
        None, exceptions raised must be derived from L{FrameworkError}
    """ 
    import atf.framework.SystemConfig as SystemConfig
    if (type == SystemConfig.SystemConfig.PCD_TYPE_PERLE):
        import PerlePCS
        return PerlePCS.PerlePCS(deviceSessionConfig, diagLevel)
    elif (type == SystemConfig.SystemConfig.PCD_TYPE_APC):
        import APCPCS
        return APCPCS.APCPCS(deviceSessionConfig, diagLevel)
    elif (type == SystemConfig.SystemConfig.PCD_TYPE_APC_7932):
        import APCPCS7932
        return APCPCS7932.APCPCS(deviceSessionConfig, diagLevel)
    else:
        return None
    
