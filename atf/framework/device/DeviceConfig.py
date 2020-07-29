import os
import re
import sys
import time
import errno
#import pcs
import logging

class DeviceConfig(object):
    r"""
    Encapsulate all the VM agnostic configuration information needed
    to set up a generic Device.
    """
    ###
    # Class type definitions
    ###
    # Define supported System image types
    (IMAGE_ISO)      = 'iso'
    """System image type: ISO"""
    (IMAGE_PXE)      = 'pxe'
    """System image type: PXE"""
    (IMAGE_USB)      = 'usb'
    """System image type: USB"""
    (IMAGE_LIVE)     = 'live'
    """System image type: Live""" 
    (IMAGE_VHD)      = 'vhd'
    """System image type: VHD"""
    (IMAGE_QCOW2)    = 'qcow2'
    """System image type: QCOW2"""
    
    def __init__(self, networks=None, systemImages=None, 
                 networkSetupDevices=None, powerController=None, 
                 consoleServer=None):
        r"""
        Save the network specifications
         
        @param networks:
            A collection of networks reachable from the host
            This configuration option takes the following form:
                - E{lb} host-network-device : HostInterface E{rb}

        @param systemImages:
            The location of images to use for device start.
        
        @param networkSetupDevices:
            A dictionary associating details about all used network setup 
            devices with a user-defined name.
            This dictionary takes the following form;
                - E{lb} <network-setup-device-name>: (<nsd-type>, <nsd-ip>, 
                  <nsd-ip-port>, <device name>, <username>, 
                  <password>), ... E{rb} 
              
        @param powerController:
            A tuple describing the power controller for this device of the 
            form;
                - ( <controller-type>, <controller-ip>, <controller-port>, 
                  <port#>, <username>, <password> )
                  
        @param consoleServer:
            A tuple describing the console server for this device of the
            form;
                - ( <server-type>, <server-ip>, <server-port>, <port#>, 
                  <username>, <password> )
        """
        self.networks = networks
        """A list of networks associated with the device"""
        self.systemImages = systemImages
        """A map of system images that are available for use with the device"""
        self.networkSetupDevices = networkSetupDevices
        """A map of network setup devices associated with the device"""
        self.powerController = powerController
        """A tuple describing the power controller associated with the device"""
        self.consoleServer = consoleServer
        """A tuple describing the console server associated with the device"""

