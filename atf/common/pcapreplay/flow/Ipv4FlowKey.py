# System

# PCS

# PcapReplay
import atf.common.pcapreplay
from atf.common.pcapreplay.PcapReplayBase import *
from IpFlowKey import *

##
# Globals

##
# Classes
class Ipv4FlowKey(IpFlowKey):
    """
    The IPv4 based 5-tuple flowkey.

    Represents a unique identifier for a data flow that consists of;
        - Source IPv4 address
        - Destination IPv4 address
        - Protocol
        - (optional) Source port
        - (optional) Destination port
    """
    ##
    # Methods
    def __hash__(self):
        """
        Generate a hash for each flowkey
        
        @return:
            L{object} hash
        """
        return hash("IPv4%s%s%s%s%s" % (self.src, self.dst, self.proto,
                                          self.sport, self.dport))
 
    def __eq__(self, flowKey):
        """
        Comparison equivalency method for FlowKey.

        @param flowKey:
            The other flowkey to be compared against
            
        @return:
            True on equals, False otherwise
        """
        ret = True
        if (flowKey is None or not isinstance(flowKey, Ipv4FlowKey) or
            flowKey.proto != self.proto or 
            flowKey.src != self.src or flowKey.dst != self.dst or 
            flowKey.sport != self.sport or flowKey.dport != self.dport):
            ret = False
        return ret
