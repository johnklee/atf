# System

# PCS
import pcs
from pcs.packets.tcp import *
from pcs.packets.ipv4 import *
from pcs.packets.ipv6 import *
from pcs.packets.ethernet import *

# PcapReplay
import atf.common.pcapreplay
import Trigger
from atf.common.pcapreplay.PcapReplayBase import PcapReplayError
from atf.common.pcapreplay.Protocol import *

##
# Globals

##
# Classes
class TcpTrigger(Trigger.Trigger):
    ##
    # Constants

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
        Trigger.Trigger.__init__(self, type, value, action)
        self.proto = TCP
        """Trigger protocol"""

        # Populate the type map with all possible values that
        # may be triggered on
        self.typeMap['reset'] = [1]
        
    def testTrigger(self, pkt):
        """
        Tests whether a pkt satisfies the trigger's action conditions.
        
        @param pkt:
            The packet against which a trigger is tested
            
        @return:
            A boolean indicating success or failure of a trigger test
        """
        retVal = False
    
        # Action based on trigger type
        if self.type == 'reset':
            # Test if pkt is really a HTTP packet
            (p, i) = pkt.chain().find_first_of(pcs.packets.tcp.tcp)
            if not p:
                return retVal

            # Inspect the packet and match it against the trigger
            tcp = pkt.data.data
            if tcp.reset == int(self.value):
                retVal = True
        return retVal 

    def executeTrigger(self, pkt):
        """
        Execute the trigger action the pkt which satisfies the trigger's 
        action conditions.
        
        @param pkt:
            The packet against which a trigger is actioned
            
        @return:
            A trigger Chain for transmission, None if action is internal
        """
        retChain = None

        # Action based on trigger type
        if self.action == Trigger.Trigger.STOP:
            # Test if pkt is really a HTTP packet
            (p, i) = pkt.chain().find_first_of(pcs.packets.tcp.tcp)
            if not p:
                self.logger.debug("TCP trigger.STOP:\n%s" % pkt.chain())
                raise PcapReplayError(Trigger.ERR_PCAPR_TRIGGER_INVALID, 
                                      'executeTrigger : Invalid trigger/pkt ' +
                                      'pair execution')
        return retChain
