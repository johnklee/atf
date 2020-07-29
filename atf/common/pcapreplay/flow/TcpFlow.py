# System

# PCS
import pcs
from pcs.packets.tcp import *
from pcs.packets.ipv4 import *
from pcs.packets.ipv6 import *
from pcs.packets.vlan import *

# PyReplay
import Flow
from FlowKey import *
from atf.common.pcapreplay.Protocol import *

##
# Globals

##
# Classes
class TcpFlow(Flow.Flow):
    """
    A TcpFlow contains all information and operatives that are associated
    with a TCP data flow.

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
    def __init__(self, diagLevel=logging.ERROR):
        """
        TcpFlow's constructor.

        @param diagLevel:
            The desired level of logging
        """
        Flow.Flow.__init__(self, diagLevel)
        self.flowConnected = False
        """Flow connected state indicator"""
        self.flowActvClose = False
        """Flow active close state indicator"""
        self.flowPasvClose = False
        """Flow passive close state indicator"""

    def getLastPacket(self):
        """
        Find and return the last packet in the TcpFlow's packet list.

        @return:
            The last packet in TcpFlow's packet list
        """
        retVal = None
        if len(self.pkts) > 0:
            retVal = self.pkts[-1][1]
        return retVal

    def getLastTwoPackets(self):
        """
        Find and return the last two packets in the TcpFlow's packet list.

        @return:
            An array that contains the last two packets in the TcpFlow's
            packet list
        """
        retVal = []
        if len(self.pkts) > 1:
            retVal = [self.pkts[-1][1], self.pkts[-2][1]]
        return retVal

    def getLastPayloadLength(self):
        """
        Find and return the length of the payload of the last packet on
        the TcpFlow's packet list.

        @return:
            The length of the payload of the last packet on the TcpFlow's
            packet list as an integer
        """
        payLen = 0
        lastPkt = self.pkts[-1][1]
        if lastPkt.data.data.data:
            payLen = len(lastPkt.data.data.data)
        return payLen

    @staticmethod
    def flowKeyCreate(pkt):
        """
        A static method.
        Create a flowkey based on protocol particulars.

        @param pkt:
            The packet from which a L{FlowKey} is to be created

        @return:
            None, Can raise L{PcapReplayError} exceptions
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
        tcp = layer.data

        # Create the key for return
        return FlowKeyFactory.getFlowKey(t, layer.src, layer.dst, TCP, tcp.sport,
                                         tcp.dport)
