import logging
import copy

from FrameworkBase import *
from atf.framework.device.DeviceConfig import *
from atf.framework.device.ProxyDevice import *
from atf.framework.device.ProxyQemu import *
from atf.framework.device.ProxyVMware import *
from atf.framework.device.ProxyVMwareESX import *
from atf.framework.device.ProxyGX4004 import *
from atf.framework.device.ProxyMX1004 import *
from atf.framework.device.ProxyFWA3210es0 import *
from atf.framework.device.ProxyFWA3210es1 import *
from atf.framework.device.ProxyFWA3211es import *
from atf.framework.device.ProxyFWA6501 import *
from atf.framework.device.ProxyXGS3100 import *
from atf.framework.device.ProxyXGS4100 import *
from atf.framework.device.ProxyXGS5100 import *
from atf.framework.device.ProxyXGS5200 import *
from atf.framework.device.ProxyXGS7100 import *
from atf.framework.device.ProxyCloudStack import *
from atf.framework.device.ProxyDocker import *


class IPv4(object):
    """
    IPv4 construct.
    """
    def __init__(self, address='', netmaskLength='24', type='dhcp'):
        self.address = address
        """ipv4 address e.g. 10.0.0.1 """

        self.netmaskLength = netmaskLength
        """ipv4 netmaskLength e.g. 24"""

        self.type = type
        """ip address assignment indicator. Values: 'static', 'dhcp'"""


class IPv6(object):
    """
    IPv6 construct.
    """
    def __init__(self, address='', prefixLength='64', type='dhcp'):
        self.address = address
        """ipv6 address e.g. 2001:db8:85a3::8a2e:370:100 """

        self.prefixLength = prefixLength
        """ipv6 prefix e.g. 64"""

        self.type = type
        """ip address assignment indicator. Values: 'static', 'dhcp'"""


class VLan(object):
    """
    Details of connected vlan.
    """
    def __init__(self, deviceName='', devicePort=0, vlanId=0):
        self.deviceName = deviceName
        """device name (key into networkSetupDevices)"""

        self.devicePort = devicePort
        """port on the connected network device"""

        self.vlanId = vlanId
        """
        vlanId on the connected network device.
        Values: 0 = No vlan, 1 = mgmt, 2+ = Valid
        """


class ProxyInterface(object):
    """
    Details of network configuration of an interface on proxied system.

    Various fields will be present/set based on exact nature of interface.
    """
    def __init__(self, ip=None, mac='', bridgeHostInterface='', vlan=None):

        self.ip = ip
        """List of IP addresses to associate with the interface"""

        self.mac = mac
        """Hardware MAC Address"""

        self.bridgeHostInterface = bridgeHostInterface
        """host interface associated with the bridge"""

        self.vlan = vlan
        """L{VLan} for connected network device"""


class SystemInterfaces(object):
    """
    Details of a network reachable from the host.
    """
    def __init__(self, interfaces={}, vlan=None):
        self.interfaces = interfaces
        """
        Collection of L{ProxyInterface} objects which represent reachable interfaces.
        The key is the interface name (e.g. eth0) the value is a L{ProxyInterface} object
        """

        self.vlan = vlan
        """L{VLan} that the host is connected to."""


class SystemConfig(object):
    r"""
    Encapsulate all the VM agnostic configuration information needed
    to set up a generic System
    """
    #
    # Class error definitions
    #
    # Failed in creation of runtime configuration settings
    (ERR_RUN_MODE) = FrameworkError.ERR_SYSCFG

    #
    # Class type definitions
    #
    # Define supported System run modes
    # [Emulation Run Modes]
    (RUN_MODE_QEMU) = 1
    """Run system in QEMU"""
    (RUN_MODE_VMWARE) = 2
    """Run system in VMWARE"""
    (RUN_MODE_VMWARE_ESX) = 3
    """Run system in VMWARE ESX"""
    (RUN_MODE_CLOUDSTACK) = 4
    """Run system in CloudStack"""
    (RUN_MODE_DOCKER) = 5
    """Run system in Container"""
    
    (RUN_MODE_EMULATION) = (RUN_MODE_QEMU)
    """Starting value for emulation run modes. To be used for identification"""
    # [Hardware Run Modes]
    (RUN_MODE_GX4004) = 100
    """Run system in GX4004"""
    (RUN_MODE_MX1004) = 101
    """Run system in MX1004"""
    (RUN_MODE_FWA3210_ES0) = 102
    """Run system in FWA3210_ES0"""
    (RUN_MODE_FWA3210_ES1) = 103
    """Run system in FWA3210_ES1"""
    (RUN_MODE_FWA3211_ES) = 104
    """Run system in FWA3211_ES"""
    (RUN_MODE_FWA6501) = 105
    """Run system in FWA6501"""
    (RUN_MODE_XGS3100) = 106
    """Run system in XGS3100"""
    (RUN_MODE_XGS4100) = 107
    """Run system in XGS4100"""
    (RUN_MODE_XGS5100) = 108
    """Run system in XGS5100"""
    (RUN_MODE_XGS7100) = 109
    """Run system in XGS7100"""
    (RUN_MODE_XGS5200) = 110
    """Run system in XGS5200"""

    (RUN_MODE_HARDWARE) = (RUN_MODE_GX4004)
    """Starting value for hardware run modes. To be used for identification"""

    # Define supported System network setup devices
    # (i.e. switches, routers, etc)
    (NSD_TYPE_CISCOIOS) = 1
    """Switch type Cisco IOS)"""
    (NSD_TYPE_CISCOCATOS) = 2
    """Switch type Cisco CatOS)"""

    # Define supported System power controllers devices
    (PCD_TYPE_PERLE) = 1
    """Power controller type Perle"""
    (PCD_TYPE_APC) = 2
    """Power controller type APC7901"""
    (PCD_TYPE_APC_7932) = 3
    """Power controller type APC7932"""

    # Define supported System console server devices
    (CSD_TYPE_BELKIN) = 1
    """Console server type Belkin"""
    (CSD_TYPE_PERLE) = 2
    """Console server type Perle"""
    (CSD_TYPE_PORTMASTER) = 3
    """Console server type Portmaster"""

    def __init__(self, systemConfig=None, deviceConfig=None):
        r"""
        Save the installation image location and DeviceConfig derived object

        @param systemConfig:
            A pre-constructed systemConfig object.

        @param deviceConfig:
            A pre-constructed DeviceConfig derived object.
        """
        #
        # === Settings ===
        #

        if (systemConfig == None):
            #
            # General Settings
            #
            self.diagLevel = int(os.environ.get('ATF_LOG_LEVEL', logging.WARNING))
            """Default logging level for all test objects created during testing
            When specifying the LOG_LEVEL environment variable the following
            numeric values should be assigned :
                - CRITICAL = 50
                - ERROR = 40
                - WARNING = 30
                - INFO = 20
                - DEBUG = 10
                - NOTSET = 0"""

            self.runMode = int(os.environ.get('ATF_RUN_MODE', SystemConfig.RUN_MODE_QEMU))
            """The run mode to indicate the environment in which the System is to be run.
            One of:
                - L{RUN_MODE_QEMU}
                - L{RUN_MODE_VMWARE}
                - L{RUN_MODE_VMWARE_ESX}
                - L{RUN_MODE_GX4004}
                - L{RUN_MODE_MX1004}
                - L{RUN_MODE_FWA3210_ES0}
                - L{RUN_MODE_FWA3210_ES1}
                - L{RUN_MODE_FWA3211_ES}
                - L{RUN_MODE_FWA6501}
                - L{RUN_MODE_XGS3100}
                - L{RUN_MODE_XGS4100}
                - L{RUN_MODE_XGS5100}
                - L{RUN_MODE_XGS5200}
                - L{RUN_MODE_XGS7100}
                - L{RUN_MODE_DOCKER}

            Defaults to RUN_MODE_QEMU."""

            self.installUser = os.environ.get('ATF_INSTALL_USER', 'root')
            """The installation user name for the Systems. These must all be the same
            for multiple System tests. Defaults to 'root'."""

            self.installPasswd = os.environ.get('ATF_INSTALL_PASSWD', 'admin')
            """The installation password for the Systems. These must all be the same for
            multiple System tests. Defaults to 'admin'."""

            self.adminUser = os.environ.get('ATF_ADMIN_USER', 'root')
            """The administration user name for the SUTs. These must all be the same
            for multiple SUT tests. Defaults to 'root'."""

            self.adminPasswd = os.environ.get('ATF_ADMIN_PASSWD', 'admin')
            """The administration password for the SUTs. These must all be the same
            for multiple SUT tests. Defaults to 'admin'."""

            self.pxelinux = os.environ.get('ATF_PXELINUX', '')
            """The location of the PXElinux file used for PXE booting.
            Defaults to ''."""

            self.systemImages = {
                DeviceConfig.IMAGE_ISO:
                os.environ.get('ATF_ISO_INST_IMG', ''),
                DeviceConfig.IMAGE_PXE:
                os.environ.get('ATF_PXE_INST_IMG', ''),
                DeviceConfig.IMAGE_USB:
                os.environ.get('ATF_USB_INST_IMG', ''),
                DeviceConfig.IMAGE_LIVE:
                os.environ.get('ATF_LIVE_IMG', ''),
                DeviceConfig.IMAGE_VHD:
                os.environ.get('ATF_VHD',''),
                DeviceConfig.IMAGE_QCOW2:
                os.environ.get('ATF_QCOW2_IMG','')
                }
            """A dictionary of the System images available for boot
            Valid image keys are : 'iso', 'pxe', 'usb', 'live', 'vhd, 'qcow2',
            Defaults to '' for all keys."""

            self.networkSetupDevices = {}
            """A dictionary associating details about all used network setup devices with
            a user-defined name.
            This configuration option takes the following form:
                - E{lb} <network-setup-device-name>:
                  (<switch-type>, <switch-ip>, <switch-ip-port>, <device name>, <username>, <password>), E{rb}
                - switch-type : 1 = cisco-ios, 2 = cisco-catos
            Defaults to {}."""

            self.networks = None
            """A collection of networks reachable from the host
            This configuration option takes the following form:
                - E{lb} host-network-device : <L{SystemInterfaces}-object> E{rb}
            e.g::
              Emulator =
              {'br0':
               SystemInterfaces({'eth0':
                                 ProxyInterface([IPv4('10.0.254.2')])})}

              Real H/W =
              {'br0':
               SystemInterfaces({'eth0':
                                 ProxyInterface([IPv4('10.0.254.2')],
                                                mac='aa:bb:cc:dd:ee:ff',
                                                vlan=Vlan('vlan1', 5))},
                                 Vlan('vlan2', 2, 201))}

            Defaults to None."""

            self.proxySystemRoute = None
            """A dictionary that contains a mapping of host network device to
            proxied system network address. It is used to install an IP address
            and implicit route on the network device to the proxied system.
            This configuration option takes the following form:
                - E{lb} <host-network-device> : <L{IPv4}-object> E{rb}
            Defaults to None."""

            self.defaultGatewayIp = None
            """Systems default gateway IP. Format: L{IPv4} object.
            Defaults to None."""

            self.defaultGatewayIpv6 = None
            """Systems default gateway IP. Format: L{IPv6} object.
            Defaults to None."""

            self.dnsIp = None
            """Systems DNS IP. Format: L{IPv4} object.
            Defaults to None."""

            self.forwarding = ''
            """Network forwarding information. Format: 'srcIfName|dstIfName'.
            Defaults to None."""

            self.routing = None
            """List of routing information.
            Format:
            [ ( <dest-L{IPv4}-object>, <ifName> or <gateway-L{IPv4}-object> ) ]

            Defaults to None.
            """

            self.seleniumConfig = {}
            r"""A collection of selenium configuration parameters
            Format:
            dict(
            'ip'     : selenium server IP address,
            'port'   : selenium server port,
            'url'    : selenium base URL,
            'browser': selenium browser type to use:

            *firefox
            *mock
            *firefoxproxy
            *pifirefox
            *chrome
            *iexploreproxy
            *iexplore
            *firefox3
            *safariproxy
            *googlechrome
            *konqueror
            *firefox2
            *safari
            *piiexplore
            *firefoxchrome
            *opera
            *iehta
            *custom
            )

            Example:
            {
            'ip'      : '192.168.0.2',
            'port'    : '4444',
            'url'     : 'http://google.com/',
            'browser' : '*firefox'
            }

            Defaults to {}.
            """

            #
            # General Emulator Settings
            #
            self.emuMemory = int(os.environ.get('ATF_EMU_MEMORY', 1024))
            """The amount of host memory allocated to the system emulator device.
            Defaults to 1024."""

            self.emuDiskSize = os.environ.get('ATF_EMU_DISK_SIZE', '4G')
            """The amount of host disk allocated to the system emulator device.
            Defaults to 4G."""

            self.emuUseTmpfs = bool(int(os.environ.get('ATF_EMU_USE_TMPFS', 1)))
            """Use tmpfs for any dynamically created system disks. Defaults to 1."""

            self.emuSnats = {}
            """The SNATs definition required for proxied system external access
            It is a dictionary of the form:
                - { <proxied-system-interface> : <host-network-device-interface> }
            Defaults to {}."""

            self.emuImageRoot = os.environ.get('ATF_EMU_IMAGE_ROOT', '/tssImages')
            """The root directory path of the TSS images to use. Defaults to '/tssImages'"""

            self.emuImageName = None
            """Short name of a emulator image to run.
            If set, then ISSTestBase.runTSS will construct the required value of
            emuForceSystemDisk to run the image.
            If emuforceSsytemDisk is set, then it takes precedence.
            Defaults to None."""

            self.emuImageType = None
            """ISSTestBase System type of the emulator image to run.
            If emuImageName is also set, then ISSTestBase.runTSS
            will construct the required value of emuForceSystemDisk to run the image.
            If emuforceSystemDisk is set, then it takes precedence.
            Currently supported values are:
                - ISSTestBase.SYSTEM_TYPE_MESA_SUT
                - ISSTestBase.SYSTEM_TYPE_ALPS_SUT
                - ISSTestBase.SYSTEM_TYPE_LINUX_TSS
            Defaults to None."""

            self.emuForceSystemDisk = os.environ.get('ATF_EMU_FORCE_SYSTEM_DISK', None)
            """Force the system disk to this specific file image (i.e. do NOT
            create a dynamic system disk when required). Defaults to None."""

            #
            # QEMU Settings
            #
            self.qemuWaitForGdb = bool(int(os.environ.get('ATF_QEMU_GDB_WAIT', 0)))
            """Signal that the emulation start up should block on GDB connection before
            guest OS bring up. Defaults to 0."""

            self.qemuSnapshot = bool(int(os.environ.get('ATF_EMU_USE_SNAPSHOT', 0)))
            """Use emulator snapshot mode.
            If set, any persistent modifications that being made to the system image are
            not saved.
            Defaults to False"""

            self.qemuKVM = bool(int(os.environ.get('ATF_QEMU_KVM', 0)))
            """Enables the use of KVM acceleration during the execution of QEMU.
            1 for enabled, 0 otherwise. Defaults to 0."""

            self.qemuUSB = bool(int(os.environ.get('ATF_QEMU_USB', 0)))
            """Enables the attachment of a USB image during the execution of QEMU.
            This will be generated by default. 1 for enabled, 0 otherwise. Defaults to 0."""

            self.qemuUSBSize = os.environ.get('ATF_QEMU_USB_SIZE', '1G')
            """Specifies the size of the USB image to be created for QEMU.
            Value to set. Defaults to 1G."""

            self.qemuForceUSBImage = os.environ.get('ATF_QEMU_FORCE_USB_IMAGE', None)
            """Force the emulator to start up with this specific image mounted
            as it's USB key image (i.e. do NOT create a dynamic USB key image when
            required). Defaults to None"""

            self.qemuCpu = os.environ.get('ATF_QEMU_CPU', None)
            """The -cpu argument QEMU uses when starting a SUT"""

            #
            # Container Settings
            #
            self.dockerImgInfo = None
            """ TSS Image information: Repository/Stream/Tag/Services """

            #
            # VMWware settings
            #
            # None

            #
            # VMWware ESX settings
            #
            self.vmwareESXVMFS = os.environ.get('ATF_VMWARE_ESX_VMFS_ROOT', '/vmfs/volumes/')
            """The root directory path of the VMware ESX VMFS datastore. Defaults to '/vmfs/volumes/'"""

            #
            # H/W Settings
            #
            self.powerController = None
            """Describe the power controller associated with this System.
            This configuration option takes the following form:
                - (<controller-type>, <controller-ip>, <controller-port>, <port#>, <username>, <password>)
                - controller-type: 1 = belkin, 2 = perle, 3 = apc
            Defaults to None."""

            self.consoleServer = None
            """Describe the console Server associated with this System.
            This configuration option takes the following form:
                - (<server-type>, <server-ip>, <server-port>, <port#>, <username>, <password>)
                - controller-type: 1 = belkin, 2 = perle, 3 = powermaster
            Defaults to None."""
            
            
            #
            # CloudStack Settings
            #
            self.fralvor = None

            self.urlLocation = None
            """The location of the VHD/qcow2 drive to will be used to create the SUT template"""
            
            self.name = None
            self.description = None
            """The name and description for the virtual machine and template to be created"""
            
            self.imageId = None
            """The ID of the image which the virtual machine will be created
            from. This should be None for the sut as a template will be created
            and should be set for any TSSs"""
            
            self.osAuthUrl=None,
            self.osTenantName=None,
            self.osUsername=None,
            self.osPassword=None,
            self.osRegionName=None
        else:
            # Copy all settings of a SystemConfiguration that has been passed in
            self.diagLevel = systemConfig.diagLevel
            self.runMode = systemConfig.runMode
            self.installUser = systemConfig.installUser
            self.installPasswd = systemConfig.installPasswd
            self.adminUser = systemConfig.adminUser
            self.adminPasswd = systemConfig.adminPasswd
            self.pxelinux = systemConfig.pxelinux
            self.systemImages = systemConfig.systemImages
            self.networks = systemConfig.networks
            self.networkSetupDevices = systemConfig.networkSetupDevices
            self.proxySystemRoute = systemConfig.proxySystemRoute
            self.defaultGatewayIp = systemConfig.defaultGatewayIp
            self.defaultGatewayIpv6 = systemConfig.defaultGatewayIpv6
            self.dnsIp = systemConfig.dnsIp
            self.forwarding = systemConfig.forwarding
            self.routing = systemConfig.routing
            self.emuMemory = systemConfig.emuMemory
            self.emuDiskSize = systemConfig.emuDiskSize
            self.emuUseTmpfs = systemConfig.emuUseTmpfs
            self.emuSnats = systemConfig.emuSnats
            self.emuImageRoot = systemConfig.emuImageRoot
            self.emuImageName = systemConfig.emuImageName
            self.emuImageType = systemConfig.emuImageType
            self.emuForceSystemDisk = systemConfig.emuForceSystemDisk
            self.qemuSnapshot = systemConfig.qemuSnapshot
            self.qemuWaitForGdb = systemConfig.qemuWaitForGdb
            self.qemuKVM = systemConfig.qemuKVM
            self.qemuUSB = systemConfig.qemuUSB
            self.qemuUSBSize = systemConfig.qemuUSBSize
            self.qemuForceUSBImage = systemConfig.qemuForceUSBImage
            self.qemuCpu = systemConfig.qemuCpu
            self.vmwareESXVMFS = systemConfig.vmwareESXVMFS
            self.powerController = systemConfig.powerController
            self.consoleServer = systemConfig.consoleServer
            self.seleniumConfig = systemConfig.seleniumConfig
            self.urlLocation = systemConfig.urlLocation
            self.name = systemConfig.name
            self.imageId = systemConfig.imageId
            self.osAuthUrl=systemConfig. osAuthUrl
            self.osTenantName=systemConfig.osTenantName
            self.osUsername=systemConfig.osUsername
            self.osPassword=systemConfig.osPassword
            self.osRegionName=systemConfig.osRegionName
            self.dockerImgInfo = systemConfig.dockerImgInfo
        #
        # === Non-Settings ===
        #
        # The device config associated with this system configuration. This
        # should not be set when constructing the test RunConfig/SystemConfig
        # files
        self.deviceConfig = deviceConfig

    def createDeviceConfig(self):
        r"""
        Create an appropriate L{DeviceConfig} based on the SystemConfig run mode
        and other ancillary information stored within SystemConfig itself.

        @return:
            A SystemConfig object constructed on type and settings
            information, exceptions raised must be derived from
            L{FrameworkError}
        """
        deviceConfig = None

        if (self.runMode == SystemConfig.RUN_MODE_QEMU):
            if (self.emuForceSystemDisk != None):
                dir = os.path.dirname(self.emuForceSystemDisk)
                fn = os.path.basename(self.emuForceSystemDisk)
                workspace = QemuWorkspace(name=dir,
                                          useTmpfs=self.emuUseTmpfs,
                                          diagLevel=self.diagLevel)
                workspace.setDisk(name=fn)
                if (self.qemuUSB == True):
                    if (self.qemuForceUSBImage == None):
                        workspace.createUSB(name='usb.img', size=self.qemuUSBSize)
                    else:
                        workspace.setUSB(name=self.qemuForceUSBImage)
            else:
                workspace = None

            # bundle usb options
            if (self.qemuUSB):
                usbOpts = [self.qemuForceUSBImage, self.qemuUSBSize]
            else:
                usbOpts = None

            deviceConfig = \
                QemuConfig(memory=self.emuMemory,
                           diskSize=self.emuDiskSize,
                           systemImages=self.systemImages,
                           networks=self.networks,
                           networkSetupDevices=self.networkSetupDevices,
                           guestGWs=self.proxySystemRoute,
                           workspace=workspace,
                           useTmpfs=self.emuUseTmpfs,
                           snats=self.emuSnats,
                           snapshot=self.qemuSnapshot,
                           waitForGdb=self.qemuWaitForGdb,
                           kvm=self.qemuKVM,
                           cpu=self.qemuCpu,
                           usbOpts=usbOpts)
        elif (self.runMode == SystemConfig.RUN_MODE_DOCKER):
            deviceConfig = \
                DockerConfig(memory=self.emuMemory,
                             networks=self.networks, 
                             networkSetupDevices=self.networkSetupDevices,
                             guestGWs=self.proxySystemRoute,
                             snats=self.emuSnats,
                             imgInfo=self.dockerImgInfo)
        elif (self.runMode == SystemConfig.RUN_MODE_VMWARE):
            if (self.emuForceSystemDisk != None):
                dir = os.path.dirname(self.emuForceSystemDisk)
                fn = os.path.basename(self.emuForceSystemDisk)
                workspace = VMwareWorkspace(name=dir,
                                            useTmpfs=self.emuUseTmpfs,
                                            diagLevel=self.diagLevel)
                workspace.setDisk(name=fn)
            else:
                workspace = None

            deviceConfig = \
                VMwareConfig(memory=self.emuMemory,
                             diskSize=self.emuDiskSize,
                             systemImages=self.systemImages,
                             networks=self.networks,
                             networkSetupDevices=self.networkSetupDevices,
                             guestGWs=self.proxySystemRoute,
                             workspace=workspace,
                             useTmpfs=self.emuUseTmpfs,
                             snats=self.emuSnats)
        elif (self.runMode == SystemConfig.RUN_MODE_VMWARE_ESX):
            if (self.emuForceSystemDisk != None):
                dir = os.path.dirname(self.emuForceSystemDisk)
                fn = os.path.basename(self.emuForceSystemDisk)
                workspace = VMwareESXWorkspace(vmfsPath=self.vmwareESXVMFS,
                                               name=dir,
                                               useTmpfs=self.emuUseTmpfs,
                                               diagLevel=self.diagLevel)
                workspace.setDisk(name=fn)
            else:
                workspace = None

            deviceConfig = \
                VMwareESXConfig(vmfs=self.vmwareESXVMFS,
                                memory=self.emuMemory,
                                systemImages=self.systemImages,
                                networks=self.networks,
                                networkSetupDevices=self.networkSetupDevices,
                                guestGWs=self.proxySystemRoute,
                                workspace=workspace,
                                useTmpfs=self.emuUseTmpfs,
                                snats=self.emuSnats)
        elif (self.runMode == SystemConfig.RUN_MODE_GX4004):
            deviceConfig = \
                GX4004Config(systemImages=self.systemImages,
                             networks=self.networks,
                             networkSetupDevices=self.networkSetupDevices,
                             powerController=self.powerController,
                             consoleServer=self.consoleServer,
                             guestGWs=self.proxySystemRoute)
        elif (self.runMode == SystemConfig.RUN_MODE_MX1004):
            deviceConfig = \
                MX1004Config(systemImages=self.systemImages,
                             networks=self.networks,
                             networkSetupDevices=self.networkSetupDevices,
                             powerController=self.powerController,
                             consoleServer=self.consoleServer,
                             guestGWs=self.proxySystemRoute)
        elif (self.runMode == SystemConfig.RUN_MODE_FWA3210_ES0):
            deviceConfig = \
                FWA3210es0Config(systemImages=self.systemImages,
                                 networks=self.networks,
                                 networkSetupDevices=self.networkSetupDevices,
                                 powerController=self.powerController,
                                 consoleServer=self.consoleServer,
                                 guestGWs=self.proxySystemRoute)
        elif (self.runMode == SystemConfig.RUN_MODE_FWA3210_ES1):
            deviceConfig = \
                FWA3210es1Config(systemImages=self.systemImages,
                                 networks=self.networks,
                                 networkSetupDevices=self.networkSetupDevices,
                                 powerController=self.powerController,
                                 consoleServer=self.consoleServer,
                                 guestGWs=self.proxySystemRoute)
        elif (self.runMode == SystemConfig.RUN_MODE_FWA3211_ES):
            deviceConfig = \
                FWA3211esConfig(systemImages=self.systemImages,
                                networks=self.networks,
                                networkSetupDevices=self.networkSetupDevices,
                                powerController=self.powerController,
                                consoleServer=self.consoleServer,
                                guestGWs=self.proxySystemRoute)
        elif (self.runMode == SystemConfig.RUN_MODE_FWA6501):
            deviceConfig = \
                FWA6501Config(systemImages=self.systemImages,
                              networks=self.networks,
                              networkSetupDevices=self.networkSetupDevices,
                              powerController=self.powerController,
                              consoleServer=self.consoleServer,
                              guestGWs=self.proxySystemRoute)
        elif (self.runMode == SystemConfig.RUN_MODE_XGS3100):
            deviceConfig = \
                XGS3100Config(systemImages=self.systemImages,
                              networks=self.networks,
                              networkSetupDevices=self.networkSetupDevices,
                              powerController=self.powerController,
                              consoleServer=self.consoleServer,
                              guestGWs=self.proxySystemRoute)
        elif (self.runMode == SystemConfig.RUN_MODE_XGS4100):
            deviceConfig = \
                XGS4100Config(systemImages=self.systemImages,
                              networks=self.networks,
                              networkSetupDevices=self.networkSetupDevices,
                              powerController=self.powerController,
                              consoleServer=self.consoleServer,
                              guestGWs=self.proxySystemRoute)
        elif (self.runMode == SystemConfig.RUN_MODE_XGS5100):
            deviceConfig = \
                XGS5100Config(systemImages=self.systemImages,
                              networks=self.networks,
                              networkSetupDevices=self.networkSetupDevices,
                              powerController=self.powerController,
                              consoleServer=self.consoleServer,
                              guestGWs=self.proxySystemRoute)
        elif (self.runMode == SystemConfig.RUN_MODE_XGS5200):
            deviceConfig = \
                XGS5200Config(systemImages=self.systemImages,
                              networks=self.networks,
                              networkSetupDevices=self.networkSetupDevices,
                              powerController=self.powerController,
                              consoleServer=self.consoleServer,
                              guestGWs=self.proxySystemRoute)
        elif (self.runMode == SystemConfig.RUN_MODE_XGS7100):
            deviceConfig = \
                XGS7100Config(systemImages=self.systemImages,
                              networks=self.networks,
                              networkSetupDevices=self.networkSetupDevices,
                              powerController=self.powerController,
                              consoleServer=self.consoleServer,
                              guestGWs=self.proxySystemRoute)
        elif(self.runMode == SystemConfig.RUN_MODE_CLOUDSTACK):
            deviceConfig = \
                CloudStackConfig(osAuthUrl=self.osAuthUrl, osRegionName=self.osRegionName, osTenantName=self.osTenantName,
                              osUsername=self.osUsername, osPassword=self.osPassword, networks=self.networks,
                              name=self.name, urlLocation=self.urlLocation, flavor=self.flavor, imageId=self.imageId,
                              )
        else:
            raise (FrameworkError(SystemConfig.ERR_RUN_MODE,
                                  'Failed : unknown system configuration run mode : %s' %
                                  self.runMode))
        return deviceConfig
