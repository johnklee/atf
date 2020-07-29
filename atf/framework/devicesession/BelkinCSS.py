import pexpect
import pcs
import logging

from atf.framework.FrameworkBase import *
from atf.framework.SystemConfig import *
from DeviceSession import *
from ConsoleServerSession import *

class BelkinCSS(ConsoleServerSession):
    r"""
    The BelkinCSS class provides support for Belkin console servers.
    """
    ###
    # Class Definitions
    ###
    # Constants
    (EXPECT_TIMEOUT) = 300 
    """Generic expect time out""" 
    (CONNECT_TIMEOUT) = 30
    """Expect timeout used on telnet connection"""
    
    # Regex Patterns
    (REGEX_TELNET_BUSY) = "Port already in use"
    """Pattern expected on telnet busy state."""
    (REGEX_TELNET_LOGIN) = "login:"
    """Pattern expected for the user name during a login."""
    (REGEX_TELNET_PASSWD) = "[Pp]assword:"
    """Pattern expected for the password during a login."""
    
    def __init__(self,  deviceSessionConfig=None, diagLevel=logging.WARNING):
        r"""
        Refer base class for a description of this interface method.

        @param deviceSessionConfig:
            A pre-constructed L{DeviceSessionConfig} object
            
        @param diagLevel:
            What debug level to run this object in.    
        """
        ConsoleServerSession.__init__(self, 
             deviceSessionConfig=deviceSessionConfig, 
             diagLevel=diagLevel)
             
        # Belkin console connections do not support SSH
        if (self.config != None and 
            self.config.connectionType == DeviceSessionConfig.SSH_SESSION):
            raise (FrameworkError(DeviceSession.ERR_FAILED_SESSION_CONNECT,
                'An SSH connection type is not supported for the Belkin')) 
        
        # Belkin console connections are mapped ports, adjust config port
        try:
            if (self.config != None):
                self.config.port = '%d' % \
                    (int(self.config.port) + int(self.config.consolePort))
        except:
            raise (FrameworkError(DeviceSession.ERR_FAILED_SESSION_CONNECT,
                'Belkin port and consolePort not well defined')) 

    def connect(self):
        r"""
        Refer base class for a description of this interface method.
        
        @return:
            None, exceptions raised must be derived from L{FrameworkError}
        """
        ConsoleServerSession.connect(self)

        # Check that a username has been provided
        if (self.config.username == None):
            raise (FrameworkError(DeviceSession.ERR_FAILED_SESSION_CONNECT,
                                  'Belkin CSS username has not been configured'))
                                  
        # Check that a password has been provided
        if (self.config.password == None):
            raise (FrameworkError(DeviceSession.ERR_FAILED_SESSION_CONNECT,
                                  'Belkin CSS password has not been configured'))
        
        # A busy terminal is indicated by a telnet disconnect from the host,
        # this test looks for this to happen in a short timeout
        try:
            self.tty = pexpect.spawn(self.cmd)
            if (self.logger.getEffectiveLevel() <= logging.DEBUG):
                self.tty.logfile_read = sys.stdout
            self.tty.expect(BelkinCSS.REGEX_TELNET_BUSY,
                            timeout=BelkinCSS.CONNECT_TIMEOUT)
                            
            # If the last expect is successful, we have entered an error
            # state handle accordingly.
            self.tty = None
            self.state != DeviceSession.STATE_DISCONNECTED
        except:
            pass
        else:
            raise (FrameworkError(DeviceSession.ERR_FAILED_SESSION_CONNECT,
                                  'Error encountered while connecting')) 
                                  
        # The terminal is not busy, assume that the previous connect has worked,
        # consume the telnet connect string and send a carriage return
        try:
            self.tty.expect(BelkinCSS.REGEX_TELNET_LOGIN,
                            timeout=BelkinCSS.EXPECT_TIMEOUT)

            for i in self.config.username:
                self.tty.send(i)

            self.tty.expect(self.config.username) 
            self.tty.send(DeviceSession.CMD_CR)
            self.tty.expect(BelkinCSS.REGEX_TELNET_PASSWD,timeout=BelkinCSS.EXPECT_TIMEOUT)

            for j in self.config.password:
                self.tty.send(j)

            self.tty.send(DeviceSession.CMD_CR)

            self.state = DeviceSession.STATE_CONNECTED
        except:
            # If the last expect is successful, we have entered an error
            # state handle accordingly.
            self.tty = None
            self.state != DeviceSession.STATE_DISCONNECTED
            raise (FrameworkError(DeviceSession.ERR_FAILED_SESSION_CONNECT,
                   'Error encountered while connecting')) 
                                  
    def disconnect(self):
        r"""
        Refer base class for a description of this interface method.

        @return:
            None, exceptions raised must be derived from L{FrameworkError}
        """
        ConsoleServerSession.disconnect(self)
        
        # Attempt to disconnect
        try:
            self.tty.sendcontrol(']')
            self.tty.expect(DeviceSession.REGEX_TELNET_QUITPROMPT, 
                            timeout=BelkinCSS.EXPECT_TIMEOUT)
            self.tty.sendline('quit')
            self.tty.expect(DeviceSession.REGEX_TELNET_CLOSED, 
                            timeout=BelkinCSS.EXPECT_TIMEOUT)
            self.state = DeviceSession.STATE_DISCONNECTED
            self.tty = None
        except:
            raise (FrameworkError(DeviceSession.ERR_FAILED_SESSION_DISCONNECT,
                                  'Unable to disconnect from the device'))
        
    def ttyAvailable(self) :
        r"""
        Refer base class for a description of this interface method.

        @return:
            None, exceptions raised must be derived from L{FrameworkError}
        """  
        try:
            self.connect()
            self.disconnect()
            return True
        except:
            return False
        
    def ttyConnect(self):
        r"""
        Refer base class for a description of this interface method.

        @return:
            None, exceptions raised must be derived from L{FrameworkError}
        """  
        pass
    
    def ttyDisconnect(self):
        r"""
        Refer base class for a description of this interface method.

        @return:
            None, exceptions raised must be derived from L{FrameworkError}
        """  
        pass
    
