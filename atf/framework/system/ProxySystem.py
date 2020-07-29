import logging

from atf.framework.FrameworkBase import *
from atf.framework.device.ProxyDevice import *
from atf.framework.device.ProxyQemu import *
from atf.framework.device.ProxyVMware import *
from atf.framework.device.ProxyVMwareESX import *
from atf.framework.device.ProxyGX4004 import *
from atf.framework.device.ProxyMX1004 import *
from atf.framework.device.ProxyFWA3210es0 import *
from atf.framework.device.ProxyFWA3210es1 import *
from atf.framework.device.ProxyFWA3211es import *
from atf.framework.device.ProxyFWA6501 import *
from atf.framework.device.ProxyXGS3100 import *
from atf.framework.device.ProxyXGS4100 import *
from atf.framework.device.ProxyXGS5100 import *
from atf.framework.device.ProxyXGS5200 import *
from atf.framework.device.ProxyXGS7100 import *
from atf.framework.device.ProxyDocker import *
from atf.framework.device.ProxyCloudStack import *


class ProxySystem(FrameworkBase):
    r"""
    The ProxySystem class provides access to the underlying ProxyDevice as well
    as high level environment setup methods for the System.
    The intention is to allow an easy way for test writers to get
    a bare system installed and booted to a known good state before
    specific tests are run. Most methods in this class are abstract as it
    defines the interface but leaves implementation to derived classes.
    """

    #
    # Class error definitions
    #

    (ERR_UNKNOWN_DEVICE_TYPE) = FrameworkError.ERR_SYSTEM
    """Unknown device type configured to run system on."""
    (ERR_INVALID_SYSTEM_STATE) = FrameworkError.ERR_SYSTEM+1
    """System is in an invalid state to perform the requested operation."""
    (ERR_LOGIN_ATTEMPT_FAILED) = FrameworkError.ERR_SYSTEM+2
    """Attempt to login to the system failed."""
    (ERR_LOGOUT_ATTEMPT_FAILED) = FrameworkError.ERR_SYSTEM+3
    """Attempt to logout of the system failed."""
    (ERR_INSTALL_FAILED) = FrameworkError.ERR_SYSTEM+4
    """Clean installation attempt failed."""
    (ERR_SHUTDOWN_FAILED) = FrameworkError.ERR_SYSTEM+5
    """Clean system shutdown failed."""
    (ERR_REBOOT_FAILED) = FrameworkError.ERR_SYSTEM+6
    """System reboot failed."""
    (ERR_CLI_FAILED) = FrameworkError.ERR_SYSTEM+7
    """System CLI command failed to return a known result"""
    (ERR_COPY_FAILED) = FrameworkError.ERR_SYSTEM+8
    """System file copy failed."""

    # Define valid states that a ProxySystem can be in.
    (STATE_UNKNOWN) = 0
    """Undetermined system state."""
    (STATE_INITIALISED) = 1
    """System object initialised but not really useable"""
    (STATE_OFF) = 2
    """System is powered off"""
    (STATE_STARTING) = 3
    """system is performing power on processing."""
    (STATE_LOGIN_PROMPT) = 4
    """System is at login prompt"""
    (STATE_CLI_PROMPT) = 5
    """System is at command line interface prompt."""
    (STATE_SHUTTING_DOWN) = 6
    """System is performing system shutdown/power off processing."""
    (STATE_STOPPING) = 7
    """System is performing device power off processing."""

    # These are *HOST* specific commands variables. Until
    # a distinction is made on which platform ATF is executing
    # on, these are linux/bash specific.
    (CMD_HOSTSHELL) = 'bash'
    """ This is a host bash shell spawn command """
    (CMD_HOSTSHELL_PROMPT) = 'export PS1=#'
    """ This is a host bash shell modification command """
    (REGEX_HOSTSHELL_PROMPT) = '#'
    """ This is a host bash shell prompt """
    (REGEX_HOSTSHELL_SSHERROR) = 'ssh: connect to host'
    """ SSH pattern on error """

    (FILESCP_TIMEOUT) = 30 * RunConfig.TIMEOUT_MULTIPLIER
    """ Time out associated with file transfer """
    (CMD_FILESCP) = 'scp -p -o CheckHostIP=no -o StrictHostKeyChecking=no ' \
                    + '-o UserKnownHostsFile=/dev/null '
    """ This is the scp command for file transfer, it removes sundry ssh checks
        such as spoof checking and hostfile modification.
        -p option preserves permissions modification"""
    (REGEX_FILESCP_PASSWD) = 'Password:'
    """ This is the expected password prompt for file transfer """

    def __init__(self, systemConfig=None, diagLevel=logging.WARNING):
        r"""
        Set up diagnostics output and save config details.
        Move to L{STATE_UNKNOWN} (i.e. it is up to derived classes to complete
        initialisation and change to L{STATE_INITIALISED}).

        @param systemConfig:
            A pre-constructed SystemConfig derived object

        @param diagLevel:
            What debug level to run this object in.
        """
        FrameworkBase.__init__(self, diagLevel)

        self.state = ProxySystem.STATE_UNKNOWN
        """current STATE_ of the system."""

        self.device = None
        """L{ProxyDevice} that this system is using."""

        self.systemConfig = systemConfig
        """L{SystemConfig} that this system is using."""

        self.shell = None
        """The L{Shell} object available for interaction after login."""

        self.lastCmdOutput = ''
        """The string buffer available for the output of the last command
           executed on the system via executeCLICommand. It's method of
           population is System specific"""

        # Check to see if we have an install image in the system config
        # that needs to replace the one in the device config.
        if ((self.systemConfig != None) and
            (self.systemConfig.systemImages != None)):
                self.systemConfig.deviceConfig.systemImages = \
                    self.systemConfig.systemImages

        if (self.systemConfig.systemImages == None):
            self.logger.warning('No install image specified in configuration')

    def __del__(self):
        r"""
        Make sure that we cleanup any underlying device by telling it
        to stop() if it hasn't already.
        """
        if ((self.device != None) and
            (self.device.isStoppable() == CommonError.ERR_OK)):
            self.device.stop()

    def createDevice(self):
        r"""
        Simply create the correct L{ProxyDevice} concrete class based on the
        L{DeviceConfig} object we were constructed with and save it.

        @return:
            None, can raise a L{FrameworkError} exception if an unknown
            L{SystemConfig} derived object was provided at construction.
        """
        from atf.framework.device.ProxyDocker import *
        if (isinstance(self.systemConfig.deviceConfig, QemuConfig)):
            self.device = ProxyQemu(emuConfig=self.systemConfig.deviceConfig,
                                    diagLevel=self.logger.getEffectiveLevel())
        elif (isinstance(self.systemConfig.deviceConfig, DockerConfig)):         
            self.device = ProxyDocker(dkConfig=self.systemConfig.deviceConfig,
                                      diagLevel=self.logger.getEffectiveLevel())
        elif (isinstance(self.systemConfig.deviceConfig, VMwareConfig)):
            self.device = ProxyVMware(emuConfig=self.systemConfig.deviceConfig,
                                      diagLevel=self.logger.getEffectiveLevel())
        elif (isinstance(self.systemConfig.deviceConfig, VMwareESXConfig)):
            self.device = ProxyVMwareESX(emuConfig=self.systemConfig.deviceConfig,
                                         diagLevel=self.logger.getEffectiveLevel())
        elif (isinstance(self.systemConfig.deviceConfig, GX4004Config)):
            self.device = ProxyGX4004(hwConfig=self.systemConfig.deviceConfig,
                                      diagLevel=self.logger.getEffectiveLevel())
        elif (isinstance(self.systemConfig.deviceConfig, MX1004Config)):
            self.device = ProxyMX1004(hwConfig=self.systemConfig.deviceConfig,
                                      diagLevel=self.logger.getEffectiveLevel())
        elif (isinstance(self.systemConfig.deviceConfig, FWA6501Config)):
            self.device = ProxyFWA6501(hwConfig=self.systemConfig.deviceConfig,
                                       diagLevel=self.logger.getEffectiveLevel())
        elif (isinstance(self.systemConfig.deviceConfig, FWA3210es0Config)):
            self.device = ProxyFWA3210es0(hwConfig=self.systemConfig.deviceConfig,
                                          diagLevel=self.logger.getEffectiveLevel())
        elif (isinstance(self.systemConfig.deviceConfig, FWA3210es1Config)):
            self.device = ProxyFWA3210es1(hwConfig=self.systemConfig.deviceConfig,
                                          diagLevel=self.logger.getEffectiveLevel())
        elif (isinstance(self.systemConfig.deviceConfig, FWA3211esConfig)):
            self.device = ProxyFWA3211es(hwConfig=self.systemConfig.deviceConfig,
                                         diagLevel=self.logger.getEffectiveLevel())
        elif (isinstance(self.systemConfig.deviceConfig, XGS3100Config)):
            self.device = ProxyXGS3100(hwConfig=self.systemConfig.deviceConfig,
                                       diagLevel=self.logger.getEffectiveLevel())
        elif (isinstance(self.systemConfig.deviceConfig, XGS4100Config)):
            self.device = ProxyXGS4100(hwConfig=self.systemConfig.deviceConfig,
                                       diagLevel=self.logger.getEffectiveLevel())
        elif (isinstance(self.systemConfig.deviceConfig, XGS5100Config)):
            self.device = ProxyXGS5100(hwConfig=self.systemConfig.deviceConfig,
                                       diagLevel=self.logger.getEffectiveLevel())
        elif (isinstance(self.systemConfig.deviceConfig, XGS5200Config)):
            self.device = ProxyXGS5200(hwConfig=self.systemConfig.deviceConfig,
                                       diagLevel=self.logger.getEffectiveLevel())
        elif (isinstance(self.systemConfig.deviceConfig, XGS7100Config)):
            self.device = ProxyXGS7100(hwConfig=self.systemConfig.deviceConfig,
                                       diagLevel=self.logger.getEffectiveLevel())
        elif (isinstance(self.systemConfig.deviceConfig, CloudConfig)):
            self.device = ProxyCloudStack(emuConfig=self.systemConfig.deviceConfig,
                                       diagLevel=self.logger.getEffectiveLevel())
        else:
            # Unknown device type, we don't handle this.
            raise (FrameworkError(ProxySystem.ERR_UNKNOWN_DEVICE_TYPE,
                                  'Unknown device type of %s' %
                                  type(self.systemConfig.deviceConfig)))

    def isOnable(self):
        r"""
        Classes can use this method to ensure that the ProxySystem is in
        a suitably initialised state to attempt to powerOn().

        @return:
            - L{CommonError.ERR_OK} if ok to powerOn
            - L{ProxySystem.ERR_INVALID_SYSTEM_STATE} invalid state for powerOn
        """
        if ((self.state != ProxySystem.STATE_INITIALISED) and
            (self.state != ProxySystem.STATE_OFF)):
            return(ProxySystem.ERR_INVALID_SYSTEM_STATE)
        else:
            return(CommonError.ERR_OK)

    def isOffable(self):
        r"""
        Classes can use this method to ensure that the ProxySystem is in a
        suitable running state to attempt to powerOff().

        @return:
            - L{CommonError.ERR_OK} if ok to powerOff
            - L{ProxySystem.ERR_INVALID_SYSTEM_STATE} invalid state for powerOff
        """
        if (self.state > ProxySystem.STATE_OFF):
            return(CommonError.ERR_OK)
        else:
            return(ProxySystem.ERR_INVALID_SYSTEM_STATE)

    def powerOn(self, packageType=None):
        r"""
        Perform Device start and make sure the System comes up into a valid
        STATE_STARTING.

        @param packageType:
            The type of image to use during device start. One of:
                - None.
                - L{DeviceConfig.IMAGE_ISO}
                - L{DeviceConfig.IMAGE_PXE}
                - L{DeviceConfig.IMAGE_USB}
                - L{DeviceConfig.IMAGE_LIVE}

        @return:
            None, exceptions raised must be derived from L{FrameworkError}
        """
        raise (NotImplementedError())

    def powerOff(self):
        r"""
        Unceremoniously yank the power from the Device environment

        @return:
            None, exceptions raised must be derived from L{FrameworkError}
        """
        raise (NotImplementedError())

    def shutdown(self):
        r"""
        powerOff() the System after cleanly shutting down or at least
        giving the System every chance to shut down cleanly.

        @return:
            None, exceptions raised must be derived from L{FrameworkError}
        """
        raise (NotImplementedError())

    def reboot(self):
        r"""
        Halt the System then bring it back up without powering off
        the device (i.e. on linux Systems this is simply the reboot command).
        Check that the system has returned to a login prompt.

        @return:
            None, exceptions raised must be derived from L{FrameworkError}
        """
        raise (NotImplementedError())

    def login(self, user, passwd, timeout, loginPrompt):
        r"""
        Login as the user specified.
        The method will first check that it is at a login prompt, then
        perform a login attempt using the password given.

        @param user:
            System user name to login as.

        @param passwd:
            Password for the specified user.

        @param timeout:
            Max time to wait for a login prompt before failing

        @param loginPrompt:
            prompt to expect after logging in

        @return:
            None, exceptions raised must be derived from L{FrameworkError}
        """
        raise (NotImplementedError())

    def logout(self):
        r"""
        Logout of the system.
        The method will first check that it is in a valid state to logout, then
        perform the logout operation and ensure the system returns to the login
        prompt.

        @return:
            None, exceptions raised must be derived from L{FrameworkError}
        """
        raise (NotImplementedError())

    def executeCLICommand(self, cmd, cmdTimeout=None):
        r"""
        Execute a CLI system command and return a success or failure indication.
        The method will first check that it is at a login prompt, then
        perform the command specified.

        @param cmd:
            The CLI cmd to execute and check result of.

        @param cmdTimeout:
            The amount of time to allow the command itself to run and return
            to the CLI prompt.

        @return:
            Return status from the executed command.
        """
        raise (NotImplementedError())

    def interact(self, escapeCharacter='\x1d'):
        r"""
        This gives control of the child process to the interactive user (the
        human at the keyboard). Keystrokes are sent to the child process, and
        the stdout and stderr output of the child process is printed.

        When the user types the escape_character this method will stop.
        The default for escape_character is ^] (ctrl+']').

        @param escapeCharacter:
            The escape character to use to leave interact mode.
        """
        raise (NotImplementedError())

    def addRoute(self, ip, interface=None, gateway=None):
        r"""
        Setup a route to the specific IP via the specific Interface/Gateway.

        @param ip:
            The IP to add a route to.

        @param interface:
            The interface to associate with the route.

        @param gateway:
            The gateway to associate with the route.
        """
        raise (NotImplementedError())

    def copyFileToSystem(self, hostFile, systemFile, ip=None, user=None, passwd=None, timeout=FILESCP_TIMEOUT):
        r"""
        Copy a file to the ProxySystem.

        The mechanism involved in the file transfer is based on the features and
        capabilities provided by the target system.

        @param hostFile:
            The name of the file on the host that is to be copied to the system.

        @param systemFile:
            The name of the file on the system that is the target for the
            file copy.

        @param ip:
            The IP of the ProxySystem to transfer the file from. Optional for
            systems that use a non-network based mechanism.

        @param user:
            The system username to use for the file transfer. Optional if configuration
            defaults for the system are sufficient.

        @param passwd:
            The password for the specified user. Optional if configuration
            defaults for the system are sufficient.

        @param timeout:
            Time out associated with file transfer. Optional if configuration
            defaults for the system are sufficient.
        """
        raise (NotImplementedError())

    def copyFileFromSystem(self, systemFile, hostFile, ip=None, user=None, passwd=None, timeout=FILESCP_TIMEOUT):
        r"""
        Copy a file from the ProxySystem.

        The mechanism involved in the file transfer is based on the features and
        capabilities provided by the target system.

        @param systemFile:
            The name of the file on the system that is to be copied to the host.

        @param hostFile:
            The name of the file on the host that is the target for the file copy.

        @param ip:
            The IP of the ProxySystem to transfer the file from. Optional for
            systems that use a non-network based mechanism.

        @param user:
            The system username to use for the file transfer. Optional if configuration
            defaults for the system are sufficient.

        @param passwd:
            The password for the specified user. Optional if configuration
            defaults for the system are sufficient.

        @param timeout:
            Time out associated with file transfer. Optional if configuration
            defaults for the system are sufficient.
        """
        raise (NotImplementedError())
