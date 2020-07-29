#
# This file contains basic test system classes that are used
# throughout as base classes and which are not specific to any one area
# of the python testing system.
#
import os
import stat
import logging
import coloredlogs
import tempfile
import subprocess
import unittest
import inspect
import re
import sys
import functools
import pdb
import signal
import time
import imp
import bdb
from time import sleep
from io import StringIO
from io import BytesIO
import socket as socketHelper

class ATFLogHandler(logging.StreamHandler):
    def __init__(self):
        logging.StreamHandler.__init__(self)

class singleton(type):
    r"""
    Singleton pattern metaclass.
    All classes that instantiate from this metaclass are singletons.
    """
    def __init__(cls, name, bases, dict):
        cls.__instance = None

    def __call__(cls, *args, **kw):
        if cls.__instance is None:
            cls.__instance = super(singleton, cls).__call__(*args, **kw)
        return cls.__instance

class staticproperty(property):
    r"""
    A decorator to define static variable in Python Class
    """
    def __get__(self, cls, owner):
        return classmethod(self.fget).__get__(None, owner)()

def pdbFixup(Pdb=pdb.Pdb):
    r"""make Pdb() tied to original stdout, this will allow to redirect std output to a file"""
    return Pdb(stdout=sys.__stdout__)


def decWithArgs(func):
    r"""
    Decorator to allow for the declaration of a decorator that has args
    """
    @functools.wraps(func)
    def wrapper(*args, **kw):
        if len(args) == 1 and len(kw) == 0 and inspect.isfunction(args[0]):
            return func(*args, **kw)

        def dFunc(wrappedFunc):
            return func(wrappedFunc, *args, **kw)
        return dFunc
    return wrapper


@decWithArgs
def enabletest(func, *args, **kw):
    r"""
    This function provides a decorator, @enabletest, that allows
    for the replay of a test within a given testsuite
    """
    func.enable = 1
    func.enableCondition = True
    func.disabledText = ""
    if len(args) >= 1:
        func.enableCondition = args[0]
        func.disabledText = "enable failed"
    if len(args) >= 2:
        func.disabledText = args[1]
    return func


class CommonBase(object):
    r"""
    This class provides the base functionality for all classes used
    in System testing. In particular it will provide the
    initialisation of the logging subsystem for each class.
    """

    def __init__(self, diagLevel=logging.ERROR):
        format = "%(levelname)s: <%(pathname)s#%(lineno)s> %(message)s"
        #"""define logger output format"""

        if 'ATF_LOG_LEVEL' in os.environ:
            try:
                diagLevel = int(os.environ.get('ATF_LOG_LEVEL', diagLevel))
            except:
                pass
        """The environment setting will override program setting"""

        self.diagLevel = diagLevel
        """set the diagLevel so that all parts of the code can share it"""

        logging.basicConfig(format=format)

        self.logger = logging.getLogger(str(self.__class__))
        """access to standard python L{logging} object."""

        self.logger.setLevel(level=diagLevel)
        self.logger.propagate = False
        coloredlogs.install(level=diagLevel, logger=self.logger, fmt=format)
        """ register coloredlogs """
        #try:
        #    import coloredlogs
        #    imp.find_module('coloredlogs')           
        #    coloredlogs.install(level=self.diagLevel, fmt=format, logger=self.logger)
        #except:            
        #    self.logger.setLevel(level=diagLevel)


    def breakpoint(self):
        r"""
        Drop into Python debug shell.
        """
        breakpoint = int(os.environ.get('ATF_BREAKPOINT', 0))
        if breakpoint and breakpoint == 1:
            try:
                pdb.Pdb(stdout=sys.stdout).set_trace(sys._getframe().f_back)
                # pdb.Pdb(stdout=sys.stdout).set_trace()
            except bdb.BdbQuit:
                pass
        else:
            self.logger.warning('Breakpoints are disabled')


class CommonError (Exception):
    r"""
    This class defines the categories of error codes
    that will exist to be used within exceptions so that unique values can
    be used to identify the generating component.
    """

    (ERR_OK) = 0x0
    """Universal, no error value."""
    (ERR_MISSING_FILE) = 0x1
    """Universal, file does not exist."""
    (ERR_INVALID_PARAM) = 0x2
    """Universal, invalid parameter/value provided."""

    # Component error categories defined elsewhere
    (ERR_COMMON) = 0x1000
    """Common class errors"""
    (ERR_TOOLS) = 0x2000
    """Tool errors"""
    (ERR_FRAMEWORK) = 0x4000
    """Test framework class errors"""

    def __init__(self, errCode, desc=None):
        self.errCode = errCode
        self.desc = desc

    def __str__(self):
        errorString = "Error : " + repr(self.errCode)

        if (self.desc != None):
            errorString += " : " + self.desc
        return (errorString)


class CommonTestCase(unittest.TestCase):
    r"""
    This class provides the base class for all test cases. Its function
    is to provide common functionality that allows for the support
    of the enabletest decorator
    """
    testSuite = []

    def __init__(self, methodName='runTest', diagLevel=None):
        r"""
        Construct and allocate logger
        """
        unittest.TestCase.__init__(self, methodName=methodName)

        # add a logger
        if (diagLevel == None):
            diagLevel = int(os.environ.get('ATF_LOG_LEVEL', logging.WARNING))

        format = "%(levelname)s: <%(pathname)s:%(lineno)s> %(message)s"
        """define logger output format"""
        logging.basicConfig(format=format)

        self.logger = logging.getLogger(str(self.__class__))
        """access to standard python L{logging} object."""

        self.logger.setLevel(level=diagLevel)

        try:
            import coloredlogs
            self.logger.propagate = False
            imp.find_module('coloredlogs')          
            fmt =  "<%(pathname)s:%(lineno)s> %(message)s"
            coloredlogs.install(level=diagLevel, logger=self.logger, fmt=fmt)
        except:
            self.logger.warn('Please install package coloredlogs to enable colorful output!')

    def breakpoint(self):
        r"""
        Drop into Python debug shell.
        """
        breakpoint = int(os.environ.get('ATF_BREAKPOINT', 0))
        if breakpoint and breakpoint == 1:
            try:
                pdb.Pdb(stdout=sys.stdout).set_trace(sys._getframe().f_back)
                # pdb.Pdb(stdout=sys.stdout).set_trace()
            except bdb.BdbQuit:
                pass
        else:
            self.logger.warning('Breakpoints are disabled')

    @staticmethod
    def _enabledTests(kls, testList=[]):
        r"""
        A helper function for all inheriting classes. This method
        creates a list of enabled test methods via introspection and
        returns it, sorted.

        @param kls:
            The class that is to be introspected

        @param testList:
            List of test names to run. Run all if the list is empty.

        @return:
            A list of tests.
        """
        tests = []
        atf_test_re = None
        if 'ATF_TEST_RE' in os.environ:
            atf_test_re = re.compile(os.environ['ATF_TEST_RE'])
        # Add all tests that match the provided patterns, and that are enabled.
        #
        # Note that if testList==[] then patt=='' and the re.match will always
        # match - which satisfy the idea that if testList==[] then all enabled
        # tests should be run
        sys.stdout.write('=================================================\n')
        sys.stdout.write('Disabled Tests:\n')
        disabledString = ''
        patt = '%s' % '|'.join(testList)
        for name, obj in inspect.getmembers(kls, inspect.ismethod):
            # a test is identified as having the enable attribute, which is
            # added by the enabletest declaration
            if hasattr(obj, 'enable'):
                enabled = (not re.match(patt, name) == None)
                if (enabled and obj.enableCondition == False):
                    disabledString += '%s ... %s\n' % (name, obj.disabledText)
                elif atf_test_re and not atf_test_re.match(name):
                    disabledString += '%s ... Mismatch from ATF_TEST_RE\n' % (name)
                elif (enabled):
                    tests.append(name)
                else:
                    disabledString += '%s ... not enabled\n' % name
        if disabledString == '':
            disabledString = 'None\n'
        disabledString += '=================================================\n\n'
        sys.stdout.write(disabledString)
        sys.stdout.flush()

        return sorted(tests)

    @staticmethod
    def _disabledTests(kls, testList=[]):
        r"""
        A helper function for all inheriting classes. This method
        creates a list of disabled test methods via introspection and
        returns it, sorted.

        @param kls:
            The class that is to be introspected

        @param testList:
            List of test names to run. Run all if the list is empty.

        @return:
            A list of tests.
        """
        tests = []

        # Add all tests that match the provided patterns, and that are enabled.
        #
        # Note that if testList==[] then patt=='' and the re.match will always
        # match - which satisfy the idea that if testList==[] then all enabled
        # tests should be run
        patt = '%s' % '|'.join(testList)
        for name, obj in inspect.getmembers(kls, inspect.ismethod):
            # a test is identified as having the enable attribute, which is
            # added by the enabletest declaration
            if hasattr(obj, 'enable'):
                enabled = (not re.match(patt, name) == None)
                if (not enabled or (enabled and obj.enableCondition == False)):
                    tests.append(name)
        return sorted(tests)

    @staticmethod
    def _suite(kls, testList=[]):
        r"""
        A helper function for all inheriting classes. This method
        creates a list of enabled testcases via introspection and
        returns it, sorted.

        @param kls:
            The class that is to be introspected

        @return:
            A list of testcases.
        """
        kls.testSuite = CommonTestCase._enabledTests(kls, testList=testList)
        return CommonTestSuite(map(kls, kls.testSuite))


class CommonTestSuite(unittest.TestSuite):
    r"""
    This class provides the concept of test suite setUp and tearDown stages.

    A suite is setUp() before any tests are run, then all the tests are run,
    and finally suite tearDown() is called.

    It overrides/hides the TestSuite.run method to achieve this.
    """
    def __init__(self, tests=()):
        # We need to override the constructor to set up a means
        # of flagging whether a test suite run should stop
        unittest.TestSuite.__init__(self, tests)
        self.stopExecution = False

    def __del__(self):
        # Note that as a concept we should call __del__ on our parent
        # however in this case the base of our hierarchy does not inherit
        # from object and does not define __del__, so the reality is that
        # we can not call our parent __del__ because it does not exist.
        #
        # So instead of calling del on our parent, we will do the processing
        # that our parent should do (because we do not want to change the
        # third party code)
        # unittest.TestSuite.__del__(self)
        self._tests = None

    def setUp(self):
        r"""
        Invoked before running all the tests in the suite.
        """
        pass

    def tearDown(self, result):
        r"""
        Invoked after running all the tests in the suite.
        
        @param result:
            The result instance updated during test execution.
        """
        pass

    def run(self, result):
        r"""
        Execute all the tests defined in this suite.

        Call setUp() before and tearDown() after running all tests.

        @param result:
            The result instance to be updated during test execution.
        """
        # Handle all 'standard' termination signals
        signal.signal(signal.SIGTERM, self.signalHandler)
        signal.signal(signal.SIGHUP, self.signalHandler)
        signal.signal(signal.SIGINT, self.signalHandler)
        signal.signal(signal.SIGQUIT, self.signalHandler)
        signal.signal(signal.SIGUSR1, self.signalHandler)

        # If default signal handling is not specified, handle
        # all other catchable signals
        defaultSignals = int(os.environ.get('ATF_DEFAULT_SIGNAL_HANDLING', 0))
        if (defaultSignals == 0):
            signal.signal(signal.SIGABRT, self.signalHandler)
            signal.signal(signal.SIGSEGV, self.signalHandler)
            signal.signal(signal.SIGILL, self.signalHandler)
            signal.signal(signal.SIGTRAP, self.signalHandler)
            signal.signal(signal.SIGBUS, self.signalHandler)
            signal.signal(signal.SIGFPE, self.signalHandler)

        # Continue with normal execution of the test
        self.setUp()
        import datetime
        os.system('rm -f ATF_TESTCASE')
        ts_start = datetime.datetime.now()
        fc = 0; ec = 0
        for test in self._tests:
            isErr = False
            if result.shouldStop or self.stopExecution:
                break
            os.system('printf "%s" >> ATF_TESTCASE' % test)
            start = datetime.datetime.now()
            test(result)
            end = datetime.datetime.now()
            diffMin = (end-start).seconds / 60
            if len(result.failures) > fc:
                isErr = True
                fc = len(result.failures)
            if len(result.errors) > ec:
                isErr = True
                ec = len(result.errors)
            if isErr:
                os.system('printf " (%d min/Error)\n" >> ATF_TESTCASE' % (diffMin))
            else:
                os.system('printf " (%d min)\n" >> ATF_TESTCASE' % (diffMin))

        ts_end = datetime.datetime.now()
        ts_diffMin = (ts_end - ts_start).seconds / 60
        os.system('printf "Total %s mins\n" >> ATF_TESTCASE' % ts_diffMin)
        self.tearDown(result)
        #for test in self._tests:
        #    if result.shouldStop or self.stopExecution:
        #        break
        #    test(result)

        #self.tearDown(result)
        return result

    def signalHandler(self, signum, frame):
        r'''
        Handle all raised signals by stopping the execution of the
        TestSuite and raising an exception to allow standard clean
        up to occur with appropriate test output.

        @param signum:
            The number of the raised signal that invoked the handler

        @param frame:
            The current stack frame
        '''
        # ignore all signals
        # Handle all 'standard' termination signals
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
        signal.signal(signal.SIGHUP, signal.SIG_IGN)
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        signal.signal(signal.SIGQUIT, signal.SIG_IGN)

        # If default signal handling is not specified, handle
        # all other catchable signals
        defaultSignals = int(os.environ.get('ATF_DEFAULT_SIGNAL_HANDLING', 0))
        if (defaultSignals == 0):
            signal.signal(signal.SIGABRT, signal.SIG_IGN)
            signal.signal(signal.SIGSEGV, signal.SIG_IGN)
            signal.signal(signal.SIGILL, signal.SIG_IGN)
            signal.signal(signal.SIGTRAP, signal.SIG_IGN)
            signal.signal(signal.SIGBUS, signal.SIG_IGN)
            signal.signal(signal.SIGFPE, signal.SIG_IGN)

        self.stopExecution = True
        raise Exception("Terminating due to signal %d" % signum)


class Workspace(CommonBase):
    r"""
    This class provides a wrapper that will automatically create and
    destroy a temporary work area. Alternately if a "name" argument
    is given at construction time it will assume the workspace already
    exists and leave it untouched on destruction.
    """

    #
    # Class error definitions
    #
    (ERR_TMPFS_MOUNT) = CommonError.ERR_COMMON+1
    """Error while mounting tmpfs"""
    (ERR_COPY) = CommonError.ERR_COMMON+2
    """Error while copying"""
    (ERR_CREATE_DIR) = CommonError.ERR_COMMON+3
    """Error while creating a directory"""

    CMD_MOUNT_TMPFS = 'sudo mount -t tmpfs tmpfs %s'
    """Command used to mount tmpfs"""
    CMD_UNMOUNT_TMPFS = 'sudo umount -t tmpf %s'
    """Command used to unmount tmpfs"""
    CMD_RM = 'sudo rm -rf %s'
    """Command used to delete a file"""
    CMD_CP = 'sudo cp -f %s %s'
    """Command used to copy a file"""
    CMD_MKDIR = 'sudo mkdir -m %s -p %s'
    """Command used to make a directory"""
    CMD_SYMLINK       = 'sudo ln -s %s %s'
    """Command used to soft link a file"""

    TempPrefix = 'atf_tmp_'

    def __init__(self, name=None, useTmpfs=False, diagLevel=logging.WARNING):
        r"""
        If no name is given, create a temporary work area. Either way save
        knowledge of where the workarea lives internally.

        @param name:
            Location of the workarea if it already exists or None if we should
            create a temporary one.

        @param useTmpfs:
            If not None, indicates workspace should be created on a tmpfs area.
            Option is ignored if name is also not None since this calls out a
            specific location beyond our control.

        @param diagLevel:
            What debug level to run this object in.
        """
        CommonBase.__init__(self, diagLevel)
        self.tmpfsMounted = False
        self.needsCleanup = False

        self.workDir = None
        """Directory location of the workspace."""

        if (name == None):
            self.workDir = tempfile.mkdtemp(prefix=Workspace.TempPrefix,
                                            dir='/tmp') + '/'
            # Make sure that the workspace created has rw for everyone
            # otherwise tftp service out of the workspace can fail.
            os.chmod(self.workDir, (stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO))
            self.needsCleanup = True
            if (useTmpfs == True):
                self.useTmpfs = useTmpfs
                # Create the tmpfs mounted on our created directory area.
                retcode = subprocess.call(Workspace.CMD_MOUNT_TMPFS %
                                          self.workDir, shell=True)
                if (retcode != 0):
                    raise(CommonError(Workspace.ERR_TMPFS_MOUNT,
                                      'Failed : to mount tmpfs :%s: returned=%s' %
                         (self.workDir, retcode)))
                self.tmpfsMounted = True

            # prevent symlinks from removing softlinks when running with "No Install"
            if( int(os.environ.get('ATF_NO_INSTALL', 0)) == 1 ):
                subprocess.call(Workspace.CMD_MKDIR % ('777', self.workDir + '/tftp'), shell=True)

        else:
            self.workDir = name

            # ensure that the workDir ends with a trailing slash
            if (not self.workDir.endswith('/')):
                self.workDir += '/'

    def __del__(self):
        r"""
        If we created a temporary area on construction, then completely
        destroy that area.
        """
        if (self.workDir != None):
            if (self.needsCleanup == True):
                if (self.tmpfsMounted == True):
                    retcode = subprocess.call(Workspace.CMD_UNMOUNT_TMPFS %
                                              self.workDir, shell=True)
                    if (retcode != 0):
                        raise(CommonError(Workspace.ERR_TMPFS_MOUNT,
                                          'Failed : to unmount tmpfs area :%s: returned=%s' %
                             (self.workDir, retcode)))
                subprocess.call(Workspace.CMD_RM % self.workDir, shell=True)
            else:
                self.logger.warning('Left alone non-temporary workspace : %s'
                                    % self.workDir)

    def createDisk(self, name, type="buslogic", disk="4G"):
        r"""
        Construct an empty disk image inside the current workspace.

        @param name:
            The filename to use for the created image.

        @param type:
            The type of disk to create

        @param disk:
            The amount of room to put on the disk image

        @return:
            None, Can raise L{FrameworkError} exceptions
        """
        raise (NotImplementedError())

    def setDisk(self, name, type=None, disk=None):
        r"""
        Record the fact that a disk already exists in a workspace

        @param name:
            The workspace relative filename of an existing image.

        @param type:
            The type of the disk

        @param disk:
            The amount of room to put on the disk image
            Optional suffixes "K" (1024K), "M" (1024M) and "G" (1024G) are supported
        """
        raise (NotImplementedError())

    def setPersistent(self, persistence=True):
        r"""
        Allow changing of a workspaces persistence. This controls whether
        we cleanup the workspace when we destruct or not.

        @param persistence:
            If true, we will change our destruction behavior to leave the
            workspace in place. If false we will clean up the workspace
            on destruction.
        """
        self.needsCleanup = not persistence

    def copyFile(self, filename, dest=None):
        r"""
        This is a common helper routine to copy files on the local host into
        a workspace relative directory.

        @param filename:
            The absolute path to the file

        @param dest:
            The location to copy to relative to the top workDir location.

        @return:
            The full path of the copied workspace file.
        """
        if (dest == None):
            dest = self.workDir + os.path.basename(filename)
        else:
            dest = self.workDir + dest

        retcode = subprocess.call(Workspace.CMD_CP % (filename, dest),
                                  shell=True)
        if (retcode != 0):
            raise(CommonError(Workspace.ERR_COPY,
                              'Failed : copy of :%s: to :%s:returned=%s' %
                 (filename, dest, retcode)))
        return (dest)

    def symLinkFile(self, filename, dest=None):
        r"""
        This is a common helper routine to link files on the local host into
        a workspace relative directory.

        @param filename:
            The absolute path to the file
        
        @param dest:
            The location to link to relative to the top workDir location.
        
        @return:
            The full path of the linked workspace file.
        """
        if (dest==None):
            dest=self.workDir + os.path.basename(filename)
        else:
            dest=self.workDir + dest 
            
        retcode = subprocess.call(Workspace.CMD_SYMLINK % (filename,dest), shell=True)
        if (retcode != 0):
            raise(CommonError(Workspace.ERR_COPY, 
                'Failed : symLink of :%s: to :%s:returned=%s' % 
                (filename, dest,retcode)))
        return (dest)

    def createDirTree(self, dir, permissions='777'):
        r"""
        This is a common helper routine to create a directory tree inside a
        a workspace.  It will first delete any existing tree and then
        create directories in the path and set the permissions to those
        specified.

        @param dir:
            The relative path to the directory within the workspace
            permissions - access permission bits.
        """
        subprocess.call(Workspace.CMD_RM % (dir), shell=True)
        retcode = subprocess.call(Workspace.CMD_MKDIR %
                                  (permissions, self.workDir + '/' + dir),
                                  shell=True)
        if (retcode != 0):
            raise(CommonError(Workspace.ERR_CREATE_DIR,
                              'Failed : creation of :%s: returned=%s' %
                 (self.workDir + dir), retcode))


class FileTee(object):
    r"""
    Utility class which writes to a File Object that back ends to two files.
    """
    def __init__(self, f1=None, f2=None, diagLevel=logging.ERROR):
        r"""
        If filenames are not given, default to a L{StringIO} and, optionally,
        stdout.

        @param f1:
            The first file object to output to; if None, this creates an internal
            StringIO instance for reference, Defaults to None.

        @param f2:
            The second file object to output to; if None and diagLevel is
            logging.DEBUG or lower. Defaults to None.

        @param diagLevel:
            What debug level to run this object in.
        """
        if (f1 == None):
            self.file1 = StringIO()

        if (f2 == None and diagLevel <= logging.DEBUG):
            self.file2 = sys.stdout
        else:
            self.file2 = None

    #
    # cStringIO Object duck typing
    #
    def getvalue(self):
        r"""
        Retrieve the entire contents of the "file" at any time before the
        L{StringIO} object's close() method is called. Mixing Unicode and
        8-bit strings can cause this method to raise a UnicodeError.

        @return:
            getvalue() return of the first file object if available,
            None otherwise
        """
        if (self.file1 != None and hasattr(self.file1, 'getvalue')):
            return self.file1.getvalue()

        return ""

    #
    # File Object duck typing for use by
    # pexpect.spawn.logfile_read
    #
    def close(self):
        r"""
        Close both files.

        A closed file cannot be read or written any more. Any operation
        which required that the file be open will raise a L{ValueError}
        after the file has been closed. Calling close() more than once
        is allowed.
        """
        if (self.file1 != None):
            self.file1.close()

        if (self.file2 != None):
            self.file2.close()

    def flush(self):
        r"""
        Flush each file's internal buffer, like stdio's fflush().
        This may be a no-op on some file-like objects.
        """
        if (self.file1 != None):
            self.file1.flush()

        if (self.file2 != None):
            self.file2.flush()

    def write(self, s):
        r"""
        Write a string to both files. There is no return value.
        Due to buffering, the string may not actually show up in
        the file until the flush() of close() method is called.

        @param s:
            The string to write out to both file objects.
        """
        if (self.file1 != None):
            self.file1.write(s)

        if (self.file2 != None):
            self.file2.write(s)


def waitUntilSuccess(fn, grace=300, interval=5):
    r"""
    Retry function until success
    @param fn:
        Function() to exec
    @grace:
        Total time to retry
    @interval:
        interval to sleep
    """
    startTime = time.time()
    endTime = startTime + grace
    status = fn()
    while ((time.time() < endTime)):
        if  status == True:
            return True
        time.sleep(interval)
        status = fn()

    return False


def checkConn(device, publicIp, timeout=300, desc=''):
    r"""
    Check that destination is responding to ssh port.

    @param device:
        ProxyDevice object
    @param publicIp: 
        IP address to connect
    @param timeout:
        Time to retry
    @param desc:
        Description to display in log
    @return:
        True if vm responds correctly otherwise false
    """
    startTime = time.time()
    endTime = startTime + timeout
    sshPort = 22
    s = socketHelper.socket(socketHelper.AF_INET, socketHelper.SOCK_STREAM, 0)
    s.settimeout(1)
    success = False
    attempts = 0
    while ((time.time() < endTime) and not success):
        try:
            s.connect((publicIp, sshPort))
            device.logger.debug(device.config.name + ' SSH service connectivity verified.')
            success = True
        except socketHelper.error:
            device.logger.warning('Unable to connect to ' + desc + ' SSH service("%s"). Attempt # %s' % (publicIp, attempts))
            attempts += 1
            sleep(1)
            continue

    s.close()
    if(success == False):
        raise Exception('Unable to verify SSH service connectivity, current state : %s' % device.state)

    if hasattr(device, "state"):
        device.state = device.STATE_RUNNING

    return success
