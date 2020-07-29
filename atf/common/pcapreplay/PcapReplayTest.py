# System
import unittest
import struct
import logging
import array
import os
from socket import inet_ntop, inet_pton, AF_INET, AF_INET6
from atf.common.Common import *

# PCS
import pcs
from pcs.packets.payload import *
from pcs.packets.tcp import *
from pcs.packets.http import *
from pcs.packets.ipv4 import *
from pcs.packets.ipv6 import *
from pcs.packets.ethernet import *

# PcapReplay
import atf.common.pcapreplay
import atf.common.pcapreplay.PcapReplayBase as PcapReplayBase
import atf.common.pcapreplay.PcapReplay as PcapReplay
import atf.common.pcapreplay.flow.FlowKey as FlowKey
import atf.common.pcapreplay.flow.TcpFlow as TcpFlow
import atf.common.pcapreplay.flow.UdpFlow as UdpFlow
import atf.common.pcapreplay.flow.GenericFlow as GenericFlow
import atf.common.pcapreplay.trigger.Trigger as Trigger
import atf.common.pcapreplay.trigger.HttpTrigger as HttpTrigger
from atf.common.pcapreplay.Protocol import *
from atf.common.pcapreplay.PcapReplayInfo import *

##
# Globals

##
# Classes
class PcapReplayTestBase(CommonTestCase):
    """
    Base class for all PcapReplay test cases
    """
    def setUp(self):
        """
        Base setup method for all PcapReplay test cases

        args:     none
        return:   none
        """
        self.sT = '1.2.3.4' 
        self.dT = '5.6.7.8'
        self.src = struct.unpack('!L', inet_pton(AF_INET, self.sT))[0]
        self.dst = struct.unpack('!L', inet_pton(AF_INET, self.dT))[0]
        self.s6T = '1111:2222:3333:4444::' 
        self.d6T = '5555:6666:7777:8888::'
        self.src6 = inet_pton(AF_INET6, self.s6T)
        self.dst6 = inet_pton(AF_INET6, self.d6T)
        self.sport = 10 
        self.dport = 20 
        self.msT = '01:01:01:01:01:01'
        self.mdT = '02:02:02:02:02:02'
        m = self.msT.split(':')
        for i in range(0,len(m)):
            m[i] = '%c' % (int(m[i], 16))
        self.smac = ''.join(m)
        m = self.mdT.split(':')
        for i in range(0,len(m)):
            m[i] = '%c' % (int(m[i], 16))
        self.dmac = ''.join(m) 
        
    def tearDown(self):
        """
        Base teardown method for all PcapReplay test cases

        args:     none
        return:   none
        """
        pass
    
class PcapReplayObjectTestCase(PcapReplayTestBase):
    """
    PcapReplayObject test cases
    """
    def setUp(self):
        PcapReplayTestBase.setUp(self)
       
    @enabletest 
    def test00001create(self):
        pro = PcapReplayBase.PcapReplayObject(logging.DEBUG)
        self.assertEqual(pro.logger.getEffectiveLevel(), logging.DEBUG,
                         'Create failed: Logging level mismatch')
    @staticmethod 
    def suite():
        return PcapReplayObjectTestCase._suite(PcapReplayObjectTestCase)

class PcapReplayErrorTestCase(PcapReplayTestBase):
    """
    PcapReplayError test cases
    """
    def setUp(self):
        PcapReplayTestBase.setUp(self)
        self.testDesc = 'This is a test'
        
    @enabletest 
    def test01001create(self):
        pre = PcapReplayBase.PcapReplayError(PcapReplayBase.PcapReplayError.ERR_PCAPR_IMPL, 
                                             desc=self.testDesc)
        self.assertEqual(pre.errCode, PcapReplayBase.PcapReplayError.ERR_PCAPR_IMPL,
                         'Create failed: Error level mismatch')
        self.assertEqual(pre.desc, self.testDesc,
                         'Create failed: Description mismatch')

    @staticmethod 
    def suite():
        return PcapReplayErrorTestCase._suite(PcapReplayErrorTestCase)

class NetworkInfoTestCase(PcapReplayTestBase):
    """
    NetworkInfo test cases
    """
    def setUp(self):
        PcapReplayTestBase.setUp(self)
        self.netInfo = None
        
    @enabletest 
    def test02001create(self):
        self.netInfo = NetworkInfo()
        self.assertEqual(self.netInfo.clientIP4, 0,
                         'Create failed: ClientIP4 not initialised')
        self.assertEqual(self.netInfo.clientIP6, '',
                         'Create failed: ClientIP6 not initialised')
        self.assertEqual(self.netInfo.clientMAC, '',
                         'Create failed: ClientMAC not initialised')
        self.assertEqual(self.netInfo.serverIP4, 0,
                         'Create failed: ServerIP4 not initialised')
        self.assertEqual(self.netInfo.serverIP6, '',
                         'Create failed: ServerIP6 not initialised')
        self.assertEqual(self.netInfo.serverMAC, '',
                         'Create failed: ServerMAC not initialised')
        self.assertEqual(self.netInfo.ifaceC, '',
                         'Create failed: ifaceC not initialised')
        self.assertEqual(self.netInfo.ifaceS, '',
                         'Create failed: ifaceS not initialised')
        self.assertEqual(self.netInfo.clientIsIpv4, False,
                         'Create failed: clientIsIpv4 not initialised')
        self.assertEqual(self.netInfo.clientIsIpv6, False,
                         'Create failed: clientIsIpv6 not initialised')
        self.assertEqual(self.netInfo.serverIsIpv4, False,
                         'Create failed: serverIsIpv4 not initialised')
        self.assertEqual(self.netInfo.serverIsIpv6, False,
                         'Create failed: serverIsIpv6 not initialised')

    @staticmethod 
    def suite():
        return NetworkInfoTestCase._suite(NetworkInfoTestCase)

class PcapReplayTestCase(PcapReplayTestBase):
    """
    PcapReplay test cases
    """
    def setUp(self):
        PcapReplayTestBase.setUp(self)
        self.tmpPcapFile = '/tmp/pcap.cap'
        self.pcr = None
        self.proto = UDP
        self.flowType = UdpFlow.UdpFlow
        self.sT = '172.16.0.20' 
        self.dT = '10.2.1.11'
        self.src = NetworkInfo.netPToN(ipv4=self.sT) 
        self.dst = NetworkInfo.netPToN(ipv4=self.dT) 
        self.sport = 3565 
        self.dport = 53
        self.proto6 = TCP
        self.flowType6 = TcpFlow.TcpFlow
        self.s6T = '2301::10:20:2:2' 
        self.d6T = '2302::10:20:40:2'
        self.src6 = NetworkInfo.netPToN(ipv6=self.s6T) 
        self.dst6 = NetworkInfo.netPToN(ipv6=self.d6T) 
        self.sport6 = 1106 
        self.dport6 = 80
        self.protoM = GENERIC
        self.flowTypeM = GenericFlow.GenericFlow
        self.msT = '0:c:29:f2:c8:a7'
        self.mdT = '0:1:6c:9e:73:7b'
        self.smac = NetworkInfo.macPToN(self.msT)
        self.dmac = NetworkInfo.macPToN(self.mdT)
        self.pcapDumpPktNum = 27 
        self.pcapDumpProtoPktNum = {ICMP: 2, TCP: 14, UDP: 4, GENERIC: 7}
        self.pcapDumpFlowNum = {ICMP: 1, TCP: 2, UDP: 2, GENERIC: 3}
        self.pcapDump = array.array('b', 
            [ -44,  -61,  -78,  -95,    2,    0,    4,    0,    0,    0,
              0,    0,    0,    0,    0,    0,   13,    0,    1,    0,
              1,    0,    0,    0,  102,   35,   99,   60,  -32,    4,
              7,    0,   74,    0,    0,    0,   74,    0,    0,    0,
              8,    0,   32,  -94,  -95,  -94,    0, -112,   39,   -3,
             55,   71,    8,    0,   69,    0,    0,   60,   50,   29,
             64,    0,   64,    6,  -93,   82,  -84,   16,    6,  100,
            -84,   16,    6,  -56,   11,   54,    0,   80,  -63,  127,
             31,  -15,    0,    0,    0,    0,  -96,    2,   62,  -68,
             84, -105,    0,    0,    2,    4,    5,  -76,    4,    2,
              8,   10,   21,  -95,   76,  -49,    0,    0,    0,    0,
              1,    3,    3,    0,  102,   35,   99,   60,  -32,    4,
              7,    0,   78,    0,    0,    0,   78,    0,    0,    0,
              0, -112,   39,   -3,   55,   71,    8,    0,   32,  -94,
            -95,  -94,    8,    0,   69,    0,    0,   64,  -13,  -18,
             64,    0,   -1,    6,   34,  124,  -84,   16,    6,  -56,
            -84,   16,    6,  100,    0,   80,   11,   54,    3,  -67,
             44,  -16,  -63,  127,   31,  -14,  -80,   18,   39, -104,
            113,   35,    0,    0,    1,    1,    8,   10,    0,    0,
            -73,  -45,   21,  -95,   76,  -49,    1,    3,    3,    0,
              1,    1,    4,    2,    2,    4,    5,  -76,  102,   35,
             99,   60,  -32,    4,    7,    0,   66,    0,    0,    0,
             66,    0,    0,    0,    8,    0,   32,  -94,  -95,  -94,
              0, -112,   39,   -3,   55,   71,    8,    0,   69,    0,
              0,   52,   50,   30,   64,    0,   64,    6,  -93,   89,
            -84,   16,    6,  100,  -84,   16,    6,  -56,   11,   54,
              0,   80,  -63,  127,   31,  -14,    3,  -67,   44,  -15,
           -128,   16,   62,  -68, -102,  -54,    0,    0,    1,    1,
              8,   10,   21,  -95,   76,  -49,    0,    0,  -73,  -45,
            102,   35,   99,   60,  -32,    4,    7,    0,   56,    1,
              0,    0,   56,    1,    0,    0,    8,    0,   32,  -94,
            -95,  -94,    0, -112,   39,   -3,   55,   71,    8,    0,
             69,    0,    1,   42,   50,   31,   64,    0,   64,    6,
            -94,   98,  -84,   16,    6,  100,  -84,   16,    6,  -56,
             11,   54,    0,   80,  -63,  127,   31,  -14,    3,  -67,
             44,  -15, -128,   24,   62,  -68,  -78,   62,    0,    0,
              1,    1,    8,   10,   21,  -95,   76,  -49,    0,    0,
            -73,  -45,   71,   69,   84,   32,   46,   47,   47,   47,
             47,   47,   47,   47,   47,   47,   47,   47,   47,   47,
             47,   47,   47,   47,   47,   47,   47,   47,   47,   47,
             47,   47,   47,   47,   47,   47,   47,   47,   47,   47,
             47,   47,   47,   47,   47,   47,   47,   47,   47,   47,
             47,   47,   47,   47,   47,   47,   47,   47,   47,   47,
             47,   47,   47,   47,   47,   47,   47,   47,   47,   47,
             47,   47,   47,   47,   47,   47,   47,   47,   47,   47,
             47,   47,   47,   47,   47,   47,   47,   47,   47,   47,
             47,   47,   47,   47,   47,   47,   47,   47,   47,   47,
             47,   47,   47,   47,   47,   47,   47,   47,   47,   47,
             47,   47,   47,   47,   47,   47,   47,   47,   47,   47,
             47,   47,   47,   47,   47,   47,   47,   47,   47,   47,
             47,   47,   47,   47,   47,   47,   47,   47,   47,   47,
             47,   47,   47,   47,   47,   47,   47,   47,   47,   47,
             47,   47,   47,   47,   47,   47,   47,   47,   47,   47,
             47,   47,   47,   47,   47,   47,   47,   47,   47,   47,
             47,   47,   47,   47,   47,   47,   47,   47,   47,   47,
             47,   47,   47,   47,   47,   47,   47,   47,   47,   47,
             47,   47,   47,   47,   47,   47,   47,   47,   47,   47,
             47,   47,   47,   47,   47,   47,   47,   47,   47,   47,
             47,   47,   47,   47,   47,   47,   47,   47,   47,   47,
             47,   47,   47,   47,   47,   47,   47,   47,   47,   47,
             47,   47,   47,   47,   47,   47,   47,   47,   47,   47,
             47,   47,   47,   47,   47,   47,   47,   10,  102,   35,
             99,   60,  -32,    4,    7,    0,   66,    0,    0,    0,
             66,    0,    0,    0,    0, -112,   39,   -3,   55,   71,
              8,    0,   32,  -94,  -95,  -94,    8,    0,   69,    0,
              0,   52,  -13,  -17,   64,    0,   -1,    6,   34, -121,
            -84,   16,    6,  -56,  -84,   16,    6,  100,    0,   80,
             11,   54,    3,  -67,   44,  -15,  -63,  127,   32,  -24,
           -128,   16,   38,  -94,  -79,  -18,    0,    0,    1,    1,
              8,   10,    0,    0,  -73,  -45,   21,  -95,   76,  -49,
            102,   35,   99,   60,  -40, -108,   11,    0,    7,    3,
              0,    0,    7,    3,    0,    0,    0, -112,   39,   -3,
             55,   71,    8,    0,   32,  -94,  -95,  -94,    8,    0,
             69,    0,    2,   -7,  -13,  -16,   64,    0,   -1,    6,
             31,  -63,  -84,   16,    6,  -56,  -84,   16,    6,  100,
              0,   80,   11,   54,    3,  -67,   44,  -15,  -63,  127,
             32,  -24, -128,   24,   39, -104,   94,  -78,    0,    0,
              1,    1,    8,   10,    0,    0,  -73,  -43,   21,  -95,
             76,  -49,   60,  104,  116,  109,  108,   62,   10,   60,
             33,   45,   45,  116,  101,  115,  116,   32,  119,  101,
             98,   32,  112,   97,  103,  101,   32,  102,  111,  114,
             32,   82,  101,  100,   98,   97,  110,  107,   45,   62,
             10,   60,  104,  101,   97,  100,   62,   10,   32,   32,
             60,  116,  105,  116,  108,  101,   62,   82,  101,  100,
             98,   97,  110,  107,   60,   47,  116,  105,  116,  108,
            101,   62,   10,   32,   32,   60,  109,  101,  116,   97,
             32,  110,   97,  109,  101,   61,   34,  100,  101,  115,
             99,  114,  105,  112,  116,  105,  111,  110,   34,   32,
             99,  111,  110,  116,  101,  110,  116,   61,   34,   34,
             62,   10,   32,   32,   60,  109,  101,  116,   97,   32,
            110,   97,  109,  101,   61,   34,  107,  101,  121,  119,
            111,  114,  100,  115,   34,   32,   99,  111,  110,  116,
            101,  110,  116,   61,   34,   34,   62,   10,   60,   47,
            104,  101,   97,  100,   62,   10,   60,   98,  111,  100,
            121,   32,   98,  103,   99,  111,  108,  111,  114,   61,
             34,   35,   48,   48,   48,   48,   48,   48,   34,   32,
            116,  101,  120,  116,   61,   34,   35,   70,   70,   70,
             70,   70,   70,   34,   32,  108,  105,  110,  107,   61,
             34,   35,   51,   51,   54,   54,   70,   70,   34,   32,
            118,  108,  105,  110,  107,   61,   34,   35,   48,   48,
             67,   67,   70,   70,   34,   62,   10,   60,  112,   32,
             97,  108,  105,  103,  110,   61,   34,   99,  101,  110,
            116,  101,  114,   34,   62,   60,  102,  111,  110,  116,
             32,  115,  105,  122,  101,   61,   34,   54,   34,   32,
            102,   97,   99,  101,   61,   34,   65,  114,  105,   97,
            108,   34,   62,   60,   98,   62,   60,  105,   62,   71,
            114,  101,  101,  116,  105,  110,  103,  115,   44,   32,
             97,  110,  100,   32,  119,  101,  108,   99,  111,  109,
            101,   32,  116,  111,   32,   99,  114,   97,   99,  107,
             32,  116,  111,  119,  110,   46,   60,   47,  105,   62,
             60,   47,   98,   62,   60,   47,  102,  111,  110,  116,
             62,   60,   47,  112,   62,   10,   60,  104,  114,   32,
             97,  108,  105,  103,  110,   61,   34,   99,  101,  110,
            116,  101,  114,   34,   32,  119,  105,  100,  116,  104,
             61,   34,   56,   48,   37,   34,   32,  115,  105,  122,
            101,   61,   34,   55,   34,   62,   10,   60,  112,   62,
             84,  104,  105,  115,   32,  105,  115,   32,   82,  101,
            100,   98,   97,  110,  107,   32,  111,  114,   32,  115,
            111,  109,  101,  116,  104,  105,  110,  103,   60,   47,
            112,   62,   10,   60,  112,   62,   72,  101,  114,  101,
             32,   97,  114,  101,   32,  115,  111,  109,  101,   32,
            116,  101,  115,  116,   32,  108,  105,  110,  107,  115,
             58,   60,   47,  112,   62,   10,   60,  117,  108,   62,
             10,   32,   32,   32,   32,   60,  108,  105,   62,   60,
             97,   32,  104,  114,  101,  102,   61,   34,  116,  101,
            115,  116,   49,   46,  104,  116,  109,  108,   34,   62,
             74,   97,  121,   32,   97,  110,  100,   32,   66,  111,
             98,   60,   47,   97,   62,   60,   47,  108,  105,   62,
             10,   32,   32,   32,   32,   60,  108,  105,   62,   60,
             97,   32,  104,  114,  101,  102,   61,   34,  102,  105,
            108,  101,  112,   97,  114,  101,  110,  116,   46,  104,
            116,  109,  108,   34,   62,   66,   97,  116,  116,  108,
            101,  115,  116,   97,  114,   60,   47,   97,   62,   60,
             47,  108,  105,   62,   10,   32,   32,   32,   32,   60,
            108,  105,   62,   60,   97,   32,  104,  114,  101,  102,
             61,   34,  104,  116,  100,  111,   99,  115,   47,  109,
             97,  110,  117,   97,  108,   47,  105,  110,  100,  101,
            120,   46,  104,  116,  109,  108,   34,   62,   65,  112,
             97,   99,  104,  101,   32,   68,  111,   99,  115,   60,
             47,   97,   62,   60,   47,  108,  105,   62,   10,   60,
             47,  117,  108,   62,   10,   10,   60,  105,  109,  103,
             32,  115,  114,   99,   61,   34,   97,  112,   97,   99,
            104,  101,   95,  112,   98,   46,  103,  105,  102,   34,
             32,  119,  105,  100,  116,  104,   61,   34,   50,   53,
             57,   34,   32,  104,  101,  105,  103,  104,  116,   61,
             34,   51,   50,   34,   32,   97,  108,  116,   61,   34,
             34,   32,   98,  111,  114,  100,  101,  114,   61,   34,
             48,   34,   62,   10,   60,   47,   98,  111,  100,  121,
             62,   10,   60,   47,  104,  116,  109,  108,   62,   10,
             10,  102,   35,   99,   60,  -40, -108,   11,    0,   66,
              0,    0,    0,   66,    0,    0,    0,    8,    0,   32,
            -94,  -95,  -94,    0, -112,   39,   -3,   55,   71,    8,
              0,   69,    0,    0,   52,   50,   32,   64,    0,   64,
              6,  -93,   87,  -84,   16,    6,  100,  -84,   16,    6,
            -56,   11,   54,    0,   80,  -63,  127,   32,  -24,    3,
            -67,   47,  -74, -128,   16,   59,   -9, -103,  -48,    0,
              0,    1,    1,    8,   10,   21,  -95,   76,  -47,    0,
              0,  -73,  -43,  102,   35,   99,   60,  -40, -108,   11,
              0,   66,    0,    0,    0,   66,    0,    0,    0,    0,
           -112,   39,   -3,   55,   71,    8,    0,   32,  -94,  -95,
            -94,    8,    0,   69,    0,    0,   52,  -13,  -15,   64,
              0,   -1,    6,   34, -123,  -84,   16,    6,  -56,  -84,
             16,    6,  100,    0,   80,   11,   54,    3,  -67,   47,
            -74,  -63,  127,   32,  -24, -128,   17,   39, -104,  -82,
             46,    0,    0,    1,    1,    8,   10,    0,    0,  -73,
            -43,   21,  -95,   76,  -47,  102,   35,   99,   60,  112,
            -49,   11,    0,   66,    0,    0,    0,   66,    0,    0,
              0,    8,    0,   32,  -94,  -95,  -94,    0, -112,   39,
             -3,   55,   71,    8,    0,   69,    0,    0,   52,   50,
             33,   64,    0,   64,    6,  -93,   86,  -84,   16,    6,
            100,  -84,   16,    6,  -56,   11,   54,    0,   80,  -63,
            127,   32,  -24,    3,  -67,   47,  -73, -128,   16,   62,
            -68, -105,   10,    0,    0,    1,    1,    8,   10,   21,
            -95,   76,  -47,    0,    0,  -73,  -43,  102,   35,   99,
             60,  112,  -49,   11,    0,   66,    0,    0,    0,   66,
              0,    0,    0,    8,    0,   32,  -94,  -95,  -94,    0,
           -112,   39,   -3,   55,   71,    8,    0,   69,    0,    0,
             52,   50,   34,   64,    0,   64,    6,  -93,   85,  -84,
             16,    6,  100,  -84,   16,    6,  -56,   11,   54,    0,
             80,  -63,  127,   32,  -24,    3,  -67,   47,  -73, -128,
             17,   62,  -68, -105,    9,    0,    0,    1,    1,    8,
             10,   21,  -95,   76,  -47,    0,    0,  -73,  -43,  102,
             35,   99,   60,  112,  -49,   11,    0,   66,    0,    0,
              0,   66,    0,    0,    0,    0, -112,   39,   -3,   55,
             71,    8,    0,   32,  -94,  -95,  -94,    8,    0,   69,
              0,    0,   52,  -13,  -14,   64,    0,   -1,    6,   34,
           -124,  -84,   16,    6,  -56,  -84,   16,    6,  100,    0,
             80,   11,   54,    3,  -67,   47,  -73,  -63,  127,   32,
            -23, -128,   16,   39, -104,  -82,   45,    0,    0,    1,
              1,    8,   10,    0,    0,  -73,  -43,   21,  -95,   76,
            -47,  -83,  -52,  -58,   67,   15,  -18,    2,    0,   72,
              0,    0,    0,   72,    0,    0,    0,    0,    3,  -97,
            -57,  -80,   11,    0,    3,   71,  -85,  -13, -126,    8,
              0,   69,    0,    0,   58,   44, -127,    0,    0, -128,
             17,   87,    1,  -84,   16,    0,   20,   10,    2,    1,
             11,   13,  -21,    0,   53,    0,   38,  -48,    3,   46,
             11,    1,    0,    0,    1,    0,    0,    0,    0,    0,
              0,    3,  119,  119,  119,    4,  116,  101,  115,  116,
              3,  110,  101,  116,    0,    0,    1,    0,    1,  -83,
            -52,  -58,   67,  100,  -65,    3,    0,  -91,    0,    0,
              0,  -91,    0,    0,    0,    0,    3,   71,  -85,  -13,
           -126,    0,    3,  -97,  -57,  -80,   11,    8,    0,   69,
              0,    0, -105,   57,  -46,   64,    0,   -2,   17, -117,
             82,   10,    2,    1,   11,  -84,   16,    0,   20,    0,
             53,   13,  -21,    0, -125,  -19,  -62,   46,   11, -127,
           -128,    0,    1,    0,    1,    0,    2,    0,    2,    3,
            119,  119,  119,    4,  116,  101,  115,  116,    3,  110,
            101,  116,    0,    0,    1,    0,    1,  -64,   12,    0,
              1,    0,    1,    0,    0,    0,   60,    0,    4,  -57,
            -65,    1,    6,  -64,   16,    0,    2,    0,    1,    0,
              0,    0,   60,    0,   15,    3,  110,  115,   49,    8,
            109,  105,  100,  109,   97,  105,  110,  101,  -64,   21,
            -64,   16,    0,    2,    0,    1,    0,    0,    0,   60,
              0,    6,    3,  110,  115,   50,  -64,   62,  -64,   58,
              0,    1,    0,    1,    0,    0,  -53, -113,    0,    4,
            -40,  -36,  -26,   24,  -64,   85,    0,    1,    0,    1,
              0,    0,  -53, -113,    0,    4,  -40,  -36,  -26,   25,
            -83,  -52,  -58,   67, -120,  -56,    5,    0,   78,    0,
              0,    0,   78,    0,    0,    0,    0,    3,  -97,  -57,
            -80,   11,    0,    3,   71,  -85,  -13, -126,    8,    0,
             69,    0,    0,   64,   44, -121,    0,    0, -128,   17,
             86,  -11,  -84,   16,    0,   20,   10,    2,    1,   11,
             13,  -19,    0,   53,    0,   44,  -98,   51,   37,    8,
              1,    0,    0,    1,    0,    0,    0,    0,    0,    0,
              3,  119,  119,  119,    4,  117,  109,   99,  115,    5,
            109,   97,  105,  110,  101,    3,  101,  100,  117,    0,
              0,    1,    0,    1,  -83,  -52,  -58,   67,  -40,  -31,
              7,    0,  -89,    0,    0,    0,  -89,    0,    0,    0,
              0,    3,   71,  -85,  -13, -126,    0,    3,  -97,  -57,
            -80,   11,    8,    0,   69,    0,    0, -103,   57,  -45,
             64,    0,   -2,   17, -117,   79,   10,    2,    1,   11,
            -84,   16,    0,   20,    0,   53,   13,  -19,    0, -123,
            -73,   92,   37,    8, -127, -128,    0,    1,    0,    2,
              0,    2,    0,    1,    3,  119,  119,  119,    4,  117,
            109,   99,  115,    5,  109,   97,  105,  110,  101,    3,
            101,  100,  117,    0,    0,    1,    0,    1,  -64,   12,
              0,    5,    0,    1,    0,    1,   81, -128,    0,   10,
              7,   71,   65,   78,   68,   65,   76,   70,  -64,   16,
            -64,   48,    0,    1,    0,    1,    0,    1,   81, -128,
              0,    4, -126,  111,  112,   21,  -64,   16,    0,    2,
              0,    1,    0,    0,    3,  -24,    0,    9,    6,  103,
            111,  108,  108,  117,  109,  -64,   16,  -64,   16,    0,
              2,    0,    1,    0,    0,    3,  -24,    0,    2,  -64,
             48,  -64,   86,    0,    1,    0,    1,    0,    1,   81,
           -128,    0,    4, -126,  111,  112,   22, -104,    9,   31,
             71,   39,  -44,    3,    0,   42,    0,    0,    0,   42,
              0,    0,    0,    0,   25,  -86,  -43,  -59,   63,    0,
             20,  108,  -63,  -90,   81,    8,    0,   69,    0,    0,
             28, -100,   73,    0,    0,   64,    1,   15,   39,  -84,
             16,   67,  -81,  -84,   16,   51,  -95,    8,    8,   77,
            -53,  -86,   44,    0,    0, -104,    9,   31,   71,   60,
            -33,    3,    0,   60,    0,    0,    0,   60,    0,    0,
              0,    0,   20,  108,  -63,  -90,   81,    0,   25,  -86,
            -43,  -59,   63,    8,    0,   69,    0,    0,   28,  -74,
            -88,    0,    0,  127,    1,  -75,  -57,  -84,   16,   51,
            -95,  -84,   16,   67,  -81,    0,    0,   85,  -45,  -86,
             44,    0,    0,    0,    0,    0,    0,    0,    0,    0,
              0,    0,    0,    0,    0,    0,    0,    0,    0,    0,
              0,  -73,  -49,   51,   73,  119,   32,    1,    0,   42,
              0,    0,    0,   42,    0,    0,    0,   -1,   -1,   -1,
             -1,   -1,   -1,    0,    1,  108,  -98,  115,  123,    8,
              6,    0,    1,    8,    0,    6,    4,    0,    1,    0,
              1,  108,  -98,  115,  123,  -84,   22,    6,   28,    0,
              0,    0,    0,    0,    0,  -84,   22,    6, -117,  -73,
            -49,   51,   73, -120,   32,    1,    0,   42,    0,    0,
              0,   42,    0,    0,    0,   -1,   -1,   -1,   -1,   -1,
             -1,    0,    1,  108,  -98,  115,  123,    8,    6,    0,
              1,    8,    0,    6,    4,    0,    1,    0,    1,  108,
            -98,  115,  123,  -84,   22,    6,   28,    0,    0,    0,
              0,    0,    0,  -84,   22,    6, -117,  -73,  -49,   51,
             73, -120,   34,    1,    0,  106,    0,    0,    0,  106,
              0,    0,    0,    0,    1,  108,  -98,  115,  123,    0,
             12,   41,  -14,  -56,  -89,    8,    6,    0,    1,    8,
              0,    6,    4,    0,    2,    0,   12,   41,  -14,  -56,
            -89,  -84,   22,    6, -117,    0,    1,  108,  -98,  115,
            123,  -84,   22,    6,   28,    0,    0,    0,    0,    0,
              0,    0,    0,    0,    0,    0,    0,    0,    0,    0,
              0,    0,    0,    0,    0,    0,    0,    0,    0,    0,
              0,    0,    0,    0,    0,    0,    0,    0,    0,    0,
              0,    0,    0,    0,    0,    0,    0,    0,    0,    0,
              0,    0,    0,    0,    0,    0,    0,    0,    0,    0,
              0,    0,    0,    0,    0,    0,    0,    0,    0,  -73,
            -49,   51,   73, -105,   13,    9,    0,   60,    0,    0,
              0,   60,    0,    0,    0,   -1,   -1,   -1,   -1,   -1,
             -1,    0,    1,  108,  -98,  115, -118,    8,    6,    0,
              1,    8,    0,    6,    4,    0,    1,    0,    1,  108,
            -98,  115, -118,  -84,   22,    6,   76,    0,    0,    0,
              0,    0,    0,  -84,   22,    6,  -44,    0,    0,    0,
              0,    0,    0,    0,    0,    0,    0,    0,    0,    0,
              0,    0,    0,    0,    0,  -69,  -49,   51,   73,   13,
           -105,   12,    0,  106,    0,    0,    0,  106,    0,    0,
              0,    0,    1,  108,  -98,  115,  123,    0,   12,   41,
            -14,  -56,  -89,    8,    6,    0,    1,    8,    0,    6,
              4,    0,    1,    0,   12,   41,  -14,  -56,  -89,  -84,
             22,    6, -117,    0,    0,    0,    0,    0,    0,  -84,
             22,    6,   28,    0,    0,    0,    0,    0,    0,    0,
              0,    0,    0,    0,    0,    0,    0,    0,    0,    0,
              0,    0,    0,    0,    0,    0,    0,    0,    0,    0,
              0,    0,    0,    0,    0,    0,    0,    0,    0,    0,
              0,    0,    0,    0,    0,    0,    0,    0,    0,    0,
              0,    0,    0,    0,    0,    0,    0,    0,    0,    0,
              0,    0,    0,    0,    0,    0,    0,  -69,  -49,   51,
             73,   25, -105,   12,    0,   42,    0,    0,    0,   42,
              0,    0,    0,    0,   12,   41,  -14,  -56,  -89,    0,
              1,  108,  -98,  115,  123,    8,    6,    0,    1,    8,
              0,    6,    4,    0,    2,    0,    1,  108,  -98,  115,
            123,  -84,   22,    6,   28,    0,   12,   41,  -14,  -56,
            -89,  -84,   22,    6, -117,  -69,  -49,   51,   73,   35,
           -105,   12,    0,   42,    0,    0,    0,   42,    0,    0,
              0,    0,   12,   41,  -14,  -56,  -89,    0,    1,  108,
            -98,  115,  123,    8,    6,    0,    1,    8,    0,    6,
              4,    0,    2,    0,    1,  108,  -98,  115,  123,  -84,
             22,    6,   28,    0,   12,   41,  -14,  -56,  -89,  -84,
             22,    6, -117,   31,   39,  118,   73,   81,  -82,   10,
              0,   82,    0,    0,    0,   82,    0,    0,    0,    0,
             27,  -44,   38,   49,   89,    0,   12,   41,  -24,  -67,
            -25, -122,  -35,   96,    0,    0,    0,    0,   28,    6,
             64,   35,    1,    0,    0,    0,    0,    0,    0,    0,
             16,    0,   32,    0,    2,    0,    2,   35,    2,    0,
              0,    0,    0,    0,    0,    0,   16,    0,   32,    0,
             64,    0,    2,    4,   82,    0,   80,  -69,   66,    1,
           -111,    0,    0,    0,    0,  112,    2,   -6,  -16, -128,
             16,    0,    0,    2,    4,    5,  -76,    1,    1,    4,
              2,   31,   39,  118,   73,  120,  -45,   10,    0,   82,
              0,    0,    0,   82,    0,    0,    0,    0,   12,   41,
            -24,  -67,  -25,    0,   27,  -44,   38,   49,   89, -122,
            -35,   96,    0,    0,    0,    0,   28,    6,   64,   35,
              2,    0,    0,    0,    0,    0,    0,    0,   16,    0,
             32,    0,   64,    0,    2,   35,    1,    0,    0,    0,
              0,    0,    0,    0,   16,    0,   32,    0,    2,    0,
              2,    0,   80,    4,   82,  -65,  110,  -32,  -73,  -69,
             66,    1, -110,  112,   18,   -6,  -16,  -33,  -40,    0,
              0,    2,    4,    5,  -76,    1,    1,    4,    2,   31,
             39,  118,   73,   86,  -16,   10,    0,   80,    0,    0,
              0,   80,    0,    0,    0,    0,   27,  -44,   38,   49,
             89,    0,   12,   41,  -24,  -67,  -25, -122,  -35,   96,
              0,    0,    0,    0,   20,    6,   64,   35,    1,    0,
              0,    0,    0,    0,    0,    0,   16,    0,   32,    0,
              2,    0,    2,   35,    2,    0,    0,    0,    0,    0,
              0,    0,   16,    0,   32,    0,   64,    0,    2,    4,
             82,    0,   80,  -69,   66,    1, -110,  -65,  110,  -32,
            -72,   80,   16,   -6,  -16,   12,  -99,    0,    0,    0,
              0,    0,   59,   -1,   83])  

    def _createPcapFile(self):
        file = open(self.tmpPcapFile, mode='wb')
        self.pcapDump.tofile(file)
        file.close()
            
    def _deletePcapFile(self):
        if os.path.exists(self.tmpPcapFile):
            os.remove(self.tmpPcapFile)
            
    @enabletest 
    def test03001create(self):
        self.pcr = PcapReplay.PcapReplay()
        self.assertEqual(self.pcr.flowlessTcpPkts, [],
                         'Create failed: flowlessTcpPkts not initialised')
        self.assertNotEqual(self.pcr.pktList, None,
                         'Create failed: pktList not initialised')
        for proto in self.pcr.pktList:
            self.assertEqual(self.pcr.pktList[proto], [],
                             'Create failed: pktList[%s] not initialised' % 
                             proto)
        self.assertNotEqual(self.pcr.flows, None,
                         'Create failed: flows not initialised')
        for proto in self.pcr.flows:
            self.assertEqual(self.pcr.flows[proto], {},
                             'Create failed: flows[%s] not initialised' % 
                             proto)
        self.assertEqual(self.pcr.seqNum, 0,
                         'Create failed: seqNum not initialised')

    @enabletest 
    def test03002parsePktList(self):
        self.pcr = PcapReplay.PcapReplay()
        self._createPcapFile()
        pktList = []
        try:
            file = pcs.PcapConnector(self.tmpPcapFile)
        except Exception, e:
            self.fail('Parse Pkt List failed: %s' % str(e))
        while True:
            try:
                pkt = file.read()
            except:
                break
            ether = ethernet(pkt[0:len(pkt)])
            pktList.append(ether)
        self.pcr.parsePacketList(pktList)
        self.assertEqual(self.pcr.seqNum, self.pcapDumpPktNum,
                         'Parse Pkt List failed: pktList incorrectly parsed')
        self.assertEqual(len(self.pcr.pktList[ICMP]), 
                         self.pcapDumpProtoPktNum[ICMP],
                         'Parse Pkt List failed: ICMP pkts not parsed')
        self.assertEqual(len(self.pcr.pktList[TCP]), 
                         self.pcapDumpProtoPktNum[TCP],
                         'Parse Pkt List failed: TCP pkts not parsed')
        self.assertEqual(len(self.pcr.pktList[UDP]), 
                         self.pcapDumpProtoPktNum[UDP],
                         'Parse Pkt List failed: UDP pkts not parsed')
        self.assertEqual(len(self.pcr.pktList[GENERIC]), 
                         self.pcapDumpProtoPktNum[GENERIC],
                         'Parse Pkt List failed: GENERIC pkts not parsed')
        self._deletePcapFile()
        
    @enabletest 
    def test03003parsePktFile(self):
        self.pcr = PcapReplay.PcapReplay()
        self._createPcapFile()
        self.pcr.parsePcapFile(self.tmpPcapFile)
        self.assertEqual(self.pcr.seqNum, self.pcapDumpPktNum,
                         'Parse Pkt File failed: pktList incorrectly parsed')
        self.assertEqual(len(self.pcr.pktList[ICMP]), 
                         self.pcapDumpProtoPktNum[ICMP],
                         'Parse Pkt File failed: ICMP pkts not parsed')
        self.assertEqual(len(self.pcr.pktList[TCP]), 
                         self.pcapDumpProtoPktNum[TCP],
                         'Parse Pkt File failed: TCP pkts not parsed')
        self.assertEqual(len(self.pcr.pktList[UDP]), 
                         self.pcapDumpProtoPktNum[UDP],
                         'Parse Pkt File failed: UDP pkts not parsed')
        self.assertEqual(len(self.pcr.pktList[GENERIC]), 
                         self.pcapDumpProtoPktNum[GENERIC],
                         'Parse Pkt File failed: GENERIC pkts not parsed')
        self._deletePcapFile()
        
    @enabletest 
    def test03004clear(self):
        # Create PcapReplay
        self.pcr = PcapReplay.PcapReplay()
        self.assertEqual(self.pcr.flowlessTcpPkts, [],
                         'Clear failed: flowlessTcpPkts not initialised')
        self.assertNotEqual(self.pcr.pktList, None,
                         'Clear failed: pktList not initialised')
        for proto in self.pcr.pktList:
            self.assertEqual(self.pcr.pktList[proto], [],
                             'Clear failed: pktList[%s] not initialised' % 
                             proto)
        self.assertNotEqual(self.pcr.flows, None,
                         'Clear failed: flows not initialised')
        for proto in self.pcr.flows:
            self.assertEqual(self.pcr.flows[proto], {},
                             'Clear failed: flows[%s] not initialised' % 
                             proto)
        self.assertEqual(self.pcr.seqNum, 0,
                         'Clear failed: seqNum not initialised')
       
        # Populate PcapReplay 
        self._createPcapFile()
        self.pcr.parsePcapFile(self.tmpPcapFile)
        self.assertEqual(self.pcr.seqNum, self.pcapDumpPktNum,
                         'Clear failed: pktList incorrectly parsed')
        self.assertEqual(len(self.pcr.pktList[ICMP]), 
                         self.pcapDumpProtoPktNum[ICMP],
                         'Clear failed: ICMP pkts not parsed')
        self.assertEqual(len(self.pcr.pktList[TCP]), 
                         self.pcapDumpProtoPktNum[TCP],
                         'Clear failed: TCP pkts not parsed')
        self.assertEqual(len(self.pcr.pktList[UDP]), 
                         self.pcapDumpProtoPktNum[UDP],
                         'Clear failed: UDP pkts not parsed')
        self.assertEqual(len(self.pcr.pktList[GENERIC]), 
                         self.pcapDumpProtoPktNum[GENERIC],
                         'Clear failed: GENERIC pkts not parsed')
        
        # Clear PcapReplay
        self.pcr.clear()
        self.assertEqual(self.pcr.flowlessTcpPkts, [],
                         'Clear failed: flowlessTcpPkts not initialised')
        self.assertNotEqual(self.pcr.pktList, None,
                         'Clear failed: pktList not initialised')
        for proto in self.pcr.pktList:
            self.assertEqual(self.pcr.pktList[proto], [],
                             'Clear failed: pktList[%s] not initialised' % 
                             proto)
        self.assertNotEqual(self.pcr.flows, None,
                         'Clear failed: flows not initialised')
        for proto in self.pcr.flows:
            self.assertEqual(self.pcr.flows[proto], {},
                             'Clear failed: flows[%s] not initialised' % 
                             proto)
        self.assertEqual(self.pcr.seqNum, 0,
                         'Clear failed: seqNum not initialised')
        self._deletePcapFile()
        
    @enabletest 
    def test03005processFlows(self):
        # Create and populate PcapReplay
        self.pcr = PcapReplay.PcapReplay()
        self._createPcapFile()
        self.pcr.parsePcapFile(self.tmpPcapFile)
        self.assertEqual(self.pcr.seqNum, self.pcapDumpPktNum,
                         'Process Flows failed: pktList incorrectly parsed')
        self.assertEqual(len(self.pcr.pktList[ICMP]), 
                         self.pcapDumpProtoPktNum[ICMP],
                         'Process Flows failed: ICMP pkts not parsed')
        self.assertEqual(len(self.pcr.pktList[TCP]), 
                         self.pcapDumpProtoPktNum[TCP],
                         'Process Flows failed: TCP pkts not parsed')
        self.assertEqual(len(self.pcr.pktList[UDP]), 
                         self.pcapDumpProtoPktNum[UDP],
                         'Process Flows failed: UDP pkts not parsed')
        self.assertEqual(len(self.pcr.pktList[GENERIC]), 
                         self.pcapDumpProtoPktNum[GENERIC],
                         'Process Flows failed: GENERIC pkts not parsed')
        
        # Process flows
        self.pcr.processFlows()
        self.assertEqual(len(self.pcr.flows[ICMP]), 
                         self.pcapDumpFlowNum[ICMP],
                         'Process Flows failed: ICMP pkts not parsed')
        self.assertEqual(len(self.pcr.flows[TCP]), 
                         self.pcapDumpFlowNum[TCP],
                         'Process Flows failed: TCP pkts not parsed')
        self.assertEqual(len(self.pcr.flows[UDP]), 
                         self.pcapDumpFlowNum[UDP],
                         'Process Flows failed: UDP pkts not parsed')
        self.assertEqual(len(self.pcr.flows[GENERIC]), 
                         self.pcapDumpFlowNum[GENERIC],
                         'Process Flows failed: GENERIC pkts not parsed')
        self._deletePcapFile()

    @enabletest 
    def test03006getFlows(self):
        # Create and populate PcapReplay
        self.pcr = PcapReplay.PcapReplay()
        self._createPcapFile()
        self.pcr.parsePcapFile(self.tmpPcapFile)
        self.assertEqual(self.pcr.seqNum, self.pcapDumpPktNum,
                         'Get Flows failed: pktList incorrectly parsed')
        self.assertEqual(len(self.pcr.pktList[ICMP]), 
                         self.pcapDumpProtoPktNum[ICMP],
                         'Get Flows failed: ICMP pkts not parsed')
        self.assertEqual(len(self.pcr.pktList[TCP]), 
                         self.pcapDumpProtoPktNum[TCP],
                         'Get Flows failed: TCP pkts not parsed')
        self.assertEqual(len(self.pcr.pktList[UDP]), 
                         self.pcapDumpProtoPktNum[UDP],
                         'Get Flows failed: UDP pkts not parsed')
        self.assertEqual(len(self.pcr.pktList[GENERIC]), 
                         self.pcapDumpProtoPktNum[GENERIC],
                         'Get Flows failed: GENERIC pkts not parsed')
        
        # Get flows
        self.pcr.processFlows()
        flowsLen = len(self.pcr.getFlows(ICMP)) 
        self.assertEqual(flowsLen, self.pcapDumpFlowNum[ICMP],
                         'Get Flows failed: ICMP pkts not parsed')
        flowsLen = len(self.pcr.getFlows(TCP)) 
        self.assertEqual(flowsLen, self.pcapDumpFlowNum[TCP],
                         'Get Flows failed: TCP pkts not parsed')
        flowsLen = len(self.pcr.getFlows(UDP)) 
        self.assertEqual(flowsLen, self.pcapDumpFlowNum[UDP],
                         'Get Flows failed: UDP pkts not parsed')
        flowsLen = len(self.pcr.getFlows(GENERIC)) 
        self.assertEqual(flowsLen, self.pcapDumpFlowNum[GENERIC],
                         'Get Flows failed: GENERIC pkts not parsed')
        self._deletePcapFile()

    @enabletest 
    def test03007getFlow(self):
        # Create and populate PcapReplay
        self.pcr = PcapReplay.PcapReplay()
        self._createPcapFile()
        self.pcr.parsePcapFile(self.tmpPcapFile)
        self.assertEqual(self.pcr.seqNum, self.pcapDumpPktNum,
                         'Get Flow failed: pktList incorrectly parsed')
        self.assertEqual(len(self.pcr.pktList[ICMP]), 
                         self.pcapDumpProtoPktNum[ICMP],
                         'Get Flow failed: ICMP pkts not parsed')
        self.assertEqual(len(self.pcr.pktList[TCP]), 
                         self.pcapDumpProtoPktNum[TCP],
                         'Get Flow failed: TCP pkts not parsed')
        self.assertEqual(len(self.pcr.pktList[UDP]), 
                         self.pcapDumpProtoPktNum[UDP],
                         'Get Flow failed: UDP pkts not parsed')
        self.assertEqual(len(self.pcr.pktList[GENERIC]), 
                         self.pcapDumpProtoPktNum[GENERIC],
                         'Get Flow failed: GENERIC pkts not parsed')
        
        # Process
        self.pcr.processFlows()
        
        # Get IPv4 Flow
        fk = FlowKey.FlowKeyFactory.getFlowKey(IPV4, self.src, self.dst, 
                                               self.proto, self.sport, 
                                               self.dport) 
        flow = self.pcr.getFlow(fk)
        self.assertNotEqual(flow, None, 
                            'Get Flow IPv4 failed: No flow returned')
        self.assertEqual(isinstance(flow, self.flowType), True,
                         'Get Flow IPv4 failed: Flow type mismatch')
        self.assertEqual(flow.flk.src, self.src,
                         'Get Flow IPv4 failed: src not set')
        self.assertEqual(flow.flk.dst, self.dst,
                         'Get Flow IPv4 failed: dst not set')
        self.assertEqual(flow.flk.sport, self.sport,
                         'Get Flow IPv4 failed: sport not set')
        self.assertEqual(flow.flk.dport, self.dport,
                         'Get Flow IPv4 failed: dport not set')
        self.assertEqual(flow.flk.proto, self.proto,
                         'Get Flow IPv4 failed: proto is not %s' % self.proto)
        
        # Get IPv6 Flow
        fk = FlowKey.FlowKeyFactory.getFlowKey(IPV6, self.src6, self.dst6, 
                                               self.proto6, self.sport6, 
                                               self.dport6) 
        flow = self.pcr.getFlow(fk)
        self.assertNotEqual(flow, None, 
                            'Get Flow IPv6 failed: No flow returned')
        self.assertEqual(isinstance(flow, self.flowType6), True,
                         'Get Flow IPv6 failed: Flow type mismatch')
        self.assertEqual(flow.flk.src, self.src6,
                         'Get Flow IPv6 failed: src not set')
        self.assertEqual(flow.flk.dst, self.dst6,
                         'Get Flow IPv6 failed: dst not set')
        self.assertEqual(flow.flk.sport, self.sport6,
                         'Get Flow IPv6 failed: sport not set')
        self.assertEqual(flow.flk.dport, self.dport6,
                         'Get Flow IPv6 failed: dport not set')
        self.assertEqual(flow.flk.proto, self.proto6,
                         'Get Flow IPv6 failed: proto is not %s' % self.proto6)
        
        # Get Generic Flow
        fk = FlowKey.FlowKeyFactory.getFlowKey(MAC, self.smac, self.dmac, 
                                               self.protoM)
        flow = self.pcr.getFlow(fk)
        self.assertNotEqual(flow, None, 
                            'Get Flow MAC failed: No flow returned')
        self.assertEqual(isinstance(flow, self.flowTypeM), True,
                         'Get Flow MAC failed: Flow type mismatch')
        self.assertEqual(flow.flk.src, self.smac,
                         'Get Flow MAC failed: src not set')
        self.assertEqual(flow.flk.dst, self.dmac,
                         'Get Flow MAC failed: dst not set')
        self.assertEqual(flow.flk.proto, self.protoM,
                         'Get Flow MAC failed: proto is not %s' % self.protoM)
        
        self._deletePcapFile()

    @enabletest 
    def test03008replayFlows(self):
        pass
    
    @staticmethod 
    def suite():
        return PcapReplayTestCase._suite(PcapReplayTestCase)
