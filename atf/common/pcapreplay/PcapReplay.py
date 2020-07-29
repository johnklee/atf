# System

# PCS
import pcs
from pcs.packets.udp import *
from pcs.packets.tcp import *
from pcs.packets.ipv4 import *
from pcs.packets.ethernet import *

# PcapReplay
import flow.Flow as Flow
import flow.TcpFlow as TcpFlow
from PcapReplayBase import *
from flow.Flow import FlowFactory
from Protocol import *

##
# Globals

##
# Classes
class PcapReplay(PcapReplayObject):
    """
    PcapReplay contains all information and operatives that are associated 
    with all TcpFlows contained within a give packet list.

    Beyond storage of these flows, this class provides the mechanisms 
    associated with parsing a "raw" list of packets.
    """
    ##
    # Constants

    ##
    # Class Fields
 
    ##
    # Methods
    def __init__(self, diagLevel=logging.ERROR):
        """
        PcapReplay's constructor.
        
        @param diagLevel:
            The desired level of logging
        """
        PcapReplayObject.__init__(self, diagLevel)
        self.flowlessTcpPkts = []
        """A list of all flowless TCP packets"""
        self.pktList = {TCP: [], UDP: [], ICMP: [], GENERIC: []}
        """A map of all packets to protocol"""
        self.flows = {TCP: {}, UDP: {}, ICMP: {}, GENERIC: {}}
        """A map of all flows to protocol"""
        self.seqNum = 0
        """Capture file ordered sequence number"""
        
    def parsePacketList(self, pktList):
        """
        Parses a packet list and appends each packet to the appropriate 
        protocol packet list

        @param pktList:
            The list of packets to be parsed
        """
        # We are only interested in TCP, UDP and ICMP traffic
        for pkt in pktList:
            if (type(pkt.data) == pcs.packets.ipv4.ipv4 or
                type(pkt.data) == pcs.packets.ipv6.ipv6):
                ip = pkt.data
                if type(ip.data) == pcs.packets.tcp.tcp:
                    self.pktList[TCP].append((self.seqNum, pkt))
                elif type(ip.data) == pcs.packets.udp.udp:
                    self.pktList[UDP].append((self.seqNum, pkt))
                elif type(ip.data) == pcs.packets.icmpv4.icmpv4 or \
                     type(ip.data) == pcs.packets.icmpv6.icmpv6:
                    self.pktList[ICMP].append((self.seqNum, pkt))
                else:
                    self.pktList[GENERIC].append((self.seqNum, pkt))
            else:
                self.pktList[GENERIC].append((self.seqNum, pkt))
                
            # Increment sequence
            self.seqNum += 1
       
    def parsePcapFile(self, file):
        """
        Parses the named pcap file and appends to the raw protocol packet
        lists

        @param file:
            The name of the capture file to be parsed
        """
        pktList = []
    
        # Attempt to read the capture file
        try:
            file = pcs.PcapConnector(file)
        except Exception, error:
            raise PcapReplayError(PcapReplayError.ERR_PCAPR_FILE,
                                  'processPcapFile() : Error parsing "%s" : %s' % 
                                  (file, error))
        while True:
            # This is a hacky way of completing a read in the 
            # absence of a true iterator
            try:
                pkt = file.read()
            except:
                break
            ether = ethernet(pkt[0:len(pkt)])
            pktList.append(ether)
        self.parsePacketList(pktList)
        
    def clear(self):
        """
        Clears all flows and packets from PcapReplay 
        """
        self.flowlessTcpPkts = []
        self.pktList = {TCP: [], UDP: [], ICMP: [], GENERIC: []}
        self.flows = {TCP: {}, UDP: {}, ICMP: {}, GENERIC: {}}
        self.seqNum = 0

    def getFlow(self, flowKey):
        """
        Returns flow corresponding to a given flowkey

        @param flowKey:
            The flowkey that matches the flow to be retrieved
            
        @return:
            The requested flow, None otherwise
        """
        retFlow = None
        protoFlows = self.getFlows(flowKey.proto)
        if flowKey in protoFlows:
            retFlow = protoFlows[flowKey]
        return retFlow

    def getFlows(self, proto):
        """
        Returns flows of a specified protocol type.

        @param proto:
            The protocol whose flows should be returned
            
        @return:
            A dictionary of flows keyed on flowkey to flow.
        """
        if proto == '' or not self.flows.has_key(proto):
            return {}
        else:
            return self.flows[proto] 

    def getFlowDictionary(self):
        """
        Returns the flow dictionary containing all flows for all protocols.

        @return:
            The dictionary of all flows keyed on protocol to flowkey to flow.
        """
        return self.flows

    def _processTcpFlows(self):
        """
        Parses all packets within the TCP packet list and separates out all
        TCP flows that have connected as separate TcpFlows.
        """
        for seq, pkt in self.pktList[TCP]:
            if (type(pkt.data) == pcs.packets.ipv4.ipv4 or
                type(pkt.data) == pcs.packets.ipv6.ipv6):
                ip = pkt.data
                tcp = ip.data
            else:
                continue

            # Based on packet type, build up flow view
            # Note: These conditional blocks are *ordered*
            addedToFlow = False
            flow = None
            flk = TcpFlow.TcpFlow.flowKeyCreate(pkt)
            rfk = flk.reverse()
            if flk in self.flows[TCP]:
                flow = self.flows[TCP][flk]
            elif rfk in self.flows[TCP]: 
                flow = self.flows[TCP][rfk]
            if tcp.fin and tcp.push and tcp.ack:
                if flow is not None:
                    lastPkt = flow.getLastPacket()
                    if lastPkt != None:
                        lip = lastPkt.data
                        ltcp = lip.data
                        if (flow.flowConnected and
                            tcp.sequence == ltcp.ack_number):
                            flow.addPacket((seq, pkt))
                            if not flow.flowActvClose:
                                flow.flowActvClose = True
                            elif not flow.flowPasvClose:
                                flow.flowPasvClose = True
                            addedToFlow = True
            elif tcp.push and tcp.ack:
                if flow is not None:
                    plLen = flow.getLastPayloadLength()
                    lastPkt = flow.getLastPacket()
                    if lastPkt != None:
                        lip = lastPkt.data
                        ltcp = lip.data
                        if (flow.flowConnected and
                            ((tcp.sequence == ltcp.sequence + plLen and
                              tcp.ack_number == ltcp.ack_number) or
                             tcp.ack_number == ltcp.sequence + plLen or
                             tcp.sequence == ltcp.sequence or
                             tcp.sequence == ltcp.ack_number)):
                            flow.addPacket((seq, pkt))
                            addedToFlow = True
            elif tcp.fin and tcp.ack:
                if flow is not None:
                    plLen = flow.getLastPayloadLength()
                    lastPkt = flow.getLastPacket()
                    if lastPkt != None:
                        lip = lastPkt.data
                        ltcp = lip.data
                        if (flow.flowConnected and
                            ((tcp.sequence == ltcp.sequence + plLen and
                              tcp.ack_number == ltcp.ack_number) or
                             tcp.ack_number == ltcp.sequence or
                             tcp.sequence == ltcp.ack_number or
                             tcp.sequence == ltcp.sequence)):
                            flow.addPacket((seq, pkt))
                            if not flow.flowActvClose:
                                flow.flowActvClose = True
                            elif not flow.flowPasvClose:
                                flow.flowPasvClose = True
                            addedToFlow = True
            elif tcp.ack and tcp.reset:
                if flow is not None:
                    lastPkt = flow.getLastPacket()
                    if lastPkt != None:
                        lip = lastPkt.data
                        ltcp = lip.data
                        if ((flow.flowConnected and
                             tcp.ack_number == ltcp.ack_number) or
                            tcp.ack_number == ltcp.sequence + 1):
                            flow.addPacket((seq, pkt))
                            flow.flowConnected = False
                            addedToFlow = True
            elif tcp.syn and tcp.ack:
                if flow is not None:
                    lastPkt = flow.getLastPacket()
                    if lastPkt != None:
                        lip = lastPkt.data
                        ltcp = lip.data
                        if ltcp.syn and tcp.ack_number == ltcp.sequence + 1:
                            flow.addPacket((seq, pkt))
                            addedToFlow = True
            elif tcp.syn:
                if flow is None:
                    self.logger.debug("New flow created :\n%s" % (str(flk)))
                    flow = TcpFlow.TcpFlow(diagLevel=self.logger.getEffectiveLevel())
                    self.flows[TCP][flk] = flow
                flow.addPacket((seq, pkt))
                addedToFlow = True
            elif tcp.ack:
                if flow is not None:
                    plLen = flow.getLastPayloadLength()
                    lastPkts = flow.getLastTwoPackets()
                    if len(lastPkts) == 2:
                        lip0 = lastPkts[0].data
                        ltcp0 = lip0.data
                        lip1 = lastPkts[1].data
                        ltcp1 = lip1.data
                        if (not flow.flowConnected and
                            tcp.sequence == ltcp1.sequence + 1 and
                            tcp.ack_number == ltcp0.sequence + 1):
                            flow.addPacket((seq, pkt))
                            flow.flowConnected = True
                            addedToFlow = True
                        elif (flow.flowConnected and
                              (tcp.ack_number == ltcp0.sequence + plLen or
                               (tcp.ack_number == ltcp0.ack_number and
                                tcp.sequence == ltcp0.sequence + plLen) or
                               (tcp.sequence == ltcp0.ack_number) or
                               (tcp.sequence == ltcp0.sequence))):
                            flow.addPacket((seq, pkt))
                            if flow.flowPasvClose:
                                flow.flowActvClose = False
                                flow.flowPasvClose = False
                                flow.flowConnected = False
                            addedToFlow = True

            # The packet has NOT been added to a flow. This, then
            # suggests it is a stray packet and it should be stored
            # for later examination if necessary
            if addedToFlow == False:
                self.flowlessTcpPkts.append(pkt)

    def processFlows(self, simple=False):
        """
        Parses all packets within the packet list and separates out all
        packets into appropriate Flows.

        @param simple:
            Process flows without advanced heuristics governing inclusion
        """
        # Iterate through the known flow types and create as required
        for proto, v in self.flows.items():
            self.logger.debug("Processing '%s' flows", proto)
            # Certain protocols require special handling
            if proto == TCP and not simple:
                self._processTcpFlows()
            else:
                # Default handler for processing of Flows
                for seq, pkt in self.pktList[proto]:
                    flk = FlowFactory.getFlowClass(proto).flowKeyCreate(pkt)
                    rfk = flk.reverse()
                    if flk in self.flows[proto]:
                        flow = self.flows[proto][flk]
                    elif rfk in self.flows[proto]:
                        flow = self.flows[proto][rfk]
                    else:
                        self.logger.debug("New flow created :\n%s" % (str(flk)))
                        flow = FlowFactory.getFlow(proto, diagLevel=self.logger.getEffectiveLevel())
                        self.flows[proto][flk] = flow
                    flow.addPacket((seq, pkt))

    def replayFlows(self, netInfo, clientPcapC, serverPcapC, flowKeys,
                    triggers=None, delay=500, fixup=True, listPkts=False,
                    verify=0, gateway=0):
        """
        Replay all listed flows as indicated by a list of flowkeys, in 
        original capture file order.

        @param netInfo:
            NetworkInfo instance containing information about the server and 
            client network interfaces
        
        @param clientPcapC:
            The client pcap connector over which to replay
        
        @param serverPcapC:
            The server pcap connector over which to replay
        
        @param flowKeys:
            A list of flowkeys that represent the flows that are to be 
            interleaved and replayed
        
        @param triggers:
            A list of triggers to apply to the replay of flows that are 
            actioned upon when conditions for a trigger are met
        
        @param delay:
            Time (in ms) to delay between packet transmit
        
        @param fixup:
            Boolean indicating whether to fixup packet layer-2/layer-3 information
        
        @param listPkts:
            Boolean indicating whether to list details of the packets being replayed
        
        @param verify:
            Code dictating verify behaviour; of the following format:
                - L{Flow.Flow.REPLAY_NO_VERIFY} - do not verify
                - L{Flow.Flow.REPLAY_QUIET_FULL_VERIFY} - verify; drops and errors, do not display results to STDOUT
                - L{Flow.Flow.REPLAY_FULL_VERIFY} - verify; drops and errors, display results to STDOUT
                - L{Flow.Flow.REPLAY_QUIET_DROPPASS_VERIFY} - verify; errors, do not display results to STDOUT
                - L{Flow.Flow.REPLAY_DROPPASS_VERIFY} - verify; errors, display results to STDOUT

        @param gateway:
             Number of routers flow passing

        @return:
            Returns a dictionary listing all measured packet counts using various
            keys:
                - L{Flow.Flow.PACKET_COUNTER_TOTAL} - total packets processed
                - L{Flow.Flow.PACKET_COUNTER_PASSED} - packets that passed
                - L{Flow.Flow.PACKET_COUNTER_FAILED} - packets that failed
                - L{Flow.Flow.PACKET_COUNTER_DROPPED} - packets that were dropped
                - L{Flow.Flow.PACKET_COUNTER_SKIPPED} - packets that were skipped
            With the exception of the total counter, these counters are only 
            valid when the replay is being verified (zero otherwise).
        """
        # Build up a pktList map
        pktLists = {}
        for flk in flowKeys:
            flow = self.getFlow(flk)
            if flow != None:
                fixedPkts = flow.getReplayPktList(netInfo, clientPcapC,
                                             serverPcapC, fixup)
                for seq, pkt, sendIf in fixedPkts:
                    pktLists[seq] = (pkt, sendIf)

        # Create an ordered tuple list from pktLists
        tupleList = [(k, c, i) for k, (c, i) in pktLists.iteritems()]
        tupleList.sort(key=lambda tuple: tuple[0])

        # Iterate through the tupleList
        return Flow.Flow.replayPkts(netInfo, tupleList, clientPcapC, serverPcapC,
                             triggers, delay, listPkts, verify, gateway)
