# System

# PCS
import pcs
from pcs.packets.ipv4 import *
from pcs.packets.ipv6 import *
from pcs.packets.ethernet import *
from pcs.packets.vlan import *


# PyReplay
import Flow
from FlowKey import *
from atf.common.pcapreplay.Protocol import *

##
# Globals

##
# Classes
class IcmpFlow(Flow.Flow):
    """
    A IcmpFlow contains all information and operatives that are associated
    with a ICMP data flow.

    Pertinent data describing the flow includes:
        - A list of all associated packets
        - An appropriate flowkey
        - A reverse flowkey
    """
    ##
    # Constants

    ##
    # Class Fields

    ##
    # Methods
    @staticmethod
    def flowKeyCreate(pkt):
        """
        A static method.
        Create a flowkey based on protocol particulars.

        @param pkt:
            The packet from which a L{FlowKey} is to be created
        """
        # Break up layer data
        layer = pkt.data

        # search for IPv4 and IPv6 layers
        ipv4Layer = layer.chain().find_first_of(ipv4)[0]
        ipv6Layer = layer.chain().find_first_of(ipv6)[0]

        if ipv4Layer:
            layer = ipv4Layer
            t = IPV4
        elif ipv6Layer:
            layer = ipv6Layer
            t = IPV6
        else:
            raise PcapReplayError(Flow.ERR_PCAPR_FLOW_KEY_CREATE,
                                  'flowKeyCreate : Invalid pkt type %s' %
                                  type(layer))

        # Create the key for return
        return FlowKeyFactory.getFlowKey(t, layer.src, layer.dst, ICMP, 0, 0)
