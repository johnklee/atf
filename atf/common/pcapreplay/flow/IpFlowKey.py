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
class IpFlowKey(FlowKey):
    """
    The base class for all IP based 5-tuple flowkeys

    Represents a unique identifier for a data flow that consists of;
        - Source IP address
        - Destination IP address
        - Protocol
        - (optional) Source port
        - (optional) Destination port

    """
    ##
    # Methods
    def __init__(self, src, dst, proto, sport='', dport=''): 
        """
        FlowKey's constructor.
    
        @param src:
            The source IP address associated with the flowkey
            
        @param dst:
            The destination IP address associated with the flowkey
            
        @param proto:
            The protocol associated with the flowkey
            
        @param sport:
            The source port associated with the flowkey
            
        @param dport:
            The destination port associated with the flowkey
        """
        FlowKey.__init__(self, src, dst, proto)
        self.sport = sport
        """Source port associated with the flowkey"""
        self.dport = dport
        """Destination port associated with the flowkey"""
        
        
    def __str__(self):
        """
        Returns a string representing the particulars of the IpFlowKey.
        
        @return:
            String representing IpFlowKey details.
        """
        return "%s\n\tSource Port [%s]\n\tDestination Port [%s]" % \
            (FlowKey.__str__(self), self.sport, self.dport)
        
    def __hash__(self):
        """
        *** This method should not be called from this base class ***
        Generate a hash for each flowkey
        
        @return:
            L{object} hash
        """
        raise PcapReplayError(PcapReplayError.ERR_PCAPR_IMPL,
                              'IP base method called')
 
    def __eq__(self, flowKey):
        """
        *** This method should not be called from this base class ***
        Comparison equivalency method for FlowKey.

        @param flowKey:
            The other flowkey to be compared against
            
        @return:
            True on equals, False otherwise
        """
        raise PcapReplayError(PcapReplayError.ERR_PCAPR_IMPL,
                              'IP base method called')
    
    def reverse(self):
        """
        Return the reverse flow key
        
        @return:
            A reversed flowkey.
        """
        return self.__class__(self.dst, self.src, self.proto,
                              self.dport, self.sport)
