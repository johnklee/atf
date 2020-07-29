import pexpect
#import pcs
import logging
import sys

from atf.framework.FrameworkBase import *
from atf.framework.device.DeviceConfig import *

class DeviceSessionConfig(object):
    r"""
    Encapsulate basic information allowing for the connection and 
    control of a session to a device.
    """
    ###
    # Class definitions
    ###
    # Session connection types
    (TELNET_SESSION)     = 0
    """The telnet session type"""
    (SSH_SESSION)        = 1
    """The ssh session type"""
    
    def __init__(self, 
                 ip=None, 
                 port=None,
                 username=None, 
                 password=None, 
                 connectionType=TELNET_SESSION):
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
        """
        self.ip = ip
        """IP address associated with the device session."""
        self.port = port
        """Port associated with the device session."""
        self.username = username
        """User name associated with the device session login."""
        self.password = password
        """Password associated with the device session login."""
        self.connectionType = connectionType
        """Connection type associated with the device session."""
    
    
class DeviceSession(FrameworkBase):
    r"""
    The DeviceSession hierarchy abstracts the actions of connection 
    and control of a session to a running device. Common functionality
    provided by this interface mirrors the ProxyDevice hierarchy to 
    a fair degree and includes:
        - The "cons" which provides device console access using the pexpect 
          utility to script interactions.
        - The "nics" which provide a direct pipe into the ethernet interfaces
          of the Device so that packets can be directed at specific ingress and
          received from specific egress connectors. Further this allows for
          the VLAN configuration for these sessions if required.
    """
    ###
    # Class error definitions
    ###
    (ERR_MISSING_SESSION_CONFIG)      = FrameworkError.ERR_SESSION
    """A device session configuration has not been set"""
    (ERR_UNREACHABLE_DEVICE)          = FrameworkError.ERR_SESSION + 1 
    """Unable to reach the device"""
    (ERR_INVALID_SESSION_STATE)       = FrameworkError.ERR_SESSION + 2
    """The current device state is not appropriate for the attempted 
    operation"""
    (ERR_FAILED_SESSION_CONNECT)      = FrameworkError.ERR_SESSION + 3  
    """Failed to create a session to the device"""
    (ERR_FAILED_SESSION_DISCONNECT)   = FrameworkError.ERR_SESSION + 4 
    """Failed to destroy a session from the device"""
    (ERR_FAILED_SESSION_AUTHENTICATE) = FrameworkError.ERR_SESSION + 5
    """Failed to login to the device"""
    (ERR_FAILED_SESSION_OPERATION)    = FrameworkError.ERR_SESSION + 6  
    """Operation failed on device session"""

    ###
    # Class general definitions
    ###
    # Define valid states that a DeviceSessioncan be in.
    (STATE_UNKNOWN)      = 0
    """Undetermined device session state."""
    (STATE_INITIALISED)  = 1
    """Device session is initialised by not usable."""
    (STATE_CONNECTED)    = 2
    """Device session is connected."""
    (STATE_DISCONNECTED) = 3
    """Device session is disconnected."""
    
    # Commands for the creation of a session to a device
    (CMD_TELNET)         = 'telnet '
    """Command used for telnet session."""
    (CMD_SSH)            = 'ssh '
    """Command used for ssh session."""
    (CMD_REACHABLE)      = 'ping -c 3 %s'
    """Command used to determine target device reachability."""
    (CMD_SHELL)          = 'bash -c "PS1=\'# \' bash"'
    """Command used to create target device shell."""
    (CMD_CHANGESHELL)    = 'export PS1=\"# \"'
    """Command used to alter target device shell."""
    (CMD_CUSTOMIZED_CHANGESHELL)    = 'export PS1=\"%s\"'
    """Command used to alter target device shell with the customized string."""
    (CMD_RETCHECK)       = 'echo ":$?:"'
    """Command used to check command return value."""
    (CMD_CR)             = '\r\n'
    """Command used to send a line feed."""
   
    (OPTION_SSH)         = '-o CheckHostIP=no -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o GSSAPIAuthentication=no'
    """ ssh options """
    # Command timeout
    (TIMEOUT_CMD)        = 10
    """Timeout used when executing a device session command"""
    
    # Regex Patterns
    (REGEX_TELNET_FAILCONNECT)   = "Connection closed by foreign host.|Connection refused"
    """Pattern expected on the failure of a telnet connection."""
    (REGEX_TELNET_CONNECTSTRING) = "Escape character is \'\^]\'."
    """Pattern expected on the success of a telnet connection."""
    (REGEX_TELNET_QUITPROMPT)    = "telnet>"
    """Pattern expected on the quit from a telnet connection."""
    (REGEX_TELNET_CLOSED)        = "Connection closed"
    """Pattern expected on the close of a telnet connection."""
    (REGEX_LONG_MATCH)           = '.*%s'
    """ long match specific string """    
    
    def __init__(self, deviceSessionConfig=None, diagLevel=logging.WARNING):
        r"""
        Set up diagnostics output and save the network config into a 
        one way dictionary from target device IF name to local connection 
        point.

        @param deviceSessionConfig:
            A pre-constructed L{DeviceSessionConfig} object
            
        @param diagLevel:
            What debug level to run this object in.    
        """
        FrameworkBase.__init__(self, diagLevel=diagLevel)
        self.state = DeviceSession.STATE_UNKNOWN
        """State of the device session."""
        self.nics = {}
        """Network interfaces associated with the device session."""
        self.tty = None
        """Terminal associated with the device session."""
        self.config = deviceSessionConfig
        """Configuration associated with the device session."""

    def getTerminal(self):
        r"""
        Answer the object which provides access to the available terminal.
        
        In this case, it is a pexpect.spawn connection to the tty. 
        
        @return:
            A pexpect.spawn terminal.
        """
        return self.tty 

    def isReachable(self):
        r"""
        Use this method to ensure that the device whose session is to
        be created is reachable.

        @return:  
            - L{CommonError.ERR_OK} if ok to start
            - L{DeviceSession.ERR_UNREACHABLE_DEVICE} the device is unable to be 
              reached.
            - L{DeviceSession.ERR_MISSING_SESSION_CONFIG} device session config 
              file is missing or incomplete.
        """
        if (self.config == None or self.config.ip == None):
            return(DeviceSession.ERR_MISSING_SESSION_CONFIG)
        
        try:
            session = pexpect.spawn(DeviceSession.CMD_SHELL)
            if (self.logger.getEffectiveLevel() <= logging.DEBUG) :
                    session.logfile_read = sys.stdout
            session.sendline(DeviceSession.CMD_CHANGESHELL)
            session.expect_exact('#', timeout=DeviceSession.TIMEOUT_CMD)
            cmd = DeviceSession.CMD_REACHABLE % self.config.ip
            session.sendline(cmd)
            session.expect_exact(cmd[:70])
            session.expect_exact('#', timeout=DeviceSession.TIMEOUT_CMD)
            session.sendline(DeviceSession.CMD_RETCHECK)
            session.expect_exact(DeviceSession.CMD_RETCHECK[:70])
            session.expect_exact(':0:', 
                                 timeout=DeviceSession.TIMEOUT_CMD)
            session.expect_exact('#', timeout=DeviceSession.TIMEOUT_CMD)
            session.sendline('exit')
            return(CommonError.ERR_OK)
        except Exception, e:
            return(DeviceSession.ERR_UNREACHABLE_DEVICE)

    def isConnectable(self):
        r"""
        Use this method to ensure that the DeviceSession is in
        a suitably initialised state to attempt to connect().

        @return:  
            - L{CommonError.ERR_OK} if ok to start
            - L{DeviceSession.ERR_INVALID_SESSION_STATE} invalid state for 
              start
            - L{DeviceSession.ERR_MISSING_SESSION_CONFIG} no device session 
              config file.
        """
        if ((self.state != DeviceSession.STATE_INITIALISED) and 
            (self.state != DeviceSession.STATE_DISCONNECTED)): 
            return(DeviceSession.ERR_INVALID_SESSION_STATE)
        elif (self.config == None):
            return(DeviceSession.ERR_MISSING_SESSION_CONFIG)
        else:
            return(CommonError.ERR_OK)

    def isDisconnectable(self):
        r"""
        Use this method to ensure that the DeviceSession is in a 
        suitable running state to attempt to disconnect().

        @return:  
            - L{CommonError.ERR_OK} if ok to stop
            - L{DeviceSession.ERR_INVALID_SESSION_STATE} invalid state for
              disconnect
        """
        if (self.state == DeviceSession.STATE_CONNECTED):
            return(CommonError.ERR_OK)
        else:
            return(DeviceSession.ERR_INVALID_SESSION_STATE)

    def connect(self):
        r"""
        Connect to the device, creating a session. Derived classes must look 
        at the configuration passed in during construction, configure access 
        to each network identified and create the session to the device via
        a connection.
        
        @return:
            None, exceptions raised must be derived from L{FrameworkError}
        """
        # Determine connection command
        port = ''
        if (self.config.connectionType == DeviceSessionConfig.TELNET_SESSION):
            if (self.config.port != None):
                port = ' %s' % self.config.port
            self.cmd = '%s %s%s' % (DeviceSession.CMD_TELNET, self.config.ip, port)
        elif (self.config.connectionType == DeviceSessionConfig.SSH_SESSION):
            if (self.config.port != None):
                port = '-p %s' % self.config.port
            self.cmd = '%s%s %s' % (DeviceSession.CMD_SSH, port, self.config.ip)
        else:
            raise (FrameworkError(DeviceSession.ERR_FAILED_SESSION_CONNECT,
                                  'Invalid connection type encountered'))

        # Ensure the device is able to be connected to, validly and practically
        result = self.isConnectable()
        if (result != CommonError.ERR_OK):
            raise (FrameworkError(result,
                    'Unable to create session to device, current state : %s' % \
                    self.state))
        result = self.isReachable()
        if (result != CommonError.ERR_OK):
            raise (FrameworkError(result, 'Unable to reach the device'))

    def disconnect(self):
        r"""
        Derived classes must disconnect the session from the device.

        @return:
            None, exceptions raised must be derived from L{FrameworkError}
        """
        # Ensure the device is able to be disconnect from and there is a 
        # valid tty
        result = self.isDisconnectable()
        if (result != CommonError.ERR_OK):
            raise (FrameworkError(result,
                    'Unable to disconnect from device, current state : %s' % \
                    self.state))
        if (self.tty == None):
            raise (FrameworkError(DeviceSession.ERR_INVALID_SESSION_STATE, 
                                  'No connected session for this device'))

