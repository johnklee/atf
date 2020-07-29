# System

# PCS

# PcapReplay
import atf.common.pcapreplay
from atf.common.pcapreplay.PcapReplayBase import *
from atf.common.pcapreplay.Protocol import *

##
# Globals

##
# Classes
class FlowKey:
    """
    A flowkey represents a unique identifier for a data flow that consists of;
        - Generic source address
        - Generic destination address
        - Protocol
    """
    ##
    # Constants

    ##
    # Class Fields
 
    ##
    # Methods
    def __init__(self, src, dst, proto):
        """
        FlowKey's constructor.

        @param src:
            The source address associated with the flowkey
            
        @param dst:
            The destination address associated with the flowkey
            
        @param proto:
            The protocol associated with the flowkey
        """
        self.src = src
        """The source address associated with the flowkey"""
        self.dst = dst
        """The destination address associated with the flowkey"""
        self.proto = proto
        """The protocol associated with the flowkey"""
   
    def __str__(self):
        """
        Returns a string representing the particulars of the FlowKey.
        
        @return:
            String representing FlowKey details.
        """
        return "FlowKey :\n\tProtocol [%s]\n\tSource [%s]\n\tDestination [%s]" % \
            (self.proto, self.src, self.dst)
   
    def __hash__(self):
        """
        Abstract.
        Generate a hash for each flowkey
        
        @return:
            L{object} hash
        """
        raise PcapReplayError(PcapReplayError.ERR_PCAPR_IMPL,
                              'Abstract method called')
 
    def __eq__(self, flowKey):
        """
        Abstract.
        Comparison equivalency method for FlowKey.

        @param flowKey:
            The other flowkey to be compared against
            
        @return:
            True on equals, False otherwise
        """
        raise PcapReplayError(PcapReplayError.ERR_PCAPR_IMPL,
                              'Abstract method called')

    def __ne__(self, flowKey):
        """
        Comparison non-equivalency method for FlowKey.

        @param flowKey:
            The other flowkey to be compared against
            
        @return:
            False on equals, True otherwise
        """
        return not self.__eq__(flowKey)

    def reverse(self):
        """
        Return the reverse flow key
        
        @return:
            A reversed flowkey.
        """
        return self.__class__(self.dst, self.src, self.proto)
    
class FlowKeyFactory:
    """
    Creates FlowKeys based on specified trigger types
    """
    ##
    # Constants

    ##
    # Class Fields
    flowKeyTypes = {MAC: 'MacFlowKey', IPV4: 'Ipv4FlowKey', IPV6: 'Ipv6FlowKey'}

    ##
    # Methods
    @staticmethod
    def getFlowKey(fkType, src, dst, proto, sport='', dport=''):
        """
        A static method.
        Allocates a new L{FlowKey} instance by returning an appropriately typed
        L{FlowKey}
        
        @param fkType:
            The type of the L{FlowKey} to be created
            
        @param src:
            The source address associated with the L{FlowKey}
            
        @param dst:
            The destination address associated with the L{FlowKey}
            
        @param proto:
            The protocol associated with the L{FlowKey}
            
        @param sport:
            The source port associated with the L{FlowKey}
            
        @param dport:
            The destination port associated with the L{FlowKey}
            
        @return: 
            An appropriate L{FlowKey}
        """
        # Determine the type of the flow to be 
        
        module = 'atf.common.pcapreplay.flow.' + FlowKeyFactory.flowKeyTypes[fkType]
        m = __import__(module)
        module += '.' + FlowKeyFactory.flowKeyTypes[fkType]
        for comp in module.split('.')[1:]:
            m = getattr(m, comp)
        if fkType == MAC:
            flk = m(src, dst, proto)
        else: 
            flk = m(src, dst, proto, sport, dport)
        return flk
