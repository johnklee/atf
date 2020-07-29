import logging
import pexpect
import signal
import subprocess
import types

import atf.common.Common as Common
from datetime import datetime
from atf.framework.FrameworkBase import *
from ProxyDevice import *
from DeviceConfig import *

class EmulatorConfig(DeviceConfig):
    r"""
    Encapsulate emulator specific configuration information needed
    to set up an emulator hosted Device.
    """
    def __init__(self, memory=512, diskSize='4G', networks=None, networkSetupDevices=None, 
                 guestGWs=None, snats=None, systemImages=None, workspace=None, 
                 useTmpfs=False):
        r"""
        Save all arguments internally and construct base class.
        
        @param memory:
            How many MB of memory to allocate to the QEMU emulator process.
        
        @param diskSize:
            The amount of host disk allocated to the system emulator device.
            Optional suffixes "K" (1024K), "M" (1024M) and "G" (1024G) are supported

        @param networks:
            Network definitions are basic L{ProxyDevice} functionality and 
            so are handled by L{DeviceConfig}.
        
        @param networkSetupDevices:
            Network setup device definitions are basic L{ProxyDevice} 
            functionality and so are handled by L{DeviceConfig}.
            
        @param guestGWs:
            Specifies addresses for host bridged networks. This is necessary 
            to set up host routing and takes the form of a dictionary 
            whose key is the bridged network name and value is a tuple 
            containing the IPV4 address and mask length.
            
        @param snats:
            SNAT configuration is specific to virtualisation. It allows the 
            guest machine to access the real world for things such as 
            contacting external entities for license authentication etc. 
            The format is a dictionary where the keys are the networks to be
            snated and the values are the host interface to snat out.
        
        @param systemImages:
            The location of images to use for device start
            
        @param workspace:
            A pre-existing L{ProxyQemu}.Workspace object.
            
        @param useTmpfs:
            If True, indicates to use tmpfs for any dynamic workspace created
        """
        if (networks == None):
            networks = {}
                        
        DeviceConfig.__init__(self, networks=networks, 
                              systemImages=systemImages,
                              networkSetupDevices=networkSetupDevices)

        if (guestGWs == None):
            self.guestGWs = {}
        else:
            self.guestGWs = guestGWs
        
        if (snats == None):
            self.snats = {}
        else:    
            self.snats = snats

        self.extraOptions = ''
        """Additional options used on execution of emurun"""
        self.memory = memory
        """Memory allocated to emulator"""
        self.diskSize = diskSize
        """Disk allocated to emulator"""
        self.useTmpfs = useTmpfs
        """Indicator for use of tmpfs for artifact backing"""
        self.workspace = workspace
        """Workspace of the device"""
        
    def setWorkspace(self, workspace):
        r"""
        Set the workspace and optionally allow for the return 
        of extra command options based on a workspace information.
        """
        self.workspace = workspace
        return ''
    
class EmulatorWorkspace(Common.Workspace):
    r"""
    This class extends the Common.Workspace by adding methods to create
    disk images within the workspace context.
    """

    ###
    # Class error definitions
    ### 
    (ERR_DISK_CREATION)  = FrameworkError.ERR_EMU    
    """Failed in creation of emulator disk image"""    
    
    def __init__(self, name=None, useTmpfs=False, diagLevel=logging.WARNING):
        r"""
        Refer base class for a description of this interface method.
        
        @param name:
            Location of the workarea if it already exists or None if we 
            should create a temporary one.
        
        @param useTmpfs:
            If not None, indicates workspace should be created on a tmpfs 
            area. Option is ignored if name is also not None since 
            this calls out a specific location beyond our control.
        
        @param diagLevel:
            What debug level to run this object in.    
        """
        Common.Workspace.__init__(self, name=name, 
                                  useTmpfs=useTmpfs, diagLevel=diagLevel)
        self.disk = {}
        """Workspace disk parameters"""
        self.cmdCreateDisk = ''
        """Command used to create a disk"""
        self.defaultDiskSize = ''
        """Default size of the disk to be created"""
        self.defaultDiskType = ''
        """Default type of the disk to be created"""
        self.defaultDiskRegex = ''
        """Default regex to identify functionality of disk creation"""
            
    def __del__(self):
        r"""
        Refer base class for a description of this interface method.
        """
        Common.Workspace.__del__(self) 

    def createDiskCommand(self, name, type, size):
        r"""
        Constructs a disk creation command string.

        @param name:
            The filename to use for the created image.
                 
        @param type:
            The vmware type of disk to create
        
        @param size:
            The amount of room to put on the disk image
            
        @return:
            Disk creation command string, Can raise L{FrameworkError} 
            exceptions
        """
        raise (NotImplementedError())

    def createDisk(self, name, type="", size=""):
        r"""
        Refer base class for a description of this interface method.

        @param name:
            The filename to use for the created image.
            
        @param type:
            The type of disk to create
            
        @param size:
            The amount of room to put on the disk image
            Optional suffixes "K" (1024K), "M" (1024M) and "G" (1024G) are supported
            
        @return:
            None, Can raise L{FrameworkError} exceptions
        """
        if (type == ""):
            type = self.defaultDiskType
        if (size == ""):
            size = self.defaultDiskSize
            
        self.disk = {'name':name, 'type':type, 'size':size}

        cmd = self.createDiskCommand(self.workDir + name,
                                     self.disk['type'],
                                     self.disk['size'])
        try:
            terminal = pexpect.spawn('%s' % cmd)
            if (self.logger.getEffectiveLevel() <= logging.DEBUG) :
                terminal.logfile_read = sys.stdout
            terminal.expect_exact(self.defaultDiskRegex)
            terminal.expect(pexpect.EOF)
        except:
            self.logger.error('Failed : Emulator disk not created')
            # Output the terminal output from disk creation attempt
            result = str(terminal)
            self.logger.debug(result)
            raise(FrameworkError(EmulatorWorkspace.ERR_DISK_CREATION,
                                 'Failed : to create disk : %s' % result))

    def setDisk(self, name, type=None, size=None): 
        r"""
        Refer base class for a description of this interface method.

        @param name:
            The workspace relative filename of an existing image.
            
        @param type:
            The type of the disk
            
        @param size:
            The amount of room on the disk image
            Optional suffixes "K" (1024K), "M" (1024M) and "G" (1024G) are supported
        """
        self.disk = {'name':name, 'type':type, 'size':size}

class ProxyEmulator(ProxyDevice):
    r"""
    The ProxyEmulator class supports the ProxyDevice interface to control a 
    Virtual Machine.
    """    
    def __init__(self,  emuConfig=None, diagLevel=logging.WARNING):
        r"""
        Save the configuration information internally for use by
        start() and move to STATE_INITIALISED.
        
        @param emuConfig:
            A pre-constructed EmulatorConfig object
            
        @param diagLevel:
            What debug level to run this object in.
        """
        # Invoke base class initialisation
        ProxyDevice.__init__(self, emuConfig, diagLevel)
        self.state = ProxyDevice.STATE_INITIALISED

        # Define the shell program we will use to start emulator.
        # NOTE : This is NOT run sudo to avoid some potential security issues.
        self.runCmd = 'emurun '

    def __del__(self):
        r"""
        Try and make sure that qrun gets a chance to cleanup by
        sending it a signal before exit.
        """
        if (self.cons != None) :
            self.stop()
        
        # clean up all references to workspace at dtor time
        self.workspace = None
        self.config = None

    def start(self, productPackage=None):
        r"""
        Refer base class for a description of this interface method.

        @param productPackage:
            A L{ProxySUT.ProductPackage} derived class or None.
            
        @return:
            None, Can raise FrameworkError exceptions
        """

        
        result = self.isStartable()
        if (result != CommonError.ERR_OK):
            raise (FrameworkError(result,
                    'Unable to start device, current state : %s' % self.state))
        try:
            self.setupDeviceVlans()
            self.state = ProxyDevice.STATE_STARTING
            # Set up all the command line args to emurun into cmd
            cmd = self.runCmd
            if (self.config.extraOptions != ''):
                cmd += '%s ' % self.config.extraOptions
            if (self.config.memory > 0):
                cmd += '-m %s ' % self.config.memory
                
            if (self.config.workspace != None):
                # Ok if we have a workspace specified then we don't need
                # to create a new temporary one.
                self.workspace = self.config.workspace
            else:
                # No existent disk specified so create one on the fly in
                # a temporary directory area that all disappears when we do. 
                self.workspace = EmulatorWorkspace(useTmpfs=self.config.useTmpfs,
                                                   diagLevel=self.logger.getEffectiveLevel())
                self.logger.debug('Creating temporary workspace & disk : %s' \
                                  % self.workspace.workDir)
                self.workspace.createDisk(name='system.img', size=self.config.emuDisk) 
                
            # Sets the device config's workspace and appends associated extra options
            # based on this information
            cmd += self.config.setWorkspace(self.workspace)
                
            # now add the workspace disk
            cmd += '-d %s ' % (self.workspace.workDir + self.workspace.disk['name'])
            
            if (productPackage != None): 
                if (productPackage.type == DeviceConfig.IMAGE_ISO):
                    option = '-c'
                elif (productPackage.type == DeviceConfig.IMAGE_USB):
                    option = '-u'
                elif (productPackage.type == DeviceConfig.IMAGE_LIVE):
                    option = '-l'
                elif (productPackage.type == DeviceConfig.IMAGE_PXE):
                    option = '-p'
                target = productPackage.prepare(workspace=self.workspace)
                cmd += '%s %s ' % (option, target)
            # Determine the networking setup
            nets = ''
            if (self.config.networks != None):
                for (bridge, sysIFs) in self.config.networks.items():
                    nets += '-n %s' % bridge
                    # Look for any bridge that needs to be assigned an address 
                    # so that it can act as a GW to the real world.
                    for (gw, ips) in self.config.guestGWs.items():
                        if (gw == bridge):
                            if type(ips) is not types.ListType:
                                ips = [ips]
                            separator = '='
                            for ip in ips:
                                if  hasattr(ip, 'netmaskLength'):
                                    #nets += '=%s/%s' % (ip.address, ip.netmaskLength)
                                    nets += '%s%s/%s' % (separator, ip.address, ip.netmaskLength)
                                elif(hasattr(ip, 'prefixLength')):
                                    nets += '%s%s/%s' % (separator, ip.address, ip.prefixLength)
                                separator = ','
                            break
                    # Now set up having the guest interfaces on the host bridge
                    # This we simply use the eth number as the logical device
                    # number to emurun (i.e. eth0 -> 0, eth4->4).
                    for (iname, ifaces) in sysIFs.interfaces.items():
                        nets += ',%s' % (iname.lstrip('eth'))
                        if (ifaces.ip != None):
                            for ip in ifaces.ip:
                                if (ip != None and 
                                    ip.type == 'dhcp'):
                                    nets += '=%s' % ip.address
                    nets += ' '

            cmd += nets + ' '

            # Sort out masquerading for the guest if needed.
            for bridge, hostIF in self.config.snats.items():
                cmd += '-s %s,%s' % (bridge, hostIF)
                
            self.logger.debug('emulator command being executed:\n\t%s' % cmd)
            # Start the emulator instance and capture the console.
            self.cons = pexpect.spawn(cmd)
            if (self.logger.getEffectiveLevel() <= logging.DEBUG):
                self.cons.logfile_read = sys.stdout
            self.state = ProxyDevice.STATE_RUNNING
        except BaseException, failure:
            self.state = ProxyDevice.STATE_UNKNOWN
            self.logger.error('Failed to start() Emulator: %s' % str(failure))
            # Output whatever was sent to the console during the attempt.
            if (self.cons != None):
                self.logger.debug(str(self.cons))
            raise (FrameworkError(ProxyDevice.ERR_FAILED_DEVICE_START,
                                  'Unexpected failure to start, see log')) 
        

    def stop(self):
        r"""
        Refer base class for a description of this interface method.
        """
        # Check on the stoppability of the emulator
        result = self.isStoppable()
        if (result != CommonError.ERR_OK):
            raise (FrameworkError(result,
                    'Unable to stop device, current state : %s' % self.state))
        self.teardownDeviceVlans()


