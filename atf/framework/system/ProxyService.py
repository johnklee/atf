import logging

from atf.framework.FrameworkBase import *

class ProxyService(FrameworkBase):
    r"""
    This class provides access and control to all supported services operating
    on a hosting TSS. This class allows for a common means for test writers to
    control services essential to the bring up, tear down or actual execution 
    of a test environment in support of the real system(s) under test.
    """
    ###
    # Class error definitions
    ### 
    (ERR_INVALID_SERVICE_STATE)  = FrameworkError.ERR_SERVICE
    """Service is in an invalid state to perform the action"""
    (ERR_SERVICE_START_FAILED)   = FrameworkError.ERR_SERVICE + 1
    """An attempt to start the service failed"""
    (ERR_SERVICE_STOP_FAILED)    = FrameworkError.ERR_SERVICE + 2
    """An attempt to stop the service failed"""
    
    # Define valid states for a ProxyService to be in 
    (STATE_UNKNOWN)       = 0
    """The proxied service is in an unknown state.""" 
    (STATE_RUNNING)       = 1
    """The proxied service is in a running state.""" 
    (STATE_STOPPED)       = 2
    """The proxied service is in a stopped state.""" 

    def __init__(self, diagLevel=logging.WARNING):
        r"""
        Setup particulars about the service inclusive of a start command, a 
        stop command, a status command and state        
        
        @param diagLevel:
            What debug level to run this object in
        """
        FrameworkBase.__init__(self, diagLevel=diagLevel)
        self.state = ProxyService.STATE_UNKNOWN
        
    def start(self):
        r"""
        Start the represented service.
        This method should attempt to check the status of the service to try to 
        sync up state before initiating a start. If the service is already 
        running then or fails during start then an exception should be raised. 

        @return:  
            None, exceptions raised must be derived from L{FrameworkError}
        """
        raise (NotImplementedError())

    def stop(self):
        r"""
        Stop the represented service.
        This method should attempt to check the status of the service to try 
        to sync up state before and after initiating a stop. If ther service 
        fails during stop then an exception should be raised. 

        @return:  
            None, exceptions raised must be derived from L{FrameworkError}
        """
        raise (NotImplementedError())
    
    def restart(self):
        r"""
        Restart the represented service.
        This method should attempt to check the status of the service to try 
        to sync up state before and after initiating the restart. If the 
        service fails during the restart then an exception should be raised. 

        @return:  
            None, exceptions raised must be derived from L{FrameworkError}
        """
        raise (NotImplementedError())
        
    def status(self):
        r"""
        Return the status of the represented service.
        This method should attempt to check the status of the service to try 
        to sync up state before and after initiating the restart. If the 
        service fails during the restart then an exception should be raised. 

        @return:  
            The current state of the service, exceptions raised must be 
            derived from L{FrameworkError}
        """
        raise (NotImplementedError())
        
