# System
import logging
from atf.common.Common import * 

# PCS

# PcapReplay

##
# Globals

##
# Classes
class PcapReplayObject(CommonBase):
    """
    The base class used throughout PcapReplay to inherit all common
    functionality from the CommonBase class used for system testing. This
    class provides basic, consistent logging across classes that require it. 
    """
    ##
    # Constants

    ##
    # Class Fields
 
    ##
    # Methods
    def __init__(self, diagLevel=logging.ERROR):
        """
        PcapReplayObject's constructor.

        @param diagLevel:
            The desired level of logging
        """
        CommonBase.__init__(self, diagLevel)

class PcapReplayError(CommonError):
    """
    Defines all all error categories specific to PcapReplay. This
    class inherits from the CommonError class used to define all
    error categories used in system testing.
    """
    ##
    # Constants
    ERR_PCAPR_BASE      = CommonError.ERR_TOOLS
    """Base of PCAPR errors"""
    ERR_PCAPR_IMPL      = ERR_PCAPR_BASE + 0x001
    """PCAPR Implementation Error"""
    ERR_PCAPR_ARGS      = ERR_PCAPR_BASE + 0x002
    """PCAPR Argument Error"""
    ERR_PCAPR_FILE      = ERR_PCAPR_BASE + 0x003
    """PCAPR File Error"""
    ERR_PCAPR_NET       = ERR_PCAPR_BASE + 0x004
    """PCAPR Net Error"""
    ERR_PCAPR_FLOW      = ERR_PCAPR_BASE + 0x100
    """PCAPR Flow Error base"""
    ERR_PCAPR_TRIGGER   = ERR_PCAPR_BASE + 0x200
    """PCAPR Trigger Error base"""

    ##
    # Class Fields
 
    ##
    # Methods
    def __init__(self, errCode, desc=None):
        """
        PcapReplayError's constructor.

        @param errCode:
            The error code
        
        @param desc:
            A text string describing the error
        """
        CommonError.__init__(self, errCode, desc)
