class TestResult(object):
    r"""
    A common class for all test results
    """

    def __init__(self):
        self.status = "NOT_SET"
        self.msg    = ""

class TestResultUnknown(TestResult):
    r"""
    A test result for static parsing
    """
    RESULT_STRING = 'UNKNOWN'

    def __init__(self, msg=""):
        r"""
        Construct result
        """
        self.status = TestResultUnknown.RESULT_STRING
        self.msg    = msg

class TestResultPass(TestResult):
    r"""
    A test result for Pass status
    """
    RESULT_STRING = 'PASSED'

    def __init__(self):
        r"""
        Construct Pass result
        """
        self.status = TestResultPass.RESULT_STRING
        self.msg    = ""


class TestResultFail(TestResult):
    r"""
    A test result for Fail status
    """
    RESULT_STRING = 'FAILED'

    def __init__(self, error):
        r"""
        Construct Fail result

        @param error:
            A reason for Fail result, error message
        """
        self.status = TestResultFail.RESULT_STRING
        self.msg    = error

class TestResultError(TestResult):
    r"""
    A test result for Fail status
    """
    RESULT_STRING = 'ERROR'

    def __init__(self, error):
        r"""
        Construct Error result

        @param error:
            A reason for Error result, error message
        """
        self.status = TestResultError.RESULT_STRING
        self.msg    = error

class TestResultDisabled(TestResult):
    r"""
    A test result for Disabled status
    """
    RESULT_STRING = 'DISABLED'

    def __init__(self, reason):
        r"""
        Construct Disabled result

        @param reason:
            A reason for disabled result
        """
        self.status = TestResultDisabled.RESULT_STRING
        self.msg    = reason
