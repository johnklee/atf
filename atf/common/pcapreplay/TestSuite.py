# System
import unittest

# PCS

# PcapReplay
import PcapReplayTest
import flow.FlowTest as FlowTest
import trigger.TriggerTest as TriggerTest

##
# Globals

##
# Classes

##
# Functions
def runTestSuite(verbosity=2):
    """
    Run the full pcapreplay test suite as a set of ordered test suites
    of the full set of pcapreplay modules. 
    """
    suiteList = [# Base pcapreplay Module tests
                 PcapReplayTest.PcapReplayObjectTestCase.suite(), 
                 PcapReplayTest.PcapReplayErrorTestCase.suite(), 
                 PcapReplayTest.NetworkInfoTestCase.suite(),
                 
                 # flow Module Tests
                 FlowTest.FlowKeyTestCase.suite(), 
                 FlowTest.IpFlowKeyTestCase.suite(), 
                 FlowTest.Ipv4FlowKeyTestCase.suite(), 
                 FlowTest.Ipv6FlowKeyTestCase.suite(), 
                 FlowTest.MacFlowKeyTestCase.suite(),
                 FlowTest.FlowKeyFactoryTestCase.suite(),  
                 FlowTest.FlowTestCase.suite(), 
                 FlowTest.FlowIcmpTestCase.suite(),
                 FlowTest.FlowTcpTestCase.suite(), 
                 FlowTest.FlowUdpTestCase.suite(),
                 FlowTest.FlowGenericTestCase.suite(),  
                 FlowTest.FlowFactoryTestCase.suite(),
                 
                 # trigger Module Tests
                 TriggerTest.TriggerTestCase.suite(), 
                 TriggerTest.HttpTriggerTestCase.suite(), 
                 TriggerTest.TcpTriggerTestCase.suite(), 
                 TriggerTest.TriggerFactoryTestCase.suite(),
                 
                 # Top level pcareplay Module Tests             
                 PcapReplayTest.PcapReplayTestCase.suite()]
    
    suite = unittest.TestSuite(suiteList)
    unittest.TextTestRunner(verbosity=verbosity).run(suite)

if ( __name__ == '__main__' ):
    runTestSuite(verbosity=2)
