
from ProxyService import *
from Shell import *
from pexpect import ExceptionPexpect

class ProxyLinuxService(ProxyService):
    r"""
    This class provides access and control to supported Linux services operating
    on a Linux TSS. This class allows for a common means for test writers to
    control services essential to the bring up, tear down or actual execution 
    of a test environment in support of the real system(s) under test.
    """    
    ###
    # Class Definitions
    ###
    # Constants
    (CMD_TIMEOUT) = 30
    """The timeout used for the pexpect of LinuxService commands"""

    def __init__(self, name, shell, diagLevel=logging.WARNING):
        r"""
        Identify the name and shell of the Linux Service being proxied.
        
        @param name:
            The name of the service being proxied
            
        @param shell:
            The shell of the system that houses the proxied service
        """
        ProxyService.__init__(self, diagLevel=diagLevel)
        self.name = name
        """The name of the service being proxied"""
        self.shell = shell
        """The shell of the system that houses the proxied service"""

    def start(self):
        r"""
        Start the represented service.
        This method should attempt to check the status of the service to try to 
        sync up state before initiating a start. If the service is already 
        running then or fails during start then an exception should be raised. 

        @return:
            None, exceptions raised must be derived from L{FrameworkError}
        """
        if (self.shell == None):
            raise (FrameworkError(ProxyService.ERR_INVALID_SERVICE_STATE, 'invalid shell reference'))
        
        try:
            # update our state
            self.status()
            
            if (self.state == ProxyService.STATE_STOPPED):
                self.shell.sendline('service %s start' % self.name)
                self.shell.expect('Starting', timeout=ProxyLinuxService.CMD_TIMEOUT)
                self.shell.expect('OK', timeout=ProxyLinuxService.CMD_TIMEOUT)
                self.state = ProxyService.STATE_RUNNING
        except ExceptionPexpect, failure:
            self.state = ProxyService.STATE_UNKNOWN
            raise (FrameworkError(ProxyService.ERR_SERVICE_START_FAILED, 'failed to start service %s' % self.name))

    def stop(self):
        r"""
        Stop the represented service.
        This method should attempt to check the status of the service to try 
        to sync up state before and after initiating a stop. If ther service 
        fails during stop then an exception should be raised. 

        @return:
            None, exceptions raised must be derived from L{FrameworkError}
        """
        if (self.shell == None):
            raise (FrameworkError(ProxyService.ERR_INVALID_SERVICE_STATE, 'invalid shell reference'))
        
        try:
            # update our state
            self.status()
            
            if (self.state == ProxyService.STATE_RUNNING):
                self.shell.sendline('service %s stop' % self.name)
                self.shell.expect('Stopping', timeout=ProxyLinuxService.CMD_TIMEOUT)
                result = self.shell.expect(['OK', 'FAILED'], timeout=ProxyLinuxService.CMD_TIMEOUT)
                if (result == 0):
                    self.state = ProxyService.STATE_STOPPED
                else:
                    self.state = ProxyService.STATE_UNKNOWN
                    raise (FrameworkError(ProxyService.ERR_SERVICE_STOP_FAILED, 'failed to stop service %s' % self.name))
        except ExceptionPexpect, failure:
            self.state = ProxyService.STATE_UNKNOWN
            raise (FrameworkError(ProxyService.ERR_SERVICE_STOP_FAILED, 'failed to stop service %s' % self.name))
    
    def restart(self):
        r"""
        Restart the represented service.
        This method should attempt to check the status of the service to try 
        to sync up state before and after initiating the restart. If the 
        service fails during the restart then an exception should be raised. 

        @return:
            None, exceptions raised must be derived from L{FrameworkError}
        """
        self.stop()
        self.start()

    def status(self):
        r"""
        Return the status of the represented service.
        This method should attempt to check the status of the service to try 
        to sync up state before and after initiating the restart. If the 
        service fails during the restart then an exception should be raised. 

        @return:
            The current state of the service, exceptions raised must be derived 
            from L{FrameworkError}
        """
        if (self.shell == None):
            raise (FrameworkError(ProxyService.ERR_INVALID_SERVICE_STATE, 'invalid shell reference'))
        
        try:
            self.shell.sendline('service %s status' % self.name)
            result = self.shell.expect(['is running', 'is stopped'], timeout=ProxyLinuxService.CMD_TIMEOUT)
            if (result == 0):
                self.state = ProxyService.STATE_RUNNING
            elif (result == 1):
                self.state = ProxyService.STATE_STOPPED
        except ExceptionPexpect, failure:
            # Timeout or eof either way the operation failed.
            self.state = ProxyService.STATE_UNKNOWN
            
        return self.state
