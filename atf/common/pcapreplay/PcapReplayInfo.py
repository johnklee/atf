# System
import struct, commands
from socket import inet_ntop, inet_pton, AF_INET, AF_INET6

# PCS

# PcapReplay
from PcapReplayBase import *

##
# Globals

##
# Classes
class NetworkInfo(PcapReplayObject):
    """
    NetworkInfo contains all the information required for the replay of 
    a Flow. This is inclusive of FlowKey parameters and MAC addresses
    """
    ##
    # Constants

    ##
    # Class Fields
 
    ##
    # Methods
    def __init__(self, diagLevel=logging.ERROR):
        """
        NetworkInfo's constructor.
        
        @param diagLevel:
            The desired level of logging
        """
        PcapReplayObject.__init__(self, diagLevel)
        self.clientIP4 = 0
        """Client's IPv4 address"""
        self.clientIP6 = ''
        """Client's IPv6 address"""
        self.clientMAC = ''
        """Client's MAC address"""
        self.serverIP4 = 0
        """Server's IPv4 address"""
        self.serverIP6 = ''
        """Server's IPv6 address"""
        self.serverMAC = ''
        """Server's MAC address"""
        self.vlanId = ''
        """VLAN ID"""
        self.ifaceC = ''
        """Client's network interface"""
        self.ifaceS = ''
        """Server's network interface"""
        self.clientIsIpv4 = False 
        """Client's IPv4 indicator"""
        self.clientIsIpv6 = False 
        """Client's IPv6 indicator"""
        self.serverIsIpv4 = False 
        """Server's IPv4 indicator"""
        self.serverIsIpv6 = False
        """Server's IPv6 indicator"""
        self.clientNatRule = ''
        """A tuple of client NAT rule format (ClientIP, Natted ClientIP)"""
        self.serverNatRule = ''
        """A tuple of server NAT rule format (serverIP, Natted ServerIP)"""
    def _ip(self, ifname):
        ifreq = {'ifname': ifname}
        ipDump = commands.getoutput('/sbin/ip addr list %s' % ifname)
        ipDump = map(lambda x: x.lstrip().rstrip(), ipDump.split('\n'))
        parse = ipDump[1].split('link/ether ')
        if len(parse) > 1:
            ifreq['hwaddr'] = parse[1].split(' ')[0]
        else:
            ifreq['hwaddr'] = '00:00:00:00:00:00'
        for line in ipDump:
            l = line.split()
            if len(l) > 0 and l[0] == 'inet':
                ifreq['addr'] = l[1].split('/')[0]
            elif len(l) > 0 and l[0] == 'inet6':
                ifreq['in6addr'] = l[1].split('/')[0]
        return ifreq
        
    def _ifconfig(self, ifname):
        """
        Gathering of interface information associated with a named 
        interface.

        @param ifname:
            The interface name

        @return:
            A dict of interface information
        """
        ifreq = {'ifname': ifname}
        ifcfgDump = commands.getoutput('/sbin/ifconfig %s' % ifname)
        ifcfgDump = map(lambda x: x.lstrip().rstrip(), ifcfgDump.split('\n'))
        parse = ifcfgDump[0].split('HWaddr ')
        if len(parse) > 1:
            ifreq['hwaddr'] = parse[1] 
        else:
            ifreq['hwaddr'] = '00:00:00:00:00:00'
        for line in ifcfgDump:
            l = line.split()
            if len(l) > 0 and l[0] == 'inet':
                ifreq['addr'] = l[1].split('addr:')[1]
            elif len(l) > 0 and l[0] == 'inet6':
                ifreq['in6addr'] = l[2].split('/')[0]
        return ifreq

    def _listInterfaces(self):
        """
        List all active interfaces on the current system.

        @return:
            A list of all active interfaces excluding the loopback interface
        """
        cmd = '/sbin/ifconfig | grep "HWaddr" | awk \'{print $1}\''
        ifstr = commands.getoutput(cmd)
        ifs = ifstr.split()
        return ifs

    def setNetworkInfo(self, ifaceC='', ifaceS='', clientMAC='', serverMAC='',
                       clientIP4='', serverIP4='', clientIP6='', serverIP6='',
                       vlanId='', clientNatIP4='', serverNatIP4='', clientNatIP6='', serverNatIP6=''):
        """
        Set all network information pertinent to the replay of flows.

        @param ifaceC:
            The client's network interface
            
        @param ifaceS:
            The server's network interface
            
        @param clientMAC:
            The client's MAC address
            
        @param serverMAC:
            The server's MAC address
            
        @param clientIP4:
            The client's IPv4 address (if any)
            
        @param serverIP4:
            The server's IPv4 address (if any)
            
        @param clientIP6:
            The client's IPv6 address (if any)
            
        @param serverIP6:
            The server's IPv6 address (if any)

        @param vlanId:
            VLAN ID

        @param clientNatIP4:
            The client's NAT IPv4 address

        @param serverNatP4:
            The server's NAT IPv4 address

        @param clientNatIP6
            The client's NAT IPv6 address

        @param serverNatIP6
            The server's NAT IPv6 address
        """
        self.clientIP4 = NetworkInfo.netPToN(ipv4=clientIP4)
        self.clientIP6 = NetworkInfo.netPToN(ipv6=clientIP6)
        self.clientMAC = NetworkInfo.macPToN(clientMAC)
        self.serverIP4 = NetworkInfo.netPToN(ipv4=serverIP4)
        self.serverIP6 = NetworkInfo.netPToN(ipv6=serverIP6)
        self.serverMAC = NetworkInfo.macPToN(serverMAC)
        self.vlanId = vlanId
        self.ifaceC = ifaceC
        self.ifaceS = ifaceS

        if clientIP4 == '':
            self.clientIsIpv4 = False
        else:
            self.clientIsIpv4 = True
            if clientNatIP4 != '':
                self.clientNatRule = (clientIP4, clientNatIP4)
        if clientIP6 == '':
            self.clientIsIpv6 = False
        else:
            self.clientIsIpv6 = True
            if clientNatIP6 != '':
                self.clientNatRule = (clientIP6, clientNatIP6)
        if serverIP4 == '':
            self.serverIsIpv4 = False
        else:
            self.serverIsIpv4 = True
            if serverNatIP4 != '':
                self.serverNatRule = (serverIP4, serverNatIP4)
        if serverIP6 == '':
            self.serverIsIpv6 = False
        else:
            self.serverIsIpv6 = True
            if serverNatIP6 != '':
                self.serverNatRule = (serverIP6, serverNatIP6)

    def calculateNetworkInfo(self, ifaceC='', ifaceS=''):
        """
        Based on client and server interfaces, discover the information 
        pertinent to a flow replay inclusive of source and destination IP 
        and MAC addresses.

        @param ifaceC:
            The client's network interface
            
        @param ifaceS:
            The server's network interface
        """
        # Source information can be filled out from the interface alone
        # assuming it is active. First the client interface ...
        if (ifaceC != ''):
            self.ifaceC = ifaceC
        if (self.ifaceC != ''):
            ifInfo = self._ip(self.ifaceC)
            if ifInfo.has_key('addr'):  
                self.clientIP4 = NetworkInfo.netPToN(ipv4=ifInfo['addr'])             
                self.clientIsIpv4 = True
            else:
                self.clientIP4 = 0
                self.clientIsIpv4 = False
            if ifInfo.has_key('in6addr'):  
                self.clientIP6 = NetworkInfo.netPToN(ipv6=ifInfo['in6addr'])
                self.clientIsIpv6 = True
            else:
                self.clientIP6 = ''
                self.clientIsIpv6 = False
            self.clientMAC = NetworkInfo.macPToN(ifInfo['hwaddr'])

        # ... then the server interface
        if (ifaceS != ''):
            self.ifaceS = ifaceS
        if (self.ifaceS != ''):
            ifInfo = self._ip(self.ifaceS)
            if ifInfo.has_key('addr'):  
                self.serverIP4 = NetworkInfo.netPToN(ipv4=ifInfo['addr'])             
                self.serverIsIpv4 = True
            else:
                self.serverIP4 = 0
                self.serverIsIpv4 = False
            if ifInfo.has_key('in6addr'):  
                self.serverIP6 = NetworkInfo.netPToN(ipv6=ifInfo['in6addr'])
                self.serverIsIpv6 = True
            else:
                self.serverIP6 = ''
                self.serverIsIpv6 = False
            self.serverMAC = NetworkInfo.macPToN(ifInfo['hwaddr'])

    @staticmethod
    def macPToN(mac):
        """
        A static method.
        Adjust a MAC address from text to "network" format.
        
        @param mac:
            The mac address to adjust
            
        @return:
            The adjusted address or '' if blank
        """
        #  Blank argument - return '' for initialization
        if mac == '':
            return ''
        
        #  Calculate adjusted address
        try:
            retMAC = ''
            m = mac.split(':')
            for i in range(0,len(m)):
                m[i] = '%c' % (int(m[i], 16))
            retMAC = ''.join(m)
        except Exception, error:
            raise PcapReplayError(PcapReplayError.ERR_PCAPR_NET, 
                                  'macPToN() : MAC Address invalid')
        return retMAC

    @staticmethod
    def macNToP(mac):
        """
        A static method.
        Adjust a MAC address from "network" to test format.
        
        @param mac:
            The mac address to adjust
            
        @return:
            The adjusted address or '' if blank
        """
        #  Blank argument - return '' for initialization
        if mac == '':
            return ''
        
        #  Calculate adjusted address
        try:
            retMAC = ''
            m = []
            for c in range(0,6):
                if len(mac) > c:
                    m.append('%x' % ord(mac[c]))
                else:
                    m.append('0')
            retMAC = ':'.join(m)
        except Exception, error:
            print error
            raise PcapReplayError(PcapReplayError.ERR_PCAPR_NET, 
                                  'macNToP() : MAC Address invalid')
        return retMAC

    @staticmethod
    def netPToN(ipv4='', ipv6=''):
        """
        A static method.
        Adjust a IPv4 or IPv6 address from text to network format.
        
        @param ipv4:
            An ipv4 address to adjust -- mutually exclusive to ipv6
            
        @param ipv6:
            An ipv6 address to adjust -- mutually exclusive to ipv4
            
        @return:
            The adjusted address or '' if blank
        """
        #  Blank arguments - return '' for initialization
        if ipv4 == '' and ipv6 == '':
            return ''
        
        #  Calculate adjusted address
        if ipv4 != '' and ipv6 != '':
            raise PcapReplayError(PcapReplayError.ERR_PCAPR_ARGS,
                                  'netPToN() : Only one of ipv4 ' +
                                  ' or ipv6 maybe adjusted at one time.')
            
        try:
            addr = ''
            if ipv4 != '':
                addr = struct.unpack('!L', inet_pton(AF_INET, ipv4))[0]
            elif ipv6 != '':
                addr = inet_pton(AF_INET6, ipv6)
        except Exception, error:
            raise PcapReplayError(PcapReplayError.ERR_PCAPR_NET,
                                  'netPToN() : Network address invalid.')
        return addr
    
    @staticmethod
    def netNToP(ipv4='', ipv6=''):
        """
        A static method.
        Adjust a IPv4 or IPv6 address from text to network format.
        
        @param ipv4:
            An ipv4 address to adjust -- mutually exclusive to ipv6
            
        @param ipv6:
            An ipv6 address to adjust -- mutually exclusive to ipv4
            
        @return:
            The adjusted address or '' if blank
        """
        #  Blank arguments - return '' for initialization
        if ipv4 == '' and ipv6 == '':
            return ''
        
        #  Calculate adjusted address
        if ipv4 != '' and ipv6 != '':
            raise PcapReplayError(PcapReplayError.ERR_PCAPR_ARGS,
                                  'netNtoP() : Only one of ipv4 ' +
                                  ' or ipv6 maybe adjusted at one time.')
            
        try:
            addr = ''
            if ipv4 != '':
                addr = inet_ntop(AF_INET, struct.pack('!L', ipv4))
            elif ipv6 != '':
                addr = inet_ntop(AF_INET6, ipv6)
        except Exception, error:
            raise PcapReplayError(PcapReplayError.ERR_PCAPR_NET,
                                  'netNToP() : Network address invalid.')
        return addr
    
