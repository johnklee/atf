# When booting the Win2008 TSS, the pattern is:
# 1. wait for the "EVENT: The CMD command is now available." output
# 2. enter cmd at the SAC> prompt, ie SAC>cmd
# 3. wait for the "The Command Prompt session was successfully launched." output
# 4. wait for the:
#   "EVENT:   A new channel has been created.  Use "ch -?" for channel help.
#    Channel: Cmd0001" output
# 5. enter the "SAC>ch -si 1" command
# 6. wait for "Username:" prompt and enter "root"
# 7. wait for "Domain:" prompt and enter <enter>
# 8. wait for "Password:" prompt and enter "realsecure"
# 9. wait for CLI prompt, ie: "C:\Windows\system32>"
# 10. at any time enter "Press <esc><tab>0 to return to the SAC channel."

import time
import sys
from pexpect import *
import string
from socket import inet_aton, error

from atf.framework.system.ProxyTSS import *
from atf.framework.system.Shell import *
from atf.common.network.Network import NetworkUtil


class WindowsShell (Shell):
    r"""
    This class encapsulates all the functionality for interacting with
    a Windows system using the sac / cmd interfaces.
    Note that due to limitations in the interactions between pexpect and the Windows console,
    we can only use expect to check for text on the final screen, 25 lines, of output.
    """
    ###
    # Define common expect patterns and timeouts
    ###
    (INIT_CLI_PROMPT) = 'system32>'
    """The ending of the windows cmd prompt before we change it"""
    (CLI_PROMPT) = '&wintss&'
    """Windows cmd CLI prompt string for expect."""
    (CONSOLE_PROMPT) = 'SAC>'
    """Prompt for the system console"""
    (INVALID_LOGIN_MSG) = 'Unable to authenticate.'
    """Message when login authentication fails"""
    (HALTED_MSG) = 'The computer is shutting down.'
    """Pattern expected at the halt of a system."""
    (SHUTTING_DOWN_MSG) = 'preparing to shutdown the system.'
    """Pattern expected during the halt of a system."""
    (RESTARTING_MSG) = 'The computer is shutting down'
    """Pattern expected during the restart of a system."""
    (CMD_READY_EVENT) = 'The CMD command is now available'
    """Pattern expected when the TSS is ready to start a cmd shell"""
    (CHANNEL_CREATED_EVENT) = 'EVENT:\s*A new channel has been created..*for channel help.'
    """Pattern expected when the TSS has started a cmd shell"""
    (RETURN_TO_SAC_MSG) = 'Use any other key to view this channel'
    """Pattern expected when the TSS has exited a cmd shell and is ready to return to the SAC"""
    (CLI_RESPONSE_TIMEOUT) = 20 * RunConfig.TIMEOUT_MULTIPLIER
    """Expect timeout associated with the execution of commands."""

    ###
    # Define literal commands used at the CLI to make it easy to change in future.
    ###
    (CMD_HALT) = 'shutdown'
    """Command used for system halt."""
    (CMD_REBOOT) = 'shutdown -r'
    """Command used for system reboot."""
    (CMD_EXIT) = 'exit'
    """Command used to exit from the cmd shell back to the console"""
    (CMD_PROMPT) = 'PROMPT $Awintss$A'
    """Command to set the cmd shell prompt to &wintss&, ie CLI_PROMPT"""

    ###
    # Define control characters as well
    ###
    (CTL_BREAK) = 'c'   # Break 
    """Command used for execution break."""
    (KEY_ENTER) = '\r\n'
    """Windows <enter> is return+newline"""

    def __init__(self, diagLevel = logging.ERROR):
        r"""
        Define particulars about the shell's characteristics.
        
        @param diagLevel:
            The logging level at which the class will operate.
        """
        Shell.__init__(self, diagLevel = diagLevel)

        self.consolePrompt = WindowsShell.CONSOLE_PROMPT
        """The Windows SAC prompt"""
        self.InitCliPrompt = WindowsShell.INIT_CLI_PROMPT
        """The initial CLI prompt, before we change it"""
        self.CliPrompt = WindowsShell.CLI_PROMPT
        """The string the CLI Prompt should be set to."""
        self.CliTimeout = WindowsShell.CLI_RESPONSE_TIMEOUT
        """The expect timeout the CLI Prompt should be associated with."""
        self.getRetCode = r'echo ErrorLvl %ERRORLEVEL%'
        self.echoRetCode = r'ErrorLvl %ERRORLEVEL%'
        self.expectLogFile = file('/var/log/WindowsShell.log', 'w')
        self.ansiLogFile = file('/var/log/WindowsAnsi.log', 'w')

    def _expectLog(self, prePost):
        logEntry = '\nbuffer %s-process is Z%sZ' % (prePost, self.terminal.buffer)
        self.log(self.ansiLogFile, self._removeUnprintables(logEntry))
        logEntry = '\n\nbefore & after %s-process are Z%sZ \nZ%sZ' % (prePost, self.terminal.before, self.terminal.after)
        self.log(self.expectLogFile, self._removeUnprintables(logEntry))

    def _removeUnprintables(self, inStr):
        return ''.join(outStr for outStr in inStr if outStr in string.printable)

    def log(self, logFile, logEntry):
        if (self.logger.getEffectiveLevel() <= logging.DEBUG):
            logFile.write('\nFFFFFFFFFFFFFFF')
            logFile.write(logEntry)
            logFile.flush()

    def shutdown(self, timeout):
        r"""
        Shutdown the system.
        
        @param timeout:
            The timeout associated with the system halt command execution.
        """
        self.sendline(WindowsShell.CMD_HALT)
        self.expect(WindowsShell.HALTED_MSG, timeout = timeout)
        self.ansiLogFile.flush()
        self.expectLogFile.flush()
        self.ansiLogFile.close()
        self.expectLogFile.close()

    def reboot(self, timeout):
        r"""
        Reboot the system.
        
        @param timeout:
            The timeout associated with the system reboot command execution.
        """
        self.sendline(WindowsShell.CMD_REBOOT)
        self.expect(WindowsShell.RESTARTING_MSG, timeout = timeout)

    def logout(self, loginPrompt, timeout = CLI_RESPONSE_TIMEOUT):
        r"""
        Logout from the system.
       
        @param loginPrompt:
            The login prompt to expect during the execution of a logout. 
        
        @param timeout:
            The timeout associated with the system logout command execution.
        """
        self.log(self.expectLogFile, "*** WindowsShell logout")
        self.send(WindowsShell.KEY_ENTER)
        self.expect(self.CliPrompt, timeout = timeout)
        self.sendline(WindowsShell.CMD_EXIT)
        self.expect(WindowsShell.RETURN_TO_SAC_MSG, timeout = timeout)
        self.sendline()
        self.expect(WindowsShell.CONSOLE_PROMPT, timeout = timeout)

    def sendline(self, s=''):
        r"""
        This sends a string to the terminal, followed by a carriage return / line feed.
        This returns the number of bytes written.
        
        Refer to pexpect.spawn.expect for more details.
        
        @param s:
            The string to send to the terminal.
        """
        if (self.terminal == None):
            raise (FrameworkError(Shell.ERR_INVALID_TERMINAL, 'shell referencing invalid terminal'))

        s1 = s + WindowsShell.KEY_ENTER
        logEntry = '\nabout to send [%s] to Windows TSS terminal' % s1
        self.log(self.expectLogFile, logEntry)
        return self.send(s1)

    def expect(self, pattern, timeout = -1, searchwindowsize = None):
        r"""
        This seeks through the stream until a pattern is matched.
        
        Refer to pexpect.spawn.expect for more details.
        
        @param pattern:
            The pattern to match in the stream being searched
        
        @param timeout:
            The timeout to associate with the pattern matching execution
        
        @param searchwindowsize:
            Indicates how far back in the incoming search buffer 
            Pexpect will search for pattern matches.
            Current limitation: can only search in the current screen, ie 25 lines.
        """

        ret = pexpect.TIMEOUT
        self.log(self.expectLogFile, '\nexpecting %s' % pattern)
        try:
            self._expectLog('pre')
            ret = super(WindowsShell, self).expect(pattern,
                                                   timeout=timeout,
                                                   searchwindowsize=searchwindowsize)
            self._expectLog('post')
        except TypeError, te:
            #ignore type errors
            logEntry = '\nIgnoring type error [ %s ] in expect' % te
            self.log(self.expectLogFile, logEntry)
            self._expectLog('post')
        return ret

    def expect_exact(self, pattern_list, timeout = -1, searchwindowsize = -1):
        r"""
        This is similar to expect(), but uses plain string matching instead
        of compiled regular expressions in 'pattern_list'.
        
        Refer to pexpect.spawn.expect_exact for more details.
        
        @param pattern_list:
            A plain string match instead of compiled regular expressions 
            in a 'pattern_list'. The 'pattern_list' may be a string; a list 
            or other sequence of strings; or TIMEOUT and EOF.
        
        @param timeout:
            The timeout to associate with the pattern matching execution
        
        @param searchwindowsize:
            Indicates how far back in the incoming search buffer 
            Pexpect will search for pattern matches. 
            Current limitation: can only search in the current screen, ie 25 lines.
        """
        ret = pexpect.TIMEOUT
        self.log(self.expectLogFile, '\nexpecting exact %s' % pattern_list)
        try:
            self._expectLog('pre')
            ret = super(WindowsShell, self).expect_exact(pattern_list,
                                                   timeout=timeout,
                                                   searchwindowsize=searchwindowsize)
            self._expectLog('post')
        except TypeError, te:
            #ignore type errors
            logEntry = '\nIgnoring type error [ %s ] in expect_exact' % te
            self.log(self.expectLogFile, logEntry)
            self._expectLog('post')

        return ret

    def executeCLICommand(self, cmd, cmdTimeout=None):
        r"""
        Execute a command and return the status result of that command.

        @param cmd:
            The command to be executed

        @param cmdTimeout:
            The timeout associated with the system command execution.
        """
        #initialise result to some random value
        result = 13
        # allow terminal to clear the buffer
        time.sleep(3)
        self.sendline(cmd)
        self.log(self.expectLogFile, "--- expect buffer start ---")
        self.log(self.expectLogFile, self.terminal.buffer)
        self.log(self.expectLogFile, "--- expect buffer end ---")
        if (cmdTimeout != None):
            self.log(self.expectLogFile, "WindowsShell executeCLICommand, cmd = [ %s ], timeout = [ %d ]" % (cmd, cmdTimeout))
            self.expect_exact(pattern_list=self.CliPrompt, timeout=cmdTimeout)
        else:
            self.log(self.expectLogFile, "WindowsShell executeCLICommand, cmd = [ %s ], timeout = None" % cmd)
            self.expect_exact(pattern_list=self.CliPrompt)
        #get command return code (ie ERRORLEVEL)
        retCode = re.compile('ErrorLvl [\d]{1,4}', re.MULTILINE)
        #use a string ErrorLvl as a marker, coz the ANSI terminal characters make grep'ing for 1 to 3 
        # digits only almost impossible
        logEntry = 'return code strings are [%s] [%s]' % (self.getRetCode, self.echoRetCode)
        self.log(self.expectLogFile, logEntry)
        self.sendline(self.getRetCode)
        self.expect_exact(self.echoRetCode, timeout=pexpect.TIMEOUT)
        i = self.expect([retCode, pexpect.TIMEOUT])
        if (i == 1):
            logEntry = 'timeout: before & after are Z%sZ Z%sZ' % (self.terminal.before, self.terminal.after)
            self.log(self.expectLogFile, self._removeUnprintables(logEntry))
        else:
            logEntry = 'before & after are Z%sZ Z%sZ' % (self.terminal.before, self.terminal.after)
            self.log(self.expectLogFile, self._removeUnprintables(logEntry))
            searchResult = re.search('[\d]{1,4}', self.terminal.after).group(0)
            logEntry = 'searchResult is [%s]' % searchResult
            self.log(self.expectLogFile, logEntry)
            result = int(searchResult)
            # Make sure displaying CLI prompt for the subsequent command
            self.log(self.expectLogFile, 'sending echo')
            self.sendline('echo')
            self.expect_exact(self.CliPrompt)            

        #reset expect buffer
        self.log(self.expectLogFile, 'cleaning up expect buffer')
        self.terminal.buffer = ''
        #send windows cmd clear screen command to display CLI prompt for the subsequent command
        self.sendline(r'cls')
        self.expect_exact(self.CliPrompt)
        return (result)


class ProxyWindows2k8TSS(ProxyTSS):
    r"""
    The ProxyWindows2k8TSS class extends the ProxyTSS class to include methods
    that must be implemented by all proxies supporting Windows bound Test System
    Support services. 
    """
    ###
    # Define common expect patterns and timeouts
    ###
    (LOGIN_PROMPT) = 'Username: '
    """Pattern expected at the username entry during the login of a system."""
    (DOMAIN_PROMPT) = 'Domain  :'
    """Pattern expected after entering a username during login"""
    (PASSWORD_PROMPT) = 'Password: '
    """Pattern expected at the password entry during the login of a system."""
    (DEFAULT_DOMAIN) = 'TESTDOMAIN001'
    """The default Windows Domain for our Windows2k8 Server TSS"""
    (CHANNEL_ATTACH_FAIL) = 'Error:\s*There is no channel present at the specified index.'
    """Pattern expected on failure to attach to a command channel"""
    (CHANNEL_ATTACH_SUCCESS) = 'Please enter login credentials'
    """Pattern expected on successfully attaching to a command channel"""

    (BOOT_TIMEOUT) = 180 * RunConfig.TIMEOUT_MULTIPLIER
    """Expect timeout associated with the boot of a system."""
    #was 60 * when using -nographic qemu option
    (STATE_CMD_READY) = 100
    """Windows system is at the SAC prompt and ready to start a cmd shell"""

    (TERMINAL_PARSER) = "stripANSI.py"
    """Windows terminal parser. Remove all ANSI ESC characters from Windows console output"""

    def __init__(self, tssConfig = None, diagLevel = logging.ERROR):
        r"""
        Save config and diagnostics output details

        @param tssConfig:
            A pre-constructed SystemConfig object
            
        @param diagLevel:
            What debug level to run this object in.
        """
        ProxyTSS.__init__(self, tssConfig, diagLevel)
        self.state = ProxySystem.STATE_INITIALISED

    def _validateIPFormat(self, *ip):
        '''
        Check IP address format.
        
        @param ip:
            IP address or addresses to check
        '''
        try:
            map(inet_aton, ip)
        except error, failure:
            raise (FrameworkError(ip, '%s : %s' % (failure, ip)))

    def _waitForSac(self, consolePrompt, cmdReadyEvent, timeout):
        '''
        Wait until the TSS is at the SAC> prompt and can start a cmd shell
        
        @param consolePrompt:
            The login prompt to expect after the execution of a login. 
            
        @param cmdReadyEvent:
            The string output to the console when the TSS is ready to start a cmd shell
        
        @param timeout:
            The timeout associated with the system login.
        '''
        # If the TSS has been configured correctly then there is
        # no boot menu, so we should just go straight to the console prompt.
        #
        self.device.cons.expect(consolePrompt, timeout = timeout)
        #after the console prompt, we should get a "ready to start a cmd shell prompt"
        self.device.cons.expect(cmdReadyEvent, timeout = timeout)
        self.state = ProxyWindows2k8TSS.STATE_CMD_READY

        # send a new line so that the login prompt appears again - just in case
        # a test client is waiting for it
        self.device.cons.sendline()

    def _startCmd(self, cmdStartedEvent, consolePrompt, timeout):
        '''
        Start a cmd shell & switch to it
        
        @param cmdStartedEvent:
            The string output to the console when the TSS is ready to start a cmd shell

        @param consolePrompt:
            The login prompt to expect after the execution of a login. 
            
        @param timeout:
            The timeout associated with the system login.
        '''
        if (self.state != ProxyWindows2k8TSS.STATE_CMD_READY):
            raise (FrameworkError(ProxySystem.ERR_INVALID_SYSTEM_STATE,
                                  'System state invalid for cmd start : %s'
                                  % self.state))

        # now we can start our cmd shell; this start is retried in a fixed
        # number loop
        attempts = 10
        while (attempts > 0):
            self.device.cons.sendline('cmd')
            self.device.cons.expect(cmdStartedEvent, timeout = timeout)
            #wait for console prompt
            self.device.cons.expect(consolePrompt, timeout = timeout)
            # See channel list
            self.device.cons.sendline('ch')
            # wait for console prompt
            self.device.cons.expect(consolePrompt, timeout = timeout)
            # switch to the cmd shell (or channel in SAC parlance)
            switchChannelCmd = "ch -si 1"
            self.device.cons.sendline(switchChannelCmd)
            # need to send a blank line to get to login prompt
            self.device.cons.sendline()
            # check result for "ch -si 1"
            result = self.device.cons.expect([ProxyWindows2k8TSS.CHANNEL_ATTACH_SUCCESS, ProxyWindows2k8TSS.CHANNEL_ATTACH_FAIL, pexpect.TIMEOUT], timeout = timeout)

            if (result == 0):
                break
            else:
                attempts -=1
                time.sleep(1)
                continue


    def _waitForLogin(self, loginPrompt, timeout):
        '''
        Wait until the TSS has finished booting
        
        @param loginPrompt:
            The login prompt to expect after the execution of a login. 
        
        @param timeout:
            The timeout associated with the system login.
        '''
        # If the TSS has been configured correctly then there is
        # no boot menu, so we should just go straight to the console prompt.
        #
        # So all we can really do is wait for the login prompt.
        self.device.cons.expect(loginPrompt, timeout = timeout)
        self.state = ProxySystem.STATE_LOGIN_PROMPT


    def _SACLogin(self):
        #wait for the SAC prompt, then start a Windows cmd shell
        self._waitForSac(WindowsShell.CONSOLE_PROMPT, WindowsShell.CMD_READY_EVENT, self.BOOT_TIMEOUT)
        #start Windows cmd shell
        self._startCmd(WindowsShell.CHANNEL_CREATED_EVENT, WindowsShell.CONSOLE_PROMPT, self.BOOT_TIMEOUT)
        #wait for our windows login prompt
        self._waitForLogin(self.LOGIN_PROMPT, self.BOOT_TIMEOUT)


    ######
    # ProxySystem defined interfaces
    ######    

    def powerOn(self, packageType = None):
        r"""
        Perform Device start and make sure the System comes up into a valid
        L{ProxySystem.STATE_STARTING}. This involves:
            1. waiting for SAC prompt
            2. starting a cmd shell
            3. switching to the cmd shell
            4. waiting for a login prompt

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

        # Add windows terminal parser option to the config
        
        if  self.device.config != None:
            self.device.config.extraOptions += '-z %s' % ProxyWindows2k8TSS.TERMINAL_PARSER
        

        # a test support system is currently a complete system disk, as such
        # there is no need to support additional media/packageType/productPackage
        productPackage = None
        if (packageType != None):
             raise (FrameworkError(ProxyTSS.ERR_UNSUPPORTED_PACKAGE_TYPE,
                                   'Unsupported packageType specified : %s' % packageType))


        self.device.start(productPackage = packageType)
        #wait for SAC prompt, start cmd shell, wait for login prompt
        self._SACLogin()

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
            #exit to the SAC prompt
            #first send 'exit' to the cmd shell
            #DEBUG
            self.shell.sendline(WindowsShell.CMD_EXIT)
            #wait for the prompt to get back to SAC
            self.device.cons.expect(WindowsShell.RETURN_TO_SAC_MSG,
                                    timeout = WindowsShell.CLI_RESPONSE_TIMEOUT)
            #hit any key to get to the SAC prompt
            self.device.cons.sendline('a')
            #wait for SAC prompt
            self.device.cons.expect(WindowsShell.CONSOLE_PROMPT,
                                    timeout = WindowsShell.CLI_RESPONSE_TIMEOUT)
            #now we can shutdown
            self.shell.shutdown(ProxyWindows2k8TSS.BOOT_TIMEOUT)
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
            self.shell.reboot(ProxyWindows2k8TSS.BOOT_TIMEOUT)
            self.state = ProxySystem.STATE_STARTING

            # clean up
            self.shell = None
            self.services = {}
            self._SACLogin()
        except ExceptionPexpect, failure:
            self.state = ProxySystem.STATE_UNKNOWN
            raise(FrameworkError(ProxySystem.ERR_REBOOT_FAILED, '%s' % failure))


    def login(self, user, passwd,
              timeout = WindowsShell.CLI_RESPONSE_TIMEOUT,
              loginPrompt = LOGIN_PROMPT,
              shell = None):
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
            shell = WindowsShell(diagLevel = self.logger.getEffectiveLevel())

        if (self.state == ProxySystem.STATE_LOGIN_PROMPT):
            try:
                # setup our shell interaction
                self.shell = shell
                self.shell.terminal = self.device.getTerminal()

                # We are at a login prompt, send the username
                self.shell.sendline(user)
                self.shell.expect(ProxyWindows2k8TSS.DOMAIN_PROMPT, shell.CliTimeout)
                #enter nothing for the domain
                self.shell.sendline()
                self.shell.expect(ProxyWindows2k8TSS.PASSWORD_PROMPT, shell.CliTimeout)
                self.shell.sendline(passwd)
                auth = self.shell.expect([shell.InitCliPrompt, WindowsShell.INVALID_LOGIN_MSG],
                                  timeout = shell.CliTimeout)
                if (auth == 0):
                    #authentication passed
                    self.state = ProxySystem.STATE_CLI_PROMPT

                    # make sure the prompt is as short as possible, as a long
                    # prompt may interfere with further processing if a long prompt
                    # causes a command to wrap/line-break when using executeCLICommand
                    #set prompt to '&wintss&'
                    self.shell.sendline(WindowsShell.CMD_PROMPT)
                    #make sure that we have consumed all command line output
                    self.shell.expect_exact(shell.CliPrompt, shell.CliTimeout)
                elif (auth == 1):
                    #authentication failed, get back to login prompt
                    self.shell.sendline()
                    self.shell.sendline()
                    #wait for SAC prompt, start cmd shell, wait for login prompt
                    self._SACLogin()
                    #now raise login failed exception
                    raise(FrameworkError(ProxySystem.ERR_LOGIN_ATTEMPT_FAILED, 'authentication failed'))

                #FIXME: is the windows analogy required?
                # unset all aliases in TSS
                #self.device.cons.sendline('unalias -a')


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
                self.shell.log(self.shell.expectLogFile, "*** ProxyWindows logout")
                self.shell.logout(ProxyWindows2k8TSS.LOGIN_PROMPT)
                self.state = ProxyWindows2k8TSS.STATE_CMD_READY
                #start Windows cmd shell
                self._startCmd(WindowsShell.CHANNEL_CREATED_EVENT,
                               WindowsShell.CONSOLE_PROMPT, self.BOOT_TIMEOUT)

                #wait for our windows login prompt
                self._waitForLogin(self.LOGIN_PROMPT, self.BOOT_TIMEOUT)
                #set appropriate state
                self.state = ProxySystem.STATE_LOGIN_PROMPT

                # clean up
                self.shell = None
                self.services = {}
            except ExceptionPexpect, failure:
                # Timeout or eof either way the logout failed.
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
            logEntry = '\nexecuteCLICommand is Z%sZ' % cmd
            self.shell.log(self.shell.expectLogFile, logEntry)
            return self.shell.executeCLICommand(cmd=cmd, cmdTimeout=cmdTimeout)
        except ExceptionPexpect, failure:
            logEntry = '\nException: before & after are Z%sZ Z%sZ' % (self.shell.terminal.before, self.shell.terminal.after)
            self.shell._removeUnprintables(logEntry)
            self.shell.log(self.shell.expectLogFile, logEntry)
            self.state = ProxySystem.STATE_UNKNOWN
            raise(FrameworkError(ProxySystem.ERR_CLI_FAILED, '%s' % failure))

    def interact(self, escapeCharacter = '\x1d'):
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
        if (self.state != ProxySystem.STATE_CLI_PROMPT):
            raise (FrameworkError(ProxySystem.ERR_INVALID_SYSTEM_STATE,
                                  'System state invalid for entering interactive mode : %s' % self.state))

        self.shell.interact(escapeCharacter = escapeCharacter)

    def addRoute(self, dstIP, subMask, gwIP):
        r"""
        Setup a route to the specific IP via the specific Interface/Gateway
        
        @param dstIP:
            The IP to add a route to.
        
        @param subMask:
            The subnetwork mask.
            
        @param gwIP:
            The gateway IP to associate with the route. 
        """
        self._validateIPFormat(dstIP, subMask, gwIP)
        self.executeCLICommand('route ADD %s MASK %s %s' % (dstIP, subMask, gwIP))

    def setDNS(self, dnsIp):
        r"""
        Set the DNS server of the Linux TSS being proxied.
        
        @param dnsIp:
            The IP address of the DNS server to be set.
        """
        self._validateIPFormat(dnsIp)
        self.executeCLICommand('netsh interface ip set dns "Local Area Connection 2" static %s' % dnsIp)

    def enableForwarding(self, inInterface, outInterface):
        r"""
        Enable forwarding of the Linux TSS being proxied.
        
        @param inInterface:
            The ingress interface from which traffic is to be forwarded. 
        
        @param outInterface:
            The egress interface over which traffic is to be forwarded.
        """
        raise (NotImplementedError())

    def setStaticIp(self, interface, ip, netmaskLength="255.255.255.0", prefixLength="64", gateway=None):
        r"""
        Set a static IP address for a nominated interface on the Windows 2k8 TSS being proxied.

        @param interface:
            The code name for the interface, in the form LACn

        @param ip:
            The IP address that is to be statically assigned to the nominated interface.

        @param netmaskLength:
            IPv4 netmask

        @param prefixLength:
            IPv6 prefix

        @param gateway:
            The IP address default gateway
        """

        logEntry = "setStaticIp for interface %s & ip %s" % (interface, ip)
        self.shell.log(self.shell.expectLogFile, logEntry)
        #use the interface number passed in or 3 by default
        if(len(interface) == 4):
            interfaceNo = interface[3]
        else:
            interfaceNo = '3'
            logEntry = "using default interface, LAC3, in setStaticIp"
            self.shell.log(self.shell.expectLogFile, logEntry)

        if  NetworkUtil.checkAddressType(ip) == NetworkUtil.TYPE_IPV4:
            self._validateIPFormat(ip)
            cmd = 'netsh int ipv4 set add "Local Area Connection %c" static %s %s' % (interfaceNo, ip, netmaskLength)

            if gateway != None:
                cmd += ' %s' % gateway
            self.executeCLICommand(cmd, WindowsShell.CLI_RESPONSE_TIMEOUT)
        else:
            cmd = 'netsh int ipv6 set address "Local Area Connection %c" %s/%s' % (interfaceNo, ip, prefixLength)
            self.executeCLICommand(cmd, WindowsShell.CLI_RESPONSE_TIMEOUT)

            # Set IPv6 default gateway
            if gateway != None:
                cmd = 'netsh int ipv6 add route ::/0  "Local Area Connection %c" %s' % (interfaceNo, gateway)
                self.executeCLICommand(cmd, WindowsShell.CLI_RESPONSE_TIMEOUT)

