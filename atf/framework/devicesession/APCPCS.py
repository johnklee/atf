import pexpect
import pcs
import logging

from atf.framework.FrameworkBase import *
from atf.framework.SystemConfig import *
from DeviceSession import *
from PowerControllerSession import *

class APCPCS(PowerControllerSession):
    r"""
    The APCPCS class provides support for APC power controllers.
    """
   ###
    # Class Definitions
    ###
    # Constants
    (EXPECT_TIMEOUT) = 300 
    """Generic expect time out""" 
    
    # Regex Patterns
    (REGEX_PROMPT) = "> "
    """Pattern expected for the prompt of a system."""
    (REGEX_CONFIRM) = "Enter 'YES' to continue or <ENTER> to cancel :"
    """Pattern expected for a confirmation."""
    (REGEX_CONTINUE) = "continue..."
    """Pattern expected for a continue prompt."""
    (REGEX_LOGIN) = "User Name :"
    """Pattern expected for the user name during a login."""
    (REGEX_PASSWD) = "Password  :"
    """Pattern expected for the password during a login."""
    (REGEX_CLOSE) = "Connection Closed - Bye"
    """Pattern expected for the connection termination."""
    (REGEX_OCCUPIED) = "Connection closed by foreign host"
    """Pattern expected for the connection occupied."""
    (REGEX_CTLCONSOLE) = "Control Console"
    """Pattern expected for the control console state."""
    (REGEX_DEVMGR) = "Device Manager"
    """Pattern expected for the device manager state."""
    (REGEX_OUTLET) = "Outlet Control/Configuration"
    """Pattern expected for the outlet state."""
    (REGEX_OUTLETNUM) = "Outlet %s"
    """Pattern expected for the outlet number state."""
    (REGEX_CTLOUTLET) = "Control Outlet"
    """Pattern expected for the control outlet state."""
    (REGEX_OUTLET_MGMT) = "Outlet Management" 
    
    # Commands for power controller operations
    (CMD_ON)         = '1\r'
    """Command used for port power on."""
    (CMD_OFF)        = '2\r'
    """Command used for port power off."""
    (CMD_CYCLE)      = '3\r'
    """Command used for port power cycle."""
    (CMD_EXIT)       = '4\r' 
    """Command used for exit from the system."""
    (CMD_ESC)        = '\x1B\r' 
    """Command used to send an escape to the system."""
    
    
    def __init__(self,  deviceSessionConfig=None, diagLevel=logging.WARNING):
        r"""
        Refer base class for a description of this interface method.

        @param deviceSessionConfig:
            A pre-constructed L{DeviceSessionConfig} object
        @param diagLevel:
            What debug level to run this object in    
        """
        PowerControllerSession.__init__(self, 
             deviceSessionConfig=deviceSessionConfig, 
             diagLevel=diagLevel)
        self.powerState = PowerControllerSession.STATE_INITIALISED
        """The power state of the APC session"""

    def _executePowerCommand(self, command):
        r"""
        Execute a specified regex command after navigating the APC
        menu hierarchy.
        
        @param command:
            The command to execute on the APC after navigating the control 
            menus 
        
        @return:
            None, exceptions raised must be derived from L{FrameworkError}
        """        
        self.tty.send(DeviceSession.CMD_CR)
        self.tty.expect(APCPCS.REGEX_CTLCONSOLE)
        self.tty.expect(APCPCS.REGEX_PROMPT)
        self.tty.send('1\r')
        self.tty.expect(APCPCS.REGEX_DEVMGR)
        self.tty.expect(APCPCS.REGEX_PROMPT)
        self.tty.send('2\r')
        self.tty.expect(APCPCS.REGEX_OUTLET_MGMT)
        self.tty.expect(APCPCS.REGEX_PROMPT)
        self.tty.send('1\r')
        self.tty.expect(APCPCS.REGEX_OUTLET)
        self.tty.expect(APCPCS.REGEX_PROMPT)
        self.tty.send('%s\r' % self.config.powerPort)
        # comment below line to allow user-defined outlet name
        # self.tty.expect(APCPCS.REGEX_OUTLETNUM % self.config.powerPort)
        self.tty.expect(APCPCS.REGEX_PROMPT)
        self.tty.send('1\r')
        self.tty.expect(APCPCS.REGEX_CTLOUTLET)
        self.tty.expect(APCPCS.REGEX_PROMPT)
        self.tty.send(command)
        self.tty.expect(APCPCS.REGEX_CONFIRM)
        self.tty.sendline('YES')
        self.tty.sendline('\n')
        self.tty.sendline('\r')
        self.tty.expect(APCPCS.REGEX_CONTINUE)
        self.tty.sendline('\r')
        self.tty.expect(APCPCS.REGEX_CTLOUTLET)
        self.tty.expect(APCPCS.REGEX_PROMPT)
        self.tty.send(APCPCS.CMD_ESC)
        # comment below line to allow user-defined outlet name
        # self.tty.expect(APCPCS.REGEX_OUTLETNUM % self.config.powerPort)
        self.tty.expect(APCPCS.REGEX_PROMPT)
        self.tty.send(APCPCS.CMD_ESC)
        self.tty.expect(APCPCS.REGEX_OUTLET)
        self.tty.expect(APCPCS.REGEX_PROMPT)
        self.tty.send(APCPCS.CMD_ESC)
        self.tty.expect(APCPCS.REGEX_OUTLET_MGMT) 
        self.tty.expect(APCPCS.REGEX_PROMPT)      
        self.tty.send(APCPCS.CMD_ESC)             
        self.tty.expect(APCPCS.REGEX_DEVMGR)
        self.tty.expect(APCPCS.REGEX_PROMPT)
        self.tty.send(APCPCS.CMD_ESC)
        self.tty.expect(APCPCS.REGEX_CTLCONSOLE)
        self.tty.expect(APCPCS.REGEX_PROMPT)

    def connect(self):
        r"""
        Refer base class for a description of this interface method.
        
        @return:
            None, exceptions raised must be derived from L{FrameworkError}
        """
        PowerControllerSession.connect(self)
       
        # Check that a password has been provided
        if (self.config.username == None):
            raise (FrameworkError(DeviceSession.ERR_FAILED_SESSION_CONNECT,
                                  'APC PCS username has not been configured'))
                                  
        # Check that a password has been provided
        if (self.config.password == None):
            raise (FrameworkError(DeviceSession.ERR_FAILED_SESSION_CONNECT,
                                  'APC PCS password has not been configured'))
        
        # Attempt to connect 
        try:
            # self.tty.expect(APCPCS.REGEX_LOGIN, 
            #                 timeout=APCPCS.EXPECT_TIMEOUT)
            cnt = 0
            while ( True ):
                cnt = cnt + 1
                self.tty = pexpect.spawn(self.cmd)
                if (self.logger.getEffectiveLevel() <= logging.DEBUG):
                    self.tty.logfile_read = sys.stdout

                state = self.tty.expect([APCPCS.REGEX_LOGIN, APCPCS.REGEX_OCCUPIED], timeout=APCPCS.EXPECT_TIMEOUT)
                if ( state == 0 or cnt >= 20 ):
                    break
                else:
                    time.sleep(10)
                    
                        

            self.tty.send(self.config.username + '\r')
            self.tty.expect(APCPCS.REGEX_PASSWD, 
                            timeout=APCPCS.EXPECT_TIMEOUT)
            self.tty.send(self.config.password + '\r')
            self.tty.expect(APCPCS.REGEX_CTLCONSOLE)
            self.tty.expect(APCPCS.REGEX_PROMPT)
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
            self.tty.expect(APCPCS.REGEX_PROMPT)
            self.tty.sendline(APCPCS.CMD_EXIT)
            self.tty.expect(APCPCS.REGEX_CLOSE)
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
            self._executePowerCommand(APCPCS.CMD_ON)
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
            self._executePowerCommand(APCPCS.CMD_OFF)
            self.powerState = PowerControllerSession.STATE_POWEROFF
        except:
            raise (FrameworkError(DeviceSession.ERR_FAILED_SESSION_OPERATION,
                                 'Failed to power off specified port'))
    
    def powerCycle(self):
        r"""
        Refer base class for a description of this interface method.

        @return:
            None, exceptions raised must be derived from L{FrameworkError}
        """      
        PowerControllerSession.powerCycle(self)
        
        # Attempt to power on
        try:
            self._executePowerCommand(APCPCS.CMD_CYCLE)
            self.powerState = PowerControllerSession.STATE_POWERON
        except:
            raise (FrameworkError(DeviceSession.ERR_FAILED_SESSION_OPERATION,
                                 'Failed to power cycle specified port'))
