import pexpect
import pcs
import logging
import sys

from atf.framework.FrameworkBase import *
from atf.framework.SystemConfig import *
from DeviceSession import *
from NetworkSetupSession import *

class CiscoIOSNSS(NetworkSetupSession):
    r"""
    The CiscoIOSNSS class provides support for Cisco IOS Network Setup devices
    """
   
    ###
    # Class Definitions
    ###
    # Constants
    (EXPECT_TIMEOUT) = 300
    """Generic expect time out.""" 
    
    # Regex Patterns
    (REGEX_PASSWD)       = "[Pp]assword:[ ]*"
    """Pattern expected for the password during a login."""
    (REGEX_PROMPT)       = "%s>"
    """Pattern expected for the prompt of a system."""
    (REGEX_ENABLEPROMPT) = "%s#"
    """Pattern expected for the enable prompt of a system."""
    (REGEX_CONFIGPROMPT) = "%s\(config\)#"
    """Pattern expected for the config prompt of a system."""
    (REGEX_CFGIFPROMPT)  = "%s\(config-if\)#"
    """Pattern expected for the config interface prompt of a system."""
    (REGEX_CLOSE)        = "Connection closed by foreign host."
    """Pattern expected for connection close."""
        
    def __init__(self,  deviceSessionConfig=None, diagLevel=logging.WARNING):
        r"""
        Refer base class for a description of this interface method.

        @param deviceSessionConfig:
            A pre-constructed L{DeviceSessionConfig} object
            
        @param diagLevel:
            What debug level to run this object in.    
        """
        NetworkSetupSession.__init__(self, 
             deviceSessionConfig=deviceSessionConfig, 
             diagLevel=diagLevel)        

    def connect(self):
        r"""
        Refer base class for a description of this interface method.
        
        @return:
            None, exceptions raised must be derived from L{FrameworkError}
        """
        NetworkSetupSession.connect(self)
        
        # Check that a password has been provided
        if (self.config.password == None):
            raise (FrameworkError(DeviceSession.ERR_FAILED_SESSION_CONNECT,
                                  'Cisco IOS NSS password has not been configured'))

        # Attempt to connect
        try:
            # login
            self.tty = pexpect.spawn(self.cmd)
            if (self.logger.getEffectiveLevel() <= logging.DEBUG):
                self.tty.logfile_read = sys.stdout
            self.tty.expect(CiscoIOSNSS.REGEX_PASSWD, 
                            timeout=CiscoIOSNSS.EXPECT_TIMEOUT)
            self.tty.sendline(self.config.password)
            self.tty.expect(CiscoIOSNSS.REGEX_PROMPT % 
                            (self.config.deviceName))
            self.tty.sendline('enable')
            self.tty.expect(CiscoIOSNSS.REGEX_PASSWD, 
                            timeout=CiscoIOSNSS.EXPECT_TIMEOUT)
            self.tty.sendline(self.config.password)
            self.tty.expect(CiscoIOSNSS.REGEX_ENABLEPROMPT % 
                            (self.config.deviceName))
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
        NetworkSetupSession.disconnect(self)
        
        # Attempt to disconnect
        try:
            self.tty.sendline(DeviceSession.CMD_CR)
            self.tty.expect(CiscoIOSNSS.REGEX_ENABLEPROMPT % 
                            (self.config.deviceName))
            self.tty.sendline('exit')
            self.tty.expect(CiscoIOSNSS.REGEX_CLOSE)
            self.state = DeviceSession.STATE_DISCONNECTED
            self.tty = None
        except:
            raise (FrameworkError(DeviceSession.ERR_FAILED_SESSION_DISCONNECT,
                                 'Unable to disconnect from the device'))
        
    def setVlan(self, vlanID='2'):
        r"""
        Refer base class for a description of this interface method.

        @param vlanID:
            The VLAN ID to associated with the configured port. 
        
        @return:
            None, exceptions raised must be derived from L{FrameworkError}
        """  
        NetworkSetupSession.setVlan(self, vlanID=vlanID)

        # Attempt to set the VLAN
        try:
            self.tty.sendline(DeviceSession.CMD_CR)
            self.tty.expect(CiscoIOSNSS.REGEX_ENABLEPROMPT % 
                            (self.config.deviceName))
            self.tty.sendline("configure terminal")
            self.tty.expect(CiscoIOSNSS.REGEX_CONFIGPROMPT % 
                            (self.config.deviceName))
            self.tty.sendline("interface GigabitEthernet " + 
                              self.config.netPortID)
            self.tty.expect(CiscoIOSNSS.REGEX_CFGIFPROMPT % 
                            (self.config.deviceName))
            self.tty.sendline('switchport access vlan ' + vlanID)
            self.tty.expect(CiscoIOSNSS.REGEX_CFGIFPROMPT % 
                            (self.config.deviceName))
    
            # Reset the prompt
            self.tty.sendline('exit')
            self.tty.expect(CiscoIOSNSS.REGEX_CONFIGPROMPT % 
                            (self.config.deviceName))
            self.tty.sendline('exit')
            self.tty.expect(CiscoIOSNSS.REGEX_ENABLEPROMPT % 
                            (self.config.deviceName))
        except:
            raise (FrameworkError(DeviceSession.ERR_FAILED_SESSION_OPERATION,
                                  'Unable to set VLAN ID for device'))
            
    def resetVlan(self):
        r"""
        Refer base class for a description of this interface method.

        @return:
            None, exceptions raised must be derived from L{FrameworkError}
        """  
        self.setVlan('1')

