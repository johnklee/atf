#
# This file contains basic test framework classes that are used 
# throughout as base classes and which are not specific to any one area
# of the framework.
# 
from atf.common.Common import *

class FrameworkBase(CommonBase):
    r"""
    This class provides the base functionality for all classes used 
    in the System testing framework. 
    """
    
    def __init__(self, diagLevel=logging.ERROR):
        CommonBase.__init__(self, diagLevel)

class FrameworkError (CommonError):
    r"""
    This class defines the categories of error codes
    that will exist to be used within exceptions so that unique values can 
    be used to identify the generating component.
    """
    
    (ERR_DEVICE) = CommonError.ERR_FRAMEWORK          
    """ProxyDevice errors""" 
    (ERR_EMU)    = CommonError.ERR_FRAMEWORK + 0x100   
    """Emulator related errors"""
    (ERR_QEMU)   = CommonError.ERR_FRAMEWORK + 0x200 
    """QEMU related errors""" 
    (ERR_VMWARE) = CommonError.ERR_FRAMEWORK + 0x300
    """VMWARE related errors"""
    (ERR_HW)     = CommonError.ERR_FRAMEWORK + 0x400
    """Physical H/W errors"""
    (ERR_DOCKER) = CommonError.ERR_FRAMEWORK + 0x500
    """Docker related errors"""
      
    (ERR_SYSTEM) = CommonError.ERR_FRAMEWORK + 0x3000
    """ProxySystem errors""" 
    (ERR_SYSCFG) = CommonError.ERR_FRAMEWORK + 0x3100
    """SystemConfig errors""" 
    (ERR_SUT)    = CommonError.ERR_FRAMEWORK + 0x3200
    """ProxySUT errors"""
    (ERR_TSS)    = CommonError.ERR_FRAMEWORK + 0x3300
    """ProxyTSS errors""" 
    (ERR_SERVICE)= CommonError.ERR_FRAMEWORK + 0x3400
    """ProxyService errors""" 
    (ERR_SESSION)= CommonError.ERR_FRAMEWORK + 0x3500
    """DeviceSession errors""" 
    (ERR_POWER)  = CommonError.ERR_FRAMEWORK + 0x3600
    """PCS errors""" 
    (ERR_SHELL)  = CommonError.ERR_FRAMEWORK + 0x3700
    """Shell errors""" 
    (ERR_MESA)   = CommonError.ERR_FRAMEWORK + 0x3800
    """ProxyMESA errors"""
    (ERR_ISWG)   = CommonError.ERR_FRAMEWORK + 0x3900
    """ProxyISWG errors""" 
    (ERR_ALPS)   = CommonError.ERR_FRAMEWORK + 0x3a00
    """ProxyALPS errors""" 
    (ERR_UI)     = CommonError.ERR_FRAMEWORK + 0x4000
    """UI related errors"""

    (ERR_TEST)   = CommonError.ERR_FRAMEWORK + 0x8000
    """Test class errors"""
    
    def __init__(self, errCode, desc=None):
        CommonError.__init__(self, errCode=errCode, desc=desc)
                
