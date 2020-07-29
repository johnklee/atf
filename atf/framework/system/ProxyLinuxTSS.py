from pexpect import *

from ProxyTSS import *
from Shell import *
from ProxyLinuxService import *
from atf.common.network.Network import NetworkUtil
from time import sleep
import socket as socketHelper


class BashShell (Shell):
    r"""
    This class encapsulates all the functionality for interacting with
    the system using the BASH interface
    """
    ###
    # Define common expect patterns and timeouts
    ###
    (CLI_PROMPT)            = '#'
    """Bash CLI prompt string for expect."""
    (HALTED_MSG)            = 'System halted.'
    """Pattern expected at the halt of a system."""
    (SHUTTING_DOWN_MSG)     = 'The system is going down for reboot'
    """Pattern expected during the halt of a system."""
    (RESTARTING_MSG)        = 'Restarting system'
    """Pattern expected during the restart of a system."""
    
    (CLI_RESPONSE_TIMEOUT)  = 20 * RunConfig.TIMEOUT_MULTIPLIER
    """Expect timeout associated with the execution of commands."""
     
    ###
    # Define literal commands used at the CLI to make it easy to change in future.
    ###
    (CMD_HALT)              = 'halt'
    """Command used for system halt."""
    (CMD_REBOOT)            = 'reboot'
    """Command used for system reboot."""

    ###
    # Define control characters as well
    ###
    (CTL_BREAK)  = 'c'   # Break 
    """Command used for execution break."""
    (CTL_LOGOUT) = 'd'   # Logout
    """Command used for system logout."""

    def __init__(self, diagLevel=logging.ERROR):
        r"""
        Define particulars about the shell's characteristics.
        
        @param diagLevel:
            The logging level at which the class will operate.
        """
        Shell.__init__(self, diagLevel=diagLevel)
        
        self.CliPrompt  = BashShell.CLI_PROMPT
        """The string the CLI Prompt should be set to."""
        self.CliTimeout = BashShell.CLI_RESPONSE_TIMEOUT
        """The expect timeout the CLI Prompt should be associated with."""
        
    def shutdown(self, timeout):
        r"""
        Shutdown the system.
        
        @param timeout:
            The timeout associated with the system halt command execution.
        """
        self.sendline(BashShell.CMD_HALT)
        self.expect(BashShell.HALTED_MSG, timeout=timeout)

    def reboot(self, timeout):
        r"""
        Reboot the system.
        
        @param timeout:
            The timeout associated with the system reboot command execution.
        """
        self.sendline(BashShell.CMD_REBOOT)
        self.expect(BashShell.SHUTTING_DOWN_MSG, timeout=timeout)
        self.expect(BashShell.RESTARTING_MSG,    timeout=timeout)
        
    def logout(self, loginPrompt, timeout=CLI_RESPONSE_TIMEOUT):
        r"""
        Logout from the system.
       
        @param loginPrompt:
            The login prompt to expect during the execution of a logout. 
        
        @param timeout:
            The timeout associated with the system logout command execution.
        """
        # Should be able to just send a ctrl-d but send a ctrl-c first
        # just in case there is some process running that we can exit
        # and avoid a common error condition.
        self.sendcontrol(BashShell.CTL_BREAK)
        self.expect(self.CliPrompt, timeout=timeout)
        self.sendcontrol(BashShell.CTL_LOGOUT)
        self.expect(loginPrompt, timeout=timeout)

    def executeCLICommand(self, cmd, cmdTimeout=None):
        r"""
        Execute a command and return the status result of that command.
        
        @param cmd:
            The command to be executed.
        
        @param cmdTimeout:
            The timeout associated with the system command execution.
        """
        self.sendline(cmd)
        # We match the first 70 characters in the cmd as otherwise expect
        # get confused with the line breaking of output.
        self.expect_exact(cmd[:70])
        if (cmdTimeout != None):
            self.expect_exact(self.CliPrompt, timeout=cmdTimeout)
        else:
            self.expect_exact(self.CliPrompt) 
            
        self.sendline('echo $?')            
        self.expect('[\d]{1,3}')
        result = int(self.terminal.after)
        self.expect_exact(self.CliPrompt)
        return (result)


class ProxyLinuxTSS(ProxyTSS):
    r"""
    The ProxyLinuxTSS class extends the ProxyTSS class to include methods
    that must be implemented by all proxies supporting Linux bound Test System
    Support services. 
    """
    ###
    # Define common expect patterns and timeouts
    ###
    (LOGIN_PROMPT)          = 'login: '     
    """Pattern expected at the username entry during the login of a system."""
    (PASSWORD_PROMPT)       = '[Pp]assword: '
    """Pattern expected at the password entry during the login of a system."""

    (BOOT_TIMEOUT)          = 60 * RunConfig.TIMEOUT_MULTIPLIER
    """Expect timeout associated with the boot of a system."""
    
    (REGEX_SCP_PASSWD)      = '[Pp]assword:'
    """ This is the expected password prompt for scp session 
        establishment """

    def __init__(self, tssConfig=None, diagLevel=logging.ERROR):
        r"""
        Save config and diagnostics output details

        @param tssConfig:
            A pre-constructed SystemConfig object
            
        @param diagLevel:
            What debug level to run this object in.
        """
        ProxyTSS.__init__(self, tssConfig, diagLevel)
        self.state = ProxySystem.STATE_INITIALISED

    def _waitForLogin(self, loginPrompt, timeout):
        '''
        Wait until the TSS has finished booting
        
        @param loginPrompt:
            The login prompt to expect after the execution of a login. 
        
        @param timeout:
            The timeout associated with the system login.
        '''
        # If the TSS has been configured correctly then there is
        # no boot menu, so we should just go straight to the loging prompt.
        #
        # If there is a boot menu, then we might not be able to see it anyhow -
        # at least that is the case with the sample Fedora 8 image provided.
        #
        # So all we can really do is wait for the login prompt.
        self.device.cons.expect(loginPrompt, timeout=timeout)            
        self.state = ProxySystem.STATE_LOGIN_PROMPT
        
        # send a new line so that the login prompt appears again - just in case
        # a test client is waiting for it
        self.device.cons.sendline()        


    ######
    # ProxySystem defined interfaces
    ######    

    def powerOn(self, packageType=None):
        r"""
        Perform Device start and make sure the System comes up into a valid
        L{ProxySystem.STATE_STARTING}.

        @param packageType:
            The type of image to use during device start. Presently a Test 
            Support System is a complete system disk, and as such there 
            should not be a packageType.
             
        @return:  
            None, exceptions raised must be derived from L{FrameworkError}
        """
        result = self.isOnable() 
        if (result != CommonError.ERR_OK):
            raise (FrameworkError(result, 'System state invalid for powerOn() : %s' % self.state))
        
        self.state = ProxySystem.STATE_STARTING
        
        # Use base class factory to create the correct device type.
        self.createDevice()
        
        # a test support system is currently a complete system disk, as such
        # there is no need to support additional media/packageType/productPackage
        productPackage = None
        if (packageType != None):
            raise (FrameworkError(ProxyTSS.ERR_UNSUPPORTED_PACKAGE_TYPE,
                                  'Unsupported packageType specified : %s' % packageType))


        self.device.start(productPackage=packageType)
        
        # clean up
        self.services = {}

    def powerOff(self):
        r"""
        Unceremoniously yank the power from the Device environment

        @return:  
            None, exceptions raised must be derived from L{FrameworkError}
        """
        result = self.isOffable() 
        if (result != CommonError.ERR_OK):
            raise (FrameworkError(result, 'System state invalid for powerOff() : %s' % self.state))
        
        self.state = ProxySystem.STATE_STOPPING
        self.device.stop()
        self.state = ProxySystem.STATE_OFF
        
        # clean up
        self.device = None
        self.shell = None
        self.services = {}


    def shutdown(self):
        r"""
        powerOff() the System after cleanly shutting down or at least
        giving the System every chance to shut down cleanly.

        @return:
            None, exceptions raised must be derived from L{FrameworkError}
        """
        # We should be sitting at a cli prompt
        if (self.state != ProxySystem.STATE_CLI_PROMPT):
            raise (FrameworkError(ProxySystem.ERR_INVALID_SYSTEM_STATE,
                    'Incorrect system state to attempt shutdown() : %s' % self.state))

        try:
            self.state = ProxySystem.STATE_SHUTTING_DOWN
            if(self.systemConfig.runMode == SystemConfig.RUN_MODE_CLOUDSTACK):
                self.shell.sendline(BashShell.CMD_HALT)
                self.shell.expect("Connection to " + str(self.device.vmPublicIp) + " closed", timeout=ProxyLinuxTSS.BOOT_TIMEOUT)
            else:
                self.shell.shutdown(ProxyLinuxTSS.BOOT_TIMEOUT)
            self.powerOff()
            
            # powerOff does our clean up
        except ExceptionPexpect, failure:
            self.state = ProxySystem.STATE_UNKNOWN
            raise(FrameworkError(ProxySystem.ERR_SHUTDOWN_FAILED, '%s' % failure))


    def reboot(self):
        r"""
        Halt the System then bring it back up without powering off
        the device (i.e. on linux Systems this is simply the reboot command).

        @return:
            None, exceptions raised must be derived from L{FrameworkError}
        """
        # We should be sitting at a cli prompt
        if (self.state != ProxySystem.STATE_CLI_PROMPT):
            raise (FrameworkError(ProxySystem.ERR_INVALID_SYSTEM_STATE,
                                  'Incorrect system state to attempt shutdown() : %s' % self.state))

        try:
            self.state = ProxySystem.STATE_SHUTTING_DOWN
            if(self.systemConfig.runMode == SystemConfig.RUN_MODE_CLOUDSTACK):
                self.shell.sendline(BashShell.CMD_REBOOT)
                self.shell.expect(BashShell.SHUTTING_DOWN_MSG, timeout=BashShell.CLI_RESPONSE_TIMEOUT)
                self.shell.expect("Connection to " + str(self.device.vmPublicIp) + " closed", timeout=BashShell.CLI_RESPONSE_TIMEOUT)
                # Check the device is able to be logged in again before handing control back to the caller
                Common.checkConn(self, self.device.vmPublicIp, desc=self.config.name)
            else:
                self.shell.reboot(ProxyLinuxTSS.BOOT_TIMEOUT)
            self.state = ProxySystem.STATE_STARTING
            # clean up
            self.shell = None
            self.services = {}
        except ExceptionPexpect, failure:
            self.state = ProxySystem.STATE_UNKNOWN
            raise(FrameworkError(ProxySystem.ERR_REBOOT_FAILED, '%s' % failure))


    def login(self, user, passwd,
              timeout=BashShell.CLI_RESPONSE_TIMEOUT,
              loginPrompt=LOGIN_PROMPT, 
              shell=None):
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
            System login prompt to look for before logging in
            
        @return:
            None, exceptions raised must be derived from L{FrameworkError}
        """
        if (shell == None):
            shell = BashShell()

        if ((self.state == ProxySystem.STATE_STARTING) or 
            (self.state == ProxySystem.STATE_LOGIN_PROMPT)):
            try:
                if(self.systemConfig.runMode == SystemConfig.RUN_MODE_CLOUDSTACK):
                    # In cloudstack, a login is a ssh call into the machine. The machine is auto-logged in when created.
                    # Therefore we must be re logging in after a logout here. Ensure the old pexpect call is terminated
                    # and make a new ssh call
                    if(self.device.cons != None):
                        self.device.cons.sendline('exit')
                        self.device.cons.terminate(force=True)
                    cmd = "ssh -4 -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no"
                    cmd += " -o GSSAPIAuthentication=no -o PreferredAuthentications=password "
                    cmd += user+"@"+str(self.device.vmPublicIp)
                    self.device.cons = pexpect.spawn(cmd, timeout=120)
                    self.device.cons.expect(ProxyLinuxTSS.PASSWORD_PROMPT, shell.CliTimeout)
                    self.device.cons.sendline(passwd)
                    self.device.cons.expect(shell.CliPrompt, shell.CliTimeout)
                    
                    self.state = ProxySystem.STATE_CLI_PROMPT
                    
                    if (self.logger.getEffectiveLevel() <= logging.DEBUG):
                        self.device.cons.logfile_read = sys.stdout
                elif(self.systemConfig.runMode == SystemConfig.RUN_MODE_DOCKER):
                    if self.device.cons is None:
                        if self.systemConfig.defaultGatewayIp != None:
                            self.device.dkClient.network_cmd(self.device.container, cmd='ip r d default', sh=self.device.hostShell)

                        self.device.cons = self.device.dkClient.spawn_container_shell(self.device.container, passwd=self.device.config.host_passwd)

                        if self.systemConfig.defaultGatewayIp is not None:
                            self.device.dkClient.network_cmd(self.device.container, 
                                                             cmd='ip r a default via %s' % self.systemConfig.defaultGatewayIp.address, 
                                                             sh=self.device.hostShell)
                    self.state = ProxySystem.STATE_CLI_PROMPT
                else:
                    # Send a few returns to the cons to elicit a login prompt.
                    self.device.cons.sendline()
                    self._waitForLogin(loginPrompt, timeout)
                    
                    self.device.cons.sendline(user)
                    self.device.cons.expect(ProxyLinuxTSS.PASSWORD_PROMPT, shell.CliTimeout)
                    self.device.cons.sendline(passwd)
                    self.device.cons.expect(shell.CliPrompt, shell.CliTimeout)
                    self.state = ProxySystem.STATE_CLI_PROMPT
                    
                # make sure the prompt is as short as possible, as a long
                # prompt may interfere with further processing if a long prompt
                # causes a command to wrap/line-break when using executeCLICommand
                self.device.cons.sendline('export PS1=%s' % shell.CliPrompt)
                self.device.cons.expect(shell.CliPrompt, shell.CliTimeout) 
            
                # unset all aliases in TSS
                self.device.cons.sendline('unalias -a')
                try:
                    self.device.cons.expect(".*%s" % shell.CliPrompt, shell.CliTimeout) 
                except:
                    pass

                # setup our shell interaction
                self.shell = shell
                self.shell.terminal = self.device.getTerminal()
            except ExceptionPexpect, failure:
                # Timeout or eof either way the login failed.
                self.state = ProxySystem.STATE_UNKNOWN
                raise(FrameworkError(ProxySystem.ERR_LOGIN_ATTEMPT_FAILED, '%s' % failure))
            
        elif (self.state != ProxySystem.STATE_CLI_PROMPT):
            # Nothing to for STATE_CLI_PROMPT but complain if any other state. 
            raise (FrameworkError(ProxySystem.ERR_INVALID_SYSTEM_STATE,
                                  'System state invalid for login() : %s' % self.state))


    def logout(self):
        r"""
        Logout of the system.
        The method will first check that it is in a valid state to logout, then
        perform the logout operation and ensure the system returns to the login
        prompt.  

        @return:
            None, exceptions raised must be derived from L{FrameworkError}
        """
        if (self.state == ProxySystem.STATE_CLI_PROMPT):
            # Should be able to just send a ctrl-d but send a ctrl-c first
            # just in case there is some process running that we can exit
            # and avoid a common error condition.
            try:
                if(self.systemConfig.runMode == SystemConfig.RUN_MODE_CLOUDSTACK):
                    # In cloudstack, a logout is an exit to the ssh call. Thus we don't want to look for the
                    # login prompt at the end.
                    self.shell.sendcontrol(BashShell.CTL_BREAK)
                    self.shell.expect(self.shell.CLI_PROMPT)
                    self.shell.sendcontrol(BashShell.CTL_LOGOUT)
                    self.device.cons = None
                elif(self.systemConfig.runMode == SystemConfig.RUN_MODE_DOCKER):
                    self.shell.sendcontrol(BashShell.CTL_BREAK)
                    self.shell.expect(".*%s" % self.shell.CLI_PROMPT)
                    self.state = ProxySystem.STATE_LOGIN_PROMPT
                    return
                else:
                    self.shell.logout(ProxyLinuxTSS.LOGIN_PROMPT)
                self.state = ProxySystem.STATE_LOGIN_PROMPT
                
                # clean up
                self.shell = None
            except ExceptionPexpect, failure:
                # Timeout of eof either way the logout failed.
                self.state = ProxySystem.STATE_UNKNOWN
                raise(FrameworkError(ProxySystem.ERR_LOGOUT_ATTEMPT_FAILED, '%s' % failure))
            
        elif (self.state != ProxySystem.STATE_LOGIN_PROMPT):
            # Nothing to do for STATE_LOGIN_PROMPT but complain if any other state. 
            raise (FrameworkError(ProxySystem.ERR_INVALID_SYSTEM_STATE,
                                  'System state invalid for logout() : %s' % self.state))


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
        # Make sure we are already logged in
        if (self.state != ProxySystem.STATE_CLI_PROMPT):
            raise (FrameworkError(ProxySystem.ERR_INVALID_SYSTEM_STATE,
                                  'System state invalid for executing CLI command : %s' % self.state))

        try:
            # create a new FileTee to capture the result
            self.shell.terminal.logfile_read = Common.FileTee(diagLevel=self.logger.getEffectiveLevel())
            result = self.shell.executeCLICommand(cmd, cmdTimeout=cmdTimeout)
            
            # this is not nice :/
            # we want to consume the cmd off the front of the buffer, however
            # it may be split over multiple lines, so we walk one char at a time
            # ignoring new lines and white space
            value = self.shell.terminal.logfile_read.getvalue()
            vpos = value.find(cmd[:70])
            cpos = 0
            while (cpos < len(cmd)):
                if (value[vpos] == cmd[cpos]):
                    vpos += 1
                    cpos += 1
                elif (value[vpos] == '\r' or 
                      value[vpos] == '\n' or 
                      value[vpos] == ' '):
                    vpos += 1
                else:
                    break
            
            # eat one trailing new line
            if (value[vpos] == '\r' and value[vpos+1] == '\n'):
                vpos += 2

            # our cmd output is everything after the command
            self.lastCmdOutput = value[vpos:]
            
            return result
        except ExceptionPexpect, failure:
            self.state = ProxySystem.STATE_UNKNOWN
            raise(FrameworkError(ProxySystem.ERR_CLI_FAILED,
                                 '%s' % failure))

    def interact(self, escapeCharacter='\x1d'):
        r"""
        This gives control of the child process to the interactive user (the
        human at the keyboard). Keystrokes are sent to the child process, and
        the stdout and stderr output of the child process is printed.
        
        When the user types the escape_character this method will stop.
        The default for escape_character is ^] (ctrl+']')
        
        @param escapeCharacter:
            The escape character to use to leave interact mode.
        """
        # Make sure we are already logged in
        # if (self.state != ProxySystem.STATE_CLI_PROMPT):
        #     raise (FrameworkError(ProxySystem.ERR_INVALID_SYSTEM_STATE,
        #                           'System state invalid for entering interactive mode : %s' % self.state))

        # self.shell.interact(escapeCharacter=escapeCharacter)

        self.device.cons.interact(escape_character=escapeCharacter)

    def getCidr(self, ip):
        r"""
        Return the cidr address
        @parm ip:
            ip address

        @return:
            network cidr address
        """
        mask = (2L << int(ip.netmaskLength) - 1) - 1
        address = struct.unpack('i', socketHelper.inet_aton(ip.address))[0]
        broadcast = address | ~mask
        networkAddr = address & mask
        networkAddrString = socketHelper.inet_ntoa(struct.pack('i',networkAddr))
        return networkAddrString + '/' + ip.netmaskLength

    def addRoute(self, ip, interface=None, gateway=None):
        r"""
        Setup a route to the specific IP via the specific Interface/Gateway
        
        @param ip:
            The IP to add a route to.
        
        @param interface:
            The interface to associate with the route.
            
        @param gateway:
            The gateway to associate with the route. 
        """

        if NetworkUtil.checkAddressType(ip) == NetworkUtil.TYPE_IPV4:
            option = ' route '
        else:
            option = '-6 route '

        if (interface != None):
            self.executeCLICommand('ip %s add %s dev %s' % (option, ip, interface))
        elif (gateway != None):
            self.executeCLICommand('ip %s add %s via %s' % (option,ip, gateway))
        else:
            raise(CommonError(CommonError.ERR_INVALID_PARAM,
                              "must provide interface or gateway value"))

    def copyFileToSystem(self, hostFile, systemFile, ip=None, user=None, passwd=None):
        r"""
        Refer ProxySystem base class for a description of this interface method.
        """
        # Check the systemFile is not None
        if (systemFile == None or systemFile == ''):
            raise(FrameworkError(ProxySystem.ERR_COPY_FAILED, 
                'System file %s is not valid' % (systemFile)))

        # Check the hostFile exists
        if not os.path.isfile(hostFile):
            raise(FrameworkError(ProxySystem.ERR_COPY_FAILED, 
                'Host file %s does not exist' % (hostFile)))

        # Check IP is not None
        if (ip == None or ip == ''):
            raise(FrameworkError(ProxySystem.ERR_COPY_FAILED, 
                'IP address %s is not valid' % (ip)))
            
        # Adjust username and password
        username = self.systemConfig.installUser
        password = self.systemConfig.installPasswd
        if (user != None):
            username = user
        if (passwd != None):
            password = passwd

        # Build up scp command for file transfer
        cmd = ProxySystem.CMD_FILESCP 
        cmd += ' %s %s@%s:%s' % (hostFile, username, ip, systemFile)
    
        # Spawn host shell, send scp command and test return
        hostCons = pexpect.spawn(ProxySystem.CMD_HOSTSHELL)
        hostCons.sendline(ProxySystem.CMD_HOSTSHELL_PROMPT)
        hostCons.sendline(cmd)
        hostCons.expect_exact(cmd[:70])
        if (self.logger.getEffectiveLevel() <= logging.DEBUG):
            sys.stdout.write('\n[Copying host file %s to system as %s]\n' % 
                (hostFile, systemFile))
            hostCons.logfile_read = sys.stdout
        result = hostCons.expect([ProxyLinuxTSS.REGEX_SCP_PASSWD, 
            ProxySystem.REGEX_HOSTSHELL_SSHERROR, pexpect.TIMEOUT],
            timeout=ProxySystem.FILESCP_TIMEOUT)
        if (result != 0):
            raise(FrameworkError(ProxySystem.ERR_COPY_FAILED, 
                'File transfer network connection failed with TIMEOUT')) 
        hostCons.sendline(password)
        hostCons.expect_exact(ProxySystem.REGEX_HOSTSHELL_PROMPT)
        hostCons.sendline('echo $?')            
        hostCons.expect('[\d]{1,3}')
        result = int(hostCons.after)
        hostCons.expect_exact(ProxySystem.REGEX_HOSTSHELL_PROMPT)
        if (result != 0):
            raise(FrameworkError(ProxySystem.ERR_COPY_FAILED, 
                'File transfer command failed with error code: %d' % (result)))

    def copyFileFromSystem(self, systemFile, hostFile, ip=None, user=None, passwd=None):
        r"""
        Refer ProxySystem base class for a description of this interface method.
        """
        # Check the hostFile is not None
        if (hostFile == None or hostFile == ''):
            raise(FrameworkError(ProxySystem.ERR_COPY_FAILED, 
                'Host file %s is not valid' % (hostFile)))

        # Check IP is not None
        if (ip == None or ip == ''):
            raise(FrameworkError(ProxySystem.ERR_COPY_FAILED, 
                'IP address %s is not valid' % (ip)))
            
        # Adjust username and password
        username = self.systemConfig.installUser
        password = self.systemConfig.installPasswd
        if (user != None):
            username = user
        if (passwd != None):
            password = passwd

        # Build up scp command for file transfer
        cmd = ProxySystem.CMD_FILESCP 
        cmd += ' %s@%s:%s %s' % (username, ip, systemFile, hostFile)
    
        # Spawn host shell, send scp command and test return
        hostCons = pexpect.spawn(ProxySystem.CMD_HOSTSHELL)
        hostCons.sendline(ProxySystem.CMD_HOSTSHELL_PROMPT)
        hostCons.sendline(cmd)
        hostCons.expect_exact(cmd[:70])
        if (self.logger.getEffectiveLevel() <= logging.DEBUG):
            sys.stdout.write('\n[Copying system file %s to host as %s]\n' % 
                (systemFile, hostFile))
            hostCons.logfile_read = sys.stdout
        result = hostCons.expect([ProxyLinuxTSS.REGEX_SCP_PASSWD, 
            ProxySystem.REGEX_HOSTSHELL_SSHERROR, pexpect.TIMEOUT], 
            timeout=ProxySystem.FILESCP_TIMEOUT)
        if (result != 0):
            raise(FrameworkError(ProxySystem.ERR_COPY_FAILED, 
                'File transfer network connection failed with TIMEOUT')) 
        hostCons.sendline(password)
        hostCons.expect_exact(ProxySystem.REGEX_HOSTSHELL_PROMPT)
        hostCons.sendline('echo $?')            
        hostCons.expect('[\d]{1,3}')
        result = int(hostCons.after)
        hostCons.expect_exact(ProxySystem.REGEX_HOSTSHELL_PROMPT)
        if (result != 0):
            raise(FrameworkError(ProxySystem.ERR_COPY_FAILED, 
                'File transfer command failed with error code: %d' % (result)))


    ######
    # ProxyTSS defined interfaces
    ######    

    def setDNS(self, dnsIp):
        r"""
        Set the DNS server of the Linux TSS being proxied.
        
        @param dnsIp:
            The IP address of the DNS server to be set.
        """
        self.executeCLICommand('echo "nameserver %s" > /etc/resolv.conf' % dnsIp)
    
    def setDefaultGateway(self, gwIp):
        r"""
        Set the default gateway of the Linux TSS being proxied.

        @param gwIp:
            The IP address of the default gateway to be set.
        """
        self.executeCLICommand('ip route add default via %s' % gwIp)

    def setDefaultGatewayIpv6(self, gwIpv6):
        r"""
        Set the default gateway of the Linux TSS being proxied.

        @param gwIpv6:
            The IPv6 address of the default gateway to be set.
        """
        self.executeCLICommand('ip -6 route add default via %s' % gwIpv6)

    def enableForwarding(self, inInterface, outInterface):
        r"""
        Enable forwarding of the Linux TSS being proxied.
        
        @param inInterface:
            The ingress interface from which traffic is to be forwarded. 
        
        @param outInterface:
            The egress interface over which traffic is to be forwarded.
        """
        self.executeCLICommand('iptables --append FORWARD --in-interface %s --out-interface %s'
                               % (inInterface, outInterface))
        self.executeCLICommand('iptables --table nat --append POSTROUTING --out-interface %s --jump MASQUERADE'
                               % outInterface)

    def setStaticIp(self, interface, ip, netmaskLength='24', prefixLength='64'):
        r"""
        Set a static IP address for a nominated interface on the Linux TSS being proxied.

        @param interface:
            The interface that the static IP is to be associated with.

        @param ip:
            The IP address that is to be statically assigned to the nominated interface.

        @param netmaskLength:
            IPv4 netmask

        @param prefixLength:
            IPv6 prefix
        """

        if NetworkUtil.checkAddressType(ip) == NetworkUtil.TYPE_IPV4:
            self.executeCLICommand('ip link set dev %s down' % interface)
            self.executeCLICommand('ip addr flush dev %s' % interface)
            self.executeCLICommand('ip addr add dev %s %s/%s' % (interface, ip, netmaskLength))
            self.executeCLICommand('ip link set dev %s up' % interface)
        else:
            self.executeCLICommand('ip -6 addr add dev %s %s/%s' % (interface, ip, prefixLength))


