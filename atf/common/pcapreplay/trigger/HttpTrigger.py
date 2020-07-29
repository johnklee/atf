# System

# PCS
import pcs
from pcs.packets.tcp import *
from pcs.packets.http import *
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
class HttpTrigger(Trigger.Trigger):
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
        self.proto = HTTP
        """Trigger protocol"""

        # Populate the type map with all possible values that
        # may be triggered on
        self.typeMap['statusCode'] = ['404']
        
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
        if self.type == 'statusCode':
            # Test if pkt is really a HTTP packet
            (p, i) = pkt.chain().find_first_of(pcs.packets.http.httpResponse)
            if not p:
                return retVal

            # Inspect the packet and match it against the trigger
            http = pkt.data.data.data
            if http.statusCode == self.value:
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
            (p, i) = pkt.chain().find_first_of(pcs.packets.http.httpResponse)
            if not p:
                self.logger.debug("HTTP trigger.STOP:\n%s" % pkt.chain())
                raise PcapReplayError(Trigger.ERR_PCAPR_TRIGGER_INVALID, 
                                      'executeTrigger : Invalid trigger/pkt ' +
                                      'pair execution')

            # Create a terminating response chain for xmit by the caller
            ether = pkt
            e = ethernet()
            e.dst = ether.src
            e.src = ether.dst
            e.type = ether.type
            ip = pkt.data
            if type(ip) == pcs.packets.ipv4.ipv4:
                i = ipv4()
                i.tos = ip.tos
                i.protocol = ip.protocol
                i.id = 0
                i.flags = 0
            elif type(ip) == pcs.packets.ipv6.ipv6:
                i = ipv6()
                i.traffic_class = ip.traffic_class
                i.next_header = ip.next_header
            i.src = ip.dst
            i.dst = ip.src
            tcp = pkt.data.data
            t = pcs.packets.tcp.tcp()
            t.sport = tcp.dport
            t.dport = tcp.sport
            t.reset = 1
            t.ack = 1
            t.ack_number = tcp.ack_number
            t.sequence = tcp.sequence
            t.data = None
            retChain = pcs.Chain([e, i, t])
            retChain.fixup()
        return retChain
