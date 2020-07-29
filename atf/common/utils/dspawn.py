import inspect

from pexpect import ExceptionPexpect, TIMEOUT, EOF, spawn

class dspawn(spawn):
    def __init__(self, command, args=[], timeout=30, maxread=2000,
        searchwindowsize=None, logfile=None, cwd=None, env=None,
        ignore_sighup=True, echo=True):
        if len(inspect.getfullargspec(spawn.__init__)[0]) == 9:
            spawn.__init__(self, command, args, timeout, maxread, searchwindowsize, logfile,
                       cwd, env)
        else:
            spawn.__init__(self, command, args, timeout, maxread, searchwindowsize, logfile,
                       cwd, env, ignore_sighup, echo)        

        # used to match the command-line prompt
        self.UNIQUE_PROMPT_HEAD = "[PEXPECT]"
        self.UNIQUE_PROMPT = r"\[PEXPECT\][\$\#] "
        self.PROMPT = self.UNIQUE_PROMPT

        # used to set shell command-line prompt to UNIQUE_PROMPT.
        self.PROMPT_SET_SH = r"PS1='[PEXPECT]\$ '"
        self.PROMPT_SET_CSH = r"set prompt='[PEXPECT]\$ '"
        self.SSH_OPTS = ("-o'RSAAuthentication=no'"
                + " -o 'PubkeyAuthentication=no'")
        
        self.set_unique_prompt()
        
    def set_unique_prompt(self):
        '''This sets the remote prompt to something more unique than ``#`` or ``$``.
        This makes it easier for the :meth:`prompt` method to match the shell prompt
        unambiguously. This method is called automatically by the :meth:`login`
        method, but you may want to call it manually if you somehow reset the
        shell prompt. For example, if you 'su' to a different user then you
        will need to manually reset the prompt. This sends shell commands to
        the remote host to set the prompt, so this assumes the remote host is
        ready to receive commands.

        Alternatively, you may use your own prompt pattern. In this case you
        should call :meth:`login` with ``auto_prompt_reset=False``; then set the
        :attr:`PROMPT` attribute to a regular expression. After that, the
        :meth:`prompt` method will try to match your prompt pattern.
        '''

        self.sendline("unset PROMPT_COMMAND")
        self.sendline(self.PROMPT_SET_SH) # sh-style
        i = self.expect ([TIMEOUT, self.PROMPT], timeout=10)
        if i == 0: # csh-style
            self.sendline(self.PROMPT_SET_CSH)
            i = self.expect([TIMEOUT, self.PROMPT], timeout=10)
            if i == 0:
                return False
        return True
        
    def prompt(self, timeout=-1):
        '''Match the next shell prompt.

        This is little more than a short-cut to the :meth:`~pexpect.spawn.expect`
        method. Note that if you called :meth:`login` with
        ``auto_prompt_reset=False``, then before calling :meth:`prompt` you must
        set the :attr:`PROMPT` attribute to a regex that it will use for
        matching the prompt.

        Calling :meth:`prompt` will erase the contents of the :attr:`before`
        attribute even if no prompt is ever matched. If timeout is not given or
        it is set to -1 then self.timeout is used.

        :return: True if the shell prompt was matched, False if the timeout was
                 reached.
        '''

        if timeout == -1:
            timeout = self.timeout
        i = self.expect([self.PROMPT, TIMEOUT], timeout=timeout)
        if i==1:
            return False
        return True
