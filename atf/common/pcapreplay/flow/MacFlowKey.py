# System

# PCS

# PcapReplay
import atf.common.pcapreplay
from atf.common.pcapreplay.PcapReplayBase import *
from FlowKey import *

##
# Globals

##
# Classes
class MacFlowKey(FlowKey):
    """
    A MAC flowkey represents a unique identifier for a data flow that consists of;
        - Source MAC address
        - Destination MAC address
        - Protocol
    """
        ##
    # Methods
    def __hash__(self):
        """
        Generate a hash for each flowkey
        
        @return:
            L{object} hash
        """
        return hash("MAC%s%s%s" % (self.src, self.dst, self.proto))
 
    def __eq__(self, flowKey):
        """
        Comparison equivalency method for FlowKey.

        @param flowKey:
            The other flowkey to be compared against
            
        @return:
            True on equals, False otherwise
        """
        ret = True
        if (flowKey is None or not isinstance(flowKey, MacFlowKey) or
            flowKey.proto != self.proto or 
            flowKey.src != self.src or flowKey.dst != self.dst):
            ret = False
        return ret
