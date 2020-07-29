import logging

from atf.framework.FrameworkBase import *
from ProxySystem import *

class ProductPackage (FrameworkBase):
    r"""
    This interface provides a mechanism for preparing complete SUT product 
    packages in a workspace. The intention is to keep packaging details out 
    of the ProxySUT concrete classes that make use of them since packaging 
    format can change over time and between different products.  The key driver
    for this has been the PXE packaging approach within MESA which is already 
    different to preceding ISS products.
    """
        
    def __init__(self, systemConfig, pkgType, diagLevel=logging.WARNING):
        r"""
        Save the pkgFile location and pkgType, and initialise logging.

        @param systemConfig:
            A framework SystemConfig object pkgType. 
            One of:
                - L{DeviceConfig.IMAGE_ISO}
                - L{DeviceConfig.IMAGE_PXE}
                - L{DeviceConfig.IMAGE_USB}
                - L{DeviceConfig.IMAGE_LIVE}   
        """
        FrameworkBase.__init__(self, diagLevel)
        self.type = pkgType
        self.systemConfig = systemConfig
        self.pkgFile = systemConfig.systemImages[pkgType]
        self.productRoot = None
        
    def prepare(self, workspace):
        r"""
        Prepare our package for use in the workspace location provided.
        This may require creating directory structures and permission/file
        munging within the workspace for PXE type installations or it may 
        simply be a copy of a bootable installation image into the workspace.  
        Return the root location name of the prepared package within the 
        workspace.

        @param workspace:
            A Common.workspace derived class which provides the location 
            to unpack the package
            
        @return:
            The root directory path to the unpacked package.
        """
        raise (NotImplementedError())


class BootablePackage (ProductPackage):
    r"""
    This provides a simple implementation for product packages that are a 
    bootable image. At the moment this would include USB, ISO and LIVE 
    packaging.
    """

    def __init__(self, systemConfig, pkgType, diagLevel=logging.WARNING):
        r"""
        Everything is handled by the base class for construction. 
        
        @param systemConfig:
            A framework SystemConfig object pkgType.
            One of: 
                - L{DeviceConfig.IMAGE_ISO}
                - L{DeviceConfig.IMAGE_USB}
                - L{DeviceConfig.IMAGE_LIVE}     
        """
        ProductPackage.__init__(self, systemConfig=systemConfig, pkgType=pkgType, 
                       diagLevel=diagLevel)
        
    def prepare(self, workspace):
        r"""
        Refer ProductPackage base class for a description of this interface 
        method.

        @param workspace:
            A Common.workspace derived class which provides the location 
            to unpack the package
        
        @return:
            The root directory path to the unpacked package.
        """        
        # Simply copy our package file into the toplevel of the workspace.

        ###
        # If pkg is an installed image, we symLink to it instead of making a copy
        # Doing this, we can keep changes made to the image between different ATF invocations
        # Only an installed image contains partition 2
        ###
        if( int( os.system('file -L %s | grep "partition 2"' % self.pkgFile) ) == 0 ): 
            self.productRoot = workspace.symLinkFile(filename=self.pkgFile)
        else:                   
            self.productRoot = workspace.copyFile(filename=self.pkgFile)

        return (self.productRoot)
        

class ProxySUT (ProxySystem):
    r"""
    The ProxySUT class extends the L{ProxySystem} interface to include methods
    that must be implemented by proxies of Systems Under Test.
    """

    ###
    # Define defaults for common expect patterns and timeouts
    ###
    (BOOT_TIMEOUT)          = 60 * RunConfig.TIMEOUT_MULTIPLIER

    def __init__(self, sutConfig=None, diagLevel=logging.WARNING):
        r"""
        Save config and diagnostics output details

        @param sutConfig:
            A pre-constructed L{SystemConfig} object

        @param diagLevel:
            What debug level to run this object in.    
        """
        ProxySystem.__init__(self, sutConfig, diagLevel)

    def install(self):
        r"""
        Perform a clean installation of the image starting with 
        a format of the disk media. The intention is to ensure that there
        can be no old artifacts remaining before the installation begins.
        On entry the System must be in the L{ProxySystem.STATE_CLI_PROMPT}
        or L{ProxySystem.STATE_STARTING}. If in L{ProxySystem.STATE_CLI_PROMPT}
        then a local media install will be attempted. If in 
        L{ProxySystem.STATE_STARTING} a network installation will be attempted.
        After an installation has completed the system will be restarted from
        the installed system disk and returned in the 
        L{ProxySystem.STATE_STARTING}.
        
        WARNING :  This method is NOT a complete test of installation procedures
        for a product. It is rather a helper to simplify setup for general 
        test running.  It is expected that complete installation tests WILL 
        BE written as this method will not verify every single output during
        installation. Indeed this method may ignore errors that don't 
        prevent a successful installation.

        @return:
            None, exceptions raised must be derived from L{FrameworkError}
        """
        raise (NotImplementedError())


    def networkInstall(self):
        r"""
        Perform a network installation.
        On entry the System must be in the L{ProxySystem.STATE_STARTING}. 
        On exit, the install will have completed and will still be in the 
        L{ProxySystem.STATE_STARTING}.

        @return:
            None, exceptions raised must be derived from L{FrameworkError}
        """
        raise (NotImplementedError())
        
    def reinstall(self):
        r"""
        Perform a complete and clean re-installation of the image. Will 
        reformat the disk and may install to an alternate partition.

        @return:
            None, exceptions raised must be derived from L{FrameworkError}
        """
        raise (NotImplementedError())

    def upgrade(self):
        r"""
        Perform an upgrade of the image. Will NOT reformat
        the disk and may install to an alternate partition.

        @return:
            None, exceptions raised must be derived from L{FrameworkError}
        """
        raise (NotImplementedError())


