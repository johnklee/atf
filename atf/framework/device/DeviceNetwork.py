import os
import re
import sys
import time
import errno
#import pcs
import logging

from atf.framework.devicesession.NetworkSetupSession import *

class DeviceNetwork(object):
    r"""
    This class provides an interface for injecting and receiving
    packets from a single network interface on the Device
    """

    def __init__(self, networkIF, pcapDevice, proxyVlan=(), hostVlan=(),
                 diagLevel=logging.WARNING):
        r"""
        Save the network information that will allow us to open a local
        pcapDevice that can talk to the indicated networkIF on the proxied
        device.
        
        @param networkIF:
            Name of the interface as seen on the proxied device console.
        
        @param pcapDevice:
            Name of the Local host device we connect to in order to 
            communicate with networkIF on the proxied device. 
            
        @param proxyVlan:
            A tuple describing information about the proxy's VLAN. This 
            of the form:
                - (<nsd-type>, <nsd-ip>, <nsd-ip-port>, <device name>, 
                  <username>, <password>, <vlan-port#>, <vlanid>)
             
        @param hostVlan:
            A tuple describing information about the host's VLAN. This of 
            the form:
                - ( <nsd-type>, <nsd-ip>, <nsd-ip-port>, <device name>, 
                  <username>, <password>, <vlan-port#>, <vlanid>) 
            
         @param diagLevel:
             What debug level to run this object in.
        """
        self.networkIF = networkIF        
        """The name of the network interface on the proxied device 
        associated with the class"""
        self.pcapDeviceName = pcapDevice
        """The name of the pcap device associated with the class 
        network interface"""  
        self.pcsConnector = None
        """The PCS connector associated with the class pcap device""" 
        self.proxyVlanNSD = None
        """The network session device VLAN tuple associated with the
        proxied interface""" 
        self.proxyVlanID = '0'
        """The network session device VLAN ID associated with the
        proxied interface""" 
        self.hostVlanNSD = None
        """The network session device VLAN tuple associated with the
        host interface""" 
        self.hostVlanID = '0'
        """The network session device VLAN ID associated with the
        host interface""" 

        if (proxyVlan != ()):
            for (type, ip, port, name, uname, passwd, vlanPort, vlanID) in [proxyVlan]:
                proxyVlanNSDC = NetworkSetupSessionConfig(ip=ip,
                    port=port, username=uname, password=passwd, deviceName=name,
                    netPortID=vlanPort)
                self.proxyVlanID = vlanID
                self.proxyVlanNSD = getNetworkSetupSession(type=type, 
                    deviceSessionConfig=proxyVlanNSDC, diagLevel=diagLevel)
        if (hostVlan != ()): 
            for (type, ip, port, name, uname, passwd, vlanPort, vlanID) in [hostVlan]:
                hostVlanNSDC = NetworkSetupSessionConfig(ip=ip,
                    port=port, username=uname, password=passwd, deviceName=name,
                    netPortID=vlanPort)
                self.hostVlanID = vlanID 
                self.hostVlanNSD = getNetworkSetupSession(type=type, 
                    deviceSessionConfig=hostVlanNSDC, diagLevel=diagLevel)

    def connect(self):
        r"""
        Setup appropriate VLAN IDs and connect to the underlying pcap device
        """

        self.pcsConnector = pcs.PcapConnector(self.pcapDeviceName)

    def close(self):
        r"""
        Disconnect from the pcap device
        """
        self.pcsConnector.close()
        self.pcsConnector = None

    def setup(self):
        r"""
        Setup the network device including appropriate VLAN ID setup
        """ 
        if (self.proxyVlanNSD != None and self.hostVlanNSD != None):
            self.proxyVlanNSD.connect()
            self.proxyVlanNSD.setVlan(vlanID=self.proxyVlanID)            
            self.proxyVlanNSD.disconnect()
            self.hostVlanNSD.connect()
            self.hostVlanNSD.setVlan(vlanID=self.hostVlanID)            
            self.hostVlanNSD.disconnect()        
        
    def teardown(self):
        r"""
        Teardown the network device including appropriate VLAN ID teardown
        """ 
        if (self.proxyVlanNSD != None and self.hostVlanNSD != None):
            self.proxyVlanNSD.connect()
            self.proxyVlanNSD.resetVlan()            
            self.proxyVlanNSD.disconnect()
            self.hostVlanNSD.connect()
            self.hostVlanNSD.resetVlan()            
            self.hostVlanNSD.disconnect()
