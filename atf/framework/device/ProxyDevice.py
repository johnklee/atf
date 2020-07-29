import os
import re
import sys
import time
import errno
import unittest
import pexpect
#import pcs
import logging

from atf.framework.FrameworkBase import *
from DeviceConfig import *
from DeviceNetwork import *

class ProxyDevice(FrameworkBase):
    r"""
    The ProxyDevice hierarchy abstracts the QEMU emulation and real H/W 
    environments into a common interface.  Key functionality accessed
    through this interface includes :
        - The "cons" which provides device console access using the pexpect 
          utility to script interactions.
        - The "nics" which provide a direct pipe into the ethernet interfaces
          of the Device so that packets can be directed at specific ingress and
          received from specific egress connectors.
        - Basic H/W like control to start and stop the environment/HW. 
    """
    
    ###
    # Class error definitions
    ### 
    (ERR_MISSING_DEVICE_CONFIG) = FrameworkError.ERR_DEVICE 
    """No configuration for device"""
    (ERR_INVALID_DEVICE_STATE)  = FrameworkError.ERR_DEVICE+1  
    """An operation was requested when the device was in an inappropriate state""" 
    (ERR_FAILED_DEVICE_START)   = FrameworkError.ERR_DEVICE+2
    """The device was unable to start and is now in an unknown state."""
    (ERR_FAILED_DEVICE_STOP)    = FrameworkError.ERR_DEVICE+3
    """The device was unable to stop and is now in an unknown state."""

    (ERR_FAILED_DOCKER_IMG)     = FrameworkError.ERR_DEVICE+10
    """ The device was unable to retrieve image from local """
    (ERR_FAILED_DOCKER_PULL)    = FrameworkError.ERR_DEVICE+11
    """ The device was unable to pull image from registry """
    (ERR_FAILED_DOCKER_RUN)     = FrameworkError.ERR_DEVICE+12
    """ The device was failed to run container """
    (ERR_FAILED_DOCKER_CLI)     = FrameworkError.ERR_DEVICE+13
    """ The device was failed to execute cli command"""
    
    # Define valid states that a ProxyDevice can be in.
    (STATE_UNKNOWN)      = 0
    """Undetermined device state."""
    (STATE_INITIALISED)  = 1
    """Device is initialised by not usable."""
    (STATE_STOPPED)      = 2
    """Device is stopped."""
    (STATE_STARTING)     = 3
    """Device is starting."""
    (STATE_RUNNING)      = 4
    """Device is running."""
    (STATE_STOPPING)     = 5
    """Device is stopping."""
    
    
    def __init__(self, deviceConfig=None, diagLevel=logging.WARNING):
        r"""
        Set up diagnostics output and save the network config into a 
        one way dictionary from target device IF name to local connection 
        point.

        @param deviceConfig:
            A pre-constructed L{DeviceConfig} object
            
        @param diagLevel:
            What debug level to run this object in.    
        """
        FrameworkBase.__init__(self, diagLevel=diagLevel)
        self.state = ProxyDevice.STATE_UNKNOWN
        """State of the device."""
        self.nics = {}
        """Network interfaces associated with the device."""
        self.cons = None
        """Console associated with the device."""
        self.hostShell = None
        """Host shell  associated with the device."""
        if (deviceConfig != None) and (deviceConfig.networks != None):
                # walk through the network config and create objects for
                # each one defined.
                for (bridge, sysIFs) in deviceConfig.networks.items():
                    for (iname, iface) in sysIFs.interfaces.items():
                        proxyVlan = ()
                        hostVlan=()
                        if (sysIFs.vlan != None and 
                            iface.vlan != None and
                            iface.vlan.deviceName != '' and 
                            iface.vlan.devicePort != 0 and
                            deviceConfig.networkSetupDevices != {}):
                            nsd = deviceConfig.networkSetupDevices[iface.vlan.deviceName] 
                            proxyVlan = (nsd[0], nsd[1], nsd[2], nsd[3], nsd[4],
                                         nsd[5], iface.vlan.devicePort, sysIFs.vlan.vlanId)
                            nsd = deviceConfig.networkSetupDevices[sysIFs.vlan.deviceName] 
                            hostVlan = (nsd[0], nsd[1], nsd[2], nsd[3], nsd[4],
                                        nsd[5], sysIFs.vlan.devicePort, sysIFs.vlan.vlanId)
                        self.nics[iname] =  DeviceNetwork(networkIF=iname,
                                                             pcapDevice=bridge,
                                                             proxyVlan=proxyVlan,
                                                             hostVlan=hostVlan,
                                                             diagLevel=diagLevel)            
                                                             
        self.config = deviceConfig
        """Configuration associated with the device."""
        self.start_begin=None
        """ datetime object to hold start time in starting device"""
        self.start_end=None
        """ datetime object to hold end time in starting device"""

    @property
    def st(self):
        r'''
        Return the time spent in starting device.        
        '''
        if self.start_begin is None:
            return "Not start yet!"
        elif self.start_end is None:
            if self.state == ProxyDevice.STATE_STARTING:
                return "Starting"
            else: 
                return "Fail to start!"
        else:
            return "%s" % (self.start_end-self.start_begin) 

    def getTerminal(self):
        r"""
        Answer the object which provides access to the available terminal.
        
        In this case, it is a pexpect.spawn connection to the console. 
        
        @return:
            A pexpect.spawn terminal.
        """
        return self.cons 

    def isStartable(self):
        r"""
        Use this method to ensure that the ProxyDevice is in 
        a suitably initialised state to attempt to start().

        @return:
            L{CommonError.ERR_OK} if ok to start
            L{ProxyDevice.ERR_INVALID_DEVICE_STATE} invalid state for start
            L{ProxyDevice.ERR_MISSING_DEVICE_CONFIG} no device config file.
        """
        if ((self.state != ProxyDevice.STATE_INITIALISED) and 
            (self.state != ProxyDevice.STATE_STOPPED)): 
            return(ProxyDevice.ERR_INVALID_DEVICE_STATE)
        elif(self.config == None):
            return(ProxyDevice.ERR_MISSING_DEVICE_CONFIG)
        else:
            return(CommonError.ERR_OK)

    def isStoppable(self):
        r"""
        Use this method to ensure that the ProxyDevice is in a 
        suitable running state to attempt to stop().

        @return:
            L{CommonError.ERR_OK} if ok to stop
            L{ProxyDevice.ERR_INVALID_DEVICE_STATE} invalid state for stop
        """
        if (self.state > ProxyDevice.STATE_STOPPED):
            return(CommonError.ERR_OK)
        else:
            return(ProxyDevice.ERR_INVALID_DEVICE_STATE)
        
    def setupDeviceVlans(self):
        r"""
        Use this method to setup all VLANs associated with this device.

        @return:
            None. Throws an exception if an invalid network name is
            provided or a connection fails.
        """
        for x in self.nics.keys():
            self.nics[x].setup()
    
    def teardownDeviceVlans(self):
        r"""
        Use this method to teardown all VLANs associated with this device.

        @return:
            None. Throws an exception if an invalid network name is
            provided or a connection fails.
        """
        for x in self.nics.keys():
            self.nics[x].teardown()

    def connectDeviceNetworks(self, networks=None):
        r"""
        Use this method to create pcap connectors to the networks identified. 

        @param networks:
            A list of the devices network interface names that are to be
            connected.
            
        @return:
            None. Throws an exception if an invalid network name is
            provided or a connection fails.
        """
        for x in networks :
            self.nics[x].connect()
    
    def closeDeviceNetworks(self, networks=None):
        r"""
        Use this method to release pcap connectors to the networks identified. 

        @param networks:
            A list of the devices network interface names that are to be 
            closed.
        
        @return:  
            None. Throws an exception if an invalid network name is
            provided or a connection fails.
        """
        for x in networks :
            self.nics[x].close()

    def start(self, productPackage=DeviceConfig.IMAGE_ISO):
        r"""
        Start the Device.  Derived classes must look at the 
        configuration passed in during construction, configure access 
        to each network identified and turn on the device.
        
        @param productPackage:
            The type of image to use during device start. One of:
                - L{DeviceConfig.IMAGE_ISO}
                - L{DeviceConfig.IMAGE_PXE}
                - L{DeviceConfig.IMAGE_USB}
                - L{DeviceConfig.IMAGE_LIVE} 
            
        @return:
            None, exceptions raised must be derived from L{FrameworkError}
        """
        raise (NotImplementedError())


    def stop(self):
        r"""
        Derived classes must halt the Device environment

        @return:
            None, exceptions raised must be derived from L{FrameworkError}
        """
        raise (NotImplementedError())
