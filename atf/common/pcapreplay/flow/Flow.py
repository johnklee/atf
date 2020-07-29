# System
from copy import *

# PCS
import pcs
import pcs.pcap as pcap
from pcs.packets.tcp import *
from pcs.packets.http import *
from pcs.packets.ipv4 import *
from pcs.packets.ipv6 import *
from pcs.packets.ethernet import *
from pcs.packets.vlan import *

# PcapReplay
import atf.common.pcapreplay
from atf.common.pcapreplay.PcapReplayBase import *
from atf.common.pcapreplay.trigger.Trigger import *
from atf.common.pcapreplay.PcapReplayInfo import *
from atf.common.pcapreplay.Protocol import *
from atf.common.pcapreplay.TimeoutMethod import *
from FlowKey import *
from Ipv4FlowKey import *
from Ipv6FlowKey import *

##
# Globals
ERR_PCAPR_FLOW_REPLAY = PcapReplayError.ERR_PCAPR_FLOW + 1
"""Flow replay error"""
ERR_PCAPR_FLOW_VERIFY = PcapReplayError.ERR_PCAPR_FLOW + 2
"""Flow verify error"""
ERR_PCAPR_FLOW_INVALID_IF = PcapReplayError.ERR_PCAPR_FLOW + 3
"""Flow interface error"""
ERR_PCAPR_FLOW_KEY_CREATE = PcapReplayError.ERR_PCAPR_FLOW + 4
"""FlowKey error"""

##
# Classes
class Flow(PcapReplayObject):
    """
    A Flow contains all information and operatives that are associated with
    a data flow
    """
    ##
    # Constants
    REPLAY_NO_VERIFY = 0
    """Do not verify"""
    REPLAY_QUIET_FULL_VERIFY = 1
    """Verify via failing on all packet drops and failures, do not display results to STDOUT"""
    REPLAY_FULL_VERIFY = 2
    """Verify via failing on all packet drops and failures, display results to STDOUT"""
    REPLAY_QUIET_DROPPASS_VERIFY = 3
    """Verify via failing on all packet failures, do not display results to STDOUT"""
    REPLAY_DROPPASS_VERIFY = 4
    """Verify via failing on all packet failures, display results to STDOUT"""
    PACKET_COUNTER_TOTAL = 0
    """Dictionary key indicating the total number of all packets replayed"""
    PACKET_COUNTER_PASSED = 1
    """Dictionary key indicating the total number of all packets that passed during replay"""
    PACKET_COUNTER_FAILED = 2
    """Dictionary key indicating the total number of all packets that failed during replay"""
    PACKET_COUNTER_DROPPED = 3
    """Dictionary key indicating the total number of all packets that were dropped during replay"""
    PACKET_COUNTER_SKIPPED = 4
    """Dictionary key indicating the total number of all packets that were skipped during replay"""

    fixedMacAddr = [NetworkInfo.macPToN('ff:ff:ff:ff:ff:ff')]
    """MAC addresses that will be excluded from fixup"""

    ##
    # Class Fields

    ##
    # Methods
    def __init__(self, diagLevel=logging.ERROR):
        """
        Flow's constructor.

        @param diagLevel:
            The desired level of logging
        """
        PcapReplayObject.__init__(self, diagLevel)
        self.pkts = []
        """List of flow's packets"""
        self.flk = None
        """Flow's flowkey"""
        self.rfk = None
        """Flow's reverse flowkey"""
        self.flkinit = self.flowKeyCreate
        """Flow's flowkey initialization method"""

    def getFlowType(self):
        """
        Get the (protocol) type of the flow.

        @return:
            Returns a string indicating the type of the flow
        """
        return self.flk.proto

    def addPacket(self, pkt):
        """
        Add a packet tuple to Flow's packet list.

        @param pkt:
            The sequence number and packet tuple to be added
        """
        if pkt == None:
            return

        # The first packet added establishes the flow's details
        self.pkts.append(pkt)
        if self.flk is None and self.rfk is None:
            self.flk = self.flkinit(pkt[1])
            self.rfk = self.flk.reverse()

    def matchFlow(self, pkt):
        """
        Matches a packet to a Flow.

        @param pkt:
            The packet to be matched to the Flow

        @return:
            True on the packet matching the Flow, False otherwise
        """
        ret = False
        if pkt != None:
            flk = self.flkinit(pkt)
            if flk == self.flk or flk == self.rfk:
                ret = True
        return ret

    def splitFlow(self):
        """
        Splits a Flow packet list into two arrays; all packets
        associate with the flowkey and all packets associated with the
        reverse flowkey.

        @return:
            A tuple of lists of the format;
            ([flowkey packets], [reverse flowkey packets])
        """
        fFlow = []
        rFlow = []

        # Iterate over all packets and split based on comparison against
        # the Flow's flowkeys
        for seq, pkt in self.pkts:
            flk = self.flkinit(pkt)
            if flk == self.flk:
                fFlow.append((seq, pkt))
            elif flk == self.rfk:
                rFlow.append((seq, pkt))
        return fFlow, rFlow

    def __eq__(self, other):
        """
        Test if packet list for the flow is equal to other.
          - Packet lists for the flow match needs to be same sequence as the comparison and must be continuous(gap is not allowed)

        @param other:
            The flow to be compared

        @return:
            True if the packet is equal to other flow, False otherwise
        """
        return self.__internal_cmp__(other) == 0

    def __ne__(self, other):
        """
        Test if packet list for the flow is not equal to other.

        @param other:
            The flow to be compared

        @return:
            True if the packet is not equal to other flow, False otherwise
        """
        return not self.__eq__(other)

    def __lt__(self, other):
        """
        Test if packet list for the flow is a proper subset of other.
          - Packet lists for the flow match needs to be same sequence as the comparison and must be continuous(gap is not allowed)

        @param other:
            The flow to be compared

        @return:
            True the following case.
            [1,2,3] <= [1,2,3,4]
        """
        return self.__internal_cmp__(other) == -1

    def __le__(self, other):
        """
        Test if packet list for the flow is in others.
          - Packet lists for the flow match needs to be same sequence as the comparison and must be continuous(gap is not allowed)

        @param other:
            The flow to be compared

        @return:
            True the following case.
            [1,2,3] <= [1,2,3]
            [1,2,3] <= [1,2,3,4]
        """
        return  0 >= self.__internal_cmp__(other) >= -1

    def __gt__(self, other):
        """
        Test if other is a proper subset of packet list for the flow.
          - Packet lists for the flow match needs to be same sequence as the comparison and must be continuous(gap is not allowed)

        @param other:
            The flow to be compared

        @return:
            True the following case.
            [1,2,3] > [1,2]
        """

        return self. __internal_cmp__(other) == 1
    def __ge__(self, other):
        """
        Test if other is in the packet list for the flow.
          - Packet lists for the flow match needs to be same sequence as the comparison and must be continuous(gap is not allowed)

        @param other:
            The flow to be compared

        @return:
            True the following case.
            [1,2,3] >=[1,2]
            [1,2,3] >=[1,2,3]
        """
        return 0 <= self.__internal_cmp__(other) <= 1

    def  __internal_cmp__(self, other):
        """
        Compares packet list for the flow.

        @param other:
            The flow to be compared

        @return:
            1: self > other  (Same sequence, no gap allowed, see __gt__)
            0: self == other (Same sequence, no gap allowed)
            -1: self < other  (Same sequence, no gap allowed, see __lt__)
            -2: Two flows do not intersect.
        """
        # Check if other is a Flow
        if isinstance(other, Flow) == False:
            return -2

        # Generate packet lists for comparison
        selfPkt = map(list, zip(*self.pkts))[1]
        otherPkt = map(list, zip(*other.pkts))[1]

        # Check if equal to
        if len(selfPkt) == len(otherPkt):
            if [s.chain() for s in selfPkt] == [o.chain() for o in otherPkt]:
                return 0

        # Check if less than
        elif len(selfPkt) < len(otherPkt):
            for i in range(len(otherPkt)):
                if (i + len(selfPkt)) <= len(otherPkt) and otherPkt[i].chain() == selfPkt[0].chain() and \
                    [o.chain() for o in otherPkt[i:i + len(selfPkt)]] == [s.chain() for s in selfPkt]:
                        return -1

        # Check if greater than
        elif len(selfPkt) > len(otherPkt):
            for i in range(len(selfPkt)):
                if (i + len(otherPkt)) <= len(selfPkt) and selfPkt[i].chain() == otherPkt[0].chain() and \
                     [s.chain() for s in selfPkt[i:i + len(otherPkt)]] == [o.chain() for o in otherPkt]:
                    return 1

        # The two flows do not intersect.
        return -2

    def issubset(self, other):
        r"""
        Test whether every packet for the flow are in other.
          - Packet list for the flow match needs to be same sequence as the comparison, but no need be contiguous(gaps are allowed)

        @param other:
            The flow to be compared

        @return:
            True if the packet is subset of flow, False otherwise
        """
        # Check if other is a Flow
        if isinstance(other, Flow) == False:
            return False

        # Generate packet lists for comparison
        selfPkt = map(list, zip(*self.pkts))[1]
        otherPkt = map(list, zip(*other.pkts))[1]

        # Compare the two packet lists for a "gappy"
        # subset
        pktMatch = 0
        pos = 0
        for selfP in selfPkt:
            # Attempt to match self.pkt in other's packet list from the current index.
            for otherP in otherPkt[pos:]:
                if (selfP.chain() == otherP.chain()):
                    pos += 1
                    pktMatch += 1
                    break

            # if all self pkts are in other with allowing gap return True
            if (pktMatch == len(self.pkts)):
                return True
        return False

    def issuperset(self, other):
        r"""
        Test whether other is in the packet list for the flow
          - Packet list for the flow match needs to be same sequence as the comparison, but no need be contiguous(gaps are allowed)

        @param other:
            The flow to be compared

        @return:
            True if the packet is superset of flow, False otherwise
        """
        # Check if other is a Flow
        if isinstance(other, Flow) == False:
            return False
        return other.issubset(self)

    def rewrite(self, netInfo):
        r"""
        Rewrite the L{Flow} based on network information passed in.

        @param netInfo:
            NetworkInfo instance containing information about the server and
            client network interfaces
        """
        # Get the flow packet re-written with network information
        rPkts = self.getReplayPktList(netInfo, pcs.PcapConnector(), pcs.PcapConnector(), True)

        # Unzip rewritten packets and create (seq, pkt) list
        seq, pktChain, iface = map(list, zip(*rPkts))
        pkts = zip(seq, [p.packets[0] for p in pktChain])

        # Flush current Flow information
        self.pkts = []
        self.flk = None
        self.rfk = None

        # Add rewritten packets to the current Flow
        for p in pkts:
            self.addPacket(p)

    def getReplayPktList(self, netInfo, clientPcapC, serverPcapC, fixup=True):
        """
        Returns an n-tuple list of packets to be sent over respective interfaces.
        If specified, this method will fix up all flow packets with respect
        to specified client and server network interfaces and NetworkInfo.

        @param netInfo:
            NetworkInfo instance containing information about the server and
            client network interfaces

        @param clientPcapC:
            The PcapConnector for the client interface

        @param serverPcapC:
            The PcapConnector for the server interface

        @param fixup:
            A boolean indicating whether layer-2/layer-3 modification
            should occur

        @return:
            A list of n-tuples of PcapConnector with pkt, sequence number
            and egress interface
        """
        retPkts = []
        ni = netInfo

        # Sanity check arguments
        if clientPcapC is None or serverPcapC is None:
            raise PcapReplayError(ERR_PCAPR_FLOW_INVALID_IF,
                                  'getReplayPktList : Invalid PcapConnectors ' +
                                  'for packet list generation.')

        # Iterate over a copy of self.pkts and modify the
        # source and client details as required
        sendIf = clientPcapC
        capPkts = copy(self.pkts)
        for seq, pkt in capPkts:
            flk = self.flkinit(pkt)

            # check if there's a VLAN involved
            if type(pkt.data) == pcs.packets.vlan.vlan:
                vlan = pkt.data
                ip = vlan.data
            else:
                vlan = None
                ip = pkt.data
                if ni.vlanId != '':
                    self.logger.warning('VLAN id rewrite is not possible as original packet does not have VLAN tag')

            # Alter each packet's IP/MAC address based on flowkey

            if flk == self.flk:
                if fixup:
                    if isinstance(flk, Ipv6FlowKey):
                        if (ni.clientIP6 != ''):
                            ip.src = ni.clientIP6
                        if (ni.serverIP6 != ''):
                            ip.dst = ni.serverIP6
                    elif isinstance(flk, Ipv4FlowKey):
                        if (type(ni.clientIP4) == int):
                            ip.src = ni.clientIP4
                        if (type(ni.serverIP4) == int):
                            ip.dst = ni.serverIP4
                    if not pkt.src in self.fixedMacAddr:
                        if (ni.clientMAC != ''):
                            pkt.src = ni.clientMAC
                    if not pkt.dst in self.fixedMacAddr:
                        if (ni.serverMAC != ''):
                            pkt.dst = ni.serverMAC
                    if vlan and ni.vlanId != '':
                        vlan.vlan = int(ni.vlanId)
                sendIf = clientPcapC
            elif flk == self.rfk:
                if fixup:
                    if isinstance(flk, Ipv6FlowKey):
                        if (ni.serverIP6 != ''):
                            if ni.serverNatRule == '':
                                ip.src = ni.serverIP6
                            else:
                                ip.src = NetworkInfo.netPToN(ipv6=ni.serverNatRule[1])
                        if (ni.clientIP6 != ''):
                            if ni.clientNatRule == '':
                                ip.dst = ni.clientIP6
                            else:
                                ip.dst = NetworkInfo.netPToN(ipv6=ni.clientNatRule[1])
                    elif isinstance(flk, Ipv4FlowKey):
                        if (type(ni.serverIP4) == int):
                            if ni.serverNatRule == '':
                                ip.src = ni.serverIP4
                            else:
                                ip.src = NetworkInfo.netPToN(ipv4=ni.serverNatRule[1])
                        if (type(ni.clientIP4) == int):
                            if ni.clientNatRule == '':
                                ip.dst = ni.clientIP4
                            else:
                                ip.dst = NetworkInfo.netPToN(ipv4=ni.clientNatRule[1])
                    if not pkt.src in self.fixedMacAddr:
                        if (ni.serverMAC != ''):
                            pkt.src = ni.serverMAC
                    if not pkt.dst in self.fixedMacAddr:
                        if (ni.clientMAC != ''):
                            pkt.dst = ni.clientMAC
                    if vlan and ni.vlanId != '':
                        vlan.vlan = int(ni.vlanId)
                sendIf = serverPcapC

            # Send packet over client or server interfaces dependent
            # on the packet flowkey
            chain = pkt.chain()

            # Fixup the length and checksums of the current chain
            if fixup:
                chain.fixup()
            chain.encode()
            retPkts.append((seq, chain, sendIf))
        return retPkts

    def replay(self, netInfo, clientPcapC, serverPcapC, triggers=None,
                   delay=500, fixup=True, listPkts=False, verify=REPLAY_NO_VERIFY, gateway=0):
        """
        Replay all flow packets over specified client and server
        network interfaces. These packets are divided up and replayed
        based on flowkey associations.

        @param clientPcapC:
            The PcapConnector for the client interface

        @param serverPcapC:
            The PcapConnector for the server interface

        @param triggers:
            A list of triggers to apply to the replay of flows
            that are actioned upon when conditions for a trigger are met

        @param delay:
            Time (in ms) to delay between packet transmit

        @param fixup:
            Boolean indicating whether to fixup packet layer-2/layer-3
            information

        @param listPkts:
            Boolean indicating whether to list details of the packets being
            replayed

        @param verify:
            Code dictating verify behaviour; of the following format:
                - L{Flow.REPLAY_NO_VERIFY} - do not verify
                - L{Flow.REPLAY_QUIET_FULL_VERIFY} - verify; drops and errors, do not display results to STDOUT
                - L{Flow.REPLAY_FULL_VERIFY} - verify; drops and errors, display results to STDOUT
                - L{Flow.REPLAY_QUIET_DROPPASS_VERIFY} - verify; errors, do not display results to STDOUT
                - L{Flow.REPLAY_DROPPASS_VERIFY} - verify; errors, display results to STDOUT

        @param gateway:
            Number of routers flow passing

        @return:
            Returns a dictionary listing all measured packet counts using various
            keys:
                - L{Flow.PACKET_COUNTER_TOTAL} - total packets processed
                - L{Flow.PACKET_COUNTER_PASSED} - packets that passed
                - L{Flow.PACKET_COUNTER_FAILED} - packets that failed
                - L{Flow.PACKET_COUNTER_DROPPED} - packets that were dropped
                - L{Flow.PACKET_COUNTER_SKIPPED} - packets that were skipped
            With the exception of the total counter, these counters are only
            valid when the replay is being verified (zero otherwise).
        """
        retPkts = self.getReplayPktList(netInfo, clientPcapC, serverPcapC, fixup)
        return Flow.replayPkts(netInfo, retPkts, clientPcapC, serverPcapC, triggers, delay,
                        listPkts, verify, gateway)

    @staticmethod
    def replayPkts(netInfo, tupleList, clientPcapC, serverPcapC, triggers=None, delay=500,
                   listPkts=False, verify=0, gateway=0):
        """
        A static method.
        Replay a sequenced list of packets while handling trigger, display and
        delay actions
        
        @param netInfo:
            NetworkInfo instance containing information about the server and
            client network interfaces
            
        @param tupleList:
            A list of packet tuples of the format (seqNo, chain, egressIf)

        @param clientPcapC:
            The PcapConnector for the client interface

        @param serverPcapC:
            The PcapConnector for the server interface

        @param triggers:
            A list of triggers to apply to the replay of flows that are actioned
            upon when conditions for a trigger are met

        @param delay:
            Time (in ms) to delay between packet transmit

        @param listPkts:
            Boolean indicating whether to list details of the packets being
            replayed

        @param verify:
            Code dictating verify behaviour; of the following format:
                - L{Flow.REPLAY_NO_VERIFY} - do not verify
                - L{Flow.REPLAY_QUIET_FULL_VERIFY} - verify; drops and errors, do not display results to STDOUT
                - L{Flow.REPLAY_FULL_VERIFY} - verify; drops and errors, display results to STDOUT
                - L{Flow.REPLAY_QUIET_DROPPASS_VERIFY} - verify; errors, do not display results to STDOUT
                - L{Flow.REPLAY_DROPPASS_VERIFY} - verify; errors, display results to STDOUT

        @param gateway:
            Number of routers flow passing

        @return:
            Returns a dictionary listing all measured packet counts using various
            keys:
                - L{Flow.PACKET_COUNTER_TOTAL} - total packets processed
                - L{Flow.PACKET_COUNTER_PASSED} - packets that passed
                - L{Flow.PACKET_COUNTER_FAILED} - packets that failed
                - L{Flow.PACKET_COUNTER_DROPPED} - packets that were dropped
                - L{Flow.PACKET_COUNTER_SKIPPED} - packets that were skipped
            With the exception of the total counter, these counters are only
            valid when the replay is being verified (zero otherwise).
        """
        # Packet counters
        verifySuccessCount = 0
        verifyFailureCount = 0
        verifyDropCount = 0
        verifySkipCount = 0

        # Sanity check arguments
        if clientPcapC is None or serverPcapC is None:
            raise PcapReplayError(ERR_PCAPR_FLOW_INVALID_IF,
                                  'replayPkts : Invalid PcapConnectors ' +
                                  'for replay.')
        if tupleList is None or tupleList == []:
            return

        # Set the capture direction of the PcapConnectors to ingress
        # as we are only interested in what is received
        clientPcapC.setdirection(pcap.PCAP_D_IN)
        serverPcapC.setdirection(pcap.PCAP_D_IN)

        # Iterate over the list of tuples and action on each packet
        for seq, chain, sendP in tupleList:
            skipVerify = True

            # Set the filter addresses for packets
            sendEther, sendEtherPos = chain.find_first_of(ethernet)
            sendVlan, sendVlanPos =  chain.find_first_of(vlan)
            sendIP, sendIPPos = chain.find_first_of(ipv4)

            # If not IPv4, check for IPv6
            if (sendIP, sendIPPos) == (None, None):
                sendIP, sendIPPos = chain.find_first_of(ipv6)

            if (type(sendIP) == pcs.packets.ipv4.ipv4 or
                type(sendIP) == pcs.packets.ipv6.ipv6):
                if type(sendIP.src) == int or type(sendIP.src) == long:
                    sAddr = NetworkInfo.netNToP(ipv4=sendIP.src)
                    dAddr = NetworkInfo.netNToP(ipv4=sendIP.dst)
                else:
                    sAddr = NetworkInfo.netNToP(ipv6=sendIP.src)
                    dAddr = NetworkInfo.netNToP(ipv6=sendIP.dst)
                # Overwrite source/destination address with NAT address
                if netInfo.serverNatRule != '':
                    if sendP == clientPcapC:
                        dAddr = netInfo.serverNatRule[1]
                    elif sendP == serverPcapC:
                        sAddr = netInfo.serverNatRule[0]
                if netInfo.clientNatRule != '':
                    if sendP == clientPcapC:
                        sAddr = netInfo.clientNatRule[1]
                    elif sendP == serverPcapC:
                        dAddr = netInfo.clientNatRule[0]
            else:
                sAddr = NetworkInfo.macNToP(sendEther.src)
                dAddr = NetworkInfo.macNToP(sendEther.dst)

            # Set up for packet verification
            if (verify != Flow.REPLAY_NO_VERIFY):
                # Set the receiving interface
                recvP = clientPcapC
                if recvP == sendP:
                    recvP = serverPcapC

                # Set the reception filter to avoid miscellaneous mismatches
                if (type(sendIP) == pcs.packets.ipv4.ipv4 or
                    type(sendIP) == pcs.packets.ipv6.ipv6):
                    skipVerify = False
                    pcapFilter = 'host %s and host %s' % (sAddr, dAddr)
                else:
                    pcapFilter = 'ether host %s and ether host %s' % (sAddr, dAddr)

                # Don't use vlan online filter by libpcap due to bugs
                #if sendVlan:
                #    pcapFilter = 'vlan %s and ' %sendVlan.vlan + pcapFilter

                recvP.setfilter(pcapFilter)

            # Set up trigger actioning
            if triggers != None and triggers != []:
                # Set the reception filter to avoid miscellaneous mismatches
                if (type(sendIP) == pcs.packets.ipv4.ipv4 or
                    type(sendIP) == pcs.packets.ipv6.ipv6):
                    skipVerify = False
                    pcapFilter = 'host %s and host %s' % (sAddr, dAddr)
                else:
                    pcapFilter = 'ether host %s and ether host %s' % (sAddr, dAddr)

                # Don't use vlan online filter of libpcap due to it has bug
                #if sendVlan:
                #    pcapFilter = 'vlan %s and' %sendVlan.vlan + pcapFilter

                sendP.setfilter(pcapFilter)

            # List packet if required
            if listPkts:
                print '-------------------------------------------------------'
                print '[Packet %d]' % seq
                print chain

            # Send packet
            sendP.write(chain.bytes, len(chain.bytes))

            # Verify packets being transmitted
            if (verify != Flow.REPLAY_NO_VERIFY):
                # Read in a packet and do the verification
                if not recvP.poll_read(1):
                    readPkt = TimeoutMethod(recvP.read_packet, 1)
                    try:
                        recv = readPkt()
                        # Filter out non-Vlan packet by ourselves
                        if sendVlan and (None, None) == recv.chain().find_first_of(vlan):
                            raise TimeoutMethodException()
                    except TimeoutMethodException:
                        verifyDropCount += 1
                        if (verify == Flow.REPLAY_FULL_VERIFY or
                            verify == Flow.REPLAY_DROPPASS_VERIFY):
                            print '-- Packet verify failed. Xmit not received.'
                            print '--------------------------------------------'
                            print '>>> [Packet %d] sent:' % seq
                            if sendVlan:
                                print sendVlan
                            print sendIP
                            print '--------------------------------------------'
                    else:
                        # Set the filter addresses for packets
                        recvEther, recvEtherPos = recv.chain().find_first_of(ethernet)
                        recvVlan, recvVlanPos =  recv.chain().find_first_of(vlan)
                        recvIP, recvIPPos = recv.chain().find_first_of(ipv4)
                        
                        # On some OS platforms, CFI bit always got cleared after forwarding
                        # Copy it from sending-side here since we don't care about CFI bit
                        if recvVlan != None and sendVlan != None:
                            recvVlan.cfi = sendVlan.cfi

                        # If not IPv4, check for IPv6
                        if (recvIP, recvIPPos) == (None, None):
                            recvIP, recvIPPos = chain.find_first_of(ipv6)
                        # If traffic passing gateway, update ttl
                        if gateway != 0 and type(sendIP) == ipv4:
                            sendIP.ttl -= gateway
                            sendIP.calc_checksum()
                        # Update the source/destination address if NAT rule is specified
                        if netInfo.serverNatRule != '':
                            if type(sendIP) == ipv4:
                                if sendP == clientPcapC:
                                    sendIP.dst = NetworkInfo.netPToN(ipv4=netInfo.serverNatRule[1])
                                    sendIP.calc_checksum()
                                elif sendP == serverPcapC:
                                    sendIP.src = NetworkInfo.netPToN(ipv4=netInfo.serverNatRule[0])
                                    sendIP.calc_checksum()
                            elif type(sendIP) == ipv6:
                                if sendP == clientPcapC:
                                    sendIP.dst = NetworkInfo.netPToN(ipv6=netInfo.serverNatRule[1])
                                    sendIP.calc_checksum()
                                elif sendP == serverPcapC:
                                    sendIP.src = NetworkInfo.netPToN(ipv6=netInfo.serverNatRule[0])
                                    sendIP.calc_checksum()

                        if netInfo.clientNatRule != '':
                            if type(sendIP) == ipv4:
                                if sendP == clientPcapC:
                                    sendIP.src = NetworkInfo.netPToN(ipv4=netInfo.clientNatRule[1])
                                    sendIP.calc_checksum()
                                elif sendP == serverPcapC:
                                    sendIP.dst = NetworkInfo.netPToN(ipv4=netInfo.clientNatRule[0])
                                    sendIP.calc_checksum()
                            elif type(sendIP) == ipv6:
                                if sendP == clientPcapC:
                                    sendIP.dst = NetworkInfo.netPToN(ipv6=netInfo.clientNatRule[1])
                                    sendIP.calc_checksum()
                                elif sendP == serverPcapC:
                                    sendIP.src = NetworkInfo.netPToN(ipv6=netInfo.clientNatRule[0])
                                    sendIP.calc_checksum()

                        if (not skipVerify and
                            (recvIP.src != sendIP.src or
                             recvIP.dst != sendIP.dst or
                             recvIPPos != sendIPPos or
                             recvVlanPos != sendVlanPos or
                             #recvVlan != sendVlan or
                             # Some OS platform always change CFI bit after forwarding,
                             # so compare only the vlan id, priority and type inf VLAN tag
                             # defined in: lib64/python2.7/site-packages/pcs/packets/vlan.py
                             type(recvVlan) != type(sendVlan) or
                             (recvVlan and sendVlan and 
                              (recvVlan.vlan != sendVlan.vlan or
                               recvVlan.p != sendVlan.p or
                               recvVlan.type != sendVlan.type)) or
                             (type(sendIP.src) == int and
                              recvIP.checksum != sendIP.checksum))):

                            verifyFailureCount += 1
                            if (verify == Flow.REPLAY_FULL_VERIFY or
                                verify == Flow.REPLAY_DROPPASS_VERIFY):
                                print '-- Packet verify failed. Xmit mismatch.'
                                print '----------------------' + \
                                      '----------------------'

                                print '>>> [Packet %d] sent:' % seq
                                if sendVlan:
                                    print sendVlan
                                print sendIP
                                print '----------------------' + \
                                      '----------------------'
                                print '>>> [Packet %d] received:' % seq
                                if recvVlan:
                                    print recvVlan
                                print recvIP
                                print '----------------------' + \
                                      '----------------------'
                        elif skipVerify:
                            verifySkipCount += 1
                            if (verify == Flow.REPLAY_FULL_VERIFY or
                                verify == Flow.REPLAY_DROPPASS_VERIFY):
                                print '++ [Packet %d] verification skipped.' % \
                                      seq
                        else:
                            verifySuccessCount += 1
                            if (verify == Flow.REPLAY_FULL_VERIFY or
                                verify == Flow.REPLAY_DROPPASS_VERIFY):
                                print '++ [Packet %d] verified.' % seq
                elif skipVerify:
                    verifySkipCount += 1
                    if (verify == Flow.REPLAY_FULL_VERIFY or
                        verify == Flow.REPLAY_DROPPASS_VERIFY):
                        print '++ [Packet %d] verification skipped.' % seq
                else:
                    verifyDropCount += 1
                    if (verify == Flow.REPLAY_FULL_VERIFY or
                        verify == Flow.REPLAY_DROPPASS_VERIFY):
                        print '-- Packet verify failed. Xmit not received.'
                        print '--------------------------------------------'
                        print '>>> [Packet %d] sent:' % seq
                        if sendVlan:
                            print sendVlan
                        print sendIP
                        print '--------------------------------------------'

                # Reset filter
                recvP.setfilter('')

            # Iterate through triggers; test and execute if required
            if triggers != None and triggers != []:
                if not sendP.poll_read(1):
                    readPkt = TimeoutMethod(sendP.read_packet, 1)
                    try:
                        reply = readPkt()
                    except TimeoutMethodException:
                        pass
                    else:
                        for t in triggers:
                            if t.testTrigger(reply):
                                c = t.executeTrigger(reply)
                                if c is not None:
                                    sendP.write(c.bytes, len(c.bytes))
                                if t.action == Trigger.STOP:
                                    print 'Replay halted. ' + \
                                          'Trigger "%s" executed' % \
                                          (','.join([t.proto, t.type, '%s' %
                                                     t.value, t.action]))

                                    # Reset filter
                                    sendP.setfilter('')
                                    return

                # Reset filter
                sendP.setfilter('')

            # Honour transmit delay
            if delay >= 0:
                time.sleep(delay / 1000.0)

        # If a verify failure occurred, raise an error now all packets have
        # been processed
        if (verifyFailureCount > 0):
            raise  PcapReplayError(ERR_PCAPR_FLOW_VERIFY,
                                   '%d packets sent : ' % len(tupleList) +
                                   '%d verified, ' % verifySuccessCount +
                                   '%d verify skipped, ' % verifySkipCount +
                                   '%d verify failed, ' % verifyFailureCount +
                                   '%d dropped' % verifyDropCount)
        elif (verifyDropCount > 0 and
              (verify == Flow.REPLAY_FULL_VERIFY or
               verify == Flow.REPLAY_QUIET_FULL_VERIFY)):
            raise  PcapReplayError(ERR_PCAPR_FLOW_VERIFY,
                                   '%d packets sent : ' % len(tupleList) +
                                   '%d verified, ' % verifySuccessCount +
                                   '%d verify skipped, ' % verifySkipCount +
                                   '%d verify failed, ' % verifyFailureCount +
                                   '%d dropped' % verifyDropCount)
        elif (verify == Flow.REPLAY_FULL_VERIFY or
              verify == Flow.REPLAY_DROPPASS_VERIFY):
            print ('Success : %d packets sent : ' % len(tupleList) +
                   '%d verified, ' % verifySuccessCount +
                   '%d verify skipped, ' % verifySkipCount +
                   '%d verify failed, ' % verifyFailureCount +
                   '%d dropped' % verifyDropCount)

        # Return packet counts
        return {Flow.PACKET_COUNTER_TOTAL : len(tupleList),
                Flow.PACKET_COUNTER_PASSED : verifySuccessCount,
                Flow.PACKET_COUNTER_FAILED : verifyFailureCount,
                Flow.PACKET_COUNTER_DROPPED : verifyDropCount,
                Flow.PACKET_COUNTER_SKIPPED : verifySkipCount}

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
        # Flow's flowKeyCfg should never be called as Flow is not a valid
        # type for a real-world flow
        raise PcapReplayError(PcapReplayError.ERR_PCAPR_IMPL,
                              'Flow.flowKeyC() called')
        # To quiet down pylint :)
        return None

class FlowFactory:
    """
    Creates flows based on specified flow types
    """
    ##
    # Constants

    ##
    # Class Fields
    flowTypes = {TCP: 'TcpFlow', UDP: 'UdpFlow',
                 ICMP: 'IcmpFlow', GENERIC: 'GenericFlow'}
    """A supported flow types"""

    ##
    # Methods
    @staticmethod
    def getFlowClass(proto):
        """
        A static method.
        Returns the appropriate class of a L{Flow} based on protocol

        @param proto:
            The protocol whose L{Flow} class is to be returned

        @return:
            The class of the L{Flow} to be returned
        """
        module = 'atf.common.pcapreplay.flow.' + FlowFactory.flowTypes[proto]
        m = __import__(module)
        module += '.' + FlowFactory.flowTypes[proto]
        for comp in module.split('.')[1:]:
            m = getattr(m, comp)
        return m

    @staticmethod
    def getFlow(proto, diagLevel=logging.ERROR):
        """
        A static method.
        Allocates a new L{Flow} instance by returning an appropriately typed
        L{Flow}

        @param proto:
            The protocol associated with the L{Flow} to be created

        @return:
            An appropriately typed L{Flow}
        """
        return FlowFactory.getFlowClass(proto)(diagLevel=diagLevel)
