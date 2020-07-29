# System

# PCS

# PcapReplay
import atf.common.pcapreplay
from atf.common.pcapreplay.PcapReplayBase import *
from atf.common.pcapreplay.Protocol import *

##
# Globals
ERR_PCAPR_TRIGGER_INVALID = PcapReplayError.ERR_PCAPR_TRIGGER + 1  # Exec invalid

##
# Classes
class Trigger(PcapReplayObject):
    """
    A trigger defines the actions to be taken when specified response conditions
    are met during replay.
    """
    ##
    # Constants
    
    # Trigger action types
    STOP = 'STOP'
    """STOP action type"""

    ##
    # Class Fields
 
    ##
    # Methods
    def __init__(self, type, value, action):
        """
        Trigger constructor.

        @param type:
            Type of trigger condition for action
            
        @param value:
            Values that a trigger type may take to action
            
        @param action:
            Action type take on trigger condition satisfaction
        """
        PcapReplayObject.__init__(self)
        self.type = type
        """Trigger type"""
        self.value = value
        """Value to trigger on"""
        self.action = action
        """Trigger action type"""
        self.typeMap = {}
        """Map of trigger types"""
        self.proto = ''
        """Protocol of trigger"""
    
    def testTrigger(self, pkt):
        """
        Abstract.
        Tests whether a pkt satisfies the trigger's action conditions.
        
        @param pkt:
            The packet against which a trigger is tested
            
        @return:
            A boolean indicating success or failure of a trigger test
        """
        raise PcapReplayError(PcapReplayError.ERR_PCAPR_IMPL, 
                              'Abstract method called')
        
    def executeTrigger(self, pkt):
        """
        Abstract.
        Execute the trigger action whether a pkt satisfies the trigger's 
        action conditions.
        
        @param pkt:
            The packet against which a trigger is tested
            
        @return:
            A trigger packet for transmission, None if action is internal
        """
        raise PcapReplayError(PcapReplayError.ERR_PCAPR_IMPL, 
                              'Abstract method called')
    
class TriggerFactory:
    """
    Creates triggers based on specified trigger types
    """
    ##
    # Constants

    ##
    # Class Fields
    triggerTypes = {HTTP: 'HttpTrigger', TCP: 'TcpTrigger'}
    """All supported trigger types"""

    ##
    # Methods
    @staticmethod
    def getTrigger(proto, type, value, action):
        """
        A static method.
        Allocates a new Trigger instance by returning an appropriately typed
        Trigger

        @param proto:
            The protocol associated with the trigger to be created
            
        @param type:
            Type of trigger condition for action
            
        @param value:
            Values that a trigger type may take to action
            
        @param action:
            Action type take on trigger condition satisfaction
            
        @return:
            An appropriately typed trigger
        """
        module = 'atf.common.pcapreplay.trigger.' + TriggerFactory.triggerTypes[proto]
        m = __import__(module)
        module += '.' + TriggerFactory.triggerTypes[proto]
        for comp in module.split('.')[1:]:
            m = getattr(m, comp)            
        return m(type, value, action)
