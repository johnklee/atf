import logging
import os
import datetime
from lxml import builder, objectify, etree

from atf.framework.FrameworkBase import *
from atf.common.report.TestReport import *
from atf.common.report.DocStringParser import *

class TestReportGenerator(FrameworkBase):
    r"""
    A class to generate XML report from test results.
    """

    def __init__(self, diagLevel=logging.DEBUG):
        r"""
        XMLTestReport constructor
        """
        self.diagLevel = diagLevel
        self.E = builder.ElementMaker()
        
        # define xml tags for use later
        self.ROOT_ELT        = self.E.testReport
        self.ENV_ELT         = self.E.env
        self.SUITE_ELT       = self.E.suite
        self.MSG_ELT         = self.E.msg
        self.DOC_ELT         = self.E.doc
        self.USER_DOC_ELT    = self.E.userDoc
        self.RAW_ELT         = self.E.raw
        self.DESCRIPTION_ELT = self.E.description
        self.TAG_ELT         = self.E.tag
        self.TEST_ELT        = self.E.test
        
        FrameworkBase.__init__(self, diagLevel=diagLevel)

    def generate(self, outFilename, testSuiteReports):
        r"""
        Generate XML report in chosen directory. It will be appended to
        an existing report if possible.

        @param outFilename:
            output filename for XML file
        @param testSuiteReports:
            list of L{TestReport} objects
        """
        testSuiteElts = []

        # build an lxml.etree object from each testSuiteReport
        for testSuiteReport in testSuiteReports:
            testSuiteElts.append(self._buildEtree_(testSuiteReport))

        # see if there is a report in the directory already
        try:
            with open(outFilename) as f:
                xml = f.read()
                
            # open existing report and append to it
            testRunElt = objectify.fromstring(xml)
            for testSuiteElt in testSuiteElts:
                testRunElt.append(testSuiteElt)

        except IOError:
            # else start new report
            #
            # root element
            testRunElt = self.ROOT_ELT(
                self.ENV_ELT(),
                self.USER_DOC_ELT(
                    self.RAW_ELT(),
                    self.DESCRIPTION_ELT()
                )
            )
            testRunElt.set('utcCreated', '%d' % (time.time()*1000))
            
            for testSuiteElt in testSuiteElts:
                testRunElt.append(testSuiteElt)
                
            # objectify returns a different structure, so do that now to
            # standardise any following code
            testRunElt = objectify.fromstring(etree.tostring(testRunElt, pretty_print=True, xml_declaration=False, encoding="UTF-8"))

        testRunEnvElt       = testRunElt.xpath("./env")[0]
        testRunUserDocElt   = testRunElt.xpath("./userDoc")[0]

        #
        # update testReport summary
        #
        totalTestsRunTime   = 0
        totalTests          = 0
        totalPass           = 0
        totalError          = 0
        totalFail           = 0
        totalDisabled       = 0
        totalUnknown        = 0
        
        for suiteElt in testRunElt.xpath("//suite"):
            totalTestsRunTime   += int(suiteElt.get('totalTestsRunTime'))
            totalTests          += int(suiteElt.get('totalTests'))
            totalPass           += int(suiteElt.get('totalPass'))
            totalError          += int(suiteElt.get('totalError'))
            totalFail           += int(suiteElt.get('totalFail'))
            totalDisabled       += int(suiteElt.get('totalDisabled'))
            totalUnknown        += int(suiteElt.get('totalUnknown'))

        testRunElt.set('totalTestsRunTime', str(totalTestsRunTime))
        testRunElt.set('totalTests',        str(totalTests))
        testRunElt.set('totalPass',         str(totalPass))
        testRunElt.set('totalError',        str(totalError))
        testRunElt.set('totalFail',         str(totalFail))
        testRunElt.set('totalDisabled',     str(totalDisabled))
        testRunElt.set('totalUnknown',      str(totalUnknown))
        
        if totalTests == totalPass:
            testRunElt.set('result', 'PASSED')
        elif totalError > 0:
            testRunElt.set('result', 'ERROR')
        elif totalFail > 0:
            testRunElt.set('result', 'FAILED')
        elif totalTests == totalDisabled:
            testRunElt.set('result', 'DISABLED')
        else:
            # some passed and some were blocked
            testRunElt.set('result', 'UNKNOWN')

        # add env tags for the test report
        envString = ''
        for key in os.environ:
            if key.startswith("ATF_"):
                envString += "\n@"+key+":"+os.environ[key].strip()
        description, metaTags = parseDocString(envString)

        # update env tags
        for tagElt in testRunEnvElt.xpath("./tag"):
            testRunEnvElt.remove(tagElt)
        self._appendDocStringTags_(testRunEnvElt, metaTags)
        

        # add user doc for the test report
        docFname = os.environ.get('ATF_REPORT_DOC_FILE', '')
        docString = ''
        if docFname != '':
            try:
                with open(docFname) as f:
                    docString = f.read()
            except IOError:
                docString = "Failed to read docFile:"+docFname
                
        description, metaTags = parseDocString(docString)
        
        rawElt  = testRunUserDocElt.xpath("./raw")[0]
        descElt = testRunUserDocElt.xpath("./description")[0]
        rawElt._setText(docString)
        descElt._setText(description)
        
        # replace the tags
        for tagElt in testRunUserDocElt.xpath("./tag"):
            testRunUserDocElt.remove(tagElt)
        self._appendDocStringTags_(testRunUserDocElt, metaTags)

        # indicate we have touched the test report file
        testRunElt.set('utcUpdated', '%d' % (time.time()*1000))
        testRunElt.set('utcOffset',  str(time.timezone * -1))

        # create report directory if it does not exist
        pathDir = os.path.dirname(outFilename)
        if not os.path.exists(pathDir):
            try:
                os.makedirs(pathDir)
            except OSError as e:
                print e

        # write the tree to an xml file
        with open(outFilename, 'w') as f:
            f.write(etree.tostring(testRunElt, pretty_print=True, xml_declaration=True, encoding="UTF-8"))

    def _buildEtree_(self, testSuiteReport):
        r"""
        Constructs an etree from a L{TestSuiteReport} object

        @param testSuiteReport:
            A L{TestSuiteReport} object to convert into xml tree
        @return:
            An lxml etree instance containing all the testSuiteReport data
        """
        # start building a suite of tests
        testSuiteElt = self.SUITE_ELT(
            self.MSG_ELT(),
            self.DOC_ELT(
                self.RAW_ELT(testSuiteReport.rawDocString),
                self.DESCRIPTION_ELT(testSuiteReport.description)
            ),
            self.ENV_ELT(),
            self.USER_DOC_ELT(
                self.RAW_ELT(),
                self.DESCRIPTION_ELT()
            )
        )
        suiteMsgElt      = testSuiteElt[0]
        suiteDocElt      = testSuiteElt[1]
        suiteEnvElt      = testSuiteElt[2]
        suiteUserDocElt  = testSuiteElt[3]
        
        # append doc tags
        self._appendDocStringTags_(suiteDocElt, testSuiteReport.metaTags)
        
        # add ATF_ env vars for the test suite
        envString = ''
        for key in os.environ:
            if key.startswith("ATF_"):
                envString += "\n@"+key+":"+os.environ[key].strip()
                
        description, metaTags = parseDocString(envString)
        self._appendDocStringTags_(suiteEnvElt, metaTags)
        
        # add user doc for the test suite
        docFname = os.environ.get('ATF_REPORT_SUITE_DOC_FILE', '')
        docString = ''
        if docFname != '':
            try:
                with open(docFname) as f:
                    docString = f.read()
            except IOError:
                docString = "Failed to read docFile:"+docFname

        description, metaTags = parseDocString(docString)
        
        # set the user doco
        userRawElt       = suiteUserDocElt[0]
        userDescElt      = suiteUserDocElt[1]
        userRawElt.text  = docString
        userDescElt.text = description
        self._appendDocStringTags_(suiteUserDocElt, metaTags)

        # construct a TEST node for every testReport in the list
        # then populate its fields
        for testReport in testSuiteReport.tests:
            testElt = self.TEST_ELT(
                self.MSG_ELT(),
                self.DOC_ELT(
                    self.RAW_ELT(testReport.rawDocString),
                    self.DESCRIPTION_ELT(testReport.description)
                ),
            )
            testMsgElt = testElt[0]
            testDocElt = testElt[1]
            
            testElt.set('utcStart',   '%d' % (testReport.startTime*1000))
            testElt.set('utcEnd',     '%d' % (testReport.endTime*1000))
            testElt.set('msRunTime',  '%d' % (testReport.runTime*1000))
            testElt.set('name',       testReport.name)
            testElt.set('result',     testReport.result.status)
            
            # include result message if there is one
            #strip characters that cause issues in XML
            strippedMsg = ''.join([i if i in ['\n', '\t'] or (ord(i) < 128 and ord(i) > 31) else '' 
                          for i in testReport.result.msg])
            testMsgElt.text = strippedMsg
            
            self._appendDocStringTags_(testDocElt, testReport.metaTags)

            # append the resulting test node to the overall suite
            testSuiteElt.append(testElt)

        #
        # all done - populate suite meta data
        #
        
        testSuiteElt.set('utcStart',            '%d' %(testSuiteReport.startTime*1000))
        testSuiteElt.set('utcEnd',              '%d' %(testSuiteReport.endTime*1000))
        testSuiteElt.set('utcOffset',           str(time.timezone * -1))
        testSuiteElt.set('msRunTime',           '%d' % (testSuiteReport.runTime*1000))
        testSuiteElt.set('totalTestsRunTime',   '%d' % (testSuiteReport.totalTestsRunTime*1000))
        testSuiteElt.set('name',                testSuiteReport.name)
        testSuiteElt.set('path',                testSuiteReport.path)
        testSuiteElt.set('result',              testSuiteReport.result.status)
        testSuiteElt.set('totalTests',          str(len(testSuiteReport.tests)))
        testSuiteElt.set('totalPass',           str(testSuiteReport.totalPassed))
        testSuiteElt.set('totalError',          str(testSuiteReport.totalErrors))
        testSuiteElt.set('totalFail',           str(testSuiteReport.totalFailures))
        testSuiteElt.set('totalDisabled',       str(testSuiteReport.totalDisabled))
        testSuiteElt.set('totalUnknown',        str(testSuiteReport.totalUnknown))
        
        # include result message if there is one
        suiteMsgElt.text = testSuiteReport.result.msg
        
        return testSuiteElt

    def _appendDocStringTags_(self, node, metaTags):
        r"""
        Appends the fields in L{TestDoc} object to node with their
        respective tags

        @param node:
            An etree node object
        @param metaTags:
            dict which maps: str(MetaTagField.TAG) => List(MetaTagField)
        @return:
            The passed in node with extra nodes appended to it
        """
        # Check data validity for each meta data tag and append invalid
        # format tag to data before adding to the node
        # NOTE: They are sorted as it is a limitation of the XSD schema that
        #        the meta tags must be in alphabetical order
        for tag in metaTags:
            # Add all instances of the tag to the node
            for tagInstance in metaTags[tag]:
                node.append(self.TAG_ELT(tagInstance, name=tag))

        return node
