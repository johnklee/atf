from atf.framework.FrameworkBase import *

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
        
        return self.terminal.read(size=size)

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
