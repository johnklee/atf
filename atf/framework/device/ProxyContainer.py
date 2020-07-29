import logging
import pexpect
import signal
import subprocess
import types

import atf.common.Common as Common
from atf.framework.FrameworkBase import *
from atf.framework.system.ProxySystem import * 
from ProxyDevice import *
from DeviceConfig import *

class ContainerConfig(DeviceConfig):
    r"""
    Encapsulate emulator specific configuration information needed
    to set up an emulator hosted Device.
    """
    def __init__(self, image, run_config):
        r"""
        Save all arguments internally and construct base class.
        
        @param image(str):
            Image information 

        @param run_config(dict):
            Refer to below API for supported parameter(s):
            https://docker-py.readthedocs.io/en/stable/api.html#docker.api.container.ContainerApiMixin.create_container 
        """
        DeviceConfig.__init__(self)
 
        self.image = image
        """Image information"""

        self.run_config = run_config
        """Parameter(s) used to run the container"""
        
class ProxyContainer(ProxyDevice):
    r"""
    The ProxyContainer class supports the ProxyDevice interface to control a 
    Virtual Machine.
    """    
    def __init__(self,  containerConfig=None, diagLevel=logging.WARNING):
        r"""
        Save the configuration information internally for use by
        start() and move to STATE_INITIALISED.
        
        @param containerConfig:
            A pre-constructed ContainerConfig object
            
        @param diagLevel:
            What debug level to run this object in.
        """
        # Invoke base class initialisation
        ProxyDevice.__init__(self, containerConfig, diagLevel)
        self.state = ProxyDevice.STATE_INITIALISED

        # Define the shell program we will use to start emulator.
        # NOTE : This is NOT run sudo to avoid some potential security issues.
        self.runCmd = ''


    def start(self, productPackage=None):
        r"""
        Refer base class for a description of this interface method.

        @param productPackage:
            A L{ProxySUT.ProductPackage} derived class or None.
            
        @return:
            None, Can raise FrameworkError exceptions
        """
        
        raise (FrameworkError(ProxySystem.ERR_UNKNOWN_DEVICE_TYPE,
                                  'Not Implemented Yet!'))   


    def stop(self):
        r"""
        Refer base class for a description of this interface method.
        """
        raise (FrameworkError(ProxySystem.ERR_UNKNOWN_DEVICE_TYPE,
                                  'Not Implemented Yet!'))        


