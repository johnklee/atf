# System
import unittest
import struct
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

# PyReplay
import atf.common.pcapreplay.trigger.Trigger as Trigger
import atf.common.pcapreplay.trigger.HttpTrigger as HttpTrigger
import atf.common.pcapreplay.trigger.TcpTrigger as TcpTrigger
from atf.common.pcapreplay.PcapReplayBase import *
from atf.common.pcapreplay.Protocol import *

##
# Globals

##
# Classes
class TriggerTestBase(CommonTestCase):
    """
    Base class for all Trigger test cases
    """
    def setUp(self):
        """
        Base setup method for all Trigger test cases

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
        Base teardown method for all Trigger test cases

        args:     none
        return:   none
        """
        pass    
    
    def createIpv4Pkt(self, ipproto=6, layer1=None, layer2=None):
        e = ethernet()
        e.dst = self.dmac
        e.src = self.smac
        e.type = 0x0800
        i = ipv4()
        i.protocol = ipproto
        i.id = 0
        i.flags = 0
        i.src = self.src
        i.dst = self.dst
        e.data = i
        i.data = layer1
        layer1.data = layer2
        if layer2 == None:
            retChain = pcs.Chain([e, i, layer1]).packets[0]
        else:
            retChain = pcs.Chain([e, i, layer1, layer2]).packets[0]
        return retChain
    
    def createIpv6Pkt(self, ipproto=6, layer1=None, layer2=None):
        e = ethernet()
        e.dst = self.dmac
        e.src = self.smac
        e.type = 0x86dd
        i = ipv6()
        i.next_header= ipproto
        i.src = self.src6
        i.dst = self.dst6
        e.data = i
        i.data = layer1
        layer1.data = layer2
        if layer2 == None:
            retChain = pcs.Chain([e, i, layer1]).packets[0]
        else:
            retChain = pcs.Chain([e, i, layer1, layer2]).packets[0]
        return retChain
    
class TriggerTestCase(TriggerTestBase):
    """
    Trigger test cases
    """
    def setUp(self):
        TriggerTestBase.setUp(self)
        self.t = None
        self.type = 'type'
        self.value = 'value'
        self.action = Trigger.Trigger.STOP
        self.proto = ''
        
    @enabletest
    def test20001create(self):
        self.t = Trigger.Trigger(self.type, self.value, self.action)
        self.assertEqual(self.type, self.t.type, 
                         'Create failed: type mismatch')
        self.assertEqual(self.value, self.t.value, 
                         'Create failed: value mismatch')
        self.assertEqual(self.action, self.t.action, 
                         'Create failed: action mismatch')
        self.assertEqual(self.proto, self.t.proto, 
                         'Create failed: proto mismatch')
        self.assertEqual(len(self.t.typeMap), 0, 
                         'Create failed: typeMap populated')
    
    @enabletest
    def test20002testTrigger(self):
        self.t = Trigger.Trigger(self.type, self.value, self.action)
        try:
            self.t.testTrigger(None)
        except Exception, e:
            self.assertEquals(e.errCode, PcapReplayError.ERR_PCAPR_IMPL,
                              'Test trigger failed: Unexpected exception]')
    
    @enabletest
    def test20003executeTrigger(self):
        self.t = Trigger.Trigger(self.type, self.value, self.action)
        try:
            self.t.executeTrigger(None)
        except Exception, e:
            self.assertEquals(e.errCode, PcapReplayError.ERR_PCAPR_IMPL,
                              'Test trigger failed: Unexpected exception')
    
    @staticmethod 
    def suite():
        return TriggerTestCase._suite(TriggerTestCase)
    
class HttpTriggerTestCase(TriggerTestBase):
    """
    HttpTrigger test cases
    """
    def setUp(self):
        TriggerTestBase.setUp(self)
        self.tr = None
        self.proto = HTTP
        
    @enabletest
    def test20021createStatusCode(self):
        self.type = 'statusCode'
        self.value = '404'
        self.action = Trigger.Trigger.STOP
        self.tr = HttpTrigger.HttpTrigger(self.type, self.value, self.action)
        self.assertEqual(self.type, self.tr.type, 
                         'Create failed: type mismatch')
        self.assertEqual(self.value, self.tr.value, 
                         'Create failed: value mismatch')
        self.assertEqual(self.action, self.tr.action, 
                         'Create failed: action mismatch')
        self.assertEqual(self.proto, self.tr.proto, 
                         'Create failed: proto mismatch')
        self.assertEqual(self.tr.typeMap[self.type], [self.value], 
                         'Create failed: incorrect typeMap')
    
    @enabletest
    def test20022testTriggerStatusCodeAffirmative(self):
        self.type = 'statusCode'
        self.value = '404'
        self.action = Trigger.Trigger.STOP
        
        # Affirmative Test
        self.tr = HttpTrigger.HttpTrigger(self.type, self.value, self.action)
        t = pcs.packets.tcp.tcp()
        t.sport=23
        t.dport=22
        t.offset = 5
        h = pcs.packets.http.httpResponse()
        h.httpVersion = "HTTP/1.1"
        h.statusCode = self.value
        h.reasonPhrase = "Not Found"
        h.data = None
        
        # IPv4
        pkt = self.createIpv4Pkt(0x06, t, h)
        self.assertEquals(self.tr.testTrigger(pkt), True,
                          'Test trigger failed: trigger not matched')
       
        # IPv6 
        pkt = self.createIpv6Pkt(0x06, t, h)
        self.assertEquals(self.tr.testTrigger(pkt), True,
                          'Test trigger6 failed: trigger not matched')
    
    @enabletest
    def test20023testTriggerStatusCodeNegative(self):
        self.type = 'statusCode'
        self.value = '404'
        self.action = Trigger.Trigger.STOP
        
        # Negative Test
        self.tr = HttpTrigger.HttpTrigger(self.type, self.value, self.action)
        t = pcs.packets.tcp.tcp()
        t.sport=23
        t.dport=22
        t.offset = 5
        h = pcs.packets.http.httpResponse()
        h.httpVersion = "HTTP/1.1"
        h.statusCode = '0'
        h.reasonPhrase = "Not Found"
        h.data = None
        
        # IPv4
        pkt = self.createIpv4Pkt(0x06, t, h)
        self.assertEquals(self.tr.testTrigger(pkt), False,
                          'Test trigger failed: false trigger matched')
       
        # IPv6 
        pkt = self.createIpv6Pkt(0x06, t, h)
        self.assertEquals(self.tr.testTrigger(pkt), False,
                          'Test trigger6 failed: false trigger matched')
    
    @enabletest
    def test20024executeTriggerStatusCodeAffirmative(self):
        self.type = 'statusCode'
        self.value = '404'
        self.action = Trigger.Trigger.STOP
        
        # Affirmative HTTP statusCode Test
        self.tr = HttpTrigger.HttpTrigger(self.type, self.value, self.action)
        t = pcs.packets.tcp.tcp()
        t.sport=23
        t.dport=22
        t.offset = 5
        h = pcs.packets.http.httpResponse()
        h.httpVersion = "HTTP/1.1"
        h.statusCode = self.value
        h.reasonPhrase = "Not Found"
        h.data = None
        
        # IPv4
        pkt = self.createIpv4Pkt(0x06, t, h)
        chain = self.tr.executeTrigger(pkt)
        self.assertEquals(chain.packets[1].src, self.dst,
                          'Execute trigger failed: response src mismatch')
        self.assertEquals(chain.packets[1].dst, self.src,
                          'Execute trigger failed: response dst mismatch')
        self.assertEquals(chain.packets[2].reset, 1,
                          'Execute trigger failed: response reset not set')
        self.assertEquals(chain.packets[2].ack, 1,
                          'Execute trigger failed: response ack not set')
       
        # IPv6 
        pkt = self.createIpv6Pkt(0x06, t, h)
        chain = self.tr.executeTrigger(pkt)
        self.assertEquals(chain.packets[1].src, self.dst6,
                          'Execute trigger failed: response src mismatch')
        self.assertEquals(chain.packets[1].dst, self.src6,
                          'Execute trigger failed: response dst mismatch')
        self.assertEquals(chain.packets[2].reset, 1,
                          'Execute trigger failed: response reset not set')
        self.assertEquals(chain.packets[2].ack, 1,
                          'Execute trigger failed: response ack not set')
       
    @enabletest
    def test20025executeTriggerStatusCodeNegative(self):
        self.type = 'statusCode'
        self.value = '404'
        self.action = Trigger.Trigger.STOP
        self.payload = 'Bad Payload'
        
        # Negative Test
        self.tr = HttpTrigger.HttpTrigger(self.type, self.value, self.action)
        t = pcs.packets.tcp.tcp()
        t.sport=23
        t.dport=22
        t.offset = 5
        p = payload(self.payload)
        chain = None
        
        # IPv4
        pkt = self.createIpv4Pkt(0x06, t, p)
        try:
            chain = self.tr.executeTrigger(pkt)
        except Exception, e:
            self.assertEquals(e.errCode, Trigger.ERR_PCAPR_TRIGGER_INVALID,
                          'Execute trigger failed: false trigger mishandled')
        self.assertEquals(chain is None, True,
                          'Execute trigger failed: false trigger unhandled')
       
        # IPv6 
        pkt = self.createIpv6Pkt(0x06, t, p)
        try:
            chain = self.tr.executeTrigger(pkt)
        except Exception, e:
            self.assertEquals(e.errCode, Trigger.ERR_PCAPR_TRIGGER_INVALID,
                          'Execute trigger6 failed: false trigger mishandled')
        self.assertEquals(chain is None, True,
                          'Execute trigger failed: false trigger unhandled')
    
    @staticmethod 
    def suite():
        return HttpTriggerTestCase._suite(HttpTriggerTestCase)

class TcpTriggerTestCase(TriggerTestBase):
    """
    TcpTrigger test cases
    """
    def setUp(self):
        TriggerTestBase.setUp(self)
        self.tr = None
        self.proto = TCP
        
    @enabletest
    def test20041createStatusCode(self):
        self.type = 'reset'
        self.value = 1
        self.action = Trigger.Trigger.STOP
        self.tr = TcpTrigger.TcpTrigger(self.type, self.value, self.action)
        self.assertEqual(self.type, self.tr.type, 
                         'Create failed: type mismatch')
        self.assertEqual(self.value, self.tr.value, 
                         'Create failed: value mismatch')
        self.assertEqual(self.action, self.tr.action, 
                         'Create failed: action mismatch')
        self.assertEqual(self.proto, self.tr.proto, 
                         'Create failed: proto mismatch')
        self.assertEqual(self.tr.typeMap[self.type], [self.value], 
                         'Create failed: incorrect typeMap')
    
    @enabletest
    def test20042testTriggerStatusCodeAffirmative(self):
        self.type = 'reset'
        self.value = 1
        self.action = Trigger.Trigger.STOP
        
        # Affirmative Test
        self.tr = TcpTrigger.TcpTrigger(self.type, self.value, self.action)
        t = pcs.packets.tcp.tcp()
        t.sport=23
        t.dport=22
        t.offset = 5
        t.reset = 1
        
        # IPv4
        pkt = self.createIpv4Pkt(0x06, t, None)
        self.assertEquals(self.tr.testTrigger(pkt), True,
                          'Test trigger failed: trigger not matched')
       
        # IPv6 
        pkt = self.createIpv6Pkt(0x06, t, None)
        self.assertEquals(self.tr.testTrigger(pkt), True,
                          'Test trigger6 failed: trigger not matched')
    
    @enabletest
    def test20043testTriggerStatusCodeNegative(self):
        self.type = 'reset'
        self.value = 1
        self.action = Trigger.Trigger.STOP
        
        # Negative Test
        self.tr = TcpTrigger.TcpTrigger(self.type, self.value, self.action)
        t = pcs.packets.tcp.tcp()
        t.sport=23
        t.dport=22
        t.offset = 5
        
        # IPv4
        pkt = self.createIpv4Pkt(0x06, t, None)
        self.assertEquals(self.tr.testTrigger(pkt), False,
                          'Test trigger failed: false trigger matched')
       
        # IPv6 
        pkt = self.createIpv6Pkt(0x06, t, None)
        self.assertEquals(self.tr.testTrigger(pkt), False,
                          'Test trigger6 failed: false trigger matched')
    
    @enabletest
    def test20044executeTriggerStatusCodeAffirmative(self):
        self.type = 'reset'
        self.value = 1
        self.action = Trigger.Trigger.STOP
        
        # Affirmative HTTP statusCode Test
        self.tr = TcpTrigger.TcpTrigger(self.type, self.value, self.action)
        t = pcs.packets.tcp.tcp()
        t.sport=23
        t.dport=22
        t.offset = 5
        t.reset = 1
        
        # IPv4
        pkt = self.createIpv4Pkt(0x06, t, None)
        chain = self.tr.executeTrigger(pkt)
        self.assertEquals(chain, None,
                          'Execute trigger failed: response pkt not None')
       
        # IPv6 
        pkt = self.createIpv6Pkt(0x06, t, None)
        chain = self.tr.executeTrigger(pkt)
        self.assertEquals(chain, None,
                          'Execute trigger failed: response pkt not None')
       
    @enabletest
    def test20045executeTriggerStatusCodeNegative(self):
        self.type = 'reset'
        self.value = 1
        self.action = Trigger.Trigger.STOP
        self.payload = 'Bad Payload'
        
        # Negative Test
        self.tr = TcpTrigger.TcpTrigger(self.type, self.value, self.action)
        p = payload(self.payload)
        chain = None
        
        # IPv4
        pkt = self.createIpv4Pkt(0x06, p, None)
        try:
            chain = self.tr.executeTrigger(pkt)
        except Exception, e:
            self.assertEquals(e.errCode, Trigger.ERR_PCAPR_TRIGGER_INVALID,
                          'Execute trigger failed: false trigger mishandled')
        self.assertEquals(chain is None, True,
                          'Execute trigger failed: false trigger unhandled')
       
        # IPv6 
        pkt = self.createIpv6Pkt(0x06, p, None)
        try:
            chain = self.tr.executeTrigger(pkt)
        except Exception, e:
            self.assertEquals(e.errCode, Trigger.ERR_PCAPR_TRIGGER_INVALID,
                          'Execute trigger6 failed: false trigger mishandled')
        self.assertEquals(chain is None, True,
                          'Execute trigger failed: false trigger unhandled')
    
    @staticmethod 
    def suite():
        return TcpTriggerTestCase._suite(TcpTriggerTestCase)

class TriggerFactoryTestCase(TriggerTestBase):
    """
    TriggerFactory test cases
    """
    def setUp(self):
        TriggerTestBase.setUp(self)
        
    @enabletest
    def test21001createHttpTrigger(self):
        self.type = 'statusCode'
        self.value = '404'
        self.action = Trigger.Trigger.STOP
        self.tr = Trigger.TriggerFactory.getTrigger(HTTP, self.type, 
                                                    self.value, self.action)
        self.assertEqual(type(self.tr), HttpTrigger.HttpTrigger, 
                         'Create HttpTrigger failed: class mismatch')
    
    @enabletest
    def test21002createTcpTrigger(self):
        self.type = 'reset'
        self.value = 1
        self.action = Trigger.Trigger.STOP
        self.tr = Trigger.TriggerFactory.getTrigger(TCP, self.type, 
                                                    self.value, self.action)
        self.assertEqual(type(self.tr), TcpTrigger.TcpTrigger, 
                         'Create TcpTrigger failed: class mismatch')
    
    @staticmethod 
    def suite():
        return TriggerFactoryTestCase._suite(TriggerFactoryTestCase)
