# System
from signal import *

##
# Globals

##
# Classes
class TimeoutMethodException(Exception): 
    """
    Exception to raise on a timeout
    """
    ##
    # Constants
    
    ##
    # Class Fields
 
    ##
    # Methods
    def __init__(self, desc="Time Out"):
        """
        TimeoutMethodExceptions's constructor
        
        @param desc:
            Description of the exception
        """
        self.desc = desc
        """Timeout description"""
        
    def __str__(self):
        """
        TimeoutMethodExceptions's built in str representation.
        Simply print the description that was instantiated at 
        construction time.
        
        @return:
            Timeout description
        """
        return repr(self.desc)

class TimeoutMethod: 
    """
    Timeout utility class to handle methods that require a hard timeout 
    """
    ##
    # Constants
    
    ##
    # Class Fields
 
    ##
    # Methods
    def __init__(self, method, timeout): 
        """
        TimeoutMethods's constructor
        
        @param method:
            The method that is to be timed out
        
        @param timeout:
            The timeout to apply to the method in seconds
        """
        self.timeout = timeout 
        """Timeout value"""
        self.method = method
        """Method that is to be timed out"""
        
    def __call__(self, *args): 
        """
        Invocation built in that wraps the
         
        @param args:
            Arguments for the method subject to the timeout
        """
        # Save old handler for later restoration
        oldHandler = signal(SIGALRM, self.handler)
        
        # Set alarm with set timeout 
        alarm(self.timeout)
        
        # Invoke wrapped method 
        try: 
            result = self.method(*args)
        finally: 
            # Restore ol handler on completion
            signal(SIGALRM, oldHandler)
        
        # Reset alarm and return
        alarm(0)
        return result 

    def handler(self, signum, frame): 
        """
        Handle the timeout by raising an exception
        
        @param signum:
            The signal number that forced the handle invocation
            
        @param frame:
            The frame of the signal at trap time
        """
        raise TimeoutMethodException()
