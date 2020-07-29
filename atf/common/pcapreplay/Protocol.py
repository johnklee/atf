from atf.common.network.Network import NetworkUtil

##
# Globals

#
# Define all protocols use within pcapreplay
#

# FlowKeys
MAC = 'MAC'
#TODO: Move the test to NetworkUtil or some common place outside
#of pcapreply for everyones benefit
IPV4 = NetworkUtil.TYPE_IPV4
IPV6 = NetworkUtil.TYPE_IPV6

# Flows
GENERIC = 'GENERIC'
ICMP = 'ICMP'
TCP = 'TCP'
UDP = 'UDP'

# Triggers
HTTP = 'HTTP'