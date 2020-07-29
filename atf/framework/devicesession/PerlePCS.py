import pexpect
import pcs
import logging

from atf.framework.FrameworkBase import *
from atf.framework.SystemConfig import *
from DeviceSession import *
from PowerControllerSession import *

class PerlePCS(PowerControllerSession):
    r"""
    The PerlePCS class provides support for Perle power controllers.
    """
    ###
    # Class Definitions
    ###
    # Constants
    (EXPECT_TIMEOUT) = 300
    """Generic expect time out""" 
    
    # Regex Patterns
    (REGEX_PROMPT) = "RPS>"
    """Pattern expected for the prompt of a system."""
    (REGEX_CONFIRM) = "Sure\? \(Y/N\):"
    """Pattern expected for confirmation."""
    (REGEX_PASSWD) = "Enter Password:"
    """Pattern expected for password for login."""
    (REGEX_CLOSE) = "Disconnected."
    """Pattern expected for system disconnection."""
    
    # Commands for power controller operations
    (CMD_ON)         = '/On %s\r\n'
    """Command used for port power on."""
    (CMD_OFF)        = '/Off %s\r\n'
    """Command used for port power off."""
    (CMD_CYCLE)      = '/Boot %s\r\n'
    """Command used for port power cycle."""
    (CMD_EXIT)       = '/X\r\n'
    """Command used for exit from the system."""
    
    def __init__(self,  deviceSessionConfig=None, diagLevel=logging.WARNING):
        r"""
        Refer base class for a description of this interface method.

        @param deviceSessionConfig:
            A pre-constructed L{DeviceSessionConfig} object
            
        @param diagLevel:
            What debug level to run this object in.    
        """
        PowerControllerSession.__init__(self, 
             deviceSessionConfig=deviceSessionConfig, 
             diagLevel=diagLevel)
        self.powerState = PowerControllerSession.STATE_INITIALISED
        """The power state of the Perle session"""

    def connect(self):
        r"""
        Refer base class for a description of this interface method.
        
        @return:
            None, exceptions raised must be derived from L{FrameworkError}
        """
        PowerControllerSession.connect(self)
                        
        # Check that a password has been provided
        if (self.config.password == None):
            raise (FrameworkError(DeviceSession.ERR_FAILED_SESSION_CONNECT,
                                  'Perle PCS password has not been configured'))
                                  
        # Attempt to connect 
        try:
            self.tty = pexpect.spawn(self.cmd)
            if (self.logger.getEffectiveLevel() <= logging.DEBUG):
                self.tty.logfile_read = sys.stdout
            self.tty.expect(PerlePCS.REGEX_PASSWD, 
                            timeout=PerlePCS.EXPECT_TIMEOUT)
            self.tty.sendline(self.config.password + '\r\n')
            self.tty.expect(PerlePCS.REGEX_PROMPT)
            self.state = DeviceSession.STATE_CONNECTED
        except:
            self.tty = None
            self.state = DeviceSession.STATE_DISCONNECTED
            raise (FrameworkError(DeviceSession.ERR_FAILED_SESSION_CONNECT,
                                  'Error encountered while connecting'))
        
    def disconnect(self):
        r"""
        Refer base class for a description of this interface method.

        @return:
            None, exceptions raised must be derived from L{FrameworkError}
        """
        PowerControllerSession.disconnect(self)
        
        # Attempt to disconnect
        try:
            self.tty.sendline(DeviceSession.CMD_CR)
            self.tty.expect(PerlePCS.REGEX_PROMPT)
            self.tty.sendline(PerlePCS.CMD_EXIT)
            self.tty.expect(PerlePCS.REGEX_CONFIRM)
            self.tty.sendline('Y\r\n')
            self.tty.expect(PerlePCS.REGEX_CLOSE)
            self.state = DeviceSession.STATE_DISCONNECTED
            self.tty = None
        except:
            raise (FrameworkError(DeviceSession.ERR_FAILED_SESSION_DISCONNECT,
                                 'Unable to disconnect from the device'))
    
    def powerOn(self) :
        r"""
        Refer base class for a description of this interface method.

        @return:
            None, exceptions raised must be derived from L{FrameworkError}
        """      
        PowerControllerSession.powerOn(self)
        
        # Attempt to power on
        try:
            self.tty.sendline(DeviceSession.CMD_CR)
            self.tty.expect(PerlePCS.REGEX_PROMPT)
            self.tty.sendline(PerlePCS.CMD_ON % self.config.powerPort)
            self.tty.expect(PerlePCS.REGEX_CONFIRM)
            self.tty.sendline('Y\r\n')
            self.tty.expect(PerlePCS.REGEX_PROMPT)
            self.powerState = PowerControllerSession.STATE_POWERON
        except:
            raise (FrameworkError(DeviceSession.ERR_FAILED_SESSION_OPERATION,
                                 'Failed to power on specified port'))
        
    def powerOff(self):
        r"""
        Refer base class for a description of this interface method.

        @return:
            None, exceptions raised must be derived from L{FrameworkError}
        """      
        PowerControllerSession.powerOff(self)

        # Attempt to power on
        try:
            self.tty.sendline(DeviceSession.CMD_CR)
            self.tty.expect(PerlePCS.REGEX_PROMPT)
            self.tty.sendline(PerlePCS.CMD_OFF % self.config.powerPort)
            self.tty.expect(PerlePCS.REGEX_CONFIRM)
            self.tty.sendline('Y\r\n')
            self.tty.expect(PerlePCS.REGEX_PROMPT)
            self.powerState = PowerControllerSession.STATE_POWEROFF
        except:
            raise (FrameworkError(DeviceSession.ERR_FAILED_SESSION_OPERATION,
                                 'Failed to power on specified port'))
        
    def powerCycle(self):
        r"""
        Refer base class for a description of this interface method.

        @return:
            None, exceptions raised must be derived from L{FrameworkError}
        """      
        PowerControllerSession.powerCycle(self)

        # Attempt to power on
        try:
            self.tty.sendline(DeviceSession.CMD_CR)
            self.tty.expect(PerlePCS.REGEX_PROMPT)
            self.tty.sendline(PerlePCS.CMD_CYCLE % self.config.powerPort)
            self.tty.expect(PerlePCS.REGEX_CONFIRM)
            self.tty.sendline('Y\r\n')
            self.tty.expect(PerlePCS.REGEX_PROMPT)
            self.powerState = PowerControllerSession.STATE_POWERON
        except:
            raise (FrameworkError(DeviceSession.ERR_FAILED_SESSION_OPERATION,
                                 'Failed to power on specified port'))
        
