# System
import unittest
import struct
from socket import inet_ntop, inet_pton, AF_INET, AF_INET6
from atf.common.Common import *

# PCS
import pcs
from pcs.packets.payload import *
from pcs.packets.icmpv4  import *
from pcs.packets.icmpv6  import *
from pcs.packets.tcp import *
from pcs.packets.http import *
from pcs.packets.ipv4 import *
from pcs.packets.ipv6 import *
from pcs.packets.ethernet import *
from pcs.packets.vlan import *


# PyReplay
import atf.common.pcapreplay.PcapReplayBase as PcapReplayBase
import atf.common.pcapreplay.flow.Flow as Flow
import atf.common.pcapreplay.flow.FlowKey as FlowKey
import atf.common.pcapreplay.flow.IpFlowKey as IpFlowKey
import atf.common.pcapreplay.flow.Ipv4FlowKey as Ipv4FlowKey
import atf.common.pcapreplay.flow.Ipv6FlowKey as Ipv6FlowKey
import atf.common.pcapreplay.flow.MacFlowKey as MacFlowKey
import atf.common.pcapreplay.flow.IcmpFlow as IcmpFlow
import atf.common.pcapreplay.flow.TcpFlow as TcpFlow
import atf.common.pcapreplay.flow.UdpFlow as UdpFlow
import atf.common.pcapreplay.flow.GenericFlow as GenericFlow
from atf.common.pcapreplay.Protocol import *
from atf.common.pcapreplay.PcapReplayInfo import *

##
# Globals

##
# Classes
class FlowTestBase(CommonTestCase):
    """
    Base class for all Flow test cases
    """
    def setUp(self):
        """
        Base setup method for all Flow test cases

        args:     none
        return:   none
        """
        self.sT = '1.2.3.4'
        self.dT = '5.6.7.8'
        self.src = NetworkInfo.netPToN(ipv4=self.sT)
        self.dst = NetworkInfo.netPToN(ipv4=self.dT)
        self.s6T = '1111:2222:3333:4444::'
        self.d6T = '5555:6666:7777:8888::'
        self.src6 = NetworkInfo.netPToN(ipv6=self.s6T)
        self.dst6 = NetworkInfo.netPToN(ipv6=self.d6T)
        self.sport = 10
        self.dport = 20
        self.msT = '01:01:01:01:01:01'
        self.mdT = '02:02:02:02:02:02'
        self.smac = NetworkInfo.macPToN(self.msT)
        self.dmac = NetworkInfo.macPToN(self.mdT)
        self.vlanId = 100

    def tearDown(self):
        """
        Base teardown method for all Flow test cases

        args:     none
        return:   none
        """
        pass

    def createIpv4Pkt(self, ipproto=6, layer=None, reverse=False):
        i = ipv4()
        i.protocol = ipproto
        i.id = 0
        i.flags = 0
        if reverse:
            i.dst = self.src
            i.src = self.dst
        else:
            i.src = self.src
            i.dst = self.dst
        i.data = layer
        return pcs.Chain([i, layer]).packets[0]

    def createIpv6Pkt(self, ipproto=6, layer=None, reverse=False):
        i = ipv6()
        i.next_header = ipproto
        if reverse:
            i.dst = self.src6
            i.src = self.dst6
        else:
            i.src = self.src6
            i.dst = self.dst6
        i.data = layer
        return pcs.Chain([i, layer]).packets[0]

    def createVlanPkt(self, type=0x8000, layer=None):
        v = vlan()
        v.vlan = int(self.vlanId)
        v.cfi = 1
        v.p = 4
        v.type = type
        v.data = layer
        return pcs.Chain([v, layer]).packets[0]

    def createEtherPkt(self, type=0x0800, layer=None, reverse=False):
        e = ethernet()
        if reverse:
            e.src = self.dmac
            e.dst = self.smac
        else:
            e.dst = self.dmac
            e.src = self.smac
        e.type = type
        e.data = layer
        return pcs.Chain([e, layer]).packets[0]

    def testSetOperation(self, flowType, pkt1, pkt2, pkt3, pkt4):
        # Test if flow a is equal to flow b
        # Needs to be same sequence and must be continuous(gap is not allowed)
        self.a = flowType()
        self.a.addPacket((1, pkt1))
        self.a.addPacket((2, pkt2))
        self.a.addPacket((3, pkt3))
        self.b = flowType()
        self.b.addPacket((1, pkt1))
        self.b.addPacket((2, pkt2))
        self.b.addPacket((3, pkt3))

        self.assertTrue(self.a == self.b, 'Compare flow failed for a == b.')
        self.assertFalse(self.a != self.b, 'Compare flow failed for a != b.')
        self.assertTrue(self.a >= self.b, 'Compare flow failed for a >= b.')
        self.assertFalse(self.a > self.b, 'Compare flow failed for a > b.')
        self.assertTrue(self.a <= self.b, 'Compare flow failed for a <= b.')
        self.assertFalse(self.a < self.b, 'Compare flow failed for a < b.')
        self.assertTrue(self.a.issubset(self.b), 'Compare flow failed for a.issubset(b).')
        self.assertTrue(self.a.issuperset(self.b), 'Compare flow failed for a.issuperset(b).')

        # Test if flow a is not equal to flow b
        self.a = flowType()
        self.a.addPacket((1, pkt1))
        self.a.addPacket((2, pkt2))
        self.b = flowType()
        self.b.addPacket((1, pkt3))
        self.b.addPacket((2, pkt4))

        self.assertFalse(self.a == self.b, 'Compare flow failed for a == b.')
        self.assertTrue(self.a != self.b, 'Compare flow failed for a != b.')
        self.assertFalse(self.a >= self.b, 'Compare flow failed for a >= b.')
        self.assertFalse(self.a > self.b, 'Compare flow failed for a > b.')
        self.assertFalse(self.a <= self.b, 'Compare flow failed for a <= b.')
        self.assertFalse(self.a < self.b, 'Compare flow failed for a < b.')
        self.assertFalse(self.a.issubset(self.b), 'Compare flow failed for a.issubset(b).')
        self.assertFalse(self.a.issuperset(self.b), 'Compare flow failed for a.issuperset(b).')

        # Test if flow a is a proper subset of flow b
        # Needs to be same sequence and must be continuous(gap is not allowed)
        self.a = flowType()
        self.a.addPacket((1, pkt1))
        self.a.addPacket((2, pkt2))
        self.a.addPacket((3, pkt3))
        self.b = flowType()
        self.b.addPacket((1, pkt1))
        self.b.addPacket((2, pkt2))
        self.b.addPacket((3, pkt3))
        self.b.addPacket((4, pkt4))

        self.assertFalse(self.a == self.b, 'Compare flow failed for a == b.')
        self.assertTrue(self.a != self.b, 'Compare flow failed for a != b.')
        self.assertFalse(self.a >= self.b, 'Compare flow failed for a >= b.')
        self.assertFalse(self.a > self.b, 'Compare flow failed for a > b.')
        self.assertTrue(self.a <= self.b, 'Compare flow failed for a <= b.')
        self.assertTrue(self.a < self.b, 'Compare flow failed for a < b.')
        self.assertTrue(self.a.issubset(self.b), 'Compare flow failed for a.issubset(b).')
        self.assertFalse(self.a.issuperset(self.b), 'Compare flow failed for a.issuperset(b).')

        # Test if flow b is a proper subset of flow a
        # Needs to be same sequence as the comparison and must be continuous(gap is not allowed)
        self.a = flowType()
        self.a.addPacket((1, pkt1))
        self.a.addPacket((2, pkt2))
        self.a.addPacket((3, pkt3))
        self.b = flowType()
        self.b.addPacket((1, pkt1))
        self.b.addPacket((2, pkt2))

        self.assertFalse(self.a == self.b, 'Compare flow failed for a == b.')
        self.assertTrue(self.a != self.b, 'Compare flow failed for a != b.')
        self.assertTrue(self.a >= self.b, 'Compare flow failed for a >= b.')
        self.assertTrue(self.a > self.b, 'Compare flow failed for a > b.')
        self.assertFalse(self.a <= self.b, 'Compare flow failed for a <= b.')
        self.assertFalse(self.a < self.b, 'Compare flow failed for a < b.')
        self.assertFalse(self.a.issubset(self.b), 'Compare flow failed for a.issubset(b).')
        self.assertTrue(self.a.issuperset(self.b), 'Compare flow failed for a.issuperset(b).')

        self.a = flowType()
        self.a.addPacket((1, pkt1))
        self.a.addPacket((3, pkt3))
        self.b = flowType()
        self.b.addPacket((1, pkt1))
        self.b.addPacket((2, pkt2))
        self.b.addPacket((3, pkt3))
        self.b.addPacket((4, pkt4))
        # Test whether every packet for the flow a are in flow b
        # Needs to be same sequence, but no need to be contiguous(gaps are allowed)
        self.assertFalse(self.a == self.b, 'Compare flow failed for a == b.')
        self.assertTrue(self.a != self.b, 'Compare flow failed for a != b.')
        self.assertFalse(self.a >= self.b, 'Compare flow failed for a >= b.')
        self.assertFalse(self.a > self.b, 'Compare flow failed for a > b.')
        self.assertFalse(self.a <= self.b, 'Compare flow failed for a <= b.')
        self.assertFalse(self.a < self.b, 'Compare flow failed for a < b.')
        self.assertTrue(self.a.issubset(self.b), 'Compare flow failed for a.issubset(b).')
        # Test whether flow b is in the packet list for the flow a
        self.assertFalse(self.a.issuperset(self.b), 'Compare flow failed for a.issuperset(b).')

class FlowKeyTestCase(FlowTestBase):
    """
    FlowKey test cases
    """
    def setUp(self):
        FlowTestBase.setUp(self)
        self.fk = None
        self.rf = None
        self.proto = TCP

    @enabletest
    def test10001create(self):
        # Create primary test FlowKey
        self.fk = FlowKey.FlowKey(self.src, self.dst, self.proto)
        self.assertEqual(self.fk.src, self.src,
                         'FK Creation failed: src incorrect')
        self.assertEqual(self.fk.dst, self.dst,
                         'FK Creation failed: dst incorrect')
        self.assertEqual(self.fk.proto, self.proto,
                         'FK Creation failed: proto incorrect')

        # Create secondary test FlowKey
        self.rf = FlowKey.FlowKey(self.src, self.dst, self.proto)
        self.assertEqual(self.rf.src, self.src,
                         'RF Creation failed: src incorrect')
        self.assertEqual(self.rf.dst, self.dst,
                         'RF Creation failed: dst incorrect')
        self.assertEqual(self.rf.proto, self.proto,
                         'RF Creation failed: proto incorrect')

    @enabletest
    def test10002equals(self):
        self.fk = FlowKey.FlowKey(self.src, self.dst, self.proto)
        self.rf = FlowKey.FlowKey(self.src, self.dst, self.proto)
        try:
            foo = (self.fk == self.rf)
            self.fail('Equals failed: Exception not raised')
        except Exception, e:
            self.assertEqual(e.errCode, PcapReplayError.ERR_PCAPR_IMPL,
                             'Equals failed: Unexpected exception')

    @enabletest
    def test10003notEquals(self):
        self.fk = FlowKey.FlowKey(self.src, self.dst, self.proto)
        self.rf = FlowKey.FlowKey(self.src, self.dst, self.proto)
        try:
            foo = (self.fk != self.rf)
            self.fail('Not Equals failed: Exception not raised')
        except Exception, e:
            self.assertEqual(e.errCode, PcapReplayError.ERR_PCAPR_IMPL,
                              'Not Equals failed: Unexpected exception')

    @enabletest
    def test10004reverse(self):
        self.fk = FlowKey.FlowKey(self.src, self.dst, self.proto)
        self.rf = self.fk.reverse()
        self.assertEqual(self.rf.src, self.fk.dst,
                         'Reverse failed: src/dst not reversed')
        self.assertEqual(self.rf.dst, self.fk.src,
                         'Reverse failed: dst/src not reversed')

    @enabletest
    def test10005hash(self):
        # IPv4
        self.fk = FlowKey.FlowKey(self.src, self.dst, self.proto)
        self.rf = self.fk.reverse()
        try:
            testDict = {self.rf: 1, self.fk: 2}
            foo = testDict[self.fk]
            self.fail('Hash failed: Exception not raised')
        except Exception, e:
            self.assertEqual(e.errCode, PcapReplayError.ERR_PCAPR_IMPL,
                             'Hash failed: Unexpected exception')

    @staticmethod
    def suite():
        return FlowKeyTestCase._suite(FlowKeyTestCase)

class IpFlowKeyTestCase(FlowTestBase):
    """
    FlowKey test cases
    """
    def setUp(self):
        FlowTestBase.setUp(self)
        self.fk = None
        self.rf = None
        self.proto = TCP

    @enabletest
    def test10021create(self):
        # Create primary test FlowKey
        self.fk = IpFlowKey.IpFlowKey(self.src, self.dst, self.proto,
                                      self.sport, self.dport)
        self.assertEqual(self.fk.src, self.src,
                         'FK Creation failed: src incorrect')
        self.assertEqual(self.fk.dst, self.dst,
                         'FK Creation failed: dst incorrect')
        self.assertEqual(self.fk.sport, self.sport,
                         'FK Creation failed: sport incorrect')
        self.assertEqual(self.fk.dport, self.dport,
                         'FK Creation failed: dport incorrect')
        self.assertEqual(self.fk.proto, self.proto,
                         'FK Creation failed: proto incorrect')

        # Create secondary test FlowKey
        self.rf = IpFlowKey.IpFlowKey(self.src, self.dst, self.proto,
                                      self.sport, self.dport)
        self.assertEqual(self.rf.src, self.src,
                         'RF Creation failed: src incorrect')
        self.assertEqual(self.rf.dst, self.dst,
                         'RF Creation failed: dst incorrect')
        self.assertEqual(self.rf.sport, self.sport,
                         'RF Creation failed: sport incorrect')
        self.assertEqual(self.rf.dport, self.dport,
                         'RF Creation failed: dport incorrect')
        self.assertEqual(self.rf.proto, self.proto,
                         'RF Creation failed: proto incorrect')

    @enabletest
    def test10022equals(self):
        self.fk = IpFlowKey.IpFlowKey(self.src, self.dst, self.proto,
                                      self.sport, self.dport)
        self.rf = IpFlowKey.IpFlowKey(self.src, self.dst, self.proto,
                                      self.sport, self.dport)
        try:
            foo = (self.fk == self.rf)
            self.fail('Equals failed: Exception not raised')
        except Exception, e:
            self.assertEqual(e.errCode, PcapReplayError.ERR_PCAPR_IMPL,
                             'Equals failed: Unexpected exception')

    @enabletest
    def test10023notEquals(self):
        self.fk = IpFlowKey.IpFlowKey(self.src, self.dst, self.proto,
                                      self.sport, self.dport)
        self.rf = IpFlowKey.IpFlowKey(self.dst, self.src, self.proto,
                                      self.sport, self.dport)
        try:
            foo = (self.fk != self.rf)
            self.fail('Not Equals failed: Exception not raised')
        except Exception, e:
            self.assertEqual(e.errCode, PcapReplayError.ERR_PCAPR_IMPL,
                             'Not Equals failed: Unexpected exception')

    @enabletest
    def test10024reverse(self):
        self.fk = IpFlowKey.IpFlowKey(self.src, self.dst, self.proto,
                                      self.sport, self.dport)
        self.rf = self.fk.reverse()
        self.assertEqual(self.rf.src, self.fk.dst,
                         'Reverse failed: src/dst not reversed')
        self.assertEqual(self.rf.dst, self.fk.src,
                         'Reverse failed: dst/src not reversed')
        self.assertEqual(self.rf.sport, self.fk.dport,
                         'Reverse failed: sport/dport not reversed')
        self.assertEqual(self.rf.dport, self.fk.sport,
                         'Reverse failed: dport/sport not reversed')

    @enabletest
    def test10025hash(self):
        self.fk = IpFlowKey.IpFlowKey(self.src, self.dst, self.proto,
                                      self.sport, self.dport)
        self.rf = self.fk.reverse()
        try:
            testDict = {self.rf: 1, self.fk: 2}
            foo = testDict[self.fk]
            self.fail('Hash failed: Exception not raised')
        except Exception, e:
            self.assertEqual(e.errCode, PcapReplayError.ERR_PCAPR_IMPL,
                             'Hash failed: Unexpected exception')

    @staticmethod
    def suite():
        return IpFlowKeyTestCase._suite(IpFlowKeyTestCase)

class Ipv4FlowKeyTestCase(FlowTestBase):
    """
    FlowKey test cases
    """
    def setUp(self):
        FlowTestBase.setUp(self)
        self.fk = None
        self.rf = None
        self.proto = TCP

    @enabletest
    def test10041create(self):
        # Create primary test FlowKey
        self.fk = Ipv4FlowKey.Ipv4FlowKey(self.src, self.dst, self.proto,
                                          self.sport, self.dport)
        self.assertEqual(self.fk.src, self.src,
                         'FK Creation failed: src incorrect')
        self.assertEqual(self.fk.dst, self.dst,
                         'FK Creation failed: dst incorrect')
        self.assertEqual(self.fk.sport, self.sport,
                         'FK Creation failed: sport incorrect')
        self.assertEqual(self.fk.dport, self.dport,
                         'FK Creation failed: dport incorrect')
        self.assertEqual(self.fk.proto, self.proto,
                         'FK Creation failed: proto incorrect')

        # Create secondary test FlowKey
        self.rf = Ipv4FlowKey.Ipv4FlowKey(self.src, self.dst, self.proto,
                                          self.sport, self.dport)
        self.assertEqual(self.rf.src, self.src,
                         'RF Creation failed: src incorrect')
        self.assertEqual(self.rf.dst, self.dst,
                         'RF Creation failed: dst incorrect')
        self.assertEqual(self.rf.sport, self.sport,
                         'RF Creation failed: sport incorrect')
        self.assertEqual(self.rf.dport, self.dport,
                         'RF Creation failed: dport incorrect')
        self.assertEqual(self.rf.proto, self.proto,
                         'RF Creation failed: proto incorrect')

    @enabletest
    def test10042equals(self):
        self.fk = Ipv4FlowKey.Ipv4FlowKey(self.src, self.dst, self.sport,
                                          self.dport, self.proto)
        self.rf = Ipv4FlowKey.Ipv4FlowKey(self.src, self.dst, self.sport,
                                          self.dport, self.proto)
        self.assertEqual(self.fk, self.rf,
                         'Equals failed: Primary FlowKey is not equal ' +
                         'to the Secondary FlowKey')

    @enabletest
    def test10043notEquals(self):
        self.fk = Ipv4FlowKey.Ipv4FlowKey(self.src, self.dst, self.sport,
                                          self.dport, self.proto)
        self.rf = Ipv4FlowKey.Ipv4FlowKey(self.dst, self.src, self.dport,
                                          self.sport, self.proto)
        self.assertNotEqual(self.fk, self.rf,
                            'Equals failed: Primary FlowKey is not equal ' +
                            'to the Secondary FlowKey')

    @enabletest
    def test10044hash(self):
        self.fk = Ipv4FlowKey.Ipv4FlowKey(self.src, self.dst, self.sport,
                                          self.dport, self.proto)
        self.rf = self.fk.reverse()
        testDict = {self.rf: 1, self.fk: 2}
        self.assertEqual(testDict[self.fk], 2,
                         'Hash failed: dict hashing failed to return correctly')

    @staticmethod
    def suite():
        return Ipv4FlowKeyTestCase._suite(Ipv4FlowKeyTestCase)

class Ipv6FlowKeyTestCase(FlowTestBase):
    """
    FlowKey test cases
    """
    def setUp(self):
        FlowTestBase.setUp(self)
        self.fk = None
        self.rf = None
        self.proto = TCP

    @enabletest
    def test10061create(self):
        # Create primary test FlowKey
        self.fk = Ipv6FlowKey.Ipv6FlowKey(self.src6, self.dst6, self.proto,
                                          self.sport, self.dport)
        self.assertEqual(self.fk.src, self.src6,
                         'FK Creation failed: src incorrect')
        self.assertEqual(self.fk.dst, self.dst6,
                         'FK Creation failed: dst incorrect')
        self.assertEqual(self.fk.sport, self.sport,
                         'FK Creation failed: sport incorrect')
        self.assertEqual(self.fk.dport, self.dport,
                         'FK Creation failed: dport incorrect')
        self.assertEqual(self.fk.proto, self.proto,
                         'FK Creation failed: proto incorrect')

        # Create secondary test FlowKey
        self.rf = Ipv6FlowKey.Ipv6FlowKey(self.src6, self.dst6, self.proto,
                                          self.sport, self.dport)
        self.assertEqual(self.rf.src, self.src6,
                         'RF Creation failed: src incorrect')
        self.assertEqual(self.rf.dst, self.dst6,
                         'RF Creation failed: dst incorrect')
        self.assertEqual(self.rf.sport, self.sport,
                         'RF Creation failed: sport incorrect')
        self.assertEqual(self.rf.dport, self.dport,
                         'RF Creation failed: dport incorrect')
        self.assertEqual(self.rf.proto, self.proto,
                         'RF Creation failed: proto incorrect')

    @enabletest
    def test10062equals(self):
        self.fk = Ipv6FlowKey.Ipv6FlowKey(self.src6, self.dst6, self.proto,
                                          self.sport, self.dport)
        self.rf = Ipv6FlowKey.Ipv6FlowKey(self.src6, self.dst6, self.proto,
                                          self.sport, self.dport)
        self.assertEqual(self.fk, self.rf,
                         'Equals failed: Primary FlowKey is not equal ' +
                         'to the Secondary FlowKey')

    @enabletest
    def test10063notEquals(self):
        self.fk = Ipv6FlowKey.Ipv6FlowKey(self.src6, self.dst6, self.proto,
                                          self.sport, self.dport)
        self.rf = Ipv6FlowKey.Ipv6FlowKey(self.dst6, self.src6, self.proto,
                                          self.sport, self.dport)
        self.assertNotEqual(self.fk, self.rf,
                            'Equals failed: Primary FlowKey is not equal ' +
                            'to the Secondary FlowKey')

    @enabletest
    def test10064hash(self):
        self.fk = Ipv6FlowKey.Ipv6FlowKey(self.src6, self.dst6, self.proto,
                                          self.sport, self.dport)
        self.rf = self.fk.reverse()
        testDict = {self.rf: 1, self.fk: 2}
        self.assertEqual(testDict[self.fk], 2,
                         'Hash failed: dict hashing failed to return correctly')

    @staticmethod
    def suite():
        return Ipv6FlowKeyTestCase._suite(Ipv6FlowKeyTestCase)

class MacFlowKeyTestCase(FlowTestBase):
    """
    MacFlowKey test cases
    """
    def setUp(self):
        FlowTestBase.setUp(self)
        self.fk = None
        self.rf = None
        self.proto = GENERIC

    @enabletest
    def test10081create(self):
        # Create primary test FlowKey
        self.fk = MacFlowKey.MacFlowKey(self.smac, self.dmac, self.proto)
        self.assertEqual(self.fk.src, self.smac,
                         'FK Creation failed: src incorrect')
        self.assertEqual(self.fk.dst, self.dmac,
                         'FK Creation failed: dst incorrect')
        self.assertEqual(self.fk.proto, self.proto,
                         'FK Creation failed: proto incorrect')

    @enabletest
    def test10082equals(self):
        self.fk = MacFlowKey.MacFlowKey(self.smac, self.dmac, self.proto)
        self.rf = MacFlowKey.MacFlowKey(self.smac, self.dmac, self.proto)
        self.assertEqual(self.fk, self.rf,
                         'Equals failed: Primary FlowKey is not equal ' +
                         'to the Secondary FlowKey')

    @enabletest
    def test10083notEquals(self):
        self.fk = MacFlowKey.MacFlowKey(self.smac, self.dmac, self.proto)
        self.rf = MacFlowKey.MacFlowKey(self.dmac, self.smac, self.proto)
        self.assertNotEqual(self.fk, self.rf,
                            'Equals failed: Primary FlowKey is not equal ' +
                            'to the Secondary FlowKey')

    @enabletest
    def test10084hash(self):
        self.fk = MacFlowKey.MacFlowKey(self.smac, self.dmac, self.proto)
        self.rf = self.fk.reverse()
        testDict = {self.rf: 1, self.fk: 2}
        self.assertEqual(testDict[self.fk], 2,
                         'Hash failed: dict hashing failed to return correctly')

    @staticmethod
    def suite():
        return MacFlowKeyTestCase._suite(MacFlowKeyTestCase)

class FlowKeyFactoryTestCase(FlowTestBase):
    """
    FlowKeyFactory test cases
    """
    @enabletest
    def test11001createIpv4FlowKey(self):
        self.fk = FlowKey.FlowKeyFactory.getFlowKey(IPV4, self.src, self.dst,
                                                    TCP, self.sport,
                                                    self.dport)
        self.assertEqual(isinstance(self.fk, Ipv4FlowKey.Ipv4FlowKey), True,
                         'Create Ipv4FlowKey failed: getFlow type mismatch')
        self.assertEqual(self.fk.src, self.src,
                         'FK Creation failed: src incorrect')
        self.assertEqual(self.fk.dst, self.dst,
                         'FK Creation failed: dst incorrect')
        self.assertEqual(self.fk.sport, self.sport,
                         'FK Creation failed: sport incorrect')
        self.assertEqual(self.fk.dport, self.dport,
                         'FK Creation failed: dport incorrect')
        self.assertEqual(self.fk.proto, TCP,
                         'FK Creation failed: proto incorrect')

    @enabletest
    def test11002createIpv6FlowKey(self):
        self.fk = FlowKey.FlowKeyFactory.getFlowKey(IPV6, self.src6, self.dst6,
                                                    TCP, self.sport,
                                                    self.dport)
        self.assertEqual(isinstance(self.fk, Ipv6FlowKey.Ipv6FlowKey), True,
                         'Create Ipv6FlowKey failed: getFlow type mismatch')
        self.assertEqual(self.fk.src, self.src6,
                         'FK Creation failed: src incorrect')
        self.assertEqual(self.fk.dst, self.dst6,
                         'FK Creation failed: dst incorrect')
        self.assertEqual(self.fk.sport, self.sport,
                         'FK Creation failed: sport incorrect')
        self.assertEqual(self.fk.dport, self.dport,
                         'FK Creation failed: dport incorrect')
        self.assertEqual(self.fk.proto, TCP,
                         'FK Creation failed: proto incorrect')

    @enabletest
    def test11003createMacFlowKey(self):
        self.fk = FlowKey.FlowKeyFactory.getFlowKey(MAC, self.smac, self.dmac,
                                                    GENERIC)
        self.assertEqual(isinstance(self.fk, MacFlowKey.MacFlowKey), True,
                         'Create MacFlowKey failed: getFlow type mismatch')
        self.assertEqual(self.fk.src, self.smac,
                         'FK Creation failed: src incorrect')
        self.assertEqual(self.fk.dst, self.dmac,
                         'FK Creation failed: dst incorrect')
        self.assertEqual(self.fk.proto, GENERIC,
                         'FK Creation failed: proto incorrect')

    @staticmethod
    def suite():
        return FlowKeyFactoryTestCase._suite(FlowKeyFactoryTestCase)

class FlowTestCase(FlowTestBase):
    """
    Flow test cases
    """
    def setUp(self):
        FlowTestBase.setUp(self)
        self.f = None

    @enabletest
    def test12001create(self):
        self.f = Flow.Flow()
        self.assertNotEqual(self.f, None,
                            'Create failed: Flow could not be created')

    @enabletest
    def test12002addPacket(self):
        t = pcs.packets.tcp.tcp()
        t.sport = self.sport
        t.dport = self.dport
        t.ack = 1
        t.ack_number = 0
        t.sequence = 0
        t.data = None
        self.f = Flow.Flow()

        try:
            pkt = self.createIpv4Pkt(0x06, t)
            self.f.addPacket((0, pkt))
            self.fail('addPacket failed: Exception not raised')
        except Exception, e:
            self.assertEqual(e.errCode, PcapReplayError.ERR_PCAPR_IMPL,
                             'addPacket failed: Unexpected exception')

    @enabletest
    def test12003replayPkts(self):
        # Set up tap devices for transmit
        ret = -1
        if os.system('which vde_switch &> /dev/null') == 0:
            ret = os.system('killall -9 vde_switch &> /dev/null; ' +
                            'vde_switch -tap tap8 -tap tap9 --daemon && ' +
                            'ifconfig tap8 10.50.50.1 up && ' +
                            'ifconfig tap9 10.50.60.1 up')
        self.assertEqual(ret, 0, 'Replay failed: Unable to setup tap devices')

        # Setup packet
        pkts = []
        self.f = Flow.Flow()
        t = pcs.packets.tcp.tcp()
        t.sport = self.sport
        t.dport = self.dport
        t.ack = 1
        t.ack_number = 0
        t.sequence = 0
        t.data = None
        pkts.append(self.createIpv4Pkt(0x06, t))
        pkts.append(self.createIpv6Pkt(0x06, t))

        # Setup PcapConnectors
        cpc = pcs.PcapConnector('tap8')
        spc = pcs.PcapConnector('tap9')

        # ReplayPkts
        try:
            for pkt in pkts:
                self.f.replayPkts([(1, pkt.chain(), cpc)], cpc, spc, verify=1)
        except Exception, e:
            os.system('ifconfig tap8 down && ifconfig tap9 down && ' +
                      'killall -9 vde_switch')
            self.fail('Replay failed: Failed send and verify [%s]' % str(e))
        os.system('ifconfig tap8 down && ifconfig tap9 down && ' +
                  'killall -9 vde_switch')

    @staticmethod
    def suite():
        return FlowTestCase._suite(FlowTestCase)

class FlowIcmpTestCase(FlowTestBase):
    """
    IcmpFlow test cases
    """
    def setUp(self):
        FlowTestBase.setUp(self)
        self.f = None

    @enabletest
    def test12021create(self):
        self.f = IcmpFlow.IcmpFlow()
        self.assertNotEqual(self.f, None,
                            'Create failed: Flow could not be created')

    @enabletest
    def test12022addPacket(self):
        # IPv4
        self.f = IcmpFlow.IcmpFlow()
        ic = pcs.packets.icmpv4.icmpv4()
        ic.data = None
        ip = self.createIpv4Pkt(0x01, ic)
        pkt = self.createEtherPkt(layer=ip)

        self.f.addPacket((0, pkt))
        self.assertEqual(self.f.flk.src, self.src,
                         'Packet add failed: src not set')
        self.assertEqual(self.f.flk.dst, self.dst,
                         'Packet add failed: dst not set')
        self.assertEqual(self.f.flk.proto, ICMP,
                         'Packet add failed: proto is not ICMP')
        self.assertEqual(len(self.f.pkts), 1,
                         'Packet add failed: pkt not added to Flow list')

       # IPv6
        self.f = IcmpFlow.IcmpFlow()
        ic = pcs.packets.icmpv6.icmpv6()
        ic.data = None
        ip = self.createIpv6Pkt(0x01, ic)
        pkt = self.createEtherPkt(type=0x86dd, layer=ip)
        self.f.addPacket((0, pkt))
        self.assertEqual(self.f.flk.src, self.src6,
                         'Packet add6 failed: src not set')
        self.assertEqual(self.f.flk.dst, self.dst6,
                         'Packet add6 failed: dst not set')
        self.assertEqual(self.f.flk.proto, ICMP,
                         'Packet add6 failed: proto is not ICMP')
        self.assertEqual(len(self.f.pkts), 1,
                         'Packet add6 failed: pkt not added to Flow list')

       # Generic
        self.f = IcmpFlow.IcmpFlow()
        a = pcs.packets.arp.arp()
        a.data = None
        pkt = self.createEtherPkt(layer=a)
        try:
            self.f.addPacket((0, pkt))
        except Exception, e:
            self.assertEqual(isinstance(e, PcapReplayBase.PcapReplayError),
                             True, 'Packet addG failed: Unexpected Error Type')
            self.assertEqual(e.errCode, Flow.ERR_PCAPR_FLOW_KEY_CREATE,
                             'Packet addG failed: Unexpected exception')

        # VLAN
        self.f = IcmpFlow.IcmpFlow()
        ic = pcs.packets.icmpv4.icmpv4()
        ic.data = None
        ip = self.createIpv4Pkt(0x01, ic)
        vlan = self.createVlanPkt(type=0x8000, layer=ip)
        pkt = self.createEtherPkt(type=0x8100, layer=vlan)

        self.f.addPacket((0, pkt))
        self.assertEqual(self.f.flk.src, self.src,
                         'Packet add failed: src not set')
        self.assertEqual(self.f.flk.dst, self.dst,
                         'Packet add failed: dst not set')
        self.assertEqual(self.f.flk.proto, ICMP,
                         'Packet add failed: proto is not ICMP')
        self.assertEqual(len(self.f.pkts), 1,
                         'Packet add failed: pkt not added to Flow list')

    @enabletest
    def test12023matchFlow(self):
        # IPv4
        self.f = IcmpFlow.IcmpFlow()
        ic = pcs.packets.icmpv4.icmpv4()
        ic.data = None
        ip = self.createIpv4Pkt(0x01, ic)
        pkt = self.createEtherPkt(layer=ip)

        self.f.addPacket((0, pkt))
        self.assertEqual(self.f.matchFlow(pkt), True,
                        'Match flow failed: pkt not matched correctly')

        # IPv6
        self.f = IcmpFlow.IcmpFlow()
        ic = pcs.packets.icmpv6.icmpv6()
        ic.data = None
        ip = self.createIpv6Pkt(0x01, ic)
        pkt = self.createEtherPkt(type=0x86dd, layer=ip)

        self.f.addPacket((0, pkt))
        self.assertEqual(self.f.matchFlow(pkt), True,
                        'Match flow6 failed: pkt not matched correctly')

        # VLAN
        self.f = IcmpFlow.IcmpFlow()
        ic = pcs.packets.icmpv4.icmpv4()
        ic.data = None
        ip = self.createIpv4Pkt(0x01, ic)
        vlan = self.createVlanPkt(type=0x8000, layer=ip)
        pkt = self.createEtherPkt(type=0x8100, layer=vlan)

        self.f.addPacket((0, pkt))
        self.assertEqual(self.f.matchFlow(pkt), True,
                        'Match flow failed: pkt not matched correctly')

    @enabletest
    def test12024splitFlow(self):
        # IPv4
        self.f = IcmpFlow.IcmpFlow()
        ic = pcs.packets.icmpv4.icmpv4()
        ic.data = None
        ip = self.createIpv4Pkt(0x01, ic)
        pkt = self.createEtherPkt(layer=ip)

        self.f.addPacket((0, pkt))
        ic = pcs.packets.icmpv4.icmpv4()
        ic.data = None
        ip = self.createIpv4Pkt(0x01, ic, True)
        pkt = self.createEtherPkt(layer=ip)

        self.f.addPacket((1, pkt))
        f, r = self.f.splitFlow()
        self.assertEqual((len(f), len(r)), (1, 1),
                         "Split flow failed: incorrect split")
        self.assertEqual(f[0][1].data.src, self.src,
                         "Split flow failed: incorrect forward packet")
        self.assertEqual(r[0][1].data.src, self.dst,
                         "Split flow failed: incorrect reverse packet")

        # IPv6
        self.f = IcmpFlow.IcmpFlow()
        ic = pcs.packets.icmpv6.icmpv6()
        ic.data = None
        ip = self.createIpv6Pkt(0x01, ic)
        pkt = self.createEtherPkt(layer=ip)

        self.f.addPacket((0, pkt))
        ic = pcs.packets.icmpv6.icmpv6()
        ic.data = None
        ip = self.createIpv6Pkt(0x01, ic, True)
        pkt = self.createEtherPkt(type=0x86dd, layer=ip)

        self.f.addPacket((1, pkt))
        f, r = self.f.splitFlow()
        self.assertEqual((len(f), len(r)), (1, 1),
                         "Split flow6 failed: incorrect split")
        self.assertEqual(f[0][1].data.src, self.src6,
                         "Split flow6 failed: incorrect forward packet")
        self.assertEqual(r[0][1].data.src, self.dst6,
                         "Split flow6 failed: incorrect reverse packet")

    @enabletest
    def test12025getReplayPktList(self):
        pcp = pcs.PcapConnector('lo')
        ni = NetworkInfo()

        # IPv4
        ni.setNetworkInfo('', '', self.mdT, self.msT, self.dT, self.sT)
        self.f = IcmpFlow.IcmpFlow()
        ic = pcs.packets.icmpv4.icmpv4()
        ic.data = None
        ip = self.createIpv4Pkt(0x01, ic)
        pkt = self.createEtherPkt(layer=ip)

        self.f.addPacket((0, pkt))

        pkts = self.f.getReplayPktList(ni, pcp, pcp, True)
        for s, c, i in pkts:
            self.assertEqual((c.packets[1].src, c.packets[1].dst),
                             (self.dst, self.src),
                             "Replay fixup failed: incorrect addresses")
            self.assertEqual(i, pcp,
                             "Replay fixup failed: PcapConnectors incorrect")

        # IPv6
        ni.setNetworkInfo('', '', self.mdT, self.msT, '', '', self.d6T, self.s6T)
        self.f = IcmpFlow.IcmpFlow()
        ic = pcs.packets.icmpv6.icmpv6()
        ic.data = None
        ip = self.createIpv6Pkt(0x01, ic)
        pkt = self.createEtherPkt(type=0x86dd, layer=ip)

        self.f.addPacket((0, pkt))
        pkts = self.f.getReplayPktList(ni, pcp, pcp, True)
        for s, c, i in pkts:
            self.assertEqual((c.packets[1].src, c.packets[1].dst),
                             (self.dst6, self.src6),
                             "Replay fixup failed: incorrect addresses")
            self.assertEqual(i, pcp,
                             "Replay fixup failed: PcapConnectors incorrect")


    @enabletest
    def test120250getReplayPktListWithVlan(self):
        pcp = pcs.PcapConnector('lo')
        ni = NetworkInfo()

        # IPv4
        ni.setNetworkInfo('', '', self.mdT, self.msT, self.dT, self.sT, '', '', self.vlanId)
        self.f = IcmpFlow.IcmpFlow()
        ic = pcs.packets.icmpv4.icmpv4()
        ic.data = None
        ip = self.createIpv4Pkt(0x01, ic)
        vlan = self.createVlanPkt(type=0x8000, layer=ip)
        pkt = self.createEtherPkt(type=0x8100, layer=vlan)

        self.f.addPacket((0, pkt))

        pkts = self.f.getReplayPktList(ni, pcp, pcp, True)
        for s, c, i in pkts:
            self.assertEqual(c.packets[1].vlan, int(self.vlanId),
                             "Replay fixup failed: incorrect vlan id")
            self.assertEqual((c.packets[2].src, c.packets[2].dst),
                             (self.dst, self.src),
                             "Replay fixup failed: incorrect addresses")
            self.assertEqual(i, pcp,
                             "Replay fixup failed: PcapConnectors incorrect")

        # IPv6
        ni.setNetworkInfo('', '', self.mdT, self.msT, '', '', self.d6T, self.s6T, self.vlanId)
        self.f = IcmpFlow.IcmpFlow()
        ic = pcs.packets.icmpv6.icmpv6()
        ic.data = None
        ip = self.createIpv6Pkt(0x01, ic)
        vlan = self.createVlanPkt(type=0x86dd, layer=ip)
        pkt = self.createEtherPkt(type=0x8100, layer=vlan)

        self.f.addPacket((0, pkt))
        pkts = self.f.getReplayPktList(ni, pcp, pcp, True)
        for s, c, i in pkts:
            self.assertEqual(c.packets[1].vlan, int(self.vlanId),
                             "Replay fixup failed: incorrect vlan id")
            self.assertEqual((c.packets[2].src, c.packets[2].dst),
                             (self.dst6, self.src6),
                             "Replay fixup failed: incorrect addresses")
            self.assertEqual(i, pcp,
                             "Replay fixup failed: PcapConnectors incorrect")


    @enabletest
    def test12026compareFlowIPv4(self):

        # Create 4 IPv4 ICMP packets that have different checksums.
        ic1 = pcs.packets.icmpv4.icmpv4()
        ic1.checksum = 1111
        ic1.data = None
        ic2 = pcs.packets.icmpv4.icmpv4()
        ic2.checksum = 2222
        ic2.data = None
        ic3 = pcs.packets.icmpv4.icmpv4()
        ic3.checksum = 3333
        ic3.data = None
        ic4 = pcs.packets.icmpv4.icmpv4()
        ic4.checksum = 4444
        ic4.data = None
        ip1 = self.createIpv4Pkt(0x01, ic1)
        ip2 = self.createIpv4Pkt(0x01, ic2)
        ip3 = self.createIpv4Pkt(0x01, ic3)
        ip4 = self.createIpv4Pkt(0x01, ic4)

        pkt1 = self.createEtherPkt(layer=ip1)
        pkt2 = self.createEtherPkt(layer=ip2)
        pkt3 = self.createEtherPkt(layer=ip3)
        pkt4 = self.createEtherPkt(layer=ip4)

        self.testSetOperation(IcmpFlow.IcmpFlow, pkt1, pkt2, pkt3, pkt4)

    @enabletest
    def test12027compareFlowIPv6(self):
        # Create 4 IPv6 ICMP packets that have different checksums.
        ic1 =pcs.packets.icmpv6.icmpv6()
        ic1.checksum = 1111
        ic1.data = None
        ic2 = pcs.packets.icmpv6.icmpv6()
        ic2.checksum = 2222
        ic2.data = None
        ic3 =pcs.packets.icmpv6.icmpv6()
        ic3.checksum = 3333
        ic3.data = None
        ic4 = pcs.packets.icmpv6.icmpv6()
        ic4.checksum = 4444
        ic4.data = None

        ip1 = self.createIpv4Pkt(0x01, ic1)
        ip2 = self.createIpv4Pkt(0x01, ic2)
        ip3 = self.createIpv4Pkt(0x01, ic3)
        ip4 = self.createIpv4Pkt(0x01, ic4)

        pkt1 = self.createEtherPkt(type=0x86dd, layer=ip1)
        pkt2 = self.createEtherPkt(type=0x86dd, layer=ip2)
        pkt3 = self.createEtherPkt(type=0x86dd, layer=ip3)
        pkt4 = self.createEtherPkt(type=0x86dd, layer=ip4)
        self.testSetOperation(IcmpFlow.IcmpFlow, pkt1, pkt2, pkt3, pkt4)

    @enabletest
    def test12028compareFlowVlan(self):

        # Create 4 IPv4 ICMP VLAN tagged packets that have different checksums.
        ic1 = pcs.packets.icmpv4.icmpv4()
        ic1.checksum = 1111
        ic1.data = None
        ic2 = pcs.packets.icmpv4.icmpv4()
        ic2.checksum = 2222
        ic2.data = None
        ic3 = pcs.packets.icmpv4.icmpv4()
        ic3.checksum = 3333
        ic3.data = None
        ic4 = pcs.packets.icmpv4.icmpv4()
        ic4.checksum = 4444
        ic4.data = None
        ip1 = self.createIpv4Pkt(0x01, ic1)
        ip2 = self.createIpv4Pkt(0x01, ic2)
        ip3 = self.createIpv4Pkt(0x01, ic3)
        ip4 = self.createIpv4Pkt(0x01, ic4)

        vlan1 = self.createVlanPkt(type=0x8000, layer=ip1)
        vlan2 = self.createVlanPkt(type=0x8000, layer=ip2)
        vlan3 = self.createVlanPkt(type=0x8000, layer=ip3)
        vlan4 = self.createVlanPkt(type=0x8000, layer=ip4)

        pkt1 = self.createEtherPkt(layer=vlan1)
        pkt2 = self.createEtherPkt(layer=vlan2)
        pkt3 = self.createEtherPkt(layer=vlan3)
        pkt4 = self.createEtherPkt(layer=vlan4)

        self.testSetOperation(IcmpFlow.IcmpFlow, pkt1, pkt2, pkt3, pkt4)


    @staticmethod
    def suite():
        return FlowIcmpTestCase._suite(FlowIcmpTestCase)

class FlowTcpTestCase(FlowTestBase):
    """
    TcpFlow test cases
    """
    def setUp(self):
        FlowTestBase.setUp(self)
        self.f = None
        self.payload = 'HTTP/1.1'

    @enabletest
    def test12041create(self):
        self.f = TcpFlow.TcpFlow()
        self.assertNotEqual(self.f, None,
                            'Create failed: Flow could not be created')

    @enabletest
    def test12042addPacket(self):
        t = pcs.packets.tcp.tcp()
        t.sport = self.sport
        t.dport = self.dport
        t.ack = 1
        t.ack_number = 0
        t.sequence = 0
        t.data = None

        # IPv4
        self.f = TcpFlow.TcpFlow()
        ip = self.createIpv4Pkt(0x06, t)
        pkt = self.createEtherPkt(layer=ip)

        self.f.addPacket((0, pkt))
        self.assertEqual(self.f.flk.src, self.src,
                         'Packet add failed: src not set')
        self.assertEqual(self.f.flk.dst, self.dst,
                         'Packet add failed: dst not set')
        self.assertEqual(self.f.flk.sport, self.sport,
                         'Packet add failed: sport not set')
        self.assertEqual(self.f.flk.dport, self.dport,
                         'Packet add failed: dport not set')
        self.assertEqual(self.f.flk.proto, TCP,
                         'Packet add failed: proto is not TCP')
        self.assertEqual(len(self.f.pkts), 1,
                         'Packet add failed: pkt not added to Flow list')


        # IPv6
        self.f = TcpFlow.TcpFlow()
        ip = self.createIpv6Pkt(0x06, t)
        pkt = self.createEtherPkt(type=0x86dd, layer=ip)
        self.f.addPacket((0, pkt))
        self.assertEqual(self.f.flk.src, self.src6,
                         'Packet add6 failed: src not set')
        self.assertEqual(self.f.flk.dst, self.dst6,
                         'Packet add6 failed: dst not set')
        self.assertEqual(self.f.flk.sport, self.sport,
                         'Packet add6 failed: sport not set')
        self.assertEqual(self.f.flk.dport, self.dport,
                         'Packet add6 failed: dport not set')
        self.assertEqual(self.f.flk.proto, TCP,
                         'Packet add6 failed: proto is not TCP')
        self.assertEqual(len(self.f.pkts), 1,
                         'Packet add6 failed: pkt not added to Flow list')

       # Generic
        self.f = TcpFlow.TcpFlow()
        a = pcs.packets.arp.arp()
        a.data = None
        pkt = self.createEtherPkt(layer=a)
        try:
            self.f.addPacket((0, pkt))
        except Exception, e:
            self.assertEqual(isinstance(e, PcapReplayBase.PcapReplayError),
                             True, 'Packet addG failed: Unexpected Error Type')
            self.assertEqual(e.errCode, Flow.ERR_PCAPR_FLOW_KEY_CREATE,
                             'Packet addG failed: Unexpected exception')

    @enabletest
    def test12043matchFlow(self):
        t = pcs.packets.tcp.tcp()
        t.sport = self.sport
        t.dport = self.dport
        t.ack = 1
        t.ack_number = 0
        t.sequence = 0
        t.data = None

        # IPv4
        self.f = TcpFlow.TcpFlow()
        ip = self.createIpv4Pkt(0x06, t)
        pkt = self.createEtherPkt(layer=ip)

        self.f.addPacket((0, pkt))
        self.assertEqual(self.f.matchFlow(pkt), True,
                        'Match flow failed: pkt not matched correctly')

        # IPv6
        self.f = TcpFlow.TcpFlow()
        ip = self.createIpv6Pkt(0x06, t)
        pkt = self.createEtherPkt(type=0x86dd, layer=ip)

        self.f.addPacket((0, pkt))
        self.assertEqual(self.f.matchFlow(pkt), True,
                        'Match flow6 failed: pkt not matched correctly')

    @enabletest
    def test12044splitFlow(self):
        # IPv4
        self.f = TcpFlow.TcpFlow()
        t = pcs.packets.tcp.tcp()
        t.sport = self.sport
        t.dport = self.dport
        t.ack = 1
        t.ack_number = 0
        t.sequence = 0
        t.data = None
        ip = self.createIpv4Pkt(0x06, t)
        pkt = self.createEtherPkt(layer=ip)

        self.f.addPacket((0, pkt))
        t = pcs.packets.tcp.tcp()
        t.sport = self.dport
        t.dport = self.sport
        t.ack = 1
        t.ack_number = 1
        t.sequence = 1
        t.data = None
        ip = self.createIpv4Pkt(0x06, t, True)
        pkt = self.createEtherPkt(layer=ip)

        self.f.addPacket((1, pkt))
        f, r = self.f.splitFlow()
        self.assertEqual((len(f), len(r)), (1, 1),
                         "Split flow failed: incorrect split")
        self.assertEqual(f[0][1].data.src, self.src,
                         "Split flow failed: incorrect forward packet")
        self.assertEqual(r[0][1].data.src, self.dst,
                         "Split flow failed: incorrect reverse packet")

        # IP64
        self.f = TcpFlow.TcpFlow()
        t = pcs.packets.tcp.tcp()
        t.sport = self.sport
        t.dport = self.dport
        t.ack = 1
        t.ack_number = 0
        t.sequence = 0
        t.data = None
        ip = self.createIpv6Pkt(0x06, t)
        pkt = self.createEtherPkt(type=0x86dd, layer=ip)

        self.f.addPacket((0, pkt))
        t = pcs.packets.tcp.tcp()
        t.sport = self.dport
        t.dport = self.sport
        t.ack = 1
        t.ack_number = 1
        t.sequence = 1
        t.data = None
        ip = self.createIpv6Pkt(0x06, t, True)
        pkt = self.createEtherPkt(type=0x86dd, layer=ip)

        self.f.addPacket((1, pkt))
        f, r = self.f.splitFlow()
        self.assertEqual((len(f), len(r)), (1, 1),
                         "Split flow6 failed: incorrect split")
        self.assertEqual(f[0][1].data.src, self.src6,
                         "Split flow6 failed: incorrect forward packet")
        self.assertEqual(r[0][1].data.src, self.dst6,
                         "Split flow6 failed: incorrect reverse packet")

    @enabletest
    def test12045getReplayPktList(self):
        pcp = pcs.PcapConnector('lo')
        ni = NetworkInfo()

        # IPv4
        ni.setNetworkInfo('', '', self.mdT, self.msT, self.dT, self.sT)
        self.f = TcpFlow.TcpFlow()
        t = pcs.packets.tcp.tcp()
        t.sport = self.sport
        t.dport = self.dport
        t.ack = 1
        t.ack_number = 0
        t.sequence = 0
        t.data = None
        ip = self.createIpv4Pkt(0x06, t)
        pkt = self.createEtherPkt(layer=ip)

        self.f.addPacket((0, pkt))
        pkts = self.f.getReplayPktList(ni, pcp, pcp, True)
        for s, c, i in pkts:
            self.assertEqual((c.packets[1].src, c.packets[1].dst),
                             (self.dst, self.src),
                             "Replay fixup failed: incorrect addresses")
            self.assertEqual(i, pcp,
                             "Replay fixup failed: PcapConnectors incorrect")

        # IPv6
        ni.setNetworkInfo('', '', self.mdT, self.msT, '', '', self.d6T, self.s6T)
        self.f = TcpFlow.TcpFlow()
        t = pcs.packets.tcp.tcp()
        t.sport = self.sport
        t.dport = self.dport
        t.ack = 1
        t.ack_number = 0
        t.sequence = 0
        t.data = None
        ip = self.createIpv6Pkt(0x06, t)
        pkt = self.createEtherPkt(type=0x86dd, layer=ip)

        self.f.addPacket((0, pkt))
        pkts = self.f.getReplayPktList(ni, pcp, pcp, True)
        for s, c, i in pkts:
            self.assertEqual((c.packets[1].src, c.packets[1].dst),
                             (self.dst6, self.src6),
                             "Replay fixup6 failed: incorrect addresses")
            self.assertEqual(i, pcp,
                             "Replay fixup6 failed: PcapConnectors incorrect")

    @enabletest
    def test12046getLastPacket(self):
        self.f = TcpFlow.TcpFlow()
        t = pcs.packets.tcp.tcp()
        t.sport = self.sport
        t.dport = self.dport
        t.ack = 1
        t.ack_number = 0
        t.sequence = 0
        t.data = None

        # IPv4
        ip = self.createIpv4Pkt(0x06, t)
        pkt = self.createEtherPkt(layer=ip)

        self.f.addPacket((0, pkt))
        self.assertEqual(self.f.getLastPacket(), pkt,
                         "Last packet failed: last packet was not returned")

        # IPv6
        ip = self.createIpv6Pkt(0x06, t)
        pkt = self.createEtherPkt(type=0x86dd, layer=ip)

        self.f.addPacket((0, pkt))
        self.assertEqual(self.f.getLastPacket(), pkt,
                         "Last packet6 failed: last packet was not returned")

    @enabletest
    def test12047getLastTwoPackets(self):
        self.f = TcpFlow.TcpFlow()

        # IPv4
        t = pcs.packets.tcp.tcp()
        t.sport = self.sport
        t.dport = self.dport
        t.ack = 1
        t.ack_number = 0
        t.sequence = 0
        t.data = None
        ip = self.createIpv4Pkt(0x06, t)
        pkt = self.createEtherPkt(layer=ip)

        self.f.addPacket((0, pkt))
        t = pcs.packets.tcp.tcp()
        t.sport = self.sport
        t.dport = self.dport
        t.ack = 1
        t.ack_number = 1
        t.sequence = 1
        t.data = None
        ip = self.createIpv4Pkt(0x06, t)
        pkt = self.createEtherPkt(layer=ip)

        self.f.addPacket((1, pkt))
        pkts = self.f.getLastTwoPackets()
        self.assertEqual(len(pkts), 2,
                         "Last two packets failed: no packets returned")
        self.assertEqual(pkts[0].data.data.sequence, 1,
                         "Last two packets failed: incorrect packets returned")
        self.assertEqual(pkts[1].data.data.sequence, 0,
                         "Last two packets failed: incorrect packets returned")

        # IPv6
        t = pcs.packets.tcp.tcp()
        t.sport = self.sport
        t.dport = self.dport
        t.ack = 1
        t.ack_number = 0
        t.sequence = 0
        t.data = None
        ip = self.createIpv6Pkt(0x06, t)
        pkt = self.createEtherPkt(type=0x86dd, layer=ip)

        self.f.addPacket((0, pkt))
        t = pcs.packets.tcp.tcp()
        t.sport = self.sport
        t.dport = self.dport
        t.ack = 1
        t.ack_number = 1
        t.sequence = 1
        t.data = None
        ip = self.createIpv6Pkt(0x06, t)
        pkt = self.createEtherPkt(type=0x86dd, layer=ip)

        self.f.addPacket((1, pkt))
        pkts = self.f.getLastTwoPackets()
        self.assertEqual(len(pkts), 2,
                         "Last two packets6 failed: no packets returned")
        self.assertEqual(pkts[0].data.data.sequence, 1,
                         "Last two packets6 failed: incorrect packets returned")
        self.assertEqual(pkts[1].data.data.sequence, 0,
                         "Last two packets6 failed: incorrect packets returned")

    @enabletest
    def test12048getLastPayloadLength(self):
        self.f = TcpFlow.TcpFlow()
        t = pcs.packets.tcp.tcp()
        t.sport = self.sport
        t.dport = self.dport
        t.ack = 1
        t.ack_number = 0
        t.sequence = 0
        t.data = None
        ip = self.createIpv4Pkt(0x06, t)
        pkt = self.createEtherPkt(layer=ip)

        self.f.addPacket((0, pkt))
        t = pcs.packets.tcp.tcp()
        t.sport = self.sport
        t.dport = self.dport
        t.ack = 1
        t.ack_number = 1
        t.sequence = 1

        # IPv4
        t.data = payload.payload(bytes=self.payload)
        ip = self.createIpv4Pkt(0x06, t)
        pkt = self.createEtherPkt(layer=ip)

        self.f.addPacket((1, pkt))
        pll = self.f.getLastPayloadLength()
        self.assertEqual(pll, len(self.payload),
                         "Last payload length failed: incorrect length")

        # IPv6
        t.data = payload.payload(bytes=self.payload + self.payload)
        ip = self.createIpv6Pkt(0x06, t)
        pkt = self.createEtherPkt(type=0x86dd, layer=ip)

        self.f.addPacket((1, pkt))
        pll = self.f.getLastPayloadLength()
        self.assertEqual(pll, len(self.payload + self.payload),
                         "Last payload length6 failed: incorrect length")

    @enabletest
    def test12049compareFlow(self):
        # Create 4 tcp packets that have different checksums.

        t1 = pcs.packets.tcp.tcp()
        t1.sport = self.sport
        t1.dport = self.dport
        t1.ack = 1
        t1.ack_number = 0
        t1.sequence = 0
        t1.checksum = 1111
        t1.data = None

        t2 = pcs.packets.tcp.tcp()
        t2.sport = self.sport
        t2.dport = self.dport
        t2.ack = 1
        t2.ack_number = 0
        t2.sequence = 0
        t2.checksum = 2222
        t2.data = None

        t3 = pcs.packets.tcp.tcp()
        t3.sport = self.sport
        t3.dport = self.dport
        t3.ack = 1
        t3.ack_number = 0
        t3.checksum = 3333
        t3.sequence = 0

        t3.data = None

        t4 = pcs.packets.tcp.tcp()
        t4.sport = self.sport
        t4.dport = self.dport
        t4.ack = 1
        t4.ack_number = 0
        t4.sequence = 0
        t4.checksum = 4444
        t4.data = None

        # IPv4
        ip1 = self.createIpv4Pkt(0x06, t1)
        ip2 = self.createIpv4Pkt(0x06, t2)
        ip3 = self.createIpv4Pkt(0x06, t3)
        ip4 = self.createIpv4Pkt(0x06, t4)

        pkt1 = self.createEtherPkt(layer=ip1)
        pkt2 = self.createEtherPkt(layer=ip2)
        pkt3 = self.createEtherPkt(layer=ip3)
        pkt4 = self.createEtherPkt(layer=ip4)

        self.testSetOperation(TcpFlow.TcpFlow, pkt1, pkt2, pkt3, pkt4)
        # IPv6
        ip1 = self.createIpv6Pkt(0x06, t1)
        ip2 = self.createIpv6Pkt(0x06, t2)
        ip3 = self.createIpv6Pkt(0x06, t3)
        ip4 = self.createIpv6Pkt(0x06, t4)

        pkt1 = self.createEtherPkt(type=0x86dd, layer=ip1)
        pkt2 = self.createEtherPkt(type=0x86dd, layer=ip2)
        pkt3 = self.createEtherPkt(type=0x86dd, layer=ip3)
        pkt4 = self.createEtherPkt(type=0x86dd, layer=ip4)

        self.testSetOperation(TcpFlow.TcpFlow, pkt1, pkt2, pkt3, pkt4)

    @staticmethod
    def suite():
        return FlowTcpTestCase._suite(FlowTcpTestCase)

class FlowUdpTestCase(FlowTestBase):
    """
    UdpFlow test cases
    """
    def setUp(self):
        FlowTestBase.setUp(self)
        self.f = None

    @enabletest
    def test12061create(self):
        self.f = UdpFlow.UdpFlow()
        self.assertNotEqual(self.f, None,
                            'Create failed: Flow could not be created')

    @enabletest
    def test12062addPacket(self):
        u = pcs.packets.udp.udp()
        u.sport = self.sport
        u.dport = self.dport
        u.data = None

        # IPv4
        self.f = UdpFlow.UdpFlow()
        ip = self.createIpv4Pkt(0x11, u)
        pkt = self.createEtherPkt(layer=ip)

        self.f.addPacket((0, pkt))
        self.assertEqual(self.f.flk.src, self.src,
                         'Packet add failed: src not set')
        self.assertEqual(self.f.flk.dst, self.dst,
                         'Packet add failed: dst not set')
        self.assertEqual(self.f.flk.sport, self.sport,
                         'Packet add failed: sport not set')
        self.assertEqual(self.f.flk.dport, self.dport,
                         'Packet add failed: dport not set')
        self.assertEqual(self.f.flk.proto, UDP,
                         'Packet add failed: proto is not UDP')
        self.assertEqual(len(self.f.pkts), 1,
                         'Packet add failed: pkt not added to Flow list')

        # IPv6
        self.f = UdpFlow.UdpFlow()
        ip = self.createIpv6Pkt(0x11, u)
        pkt = self.createEtherPkt(type=0x86dd, layer=ip)

        self.f.addPacket((0, pkt))
        self.assertEqual(self.f.flk.src, self.src6,
                         'Packet add6 failed: src not set')
        self.assertEqual(self.f.flk.dst, self.dst6,
                         'Packet add6 failed: dst not set')
        self.assertEqual(self.f.flk.sport, self.sport,
                         'Packet add6 failed: sport not set')
        self.assertEqual(self.f.flk.dport, self.dport,
                         'Packet add6 failed: dport not set')
        self.assertEqual(self.f.flk.proto, UDP,
                         'Packet add6 failed: proto is not UDP')
        self.assertEqual(len(self.f.pkts), 1,
                         'Packet add6 failed: pkt not added to Flow list')

       # Generic
        self.f = UdpFlow.UdpFlow()
        a = pcs.packets.arp.arp()
        a.data = None
        pkt = self.createEtherPkt(layer=a)
        try:
            self.f.addPacket((0, pkt))
        except Exception, e:
            self.assertEqual(isinstance(e, PcapReplayBase.PcapReplayError),
                             True, 'Packet addG failed: Unexpected Error Type')
            self.assertEqual(e.errCode, Flow.ERR_PCAPR_FLOW_KEY_CREATE,
                             'Packet addG failed: Unexpected exception')

    @enabletest
    def test12063matchFlow(self):
        u = pcs.packets.udp.udp()
        u.sport = self.sport
        u.dport = self.dport
        u.data = None

        # IPv4
        self.f = UdpFlow.UdpFlow()
        ip = self.createIpv4Pkt(0x11, u)
        pkt = self.createEtherPkt(layer=ip)

        self.f.addPacket((0, pkt))
        self.assertEqual(self.f.matchFlow(pkt), True,
                        'Match flow failed: pkt not matched correctly')

        # IPv6
        self.f = UdpFlow.UdpFlow()
        ip = self.createIpv6Pkt(0x11, u)
        pkt = self.createEtherPkt(type=0x86dd, layer=ip)

        self.f.addPacket((0, pkt))
        self.assertEqual(self.f.matchFlow(pkt), True,
                        'Match flow6 failed: pkt not matched correctly')

    @enabletest
    def test12064splitFlow(self):
        # IPv4
        self.f = UdpFlow.UdpFlow()
        u = pcs.packets.udp.udp()
        u.sport = self.sport
        u.dport = self.dport
        u.data = None
        ip = self.createIpv4Pkt(0x11, u)
        pkt = self.createEtherPkt(layer=ip)

        self.f.addPacket((0, pkt))
        u = pcs.packets.udp.udp()
        u.sport = self.dport
        u.dport = self.sport
        u.data = None
        ip = self.createIpv4Pkt(0x11, u, True)
        pkt = self.createEtherPkt(layer=ip)

        self.f.addPacket((1, pkt))
        f, r = self.f.splitFlow()
        self.assertEqual((len(f), len(r)), (1, 1),
                         "Split flow failed: incorrect split")
        self.assertEqual(f[0][1].data.src, self.src,
                         "Split flow failed: incorrect forward packet")
        self.assertEqual(r[0][1].data.src, self.dst,
                         "Split flow failed: incorrect reverse packet")

        # IPv6
        self.f = UdpFlow.UdpFlow()
        u = pcs.packets.udp.udp()
        u.sport = self.sport
        u.dport = self.dport
        u.data = None
        ip = self.createIpv6Pkt(0x11, u)
        pkt = self.createEtherPkt(type=0x86dd, layer=ip)

        self.f.addPacket((0, pkt))
        u = pcs.packets.udp.udp()
        u.sport = self.dport
        u.dport = self.sport
        u.data = None
        ip = self.createIpv6Pkt(0x11, u, True)
        pkt = self.createEtherPkt(type=0x86dd, layer=ip)

        self.f.addPacket((1, pkt))
        f, r = self.f.splitFlow()
        self.assertEqual((len(f), len(r)), (1, 1),
                         "Split flow6 failed: incorrect split")
        self.assertEqual(f[0][1].data.src, self.src6,
                         "Split flow6 failed: incorrect forward packet")
        self.assertEqual(r[0][1].data.src, self.dst6,
                         "Split flow6 failed: incorrect reverse packet")

    @enabletest
    def test12065getReplayPktList(self):
        pcp = pcs.PcapConnector('lo')
        ni = NetworkInfo()

        # IPv4
        ni.setNetworkInfo('', '', self.mdT, self.msT, self.dT, self.sT)
        self.f = UdpFlow.UdpFlow()
        u = pcs.packets.udp.udp()
        u.sport = self.sport
        u.dport = self.dport
        u.data = None
        ip = self.createIpv4Pkt(0x11, u)
        pkt = self.createEtherPkt(layer=ip)

        self.f.addPacket((0, pkt))
        pkts = self.f.getReplayPktList(ni, pcp, pcp, True)
        for s, c, i in pkts:
            self.assertEqual((c.packets[1].src, c.packets[1].dst),
                             (self.dst, self.src),
                             "Replay fixup failed: incorrect addresses")
            self.assertEqual(i, pcp,
                             "Replay fixup failed: PcapConnectors incorrect")

        # IPv6
        ni.setNetworkInfo('', '', self.mdT, self.msT, '', '', self.d6T, self.s6T)
        self.f = UdpFlow.UdpFlow()
        u = pcs.packets.udp.udp()
        u.sport = self.sport
        u.dport = self.dport
        u.data = None
        ip = self.createIpv6Pkt(0x11, u)
        pkt = self.createEtherPkt(type=0x86dd, layer=ip)

        self.f.addPacket((0, pkt))
        pkts = self.f.getReplayPktList(ni, pcp, pcp, True)
        for s, c, i in pkts:
            self.assertEqual((c.packets[1].src, c.packets[1].dst),
                             (self.dst6, self.src6),
                             "Replay fixup6 failed: incorrect addresses")
            self.assertEqual(i, pcp,
                             "Replay fixup6 failed: PcapConnectors incorrect")

    @enabletest
    def test12066compareFlow(self):
        # Create 4 UDP packets that have different checksums.
        u1 = pcs.packets.udp.udp()
        u1.sport = self.sport
        u1.dport = self.dport
        u1.checksum = 1111
        u1.data = None

        u2 = pcs.packets.udp.udp()
        u2.sport = self.sport
        u2.dport = self.dport
        u2.checksum = 2222
        u2.data = None

        u3 = pcs.packets.udp.udp()
        u3.sport = self.sport
        u3.dport = self.dport
        u3.checksum = 3333
        u3.data = None

        u4 = pcs.packets.udp.udp()
        u4.sport = self.sport
        u4.dport = self.dport
        u4.checksum = 4444
        u4.data = None

        # IPv4
        ip1 = self.createIpv4Pkt(0x11, u1)
        ip2 = self.createIpv4Pkt(0x11, u2)
        ip3 = self.createIpv4Pkt(0x11, u3)
        ip4 = self.createIpv4Pkt(0x11, u4)

        pkt1 = self.createEtherPkt(layer=ip1)
        pkt2 = self.createEtherPkt(layer=ip2)
        pkt3 = self.createEtherPkt(layer=ip3)
        pkt4 = self.createEtherPkt(layer=ip4)
        self.testSetOperation(UdpFlow.UdpFlow, pkt1, pkt2, pkt3, pkt4)

        # IPv6
        ip1 = self.createIpv6Pkt(0x11, u1)
        ip2 = self.createIpv6Pkt(0x11, u2)
        ip3 = self.createIpv6Pkt(0x11, u3)
        ip4 = self.createIpv6Pkt(0x11, u4)

        pkt1 = self.createEtherPkt(type=0x86dd, layer=ip1)
        pkt2 = self.createEtherPkt(type=0x86dd, layer=ip2)
        pkt3 = self.createEtherPkt(type=0x86dd, layer=ip3)
        pkt4 = self.createEtherPkt(type=0x86dd, layer=ip4)

        self.testSetOperation(UdpFlow.UdpFlow, pkt1, pkt2, pkt3, pkt4)


    @staticmethod
    def suite():
        return FlowUdpTestCase._suite(FlowUdpTestCase)

class FlowGenericTestCase(FlowTestBase):
    """
    GenericFlow test cases
    """
    def setUp(self):
        FlowTestBase.setUp(self)
        self.f = None

    @enabletest
    def test12081create(self):
        self.f = GenericFlow.GenericFlow()
        self.assertNotEqual(self.f, None,
                            'Create failed: Flow could not be created')

    @enabletest
    def test12082addPacket(self):
        # IPv4
        self.f = GenericFlow.GenericFlow()
        ic = pcs.packets.icmpv4.icmpv4()
        ic.data = None
        ip = self.createIpv4Pkt(0x01, ic)
        pkt = self.createEtherPkt(layer=ip)

        self.f.addPacket((0, pkt))
        self.assertEqual(self.f.flk.src, self.src,
                         'Packet add failed: src not set')
        self.assertEqual(self.f.flk.dst, self.dst,
                         'Packet add failed: dst not set')
        self.assertEqual(self.f.flk.proto, GENERIC,
                         'Packet add failed: proto is not GENERIC')
        self.assertEqual(len(self.f.pkts), 1,
                         'Packet add failed: pkt not added to Flow list')

       # IPv6
        self.f = GenericFlow.GenericFlow()
        ic = pcs.packets.icmpv6.icmpv6()
        ic.data = None
        ip = self.createIpv6Pkt(0x01, ic)
        pkt = self.createEtherPkt(type=0x86dd, layer=ip)

        self.f.addPacket((0, pkt))
        self.assertEqual(self.f.flk.src, self.src6,
                         'Packet add6 failed: src not set')
        self.assertEqual(self.f.flk.dst, self.dst6,
                         'Packet add6 failed: dst not set')
        self.assertEqual(self.f.flk.proto, GENERIC,
                         'Packet add6 failed: proto is not GENERIC')
        self.assertEqual(len(self.f.pkts), 1,
                         'Packet add6 failed: pkt not added to Flow list')

       # Generic
        self.f = GenericFlow.GenericFlow()
        a = pcs.packets.arp.arp()
        a.data = None
        pkt = self.createEtherPkt(layer=a)
        self.f.addPacket((0, pkt))
        self.assertEqual(self.f.flk.src, self.smac,
                         'Packet addG failed: src not set')
        self.assertEqual(self.f.flk.dst, self.dmac,
                         'Packet addG failed: dst not set')
        self.assertEqual(self.f.flk.proto, GENERIC,
                         'Packet addG failed: proto is not GENERIC')
        self.assertEqual(len(self.f.pkts), 1,
                         'Packet addG failed: pkt not added to Flow list')

    @enabletest
    def test12083matchFlow(self):
        # IPv4
        self.f = GenericFlow.GenericFlow()
        ic = pcs.packets.icmpv4.icmpv4()
        ic.data = None
        ip = self.createIpv4Pkt(0x01, ic)
        pkt = self.createEtherPkt(layer=ip)

        self.f.addPacket((0, pkt))
        self.assertEqual(self.f.matchFlow(pkt), True,
                        'Match flow failed: pkt not matched correctly')

        # IPv6
        self.f = GenericFlow.GenericFlow()
        ic = pcs.packets.icmpv6.icmpv6()
        ic.data = None
        ip = self.createIpv6Pkt(0x01, ic)
        pkt = self.createEtherPkt(type=0x86dd, layer=ip)

        self.f.addPacket((0, pkt))
        self.assertEqual(self.f.matchFlow(pkt), True,
                        'Match flow6 failed: pkt not matched correctly')

        # Generic
        self.f = GenericFlow.GenericFlow()
        a = pcs.packets.arp.arp()
        a.data = None
        pkt = self.createEtherPkt(layer=a)
        self.f.addPacket((0, pkt))
        self.assertEqual(self.f.matchFlow(pkt), True,
                        'Match flowG failed: pkt not matched correctly')

    @enabletest
    def test12084splitFlow(self):
        # IPv4
        self.f = IcmpFlow.IcmpFlow()
        ic = pcs.packets.icmpv4.icmpv4()
        ic.data = None
        ip = self.createIpv4Pkt(0x01, ic)
        pkt = self.createEtherPkt(layer=ip)

        self.f.addPacket((0, pkt))
        ic = pcs.packets.icmpv4.icmpv4()
        ic.data = None
        ip = self.createIpv4Pkt(0x01, ic, True)
        pkt = self.createEtherPkt(layer=ip)

        self.f.addPacket((1, pkt))
        f, r = self.f.splitFlow()
        self.assertEqual((len(f), len(r)), (1, 1),
                         "Split flow failed: incorrect split")
        self.assertEqual(f[0][1].data.src, self.src,
                         "Split flow failed: incorrect forward packet")
        self.assertEqual(r[0][1].data.src, self.dst,
                         "Split flow failed: incorrect reverse packet")

        # IPv6
        self.f = IcmpFlow.IcmpFlow()
        ic = pcs.packets.icmpv6.icmpv6()
        ic.data = None
        ip = self.createIpv6Pkt(0x01, ic)
        pkt = self.createEtherPkt(type=0x86dd, layer=ip)

        self.f.addPacket((0, pkt))
        ic = pcs.packets.icmpv6.icmpv6()
        ic.data = None
        ip = self.createIpv6Pkt(0x01, ic, True)
        pkt = self.createEtherPkt(type=0x86dd, layer=ip)

        self.f.addPacket((1, pkt))
        f, r = self.f.splitFlow()
        self.assertEqual((len(f), len(r)), (1, 1),
                         "Split flow6 failed: incorrect split")
        self.assertEqual(f[0][1].data.src, self.src6,
                         "Split flow6 failed: incorrect forward packet")
        self.assertEqual(r[0][1].data.src, self.dst6,
                         "Split flow6 failed: incorrect reverse packet")

        # Generic
        self.f = GenericFlow.GenericFlow()
        a = pcs.packets.arp.arp()
        a.data = None
        pkt = self.createEtherPkt(layer=a)
        self.f.addPacket((0, pkt))
        a = pcs.packets.arp.arp()
        a.data = None
        pkt = self.createEtherPkt(layer=a, reverse=True)
        self.f.addPacket((1, pkt))
        f, r = self.f.splitFlow()
        self.assertEqual((len(f), len(r)), (1, 1),
                         "Split flowG failed: incorrect split")

    @enabletest
    def test12085getReplayPktList(self):
        pcp = pcs.PcapConnector('lo')
        ni = NetworkInfo()

        # IPv4
        ni.setNetworkInfo('', '', self.mdT, self.msT, self.dT, self.sT)
        self.f = IcmpFlow.IcmpFlow()
        ic = pcs.packets.icmpv4.icmpv4()
        ic.data = None
        ip = self.createIpv4Pkt(0x01, ic)
        pkt = self.createEtherPkt(layer=ip)

        self.f.addPacket((0, pkt))
        pkts = self.f.getReplayPktList(ni, pcp, pcp, True)
        for s, c, i in pkts:
            self.assertEqual((c.packets[1].src, c.packets[1].dst),
                             (self.dst, self.src),
                             "Replay fixup failed: incorrect addresses")
            self.assertEqual(i, pcp,
                             "Replay fixup failed: PcapConnectors incorrect")

        # IPv6
        ni.setNetworkInfo('', '', self.mdT, self.msT, '', '', self.d6T, self.s6T)
        self.f = IcmpFlow.IcmpFlow()
        ic = pcs.packets.icmpv6.icmpv6()
        ic.data = None
        ip = self.createIpv6Pkt(0x01, ic)
        pkt = self.createEtherPkt(type=0x86dd, layer=ip)

        self.f.addPacket((0, pkt))
        pkts = self.f.getReplayPktList(ni, pcp, pcp, True)
        for s, c, i in pkts:
            self.assertEqual((c.packets[1].src, c.packets[1].dst),
                             (self.dst6, self.src6),
                             "Replay fixup6 failed: incorrect addresses")
            self.assertEqual(i, pcp,
                             "Replay fixup6 failed: PcapConnectors incorrect")

        # Generic
        ni.setNetworkInfo('', '', self.mdT, self.msT, '', '', self.d6T, self.s6T)
        self.f = GenericFlow.GenericFlow()
        a = pcs.packets.arp.arp()
        a.data = None
        pkt = self.createEtherPkt(layer=a)
        self.f.addPacket((0, pkt))
        pkts = self.f.getReplayPktList(ni, pcp, pcp, True)
        for s, c, i in pkts:
            self.assertEqual((c.packets[0].src, c.packets[0].dst),
                             (self.dmac, self.smac),
                             "Replay fixupG failed: incorrect addresses")
            self.assertEqual(i, pcp,
                             "Replay fixupG failed: PcapConnectors incorrect")

    @enabletest
    def test12086compareFlow(self):
        # Create 4 packets that have different checksums.
        # IPv4
        ic1 = pcs.packets.icmpv4.icmpv4()
        ic1.checksum = 1111
        ic1.data = None
        ic2 = pcs.packets.icmpv4.icmpv4()
        ic2.checksum = 2222
        ic2.data = None
        ic3 = pcs.packets.icmpv4.icmpv4()
        ic3.checksum = 3333
        ic3.data = None
        ic4 = pcs.packets.icmpv4.icmpv4()
        ic4.checksum = 4444
        ic4.data = None

        ip1 = self.createIpv4Pkt(0x01, ic1)
        ip2 = self.createIpv4Pkt(0x01, ic2)
        ip3 = self.createIpv4Pkt(0x01, ic3)
        ip4 = self.createIpv4Pkt(0x01, ic4)

        pkt1 = self.createEtherPkt(layer=ip1)
        pkt2 = self.createEtherPkt(layer=ip2)
        pkt3 = self.createEtherPkt(layer=ip3)
        pkt4 = self.createEtherPkt(layer=ip4)
        self.testSetOperation(GenericFlow.GenericFlow, pkt1, pkt2, pkt3, pkt4)

        # IPv6
        ic1 = pcs.packets.icmpv6.icmpv6()
        ic1.checksum = 1111
        ic1.data = None
        ic2 = pcs.packets.icmpv6.icmpv6()
        ic2.checksum = 2222
        ic2.data = None
        ic3 = pcs.packets.icmpv6.icmpv6()
        ic3.checksum = 3333
        ic3.data = None
        ic4 = pcs.packets.icmpv6.icmpv6()
        ic4.checksum = 4444
        ic4.data = None

        ip1 = self.createIpv6Pkt(0x01, ic1)
        ip2 = self.createIpv6Pkt(0x01, ic2)
        ip3 = self.createIpv6Pkt(0x01, ic3)
        ip4 = self.createIpv6Pkt(0x01, ic4)

        pkt1 = self.createEtherPkt(type=0x86dd, layer=ip1)
        pkt2 = self.createEtherPkt(type=0x86dd, layer=ip2)
        pkt3 = self.createEtherPkt(type=0x86dd, layer=ip3)
        pkt4 = self.createEtherPkt(type=0x86dd, layer=ip4)
        self.testSetOperation(GenericFlow.GenericFlow, pkt1, pkt2, pkt3, pkt4)

        # Generic
        a1 = pcs.packets.arp.arp()
        a1.op = 1111
        a1.data = None
        a2 = pcs.packets.arp.arp()
        a2.op = 2222
        a2.data = None
        a3 = pcs.packets.arp.arp()
        a3.op = 3333
        a3.data = None
        a4 = pcs.packets.arp.arp()
        a4.op = 4444
        a4.data = None
        pkt1 = self.createEtherPkt(layer=a1)
        pkt2 = self.createEtherPkt(layer=a2)
        pkt3 = self.createEtherPkt(layer=a3)
        pkt4 = self.createEtherPkt(layer=a4)
        self.testSetOperation(GenericFlow.GenericFlow, pkt1, pkt2, pkt3, pkt4)

    @staticmethod
    def suite():
        return FlowFactoryTestCase._suite(FlowGenericTestCase)

class FlowFactoryTestCase(FlowTestBase):
    """
    FlowFactory test cases
    """
    @enabletest
    def test13001createIcmpFlow(self):
        cls = Flow.FlowFactory.getFlowClass(ICMP)
        self.assertEqual(cls, IcmpFlow.IcmpFlow,
                         'Create IcmpFlow failed: getFlowClass mismatch')
        testFlow = Flow.FlowFactory.getFlow(ICMP)
        self.assertEqual(type(testFlow), IcmpFlow.IcmpFlow,
                         'Create IcmpFlow failed: getFlow type mismatch')

    @enabletest
    def test13002createTcpFlow(self):
        cls = Flow.FlowFactory.getFlowClass(TCP)
        self.assertEqual(cls, TcpFlow.TcpFlow,
                         'Create TcpFlow failed: getFlowClass mismatch')
        testFlow = Flow.FlowFactory.getFlow(TCP)
        self.assertEqual(type(testFlow), TcpFlow.TcpFlow,
                         'Create TcpFlow failed: getFlow type mismatch')

    @enabletest
    def test13003createUdpFlow(self):
        cls = Flow.FlowFactory.getFlowClass(UDP)
        self.assertEqual(cls, UdpFlow.UdpFlow,
                         'Create UdpFlow failed: getFlowClass mismatch')
        testFlow = Flow.FlowFactory.getFlow(UDP)
        self.assertEqual(type(testFlow), UdpFlow.UdpFlow,
                         'Create UdpFlow failed: getFlow type mismatch')

    @enabletest
    def test13004createGenericFlow(self):
        cls = Flow.FlowFactory.getFlowClass(GENERIC)
        self.assertEqual(cls, GenericFlow.GenericFlow,
                         'Create UdpFlow failed: getFlowClass mismatch')
        testFlow = Flow.FlowFactory.getFlow(GENERIC)
        self.assertEqual(type(testFlow), GenericFlow.GenericFlow,
                         'Create UdpFlow failed: getFlow type mismatch')

    @staticmethod
    def suite():
        return FlowFactoryTestCase._suite(FlowFactoryTestCase)
