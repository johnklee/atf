import logging
import re

def parseDocString(docString):
    """
    Slices up a doc string into individual tags and returns them as part of a
    dictionary along with the description.

    @param docString:
        the string containing documentation about the test
    @return:
        tuple containing: (string, dict)
        the string is the description which appears before the first tag
        the dict maps: str(tag)=>List(tag values), for every tag in docString
    @rtype: tuple
    """
    description = ""
    metaTags    = {}

    # If there is no doc string
    if not docString:
        description = ""
        return description, metaTags

    currentTag   = ""
    currentValue = ""

    for line in docString.split("\n"):
        line = line.strip()
        match = re.search("@([^@:]*):(.*)", line)
        if match:
            if currentTag == "":
                # we have the description - the part before the first tag
                description = currentValue.strip()
            else:
                _updateTag_(metaTags, currentTag, currentValue)

            currentTag   = match.group(1).strip()
            currentValue = match.group(2).strip()
        elif currentValue == "":
            currentValue = line
        else:
            # re-add the new line to the tag value
            currentValue = currentValue+"\n"+line

    if currentTag != "":
        # strip off trailing \n
        if len(currentValue) > 0 and currentValue[-1]=='\n':
            currentValue = currentValue[:-1]
        _updateTag_(metaTags, currentTag, currentValue)
    elif currentValue != "":
        # no tags, just a description
        description = currentValue.strip()

    return description, metaTags

def _updateTag_(metaTags, tag, value):
    if tag not in metaTags:
        metaTags[tag] = [value]
    else:
        metaTags[tag].append(value)
    
    return metaTags
