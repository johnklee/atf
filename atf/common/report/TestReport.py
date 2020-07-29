import time

from atf.common.report.TestResult import *

class TestReport(object):
    r"""
    A Test report class. It's a container for a test result artifacts
    """
    
    def __init__(self):
        r"""
        Test report constructor

        name         - test name, which is a method name
        metaTags     - dict which maps: str(tag) => List(MetaTagField)
        runTime      - test execution time
        rawDocString - string
        description  - string
        result       - L{TestResult} object
        """
        self.name           = ""
        self.metaTags       = []
        self.startTime      = time.time()
        self.endTime        = time.time()
        self.runTime        = 0
        self.rawDocString   = ""
        self.description    = ""
        self.result         = TestResult()
        
    def setResult(self, result):
        self.result  = result
        self.endTime = time.time()
        self.runTime = self.endTime - self.startTime
        
class TestSuiteReport(TestReport):
    r"""
    A Test suite report class. It's a container for a test report objects
    """

    def __init__(self):
        r"""
        Test suite report constructor
        
        tests         - list of L{TestReport} objects
        path         - a path to the file with this test suite
        """
        TestReport.__init__(self)
        
        self.path       = ""
        self.tests      = []
        
        # calculated stats of tests
        self.totalTestsRunTime   = 0
        self.totalPassed         = 0
        self.totalErrors         = 0
        self.totalFailures       = 0
        self.totalDisabled       = 0
        self.totalUnknown        = 0

    def addTestReport(self, testReport):
        self.tests.append(testReport)
        
        # sum test runTime values
        self.totalTestsRunTime += testReport.runTime
        
        # count test results
        if isinstance(testReport.result, TestResultPass):
            self.totalPassed += 1
        elif isinstance(testReport.result, TestResultError):
            self.totalErrors += 1
        elif isinstance(testReport.result, TestResultFail):
            self.totalFailures += 1
        elif isinstance(testReport.result, TestResultDisabled):
            self.totalDisabled += 1
        elif isinstance(testReport.result, TestResultUnknown):
            self.totalUnknown += 1

    def calcSuiteResult(self):
        # set suite result (and this sets suite endTime)
        #
        if len(self.tests) == self.totalPassed:
            self.setResult(TestResultPass())
        elif self.totalErrors > 0:
            self.setResult(TestResultError("Some tests Errored"))
        elif self.totalFailures > 0:
            self.setResult(TestResultFail("Some tests Failed"))
        elif len(self.tests) == self.totalDisabled:
            self.setResult(TestResultDisabled("All tests Disabled"))
        else:
            # some passed and some were blocked
            self.setResult(TestResultUnknown())
