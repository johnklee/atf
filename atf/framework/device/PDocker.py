import logging
import pexpect
import signal
import subprocess
import json
import sys
import os

import atf.common.Common as Common
import docker

from atf.common.docker.client import DockerAgent
from atf.framework.device.state.DockerImgState import *
from datetime import datetime
from atf.framework.FrameworkBase import *
from ProxyDevice import *
from atf.common.utils.dspawn import dspawn


class Shell(FrameworkBase):
    r"""
    A shell is an interactive command line interpreter - think Bash Shell.
    
    It is typically accessed via either a local console session or a 
    remote tty session - either way the user is required to set the 
    terminal attribute before using a Shell instance.
    
    In terms of implementation, the underlying terminal is a pexpect.spawn
    object, so users of a Shell should be familiar with that class as well.
    """

    ###
    # Class error definitions
    ### 
    (ERR_INVALID_TERMINAL)  = FrameworkError.ERR_SHELL
    """terminal not set or invalid"""

    def __init__(self, diagLevel=logging.ERROR):
        r"""
        Constructor.
        
        Note that a shell is not useable after construction, the terminal
        attribute needs to be set to a pexpect.spawn object.
        
        @param diagLevel:
            What debug level to run this object in.
        """
        FrameworkBase.__init__(self, diagLevel=diagLevel)

        self.terminal = None
        """pexpect spawn object that this shell uses."""

    def read (self, size=-1):
        r"""
        This reads at most "size" bytes from the file (less if the read hits
        EOF before obtaining size bytes).
        
        Refer to pexpect.spawn.expect for more details.
        
        @param size:
            The number of bytes to read from the terminal.
        """
        if (self.terminal == None):
            raise (FrameworkError(Shell.ERR_INVALID_TERMINAL, 'shell referencing invalid terminal'))

    def readline (self, size=-1):
        r"""
        This reads and returns one entire line. A trailing newline is kept
        in the string, but may be absent when a file ends with an incomplete
        line.
        
        Refer to pexpect.spawn.expect for more details.
        
        @param size:
            The number of bytes to read from the terminal.
        """
        if (self.terminal == None):
            raise (FrameworkError(Shell.ERR_INVALID_TERMINAL, 'shell referencing invalid terminal'))

        return self.terminal.readline(size=size)

    def send(self, s):
        r"""
        This sends a string to the terminal.
        This returns the number of bytes written.
        
        Refer to pexpect.spawn.expect for more details.
        
        @param s:
            The string to send to the terminal.
        """
        return self.terminal.send(s)

    def sendline(self, s=''):
        r"""
        This sends a string to the terminal, followed by a line feed.
        This returns the number of bytes written.
        
        Refer to pexpect.spawn.expect for more details.
        
        @param s:
            The string to send to the terminal.
        """
        if (self.terminal == None):
            raise (FrameworkError(Shell.ERR_INVALID_TERMINAL, 'shell referencing invalid terminal'))

        return self.terminal.sendline(s)

    def sendcontrol(self, char):
        r"""
        This sends a control character to the child such as Ctrl-C or
        Ctrl-D. For example, to send a Ctrl-G (ASCII 7)::
            sendcontrol('g')
            
        Refer to pexpect.spawn.expect for more details.
        
        @param char:
            The controlled character to the terminal.
        """
        if (self.terminal == None):
            raise (FrameworkError(Shell.ERR_INVALID_TERMINAL, 'shell referencing invalid terminal'))

        return self.terminal.sendcontrol(char)

    def expect(self, pattern, timeout = -1, searchwindowsize=None):
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
        """
        if (self.terminal == None):
            raise (FrameworkError(Shell.ERR_INVALID_TERMINAL, 'shell referencing invalid terminal'))

        return self.terminal.expect(pattern,
                                    timeout=timeout,
                                    searchwindowsize=searchwindowsize)

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
        """
        if (self.terminal == None):
            raise (FrameworkError(Shell.ERR_INVALID_TERMINAL, 'shell referencing invalid terminal'))

        return self.terminal.expect_exact(pattern_list,
                                          timeout=timeout,
                                          searchwindowsize=searchwindowsize)

    def executeCLICommand(self, cmd, cmdTimeout=None):
        r"""
        Execute a command and return the status result of that command.
        
        Note that all output of the command is consumed, in search of the
        command prompt.
        
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
        The default for escape_character is ^] (ctrl+']')
        
        @param escapeCharacter:
            The escape character to use to leave interact mode.
        """
        self.terminal.interact(escape_character=escapeCharacter)

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

    def __init__(self, diagLevel=logging.ERROR, terminal=None):
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
        if terminal:
            self.terminal = terminal
        """The pexpect object"""

    def executeCLICommand(self, cmd, cmdTimeout=None):
        r"""
        Execute a command and return the status result of that command.
        
        @param cmd:
            The command to be executed.
        
        @param cmdTimeout:
            The timeout associated with the system command execution.

        @return:
            Tuple(return code, stdout+stderr)
        """
        self.sendline(cmd)
        # We match the first 70 characters in the cmd as otherwise expect
        # get confused with the line breaking of output.
        self.expect_exact(cmd[:70])
        if (cmdTimeout != None):
            self.expect_exact(self.CliPrompt, timeout=cmdTimeout)
        else:
            self.expect_exact(self.CliPrompt)

        out = self.terminal.logfile_read.getvalue()
        self.sendline('echo $?')
        self.expect('[\d]{1,3}')
        result = int(self.terminal.after)
        self.expect_exact(self.CliPrompt)
        return (result, out)
        
class PDocker(FrameworkBase):
    r"""
    The PDocker class supports the ProxyDevice interface to control the Virtual Machine.
    """    
    (ENV_BASH_TYPE) = 'BASH_TYPE'
    (ENV_BASH_TYPE_DOCKER) = '___docker___'   
 
    (CONTAINER_STATUS_PATH) = '/tmp/CONTAINER_STATUS'
    """ Path to file which will hold service status from container (0:Ready, 1:Starting, 2:Stopping, 3:Stopped) """

    (CMD_BASH) = "bash"

    (CMD_BASH_ROOT) = "bash -c 'cd /root && bash'"
    """ BASH interpreter """

    (DOCKER_ENV) = ""
    (CMD_DOCKER) = DOCKER_ENV + "docker"
    """ BASH interpreter """

    (DOCKER_EXEC) = CMD_DOCKER + " exec -t -i --privileged %s %s"

    def __init__(self,  diagLevel=logging.WARNING, dkClient=None):
        r"""
        Refer base class for a description of this interface method.
        
        @param dkConfig:
            A pre-constructed EmulatorConfig object
            
        @param diagLevel:
            What debug level to run this object in.
            
        @param dkClient:
            Docker client 
        """
        FrameworkBase.__init__(self, diagLevel)
        if dkClient is None:
            dkClient = DockerAgent()

        self.dkClient = dkClient
        self.container = None
        self.ecli = self.executeCLICommand

    def __del__(self):
        r"""
        Try and make sure that qrun gets a chance to cleanup by
        sending it a signal before exit.
        """
        if (hasattr(self, "container") and self.container) :
            self.stop()
        
        
    def spawn_container_shell(self, container, shell=None):
        r'''
        Spawn a pexpect object of shell in running container.
        '''
        if isinstance(container, dict):
            container = container.get('Id')

        if isinstance(container, str) == False:
            container = str(container)

        if shell:
            sh = shell
        else:
            sh = dspawn(PDocker.CMD_BASH) 

        try:
            cmd = PDocker.DOCKER_EXEC % (container, PDocker.CMD_BASH_ROOT)
            sh.sendline(cmd)
            sh.expect('.*#', timeout=20)
            if sh.after.find('Cannot run exec command') != -1: raise
            sh.sendline("echo $%s" % PDocker.ENV_BASH_TYPE)
            sh.expect('.*#', timeout=3)
            if sh.after.find(PDocker.ENV_BASH_TYPE_DOCKER) == -1: raise
        except:
            cmd = PDocker.DOCKER_EXEC % (container, PDocker.CMD_BASH_ROOT)
            sh.sendline(cmd)
            sh.expect('.*#', timeout=20)
            if sh.after.find('Cannot run exec command') != -1:
                raise errors.DockerException('Failed to do: %s' % cmd )
            sh.sendline("echo $%s" % PDocker.ENV_BASH_TYPE)
            sh.expect('.*#', timeout=3)
            if sh.after.find(PDocker.ENV_BASH_TYPE_DOCKER) == -1:
                raise errors.DockerException('Failed to do: %s' % cmd )

        sh.set_unique_prompt()

        return sh

    def start(self, image):
        r"""
        Start the container from given image

        @param image(str):
            Name/ID of image
            
        @return:
            None, Can raise L{FrameworkError} exceptions
        """                
        self.start_begin=datetime.now()
            
        self.logger.debug("Using image: %s" % image)
        img = image
        self.hostShell = dspawn(PDocker.CMD_BASH)


        # Start container from image
        host_config = self.dkClient.apiClient.create_host_config(privileged=True, publish_all_ports=True)
        try:           
            self.container = self.dkClient.run(image=image, host_config = host_config, 
                                               environment={'PPID':os.getpid(), 'SSHD_PORT':22, 
                                                            PDocker.ENV_BASH_TYPE:PDocker.ENV_BASH_TYPE_DOCKER}) 
            #self.container=self.dkClient.run(detach=True, 
            #                                 image=img, 
            #                                 network_disabled=False, 
            #                                 privileged=True, 
            #                                 mem_limit=mem_limit,
            #                                 publish_all_ports=True,
            #                                 tty=True,
            #                                 name=self.config.imgInfo.systemType,
            #                                 environment={'PPID':os.getpid(), 'VNC_PASSWORD':self.config.host_passwd,'SSHD_PORT':22})
        except docker.errors.APIError as e:
            self.container = self.dkClient.run(image=image, host_config = host_config,
                                               environment={'PPID':os.getpid(), 'SSHD_PORT':22, 
                                                            PDocker.ENV_BASH_TYPE:PDocker.ENV_BASH_TYPE_DOCKER}, 
                                               tty=True, command=PDocker.CMD_BASH)
            #self.container=self.dkClient.run(detach=True, 
            #                                 image=img, 
            #                                 network_disabled=False, 
            #                                 privileged=True, 
            #                                 publish_all_ports=True,
            #                                 name=self.config.imgInfo.systemType,
            #                                 environment={'PPID':os.getpid(), 'VNC_PASSWORD':self.config.host_passwd,'SSHD_PORT':22}, command=Client.CMD_BASH, tty=True)
            if self.container == None:
                raise (FrameworkError(ProxyDevice.ERR_FAILED_DOCKER_RUN,
                                      "Fail to start container from image='%s':\n%s\n" % (img, e)))
        except:            
            if hasattr(self, 'container') and self.container:
                self.logger.debug("Remove temporal container=%s..." % self.container)
                self.dkClient.remove_container(container=self.container)
            #raise (FrameworkError(ProxyDevice.ERR_FAILED_DOCKER_RUN,
            #                      "Fail to start container from image='%s'!" % (img)))
            raise
        self.logger.debug("Launched Container: %s" % self.container['Id'])

        # This is necessary until we can figure out why attaching to container does not always succeed in a nested jail
        cnt = 0
        maxTry = 10
        while cnt < maxTry:
            cnt += 1
            self.logger.debug("%d: docker exec: %s" % (cnt, self.container['Id']))
            try:
                self.cons=self.spawn_container_shell(self.container)
                self.shell = BashShell(terminal=self.cons)
                break
            except:
                raise
                #time.sleep(2)
                #continue

        if cnt >= maxTry:
            self.fail("Failed to attach to container: %s" % self.container['Id'])

        if (self.logger.getEffectiveLevel() <= logging.DEBUG):
                self.cons.logfile_read = sys.stdout

        # Determine the networking setup
        # <TBD>

        # Sort out masquerading for the guest if needed.
        # for bridge, hostIF in self.config.snats.items():
        #     pass            
             
        self.start_end=datetime.now()
        self.state = ProxyDevice.STATE_RUNNING
        
    def stop(self):
        r"""
        Refer base class for a description of this interface method.
        """
        try:
            self.state = ProxyDevice.STATE_STOPPING

            if self.container:
                if self.cons:
                    self.cons.sendcontrol('d') # exit container
                    self.cons.close()
                    self.cons = None
                
                self.dkClient.remove_container(container=self.container['Id'], force=True)                
                self.hostShell.close()
                self.container = None
            
            self.state = ProxyDevice.STATE_STOPPED
        except BaseException, failure:
            self.state = ProxyDevice.STATE_UNKNOWN
            self.logger.error('Failed to stop() Container : %s' % str(failure))
            # Output whatever was sent to the console during the attempt.
            self.logger.debug(str(self.cons))
            raise (FrameworkError(ProxyDevice.ERR_FAILED_DEVICE_STOP,
                                  'Unexpected failure to stop, see log')) 

    def executeCLICommand(self, cmd, cmdTimeout=None, withOutput=False):
        r"""
        Execute a CLI system command and return a success or failure indication.
        The method will first check that it is at a login prompt, then
        perform the command specified.  

        @param cmd:
            The CLI cmd to execute and check result of.
            
        @param cmdTimeout:
            The amount of time to allow the command itself to run and return 
            to the CLI prompt.

        @param withOutput(bool):
            Return the Tuple (return code, output list)
        
        @return:              
            Return status from the executed command if withOutput=False; 
            Otherwise return the Tuple(return code, output list)
        """
        # Make sure we are already logged in
        if (self.state != ProxyDevice.STATE_RUNNING):
            raise (FrameworkError(ProxyDevice.ERR_INVALID_DEVICE_STATE,
                                  'Device state invalid for executing CLI command : %s' % self.state))
        try:
            # create a new FileTee to capture the result
            self.shell.terminal.logfile_read = Common.FileTee(diagLevel=self.logger.getEffectiveLevel())
            result, eout = self.shell.executeCLICommand(cmd, cmdTimeout=cmdTimeout)

            # this is not nice :/
            # we want to consume the cmd off the front of the buffer, however
            # it may be split over multiple lines, so we walk one char at a time
            # ignoring new lines and white space
            #value = self.shell.terminal.logfile_read.getvalue()
            value = eout
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
            if withOutput:
                output_list = self.lastCmdOutput.split('\n')
                output_list = output_list[:-1]
                output_list = [l.strip() for l in output_list]
                return (result, output_list)
            else:
                return result
        except ExceptionPexpect, failure:
            self.state = ProxyDevice.STATE_UNKNOWN
            raise(FrameworkError(ProxyDevice.ERR_FAILED_DOCKER_CLI,
                                 '%s' % failure))
