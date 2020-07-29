import pexpect
#import pcs
import logging

from atf.framework.FrameworkBase import *
from DeviceSession import *

class ConsoleServerSessionConfig(DeviceSessionConfig):
    r"""
    Encapsulate basic information allowing for the connection and 
    control of a session to a console server device.
    """
    def __init__(self, 
                 ip=None, 
                 port=None,
                 username=None, 
                 password=None, 
                 connectionType=DeviceSessionConfig.TELNET_SESSION,
                 consolePort=None):
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
                 
        @param consolePort:
            The console port number that will be operated on in the course 
            of setting up the console session.
        """
        DeviceSessionConfig.__init__(self, ip, port, username, password, 
                                     connectionType)
        self.consolePort = consolePort
        """Port on the console server associated with the session.""" 
        
class ConsoleServerSession(DeviceSession):
    r"""
    The ConsoleServer hierarchy abstracts the actions of connection 
    and control of a session to a console server device. 
    Common actions provided by this hierarchy are:
        - ttyAvailable: Indicate whether the tty to connect to is 
            available for connection
        - ttyConnect: Establish a connection to the configured tty
        - ttyDisconnect: Disconnect from the configured tty
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
        """State of the console server device session."""
        
    def ttyAvailable(self) :
        r"""
        Check and return the availability of a tty for connection

        @return:  
            boolean indicating availability 
        """      
        raise (NotImplementedError())
        
    def ttyConnect(self):
        r"""
        Connect to the configured tty

        @return:  
            None, exceptions raised must be derived from L{FrameworkError}
        """      
        raise (NotImplementedError()) 
    
    def ttyDisconnect(self):
        r"""
        Disconnect from the configured tty

        @return:  
            None, exceptions raised must be derived from L{FrameworkError}
        """      
        raise (NotImplementedError()) 
    
###
# Factory Functions
###    
def getConsoleServerSession(type=None, 
                            deviceSessionConfig=None, 
                            diagLevel=logging.WARNING):
    r"""
    This function returns a L{ConsoleServerSession} associated with the 
    supplied type. 
    
    @param type:
        The type of the L{ConsoleServerSession} class derivative that is to be 
        returned.
        
    @param deviceSessionConfig:
        A pre-constructed L{DeviceSessionConfig} object
    
    @param diagLevel:
        What debug level to run this object in.
            
    @return:  
        None, exceptions raised must be derived from L{FrameworkError}
    """ 
    import atf.framework.SystemConfig as SystemConfig
    if (type == SystemConfig.SystemConfig.CSD_TYPE_BELKIN):
        import BelkinCSS
        return BelkinCSS.BelkinCSS(deviceSessionConfig, diagLevel)
    elif (type == SystemConfig.SystemConfig.CSD_TYPE_PERLE):
        import PerleCSS
        return PerleCSS.PerleCSS(deviceSessionConfig, diagLevel)
    elif (type == SystemConfig.SystemConfig.CSD_TYPE_PORTMASTER):
        import PortMasterCSS
        return PortMasterCSS.PortMasterCSS(deviceSessionConfig, diagLevel)
    else:
        return None
