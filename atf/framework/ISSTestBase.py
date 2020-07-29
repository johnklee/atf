#!/usr/bin/python
import imp
import types
import os
import sys
import time
import traceback
import datetime
from socket import socket

from atf.common.Common import *
from atf.framework.RunConfig import *
from atf.framework.FrameworkBase import *
from atf.framework.device.ProxyDevice import *
from atf.framework.device.ProxyEmulator import *
from atf.framework.device.ProxyQemu import *
from atf.framework.device.ProxyVMware import *
from atf.framework.device.ProxyHardware import *
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

from atf.framework.system.ProxySystem import *
from atf.framework.system.ProxySUT import *
from atf.framework.system.ProxyLinuxTSS import *
from atf.framework.system.ProxyWindows2k8TSS import *

#from atf.common.pcapreplay.PcapReplayInfo import *
#from atf.common.pcapreplay.PcapReplay import *
#from atf.common.pcapreplay.flow.Flow import *

from atf.data.images.TSSImageInfo import *

from atf.common.report.DocStringParser import *
from atf.common.report.TestReport import *
from atf.common.report.TestResult import *
from atf.common.report.TestReportGenerator import *

class ISSTestSuite(CommonTestSuite):
    SuiteCount = 0
    r'''
    ref count of created suites
    '''
    
    r"""
    Provide ISS specific test suite setUp and tearDown processing.
    """
    def __init__(self, tests=()):
        CommonTestSuite.__init__(self, tests=tests)

        self.tornDown = False
        """flag to indicate if our tearDown has been called."""
        
        # technically this should be in __init__ and paired with __del__ 
        # but __del__ is known to be unsafe in that you never know when 
        # (or if) it will be called
        #
        # instead we track the SuiteCount in __init__/tearDown pairs
        ISSTestSuite.SuiteCount += 1
        
    def __del__(self):
        # to be sure
        self.tearDown(None)

        if ISSTestSuite.SuiteCount <= 0:
            # make sure we don't have any references to workspaces
            # TODO: there should be a cleaner solution to cleaning up the 
            # workspaces. see defect 30692.
            for system in ISSTestBase.SavedSystems:
                if ISSTestBase.SavedSystems[system] is not None:
                    ISSTestBase.SavedSystems[system].device.config.workspace = None
                    ISSTestBase.SavedSystems[system].device.workspace = None
                    ISSTestBase.SavedSystems[system].device = None

        # Call __del__ on our parent
        CommonTestSuite.__del__(self)

    def setUp(self):
        # first let the base class setUp()
        CommonTestSuite.setUp(self)

        if os.environ.get('ATF_REPORT_DIR', '') != '':
            # Save information about a TestSuite run in a Report object
            description, metaTags = parseDocString(self._testSuiteDoc)
            
            self.testSuiteReport = TestSuiteReport()
            self.testSuiteReport.path            = self._testSuiteFile   or ""
            self.testSuiteReport.name            = self._testSuiteName   or ""
            self.testSuiteReport.rawDocString    = self._testSuiteDoc    or ""
            self.testSuiteReport.description     = description           or ""
            self.testSuiteReport.metaTags        = metaTags              or []
        else:
            # no reporting
            self.testSuiteReport = None

    def tearDown(self, result):

        if (not self.tornDown):

            # get ATF report file path from env variable
            reportDir = os.environ.get('ATF_REPORT_DIR', '')

            # get ATF loglevel from environment variable
            diagLevel = int(os.environ.get('ATF_LOG_LEVEL', '10'))

            # technically this should be in __del__ but __del__ is known to
            # be unsafe in that you never know when (or if) it will be called
            #
            # instead we track the SuiteCount in __init__/tearDown pairs
            ISSTestSuite.SuiteCount -= 1
            if ISSTestSuite.SuiteCount <= 0:
                # Making sure that at the end of all tests the
                # Persistent Workspaces get a chance to cleanup system
                # resources before we exit through the Workspace destructor(s).
                ISSTestBase.SavedWorkspaces = {}
        
                # Making sure that at the end of all tests the
                # Persistent Systems get a chance to cleanup system
                # resources before we exit through the ProxySystem destructor(s).
                # Make sure the SUT is the last to be cleaned up. This is so that
                # if the run mode is cloudstack, the networks created are cleaned
                # up properly
                sut = None
                if ISSTestBase.SavedSystems.has_key('sut'):
                    sut = ISSTestBase.SavedSystems['sut']
                    del ISSTestBase.SavedSystems['sut']
                ISSTestBase.SavedSystems = {}
                sut = None

            # now let the base class tearDown
            CommonTestSuite.tearDown(self, result)

            self.tornDown = True

            if reportDir != '':

                # For future extension, more suites can be added to this list
                # and the rest of the report generation code will still work.
                testSuiteReports = []
                
                # get reports from tests that ran in a test suite
                for test in self._tests:
                    if hasattr(test, 'testReport'):
                        if isinstance(test.testReport.result, TestResult) and result != None:
                            # the test never reached tearDown() to report the
                            # result - see if we can get more information from
                            # the pyunit result object
                            for testCase,error in result.errors:
                                if testCase._testMethodName == test._testMethodName:
                                    test.testReport.setResult(TestResultError(error=error))

                        self.testSuiteReport.addTestReport(test.testReport)

                # generate reports for all tests that didn't run in a test suite
                for test in self._disabledTests:
                    # Save information about a TestSuite run in a Report object
                    description, metaTags = parseDocString(test._testMethodDoc)
                    
                    testReport = TestReport()
                    testReport.name            = test._testMethodName   or ""
                    testReport.rawDocString    = test._testMethodDoc    or ""
                    testReport.description     = description            or ""
                    testReport.metaTags        = metaTags               or []

                    if hasattr(getattr(test, testReport.name), 'disabledText'):
                        disabledText =  getattr(test, testReport.name).disabledText
                    else:
                        disabledText = ''

                    testReport.result = TestResultDisabled(reason=disabledText)
                    self.testSuiteReport.addTestReport(testReport)

                # set suite result (and this sets suite endTime)
                self.testSuiteReport.calcSuiteResult()

                testSuiteReports.append(self.testSuiteReport)

                reportGenerator = TestReportGenerator(diagLevel=diagLevel)
                reportGenerator.generate(reportDir + "test_report.xml", testSuiteReports)


class ISSTestBase(CommonTestCase):
    r"""
    ISSTestBase provides access to the SUT and TSS proxies. It also contains
    common features like the ability to play from a captured
    file through a named interface on a SUT. This class is expected to grow
    as more common test capabilities are uncovered over time and refactor
    up from derived TestFeatureY modules.
    """

    # class to use when constructing a suite in _suite()
    SuiteClass = ISSTestSuite

    #
    # Class error definitions
    #
    # Failed during capture replay
    (ERR_CAP_REPLAY) = FrameworkError.ERR_TEST
    """An error occurred during capture replay"""
    (ERR_SUT_TYPE) = FrameworkError.ERR_TEST + 1
    """An error occurred that is related to SUT TYPE"""
    (ERR_TSS_TYPE) = FrameworkError.ERR_TEST + 2
    """An error occurred that is related to TSS TYPE"""
    (ERR_INVALID_IMAGE) = FrameworkError.ERR_TEST + 3
    """An error occurred due to an invalid image"""
    (ERR_RUN_MODE) = FrameworkError.ERR_TEST + 4
    """An error occurred due to an invalid run mode"""
    (ERR_SYSTEM_REGISTRATION) = FrameworkError.ERR_TEST + 5
    """An error occurred during system registration."""
    (ERR_SYSTEM_STARTUP) = FrameworkError.ERR_TEST + 6
    """An error occurred during system startup."""

    # Define supported system name
    (TSS_CLIENT_NAME) = 'client'
    (TSS_ROUTE_NAME) = 'router'
    (TSS_SERVER_NAME) = 'server'
    (SUT_NAME) = 'sut'

    #
    # Define the types of Systems we can create for testing
    #
    # The definition number space is partitioned to allow ease of
    # category detection
    #
    (MASK_ROLE) = 0x8000
    """A bit mask for the role of a system type."""
    (ROLE_SUT) = 0x0000
    """System under Test category."""
    (ROLE_TSS) = 0x8000
    """Test Support System category."""

    (MASK_PLATFORM) = 0x7fff
    """A bit mask for the platform of a system type."""
    (PLATFORM_MESA) = 0x0001
    """MESA Platform."""
    (PLATFORM_ISWG) = 0x0002
    """ISWG Platform."""
    (PLATFORM_ALPS) = 0x0003
    """ALPS Platform."""
    (PLATFORM_LINUX) = 0x4000
    """Generic Linux Platform."""
    (PLATFORM_XP) = 0x4001
    """Generic Win XP platform."""
    (PLATFORM_2K8) = 0x4003
    """Generic Win 2K8 platform."""
    (PLATFORM_TEST) = 0x7fff
    """Generic Test platform."""

    (SYSTEM_TYPE_MESA_SUT) = (PLATFORM_MESA | ROLE_SUT)
    """Modular Extensible Security Architecture SUT."""
    (SYSTEM_TYPE_ISWG_SUT) = (PLATFORM_ISWG | ROLE_SUT)
    """Secure Web Gateway SUT."""
    (SYSTEM_TYPE_ALPS_SUT) = (PLATFORM_ALPS | ROLE_SUT)
    """Appliance Layered Platform Services SUT."""
    (SYSTEM_TYPE_LINUX_TSS) = (PLATFORM_LINUX | ROLE_TSS)
    """Generic Linux Test Support System."""
    (SYSTEM_TYPE_XP_TSS) = (PLATFORM_XP | ROLE_TSS)
    """Windows XP Test Support System."""
    (SYSTEM_TYPE_2K8_TSS) = (PLATFORM_2K8 | ROLE_TSS)
    """Windows Server 2008 Test Support System."""

    # Test Systems
    (SYSTEM_TYPE_TEST_SUT) = (PLATFORM_TEST | ROLE_SUT)
    """Generic System Under Test."""
    (SYSTEM_TYPE_TEST_TSS) = (PLATFORM_TEST | ROLE_TSS)
    """Generic Test Support System."""

    #
    # Define supported System cacheing facilities/levels.
    #
    # The default behavior is that between test case executions, all System
    # objects are destroyed. This means that the System is at least powered off,
    # and depending on the nature of the System, it could mean that the system
    # is completely destroyed (e.g. an emulated SUT system).
    #
    # At the discretion of the test writer, if it is safe to do so, it is
    # possible to cache the workspace over test case executions to avoid the cost
    # of SUT installation between test casees. This is achieved by calling
    # saveWorkspace and poserOnSavedWorkspace.
    #
    # It is also possible, again if safe, to cache the system state
    # (e.g. powered On, logged in, e.t.c) between test cases.
    #
    # Enabling auto cacheing by setting the self.nableCache attribute will
    # result in automatic calls to saveWorkspace/saveSystemState. The test
    # writer is still responsible for calling powerOnWorkspace/restoreSystemState
    # as appropriate.
    #
    (DISABLE_CACHE) = 0
    """no automatic cacheing at createSystem time."""
    (ENABLE_WORKSPACE_CACHE) = 1
    """automatically activate workspace cache at createSystem time."""
    (ENABLE_SYSTEM_STATE_CACHE) = 2
    """automatically activate systemState cache at createSystem time."""

    SavedWorkspaces = {}
    """
    Define somewhere to store persistent workspaces between test
    cases for each system. This will be a dictionary indexed by test
    system name with values which are Common.Workspace objects.
    When the ISSTestSuite has run the last test, this dictionary is emptied
    so that the workspace(s) can be cleaned up.
    """

    SavedSystems = {}
    """
    Define somewhere to store persistent systems between test
    cases. This will be a dictionary indexed by system name with
    values which are ProxySystem objects.
    When the ISSTestSuite has run the last test, this dictionary is emptied
    so that the system(s) can be cleaned up.
    """

    RegisteredSystems = {
        SYSTEM_TYPE_LINUX_TSS: (ProxyLinuxTSS, TSSConfig),
        SYSTEM_TYPE_2K8_TSS: (ProxyWindows2k8TSS, TSSConfig)
    }
    """
    This dictionary is a registery of all known types that may be used in the
    creation of a System. Keyed to these types is a tuple that contains
    the system class and its configuration.
    """

    def __init__(self, methodName='runTest', diagLevel=None):
        r"""
        Constructor - set default attribute values
        """
        CommonTestCase.__init__(self, methodName=methodName, diagLevel=diagLevel)

        self.system = {}
        """collection of L{ProxySystem} objects being used for testing."""

        self.enableCache = ISSTestBase.DISABLE_CACHE
        """indication of automatic cacheing."""

        self.runConfig = None
        """The RunConfig instance associated with this test suite."""

        self.enableTestcaseTiming = int(os.environ.get('ATF_TESTCASE_TIMING', 0))
        """ This variable indicates whether per-testcase timing should be
            enabled. """

        self.testcaseStartTime = 0
        """ This variable is used by the testcase timing instrumentation to
            calculate duration. """

    def setUp(self):
        r"""
        Do common test fixture setup. This follows the standard python unittest
        pattern.
        """
        # Create empty System dictionary
        self.system = {}

        # Create empty list for added dict keys
        self.dictKeys = []

        # List all available installable image types
        self.installImageTypes = [DeviceConfig.IMAGE_USB,
                                  DeviceConfig.IMAGE_ISO,
                                  DeviceConfig.IMAGE_PXE,
                                  DeviceConfig.IMAGE_VHD]

        # Get the name of the runConfig to be loaded and import appropriately
        self.runConfig = None
        self.runConfigName = os.environ.get('ATF_CONFIG', '')
        if ((self.runConfigName != '') and
            os.path.exists(self.runConfigName) == True):
            module = imp.load_source('', self.runConfigName)
            self.runConfig = module.getRunConfig()
        
        # os.environ.get('ATF_DOCKER_IMG_PATH')    
        self.runModeSetting = eval(os.environ.get('ATF_DOCKER_IMG_PATH', 'None'))
        if self.runModeSetting:
            for k,v in self.runModeSetting.iteritems():
                if self.runConfig.systemConfigs.has_key(k):
                    sysConfig = self.runConfig.systemConfigs[k]
                else:
                    sysConfig = SystemConfig()
                    self.runConfig.systemConfigs[k] = sysConfig

                if v.upper() == 'QEMU':
                   sysConfig.runMode=SystemConfig.RUN_MODE_QEMU
                else:
                   sysConfig.runMode=SystemConfig.RUN_MODE_DOCKER
        

        if os.environ.get('ATF_REPORT_DIR', '') != '':
            # Save information about a test run in a Report object
            description, metaTags = parseDocString(self._testMethodDoc)
            
            self.testReport = TestReport()
            self.testReport.name            = self._testMethodName
            self.testReport.rawDocString    = self._testMethodDoc or ""
            self.testReport.description     = description or ""
            self.testReport.metaTags        = metaTags or []
        else:
            # no reporting
            self.testReport = None

        # If timing instrumentation is enabled, mark start time
        if (self.enableTestcaseTiming == 1):
            self.testcaseStartTime = time.time()

    def tearDown(self):
        r"""
        Do common test fixture tearDown. This follows the standard python
        unittest pattern.
        """
        self.system = {}
        for key in self.dictKeys:
            self.__dict__[key] = None
        self.dictKeys = []

        # default run time
        runTime = None

        # Timing complete; print time to stdout for the format
        # <testcase name> ... (Ran in Xs) ok
        excTuple = sys.exc_info()

        if (self.enableTestcaseTiming == 1 and excTuple == (None, None, None)):
            finalTime = time.time()
            runTime = finalTime - self.testcaseStartTime
            sys.stdout.write(' (Ran in %.5fs) ' % runTime)
            sys.stdout.flush()
        self.testcaseStartTime = 0

        # Save test result
        if self.testReport != None:
            if (excTuple[0] == None):
                self.testReport.setResult(TestResultPass())
            else:
                self.testReport.setResult(TestResultFail(error=traceback.format_exc(sys.exc_info())))

    def createSystem(self, name, systemType, systemConfig=None, diagLevel=None):
        r"""
        Create a new L{ProxySystem} object based on our run configuration.
        Store the object in our L{system} array.

        @param name:
            unique name of the system (used as dictionary keys)

        @param systemType:
            type as defined in L{ProxySystem}. Only supported/defined types
            can be created.

        @param systemConfig:
            L{SystemConfig} object to assign to the system.
            If None provided then a default is created.

        @param diagLevel:
            logging level for the new system.

        @return:
            newly created L{ProxySystem} object.
        """

        # Set runConfig appropriately
        if (systemConfig == None):
            systemConfig = SystemConfig()

        if (diagLevel == None):
            diagLevel = systemConfig.diagLevel

        # Construct the appropriate device and system configurations for
        # the run mode and sutType we are working with.
        if (ISSTestBase.systemIsRegistered(systemType) == True):
            systemClasses = ISSTestBase.RegisteredSystems[systemType]

            # Create the system config
            config = systemClasses[1](systemConfig=systemConfig,
                                      deviceConfig=systemConfig.createDeviceConfig())

            # Now create the system itself
            self.system[name] = systemClasses[0](config,
                                                 diagLevel=diagLevel)
        else:
            # If the system type has not been registered with the
            # framework for use, raise an exception
            raise(FrameworkError(ISSTestBase.ERR_SUT_TYPE,
                                 'Failed : system type not registered : %s'
                                 % systemType))

        # if automatic cacheing is enabled, then act upon it
        if (self.enableCache == ISSTestBase.ENABLE_WORKSPACE_CACHE):
            # to cache the workspace, we first have to create it.
            #
            # Workspace creation is based on the runMode

            # convenience accessors
            mySystem = self.system[name]
            myConfig = mySystem.systemConfig

            # above we should have set the systemConfig and the deviceConfig
            # this means that we can create the workspace for the device
            # to use and cache it right now - as opposed to waiting for
            # it to be created when the system is powered On (which in turn
            # starts the device).
            if (myConfig != None and myConfig.deviceConfig != None):
                # check to see if the workspace is already cached, and if so
                # then restore it
                if (name in ISSTestBase.SavedWorkspaces):
                    myConfig.deviceConfig.workspace = ISSTestBase.SavedWorkspaces[name]

                # create the workspace if it does not already exist
                #
                # It will exist for example in the case of emuForceSystemDisk
                # being set before a call to createSystem
                if (myConfig.deviceConfig.workspace == None):
                    workspace = None
                    if (myConfig.runMode == SystemConfig.RUN_MODE_QEMU):
                        workspace = QemuWorkspace(useTmpfs=myConfig.emuUseTmpfs,
                                                  diagLevel=diagLevel)
                        self.logger.debug('Created temporary workspace : %s' % workspace.workDir)
                        workspace.createDisk(name='system.img', size=myConfig.emuDiskSize)
                        if (myConfig.qemuUSB == True):
                            if (myConfig.qemuForceUSBImage == None):
                                workspace.createUSB(name='usb.img', size=myConfig.qemuUSBSize)
                            else:
                                workspace.setUSB(name=myConfig.qemuForceUSBImage)
                    elif (myConfig.runMode == SystemConfig.RUN_MODE_DOCKER):
                        workspace = DockerWorkspace(useTmpfs=myConfig.emuUseTmpfs,
                                                    diagLevel=diagLevel) 
                    elif (myConfig.runMode == SystemConfig.RUN_MODE_VMWARE):
                        workspace = VMwareWorkspace(useTmpfs=myConfig.emuUseTmpfs,
                                                    diagLevel=diagLevel)
                        self.logger.debug('Created temporary workspace : %s' % workspace.workDir)
                        workspace.createDisk(name='system.img', size=myConfig.emuDiskSize)
                    elif (myConfig.runMode == SystemConfig.RUN_MODE_VMWARE_ESX):
                        workspace = VMwareWorkspace(vmfsPath=myConfig.vmwareESXVMFS,
                                                    useTmpfs=myConfig.emuUseTmpfs,
                                                    diagLevel=diagLevel)
                        self.logger.debug('Created temporary workspace : %s' % workspace.workDir)
                        workspace.createDisk(name='system.img', size=myConfig.emuDiskSize)
                    elif (myConfig.runMode == SystemConfig.RUN_MODE_GX4004):
                        workspace = HardwareWorkspace(diagLevel=diagLevel)
                        self.logger.debug('Created temporary workspace : %s' % workspace.workDir)
                    elif (myConfig.runMode == SystemConfig.RUN_MODE_MX1004):
                        workspace = HardwareWorkspace(diagLevel=diagLevel)
                        self.logger.debug('Created temporary workspace : %s' % workspace.workDir)
                    elif (myConfig.runMode == SystemConfig.RUN_MODE_FWA6501):
                        workspace = HardwareWorkspace(diagLevel=diagLevel)
                        self.logger.debug('Created temporary workspace : %s' % workspace.workDir)
                    elif (myConfig.runMode == SystemConfig.RUN_MODE_FWA3210_ES0):
                        workspace = HardwareWorkspace(diagLevel=diagLevel)
                        self.logger.debug('Created temporary workspace : %s' % workspace.workDir)
                    elif (myConfig.runMode == SystemConfig.RUN_MODE_FWA3210_ES1):
                        workspace = HardwareWorkspace(diagLevel=diagLevel)
                        self.logger.debug('Created temporary workspace : %s' % workspace.workDir)
                    elif (myConfig.runMode == SystemConfig.RUN_MODE_FWA3211_ES):
                        workspace = HardwareWorkspace(diagLevel=diagLevel)
                    elif (myConfig.runMode == SystemConfig.RUN_MODE_XGS3100):
                        workspace = HardwareWorkspace(diagLevel=diagLevel)
                    elif (myConfig.runMode == SystemConfig.RUN_MODE_XGS4100):
                        workspace = HardwareWorkspace(diagLevel=diagLevel)
                    elif (myConfig.runMode == SystemConfig.RUN_MODE_CLOUDSTACK):
                        workspace = CloudWorkspace(diagLevel=diagLevel)
                    else:
                        raise (FrameworkError(ISSTestBase.ERR_RUN_MODE,
                                              'Failed : unknown system configuration run mode : %s' %
                                              myConfig.runMode))

                    # set the workspace in the device config so that it is
                    # used later when the device is started
                    myConfig.deviceConfig.workspace = workspace

                # now cache the workspace
                self.saveWorkspace(name, myConfig.deviceConfig.workspace)

        elif (self.enableCache == ISSTestBase.ENABLE_SYSTEM_STATE_CACHE):
            # cache the newly created system
            self.saveSystemState(name)

        else:
            # no automatic cacheing
            pass

        return self.system[name]

    def saveWorkspace(self, systemName, workspace):
        r"""
        Save the passed workspace in the global SavedWorkspaces dictionary
        so that later tests can use the same workspace. These will
        automatically get the chance to destruct at the end of all tests
        in a suite through ISSTestSuite.tearDown()

        @param systemName:
            Name to associate the saved workspace with

        @param workspace:
            The L{Workspace} to be saved
        """
        ISSTestBase.SavedWorkspaces[systemName] = workspace

    def powerOnSavedWorkspace(self, systemName, systemType,
                              timeout=ProxySUT.BOOT_TIMEOUT,
                              packageType=None):
        r"""
        This is a helper routing to powerOn a System using a
        ISSTestBase.SavedWorkspace that was previously created.

        Perform Device start and make sure the System comes up into a valid
        L{ProxySystem.STATE_STARTING}.

        @param systemName:
            The name associated with the workspace to be powered on

        @param systemType:
            The type of the system with which to start the workspace will be
            associated.

        @param timeout:
            The timeout associated with the booting procedure of the
            saved workspace.

        @param packageType:
            The package that will be used in the boot of the saved
            workspace.
        """
        self.createSystem(name=systemName,
                          systemConfig=self.runConfig.systemConfigs[systemName],
                          systemType=systemType)
        self.assertEqual(self.system[systemName].state,
                         ProxySystem.STATE_INITIALISED,
                         'Failed with unexpected system state of %s' %
                         self.system[systemName].state)
        self.system[systemName].systemConfig.deviceConfig.workspace = \
            ISSTestBase.SavedWorkspaces[systemName]

        self.system[systemName].powerOn(packageType=packageType)
        self.assertEqual(self.system[systemName].state,
                         ProxySystem.STATE_STARTING,
                         'Failed with unexpected system state of %s' %
                         self.system[systemName].state)

    def saveSystemState(self, systemName):
        r"""
        Save the specified system in the global SavedSystems dictionary
        so that later tests can use the same system. These will
        automatically get the chance to destruct at the end of all tests
        in a suite through ISSTestSuite.tearDown()

        @param systemName:
            The name to associate the saved system with
        """
        ISSTestBase.SavedSystems[systemName] = self.system[systemName]

    def restoreSystemState(self, systemName):
        r"""
        This is a helper routing to restore a cached system from the
        ISSTestBase.SavedSystem cache to the working self.system collection.

        @param systemName:
            The name associated with the system to be restored
        """
        self.system[systemName] = ISSTestBase.SavedSystems[systemName]

    def runSUT(self, systemName, systemType, packageType):
        r"""
        Utility function to handle the creation, installation and starting
        of a System Under Test.

        @param systemName:
            Unique name of the SUT.

        @param systemType:
            The type of the SUT to be run.

        @param packageType:
            Installation image type as defined in L{DeviceConfig}.
        """
        # ease of use reference :)
        myConfig = self.runConfig.systemConfigs[systemName]

        if (systemName in ISSTestBase.SavedSystems):
            # we have a saved system, just restore it
            self.restoreSystemState(systemName)
        elif (systemName in ISSTestBase.SavedWorkspaces):
            # we have a saved workspace, power it on
            self.powerOnSavedWorkspace(systemName, systemType)
        else:
            # no saved workspace, create one
            createDisk = True

            # create our system
            #
            # Note that self.enableCache will determine what level of automatic
            # cacheing will occur.
            self.createSystem(systemName, systemType, myConfig)
            atf_sut_exists = int(os.environ.get('ATF_SUT_EXISTS', '0') ) 
            if(atf_sut_exists == True):
                if not (str(self.__class__).find('Interact_Test') != -1 and 
                        self._testMethodName.find('_interact') != -1):
                    os.system("bash -c \"kill -10 $(pstree -Aclp | grep 'make.*python'  | grep -o  'python([0-9]\+).*emurun([0-9]\+).*dnsmasqrun([0-9]\+)' | grep -o 'python([0-9]\+)' | grep -o '[0-9]\+') \" ")

                sutIp = self.system[systemName].systemConfig.networks[sorted(self.system[systemName].systemConfig.networks)[0]].interfaces['eth0'].ip[0].address
                sshPort = 22
                attempts  = 5
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
                s.settimeout(1)
                while (attempts > 0):
                    try:
                        s.connect((sutIp, sshPort))
                        self.logger.debug('SUT SSH service connectivity verified.')
                        break
                    except error:
                        self.logger.warning('Unable to connect to TSS server SSH service.')
                        attempts -=1
                        continue
                s.close()
                if attempts <= 0:
                    raise(FrameworkError(ISSTestBase.ERR_SYSTEM_STARTUP, 'No standalone SUT exists or it is not SSH connectable'))

                self.system[systemName].device = ProxyQemu(emuConfig=self.system[systemName].systemConfig.deviceConfig,diagLevel=self.logger.getEffectiveLevel())
                self.system[systemName].state = ProxySystem.STATE_STARTING
                self.system[systemName].login(myConfig.adminUser, myConfig.adminPasswd)

            # if we created the disk image and have an install image, then
            # power on the system and do the installation
            elif (createDisk and not packageType == None and packageType != DeviceConfig.IMAGE_LIVE and int(os.environ.get('ATF_NO_INSTALL', '0')) != 1 ):
                self.system[systemName].powerOn(packageType=packageType)

                # since we are creating the appliance,
                # we first need to install it
                #
                # Note that for PXE there is no need to login first
                if (packageType != DeviceConfig.IMAGE_PXE):
                    self.system[systemName].login('admin',
                                                  myConfig.adminPasswd)

                self.system[systemName].install()

                # now we are back to STATE_STARTING, just after a powerOn

            # now power it up - being aware that we still need packageType for live
            if(atf_sut_exists == True):
                pass
            elif (packageType == DeviceConfig.IMAGE_LIVE):
                self.system[systemName].powerOn(packageType=packageType)
            elif (self.system[systemName].isOnable() == CommonError.ERR_OK):
                self.system[systemName].powerOn()

        # finally, create accessors for the system
        # for example self.sutSystem
        self.__dict__[systemName + "System"] = self.system[systemName]
        self.__dict__[systemName + "Config"] = self.runConfig.systemConfigs[systemName]
        self.dictKeys += [systemName + "System", systemName + "Config"]

    def runTSS(self, systemName, services=None):
        r"""
        Utility function to handle the starting of a L{ProxyTSS} Test Support System.

        @param systemName:
            Unique name of the TSS.
        """
        # ease of use reference :)
        myConfig = self.runConfig.systemConfigs[systemName]

        # find the path of our TSS image
        st_time = datetime.datetime.now()
        imagePath = ''
        imageInfo = None
        if (myConfig.emuForceSystemDisk != None):
            imagePath = myConfig.emuForceSystemDisk
        elif (myConfig.emuImageName != None):
            if (myConfig.runMode == SystemConfig.RUN_MODE_QEMU):
                imageInfo = TSSImageInfo.getImageInfo(myConfig.emuImageName,
                                                      'img',
                                                      imageRoot=myConfig.emuImageRoot)
            elif (myConfig.runMode == SystemConfig.RUN_MODE_VMWARE):
                imageInfo = TSSImageInfo.getImageInfo(myConfig.emuImageName,
                                                      'vmdk',
                                                      imageRoot=myConfig.emuImageRoot)
            elif (myConfig.runMode == SystemConfig.RUN_MODE_CLOUDSTACK):
                imageInfo = TSSImageInfo(imageDisk=None)
            elif (myConfig.runMode == SystemConfig.RUN_MODE_DOCKER):
                imageInfo = TSSImageInfo(imageDisk=None, services=services, systemType=systemName, rms=self.runModeSetting)
                myConfig.dockerImgInfo = imageInfo
            else:
                raise(FrameworkError(ISSTestBase.ERR_INVALID_IMAGE,
                                     'unsupported TSS run mode:%d'
                                     % myConfig.runMode))

            if ( (systemName.lower().find('server') >= 0 and os.environ.get('ATF_TSS_SERVER', None) == 'qemu') or (systemName.lower().find('client') >= 0 and os.environ.get('ATF_TSS_CLIENT', None) == 'qemu') or (systemName.lower().find('router') >= 0 and os.environ.get('ATF_TSS_ROUTER', None) == 'qemu') ):
                myConfig.runMode = SystemConfig.RUN_MODE_QEMU
                imageInfo = TSSImageInfo.getImageInfo(myConfig.emuImageName,
                                                      'img',
                                                      imageRoot=myConfig.emuImageRoot)
            elif ( (systemName.lower().find('server') >= 0 and os.environ.get('ATF_TSS_SERVER', None) == 'docker') or (systemName.lower().find('client') >= 0 and os.environ.get('ATF_TSS_CLIENT', None) == 'docker') or (systemName.lower().find('router') >= 0 and os.environ.get('ATF_TSS_ROUTER', None) == 'docker') ):
                myConfig.runMode = SystemConfig.RUN_MODE_DOCKER
                imageInfo = TSSImageInfo(imageDisk=None, services=services, systemType=systemName, rms=self.runModeSetting)
                myConfig.dockerImgInfo = imageInfo


            imagePath = imageInfo.imageDisk
        else:
            raise(FrameworkError(ISSTestBase.ERR_INVALID_IMAGE, 'unspecified TSS image'))

        # flag to tell us is we need to configure the system
        reconfigureSystem = True

        if (systemName in ISSTestBase.SavedSystems):
            # we have a saved system, just restore it
            self.restoreSystemState(systemName)
            reconfigureSystem = False
        elif (systemName in ISSTestBase.SavedWorkspaces):
            # we have a saved workspace, power it on
            self.powerOnSavedWorkspace(systemName, myConfig.emuImageType)
        else:
            # specify the server disk
            myConfig.emuForceSystemDisk = imagePath

            # create our system
            #
            # Note that self.enableCache will determine what level of automatic
            # cacheing will occur.
            self.createSystem(systemName, myConfig.emuImageType, myConfig)
            # now power it up
            self.system[systemName].powerOn()

        # ease of access
        mySystem = self.system[systemName]

        # if the system state was not cached, then we need to reconfigure it
        if (reconfigureSystem):
            # login so we can configure the system
            if imageInfo != None:
                loginUser = imageInfo.adminUser
                loginPasswd = imageInfo.adminPasswd
            else:
                loginUser = myConfig.adminUser
                loginPasswd = myConfig.adminPasswd

            mySystem.login(loginUser,
                           loginPasswd,
                           timeout=mySystem.BOOT_TIMEOUT)
            # check our interfaces, if any are static then set them
            if myConfig.networks != None and myConfig.runMode != SystemConfig.RUN_MODE_CLOUDSTACK:
                for (bridge, sysIFs) in myConfig.networks.items():
                    for (iname, iface) in sysIFs.interfaces.items():
                        if (iface != None):
                            for ip in iface.ip:
                                if (isinstance(ip, IPv4) and ip.type == 'static'):
                                    mySystem.setStaticIp(iname, ip.address)
                                # Set IPv6 address
                                if (isinstance(ip, IPv6) and ip.type == 'static'):
                                    mySystem.setStaticIp(iname, ip.address, prefixLength=ip.prefixLength)

            # check to see if we need to set a default gateway
            if (myConfig.defaultGatewayIp != None):
                mySystem.setDefaultGateway(myConfig.defaultGatewayIp.address)

            if (myConfig.defaultGatewayIpv6 != None):
                mySystem.setDefaultGatewayIpv6(myConfig.defaultGatewayIpv6.address)

            # check to see if we need to set a dns
            if (myConfig.dnsIp != None):
                mySystem.setDNS(myConfig.dnsIp.address)

            # check to see if we need to setup forwarding
            if (myConfig.forwarding != ''):
                forwardDetails = myConfig.forwarding.split('|')
                mySystem.enableForwarding(inInterface=forwardDetails[0],
                                          outInterface=forwardDetails[1])

            # set up our routing
            if (myConfig.routing != None):
                for (destIp, via) in myConfig.routing:
                    if (type(destIp) == IPv4):
                        if (type(via) == IPv4):
                            mySystem.addRoute(destIp.address, gateway=via.address)
                        else:
                            mySystem.addRoute(destIp.address, interface=via)
                    # Set up IPv6 route
                    if (type(destIp) == IPv6):
                        if (type(via) == IPv6):
                            mySystem.addRoute(destIp.address, gateway=via.address)
                        else:
                            mySystem.addRoute(destIp.address, interface=via)

            # Set up networks and routing for cloudstack
            if(self.runConfig.systemConfigs[systemName].runMode == SystemConfig.RUN_MODE_CLOUDSTACK):
                if systemName == 'server':
                    if self.runConfig.e0SutIp != None:
                        hisAddr = mySystem.getCidr(self.runConfig.clientTssIp)
                        self.system[systemName].executeCLICommand("ip route add %s via %s" % (str(hisAddr), str(self.runConfig.e0SutIp.address)))
                    if self.runConfig.serverTssIpv6 != None:
                        self.system[systemName].executeCLICommand("ip -6 addr add " + str(self.runConfig.serverTssIpv6.address) + "/" +str(self.runConfig.serverTssIpv6.prefixLength) + 
                                                                  " dev " +  self.runConfig.serverTssIf)
                        self.system[systemName].executeCLICommand("ip -6 route add %s via %s" % (self.runConfig.clientTssIpv6.address, self.runConfig.m2SutIpv6.address))
                if systemName == 'client':
                    if self.runConfig.e1SutIp != None:
                        hisAddr = mySystem.getCidr(self.runConfig.serverTssIp)
                        self.system[systemName].executeCLICommand("ip route add %s via %s" % (str(hisAddr), str(self.runConfig.e1SutIp.address)))
                    if self.runConfig.clientTssIpv6 != None:
                        self.system[systemName].executeCLICommand("ip -6 addr add " + str(self.runConfig.clientTssIpv6.address) + "/" + str(self.runConfig.clientTssIpv6.prefixLength) + 
                                                                  " dev " +  self.runConfig.clientTssIf)
                        self.system[systemName].executeCLICommand("ip -6 route add %s via %s" % (self.runConfig.serverTssIpv6.address, self.runConfig.m1SutIpv6.address))

            # leave our system in a known state - power on but not logged in
            mySystem.logout()

        # finally, create accessors for the system
        # for example self.sutSystem
        self.__dict__[systemName + "System"] = self.system[systemName]
        self.__dict__[systemName + "Config"] = self.runConfig.systemConfigs[systemName]
        self.dictKeys += [systemName + "System", systemName + "Config"]

    def runServices(self, systemName, services):
        """
        Start the provided services on the system if they are not already
        running.

        @param systemName:
            Name of the system to start the services on.

        @param services:
            List of service object constructors to auto-start.
            For Example: runServices('mySystem', services=[ProxyLinuxHttpdService]).
        """
        # see if we need to auto start some services
        if (services != None):
            mySystem = self.system[systemName]

            # login if we need to - remember if we need to logout
            doLogout = False
            if (mySystem.state != ProxySystem.STATE_CLI_PROMPT):
                mySystem.login('root', 'realsecure')
                doLogout = True

            # construct our services and start them if required
            for ctor in services:
                service = ctor(mySystem.shell)
                mySystem.services[service.name] = ctor
                if (service.status() != ProxyService.STATE_RUNNING):
                    service.start()

            # restore my system login state
            if (doLogout):
                mySystem.logout()

    def assertEqualsCLICommand(self, system, cmd, result=0, errMsg=None, cmdTimeout=None):
        """
        Call system.executeCLICommand(cmd) and assertEquals the return value against
        the specified result.

        @param system:
            The L{ProxySystem} instance on which a CLI command is to be executed

        @param cmd:
            The command that is to be executed.

        @param result:
            The result to be used to assertEquals the result of the command execution
            against.

        @param errMsg:
            The error message to be used on an assertion failure.

        @param cmdTimeout:
            The timeout associated with the CLI command execution.
        """
        cmdResult = system.executeCLICommand(cmd, cmdTimeout)
        assertMsg = '%s\n\nReturn Code: %d' % (errMsg, cmdResult) + \
            '\n\nLast Command Buffer Dump:\n' + \
            '----------------------------------------------\n%s' % \
            system.lastCmdOutput + \
            '\n----------------------------------------------\n'
        self.assertEquals(cmdResult, result, assertMsg)

    def assertNotEqualsCLICommand(self, system, cmd, result=0, errMsg=None, cmdTimeout=None):
        """
        Call system.executeCLICommand(cmd) and assertNotEquals the return value against
        the specified result.

        @param system:
            The L{ProxySystem} instance on which a CLI command is to be executed

        @param cmd:
            The command that is to be executed.

        @param result:
            The result to be used to assertNotEquals the result of the command execution
            against.

        @param errMsg:
            The error message to be used on an assertion failure.

        @param cmdTimeout:
            The timeout associated with the CLI command execution.
        """
        cmdResult = system.executeCLICommand(cmd, cmdTimeout)
        assertMsg = '%s\n\nReturn Code: %d' % (errMsg, cmdResult) + \
            '\n\nLast Command Buffer Dump:\n' + \
            '----------------------------------------------\n%s' % \
            system.lastCmdOutput + \
            '\n----------------------------------------------\n'
        self.assertNotEquals(cmdResult, result, assertMsg)

    def assertContains(self, pattern, str, errMsg=None, flags=re.MULTILINE):
        """
        Assert that the re pattern is in the specified string.

        @param pattern:
            The regex pattern to be searched for in the specified string.

        @param str:
            The string to perform a regex pattern search.

        @param errMsg:
            The error message to be used on an assertion failure.

        @param flags:
            The flags to use while performing the regex of the specified
            pattern against the specified string.

        @return:
            The re.search MatchObject upon success.
        """
        match = re.search(pattern, str, flags)
        assertMsg = '%s\n\nString Dump:\n' % errMsg + \
            '----------------------------------------------\n%s' % str + \
            '\n----------------------------------------------\n'
        self.assertNotEquals(match, None, assertMsg)
        return match

    def assertNotContains(self, pattern, str, errMsg=None, flags=re.MULTILINE):
        """
        Assert that the re pattern is not in the specified string.

        @param pattern:
            The regex pattern to be searched for in the specified string.

        @param str:
            The string to perform a regex pattern search.

        @param errMsg:
            The error message to be used on an assertion failure.

        @param flags:
            The flags to use while performing the regex of the specified
            pattern against the specified string.

        @return:
            The re.search MatchObject (None) upon success.
        """
        match = re.search(pattern, str, flags)
        assertMsg = '%s\n\nString Dump:\n' % errMsg + \
            '----------------------------------------------\n%s' % str + \
            '\n----------------------------------------------\n'
        self.assertEquals(match, None, assertMsg)
        return match

    @staticmethod
    def addSystem(systemType, systemClass, systemConfigClass):
        r"""
        Adds a System class and its configuration class keyed
        to a provided systemType enumeration. This method adds to
        a class dictionary and does not allow for overwriting
        on registration.

        @param systemType:
            An enumeration that is to be associated with the system
            class on registration

        @param systemClass:
            The class that is to be registered

        @param systemConfigClass:
            The configuration class that is to be registered

        @return:
            A boolean indicating the success of the registration
        """
        # Check the systemType has not already been registered
        if (ISSTestBase.RegisteredSystems.has_key(systemType)):
            return False

        # Check valid types are being passed in
        if ((type(systemClass) != types.ClassType and
             type(systemClass) != types.TypeType) or
            (type(systemConfigClass) != types.ClassType and
             type(systemConfigClass) != types.TypeType)):
            return False

        # make sure we are registering a recognised SUT
        if ((systemType & ISSTestBase.MASK_ROLE) == ISSTestBase.ROLE_SUT and
            systemType not in [ISSTestBase.SYSTEM_TYPE_MESA_SUT,
                               ISSTestBase.SYSTEM_TYPE_ISWG_SUT,
                               ISSTestBase.SYSTEM_TYPE_ALPS_SUT,
                               ISSTestBase.SYSTEM_TYPE_TEST_SUT]):
            return False

        # Add the key to the registery
        ISSTestBase.RegisteredSystems[systemType] = (systemClass,
                                                     systemConfigClass)
        return True

    @staticmethod
    def removeSystem(systemType):
        r"""
        Removes a System class and its configuration class
        associated with a nominated systemType enumeration. This method
        removes from the registration dictionary.

        @param systemType:
            An enumeration that is to be associated with the system class
            on registration

        @return:
            A boolean indicating the success of the unregistration
        """
        # Check the systemType has been registered
        if (ISSTestBase.RegisteredSystems.has_key(systemType) == False):
            return False

        # Remove the key from the registery
        del(ISSTestBase.RegisteredSystems[systemType])
        return True

    @staticmethod
    def systemIsRegistered(systemType):
        r"""
        Returns whether a systemType is currently associated with a
        System class and its configuration class.

        @param systemType:
            An enumeration that is to be associated with the system
            class on registration

        @return:
            A boolean indicating whether the systemType is registered
        """
        # Check the systemType has been registered
        return ISSTestBase.RegisteredSystems.has_key(systemType)

    @staticmethod
    def registerSystem(systemType, systemClass, systemConfigClass):
        r"""
        Registers a System class and its configuration class keyed
        to a provided systemType enumeration. This method adds to
        a class dictionary and does not allow for overwriting
        on registration.

        @param systemType:
            An enumeration that is to be associated with the system
            class on registration

        @param systemClass:
            The class that is to be registered

        @param systemConfigClass:
            The configuration class that is to be registered

        @return:
            A boolean indicating the success of the registration
        """
        if not ISSTestBase.systemIsRegistered(systemType):
            ret = ISSTestBase.addSystem(systemType, systemClass, systemConfigClass)
            if (ret == False):
                raise (FrameworkError(ISSTestBase.ERR_SYSTEM_REGISTRATION,
                       'Unable to register %s. Type in use or non-class objects used for registration.' % systemClass.__name__))
        else:
            regClasses = ISSTestBase.RegisteredSystems[systemType]
            if ((regClasses[0].__name__, regClasses[1].__name__) !=
                (systemClass.__name__, systemConfigClass.__name__)):
                raise (FrameworkError(ISSTestBase.ERR_SYSTEM_REGISTRATION,
                                      'Unable to register %s, type %d is in use' %
                      (systemClass.__name__, systemType)))

    @staticmethod
    def unregisterSystem(systemType):
        r"""
        Unregister a System class and its configuration class
        associated with a nominated systemType enumeration. This method
        removes from the registration dictionary.

        @param systemType:
            An enumeration that is to be associated with the system class
            on registration

        @return:
            A boolean indicating the success of the unregistration
        """
        return ISSTestBase.removeSystem(systemType)

    @staticmethod
    def printTestInfo():
        """
        Utility function which calls print to display test environment related
        information.
        """
        # print all ATF_ environment variables
        sys.stdout.write('Environment vars:\n')
        for (name, value) in os.environ.items():
            if (name.startswith('ATF_')):
                sys.stdout.write(name + '=' + value + '\n')

        # print doc string of the config module
        sys.stdout.write('\nRunConfig docstring:\n')
        runConfigName = os.environ.get('ATF_CONFIG', '')
        if ((runConfigName != '') and
            os.path.exists(runConfigName) == True):
            module = imp.load_source('', runConfigName)
            if (module.__doc__ != None):
                sys.stdout.write(module.__doc__)

        sys.stdout.flush()

    @staticmethod
    def _suite(kls, testList=[]):
        r"""
        A helper function for all inheriting classes. This method
        creates a list of enabled test methods via introspection and
        returns it, sorted.

        @param kls:
            The class that is to be introspected

        @param testList:
            list of test names to run. Run all if the list is empty.

        @return:
            A list of testcases.
        """
        ISSTestBase.printTestInfo()

        kls.testSuite = CommonTestCase._enabledTests(kls, testList=testList)
        its = kls.SuiteClass(map(kls, kls.testSuite))
        
        # copy the 'suite' documentation to the TestSuite for use in reporting
        its._testSuiteFile = os.path.abspath(inspect.getmodule(kls).__file__)
        its._testSuiteName = kls.__name__
        its._testSuiteDoc  =  kls.__doc__
        
        # sav disabled tests for reporting
        its._disabledTests = map(kls, CommonTestCase._disabledTests(kls, testList=testList))
        return its
