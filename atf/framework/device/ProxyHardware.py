import logging
import pexpect
import signal
import subprocess
import types

import atf.common.Common as Common
from atf.framework.FrameworkBase import *
from ProxyDevice import *
from DeviceConfig import *
from atf.framework.devicesession.ConsoleServerSession import *
from atf.framework.devicesession.PowerControllerSession import *
from atf.common.network.Network import NetworkUtil


class HardwareConfig(DeviceConfig):
    r"""
    Encapsulate hardware specific configuration information needed
    to set up a hardware hosted Device.
    """
    def __init__(self, networks=None, networkSetupDevices=None, 
                 powerController=None, consoleServer=None,
                 guestGWs=None, systemImages=None,  
                 workspace=None):
        r"""
        Save all arguments internally and construct base class.
        
        @param networks:
            Network definitions are basic L{ProxyDevice} 
            functionality and so are handled by L{DeviceConfig}.
            
        @param networkSetupDevices:
            Network setup device definitions are basic L{ProxyDevice}
            functionality and so are handled by L{DeviceConfig}.
            
        @param powerController:
            Power control device location and access definition
        
        @param consoleServer:
            Console server device location and access definition
            
        @param guestGWs:
            Specifies addresses for interface networks. This is 
            necessary to set up host routing and takes the form of a 
            dictionary whose key is the interface name and value 
            is a tuple containing the IPV4 address and mask length.
                
        @param systemImages:
            The location of images to use for device start
            
        @param workspace:
            A pre-existing ProxyHardware.Workspace object.
        """
        if (networks == None):
            networks = []
                        
        DeviceConfig.__init__(self, networks=networks, 
                              networkSetupDevices=networkSetupDevices,
                              systemImages=systemImages,
                              powerController=powerController,
                              consoleServer=consoleServer)

        if (guestGWs == None):
            self.guestGWs = {}
        else:
            self.guestGWs = guestGWs
        
        self.workspace = workspace
    
    
class HardwareWorkspace(Common.Workspace):
    r"""
    This class extends the Common.Workspace by adding methods to create
    device related resources within the workspace context.
    """

    def __init__(self, name=None, diagLevel=logging.WARNING):
        r"""
        Refer base class for a description of this interface method.
        
        @param name:
            Location of the workarea if it already exists or None 
            if we should create a temporary one.
        
        @param diagLevel:
            What debug level to run this object in.    
        """
        Common.Workspace.__init__(self, name=name, diagLevel=diagLevel)
            
    def __del__(self):
        r"""
        Refer base class for a description of this interface method.
        """
        Common.Workspace.__del__(self) 


class ProxyHardware(ProxyDevice):
    r"""
    The ProxyHardware class supports the ProxyDevice interface to control a 
    Physical Machine.
    """    
    
    ###
    # Class error definitions
    ### 
    (ERR_UNSUPPORTED_INSTALLATION)  = FrameworkError.ERR_HW    
    """Unsupported installation type detected""" 
    (ERR_SUPPORT_DEVICES_MISSING)  = FrameworkError.ERR_HW + 1    
    """Support devices not found"""

    ###
    # Class Definitions
    ###
    # Constants
    (EXPECT_TIMEOUT) = 60
    """Generic expect time out"""
    
    # Regex Patterns
    (REGEX_NETWORKSETUP) = "Networks setup successfully"
    """Pattern expected on successful network setup."""

    
    def __init__(self,  hwConfig=None, diagLevel=logging.WARNING):
        r"""
        Save the configuration information internally for use by
        start() and move to STATE_INITIALISED.
        
        @param hwConfig:
            A pre-constructed HardwareConfig object
            
        @param diagLevel:
            What debug level to run this object in.    
        """
        # Invoke base class initialisation
        ProxyDevice.__init__(self, hwConfig, diagLevel)
        self.state = ProxyDevice.STATE_INITIALISED
        """Device state"""
        self.powerControllerSession = None
        """Device power controller session"""
        self.consoleServerSession = None
        """Device console server session"""
        self.nwCons = None
        """Network setup console"""
        self.dnsmCons = None
        """DNS setup console"""

        # Define the shell programs used to setup the network
        self.nwSetupCmd = 'networksetup '
        """Network setup command"""
        self.dnsmasqCmd = 'dnsmasqrun '
        """DNS setup command"""

    def __del__(self):
        r"""
        Ensure some level of clean up of the hardware and its
        spawned services.
        """
        if (self.cons != None) :
            self.stop()
            
    def start(self, productPackage=None):
        r"""
        Refer base class for a description of this interface method.

        @param productPackage:
            A L{ProxySUT.ProductPackage} derived class or None.
            
        @return:
            None, Can raise L{FrameworkError} exceptions
        """
        result = self.isStartable()
        if (result != CommonError.ERR_OK):
            raise (FrameworkError(result,
                    'Unable to start device, current state : %s' % self.state))                   
        try:
            self.setupDeviceVlans()
            self.state = ProxyDevice.STATE_STARTING
            nwCmd = self.nwSetupCmd
            dnsmCmd = self.dnsmasqCmd
    
            # Setup workspace
            if (self.config.workspace != None):
                # Ok if we have a workspace specified then we don't need
                # to create a new temporary one.
                self.workspace = self.config.workspace
            else:
                # No existent disk specified so create one on the fly in
                # a temporary directory area that all disappears when we do. 
                self.workspace = HardwareWorkspace()
                self.logger.debug('Creating temporary workspace : %s' \
                                  % self.workspace.workDir)
                
            # Generate the config file for dnsmasqrun
            dnsmasqConf = open("/tmp/dnsmasq-%s.conf" % os.getpid(), "w+")
            dnsmasqConf.write("#File automatically generated by ATF - DO NOT HAND EDIT\n")
            
            if (productPackage != None): 
                if (productPackage.type == DeviceConfig.IMAGE_PXE):
                    option = '-p'
                elif (productPackage.type == DeviceConfig.IMAGE_ISO or
                      productPackage.type == DeviceConfig.IMAGE_USB or
                      productPackage.type == DeviceConfig.IMAGE_LIVE):
                    raise (FrameworkError(
                               ProxyHardware.ERR_UNSUPPORTED_INSTALLATION,
                               'Unable to install with package type "%s"' % 
                               productPackage.type))
                target = productPackage.prepare(workspace=self.workspace)
                #dnsmCmd += '%s %s ' % (option, target)
                
            # Determine the networking setup
            nets = ''
    
            for (hostDevice, sysIFs) in self.config.networks.items():
                # If the bridgeIf is set we assume that the hostDevice is a
                # bridge device
                isBridge = False
                for (iname, iface) in sysIFs.interfaces.items():
                    if (iface.bridgeHostInterface != ''):
                        isBridge = True
                        break
                if (isBridge == False):
                    nets += ' -i %s' % hostDevice
                else:
                    nets += ' -n %s' % hostDevice
                # Look for any interface that needs to be assigned an address 
                # so that it can act as a GW to the real world.
                for (gw, ips) in self.config.guestGWs.items() :
                    if (gw == hostDevice) :
                        if type(ips) is not types.ListType:
                            ips = [ips]
                        for ip in ips:
                            if  NetworkUtil.checkAddressType(ip.address) == NetworkUtil.TYPE_IPV4:
                                dnsmasqConf.write("listen-address=%s\n" % ip.address)
                                dnsmasqConf.write("dhcp-range=%s,static\n" % ip.address)
                                nets += '=%s/%s' % (ip.address, ip.netmaskLength)
                            elif(NetworkUtil.checkAddressType(ip.address) == NetworkUtil.TYPE_IPV6):
                                nets += ',%s/%s' % (ip.address, ip.prefixLength)
                        break
                    
                for (iname, ifaces) in sysIFs.interfaces.items():
                    if (ifaces.bridgeHostInterface != ''):
                        nets += ',%s' % (iface.bridgeHostInterface)
                    if (ifaces.ip != None):
                        for ip in ifaces.ip:
                            if (ifaces.mac != '' and
                                ip != None and
                                ip.address != '' and
                                NetworkUtil.checkAddressType(ip.address) == NetworkUtil.TYPE_IPV4 and                                 
                                ip.type == 'dhcp'):
                                dnsmasqConf.write("#workspace=%s:%s\n" %(ip.address, self.workspace.workDir + 'tftp/'))
                                dnsmasqConf.write("dhcp-host=%s,%s\n" % (iface.mac, ip.address))
                
            nwCmd += nets + ' '
            dnsmasqConf.close()
            dnsmCmd += " -f /tmp/dnsmasq-%s.conf" % os.getpid()
    
            # Execute networksetup and dnsmasq commands
            self.logger.debug('networksetup command being executed:\n\t%s' % nwCmd)
            self.nwCons = pexpect.spawn(nwCmd)
            if (self.logger.getEffectiveLevel() <= logging.DEBUG):
                self.nwCons.logfile_read = sys.stdout
            self.nwCons.expect(ProxyHardware.REGEX_NETWORKSETUP, 
                               timeout=ProxyHardware.EXPECT_TIMEOUT)
            self.logger.debug('dnsmasqrun command being executed:\n\t%s' % dnsmCmd)
            self.dnsmCons = pexpect.spawn(dnsmCmd)
            if (self.logger.getEffectiveLevel() <= logging.DEBUG):
                self.dnsmCons.logfile_read = sys.stdout

            self.dnsmCons.expect('dnsmasqrun setup successfully',timeout=(ProxyHardware.EXPECT_TIMEOUT * 4) ) # To avoid conflicts during pxe install, dnsmasqrun ensures this

            # Connect to the power console and serial console sessions
            if (self.config.consoleServer == None or 
                self.config.powerController == None):
                raise (FrameworkError(ProxyHardware.ERR_SUPPORT_DEVICES_MISSING,
                       'Power Controller or Console Server was not configured'))
            cs = self.config.consoleServer
            cssCfg = ConsoleServerSessionConfig(ip=cs[1], port=cs[2], 
                         username=cs[4], password=cs[5], consolePort=cs[3]) 
            self.consoleServerSession = getConsoleServerSession(cs[0], cssCfg, 
                diagLevel=self.logger.getEffectiveLevel())
            pc = self.config.powerController
            pcsCfg = PowerControllerSessionConfig(ip=pc[1], port=pc[2], 
                         username=pc[4], password=pc[5], powerPort=pc[3]) 
            self.powerControllerSession = getPowerControllerSession(pc[0], pcsCfg,
                diagLevel=self.logger.getEffectiveLevel())
                
            # Connect console server and pass tty off as cons
            self.consoleServerSession.connect()
            self.cons = self.consoleServerSession.tty
            if (self.logger.getEffectiveLevel() <= logging.DEBUG):
                self.cons.logfile_read = sys.stdout
            self.state = ProxyDevice.STATE_RUNNING
        except BaseException, failure:
            self.state = ProxyDevice.STATE_UNKNOWN
            self.logger.error('Failed to start() Hardware: %s' % str(failure))
            # Output whatever was sent to the console during the attempt.
            if (self.cons != None):
                self.logger.debug(str(self.cons))
            raise (FrameworkError(ProxyDevice.ERR_FAILED_DEVICE_START,
                                  'Unexpected failure to start, see log'))

    def stop(self):
        r"""
        Refer base class for a description of this interface method.
        """
        # Check on the stoppability 
        result = self.isStoppable()
        if (result != CommonError.ERR_OK):
            raise (FrameworkError(result,
                    'Unable to stop device, current state : %s' % self.state))
        self.teardownDeviceVlans()
        
        # Clean up support sessions
        self.nwCons.kill(signal.SIGCONT)
        self.nwCons.expect(pexpect.EOF)
        os.killpg(os.getpgid(self.dnsmCons.pid), signal.SIGTERM)
        self.dnsmCons.expect(pexpect.EOF)
        self.consoleServerSession.disconnect()
        self.consoleServerSession = None
        self.cons = None

        if( int(os.environ.get('ATF_NO_SHUTDOWN', 0)) == 0 ):
            self.powerControllerSession.connect()
            self.powerControllerSession.powerOff()
            self.powerControllerSession.disconnect()

        self.powerControllerSession = None
        self.dnsmCons = None
        self.nwCons = None
