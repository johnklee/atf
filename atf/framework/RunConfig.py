# This file contains all the parameters necessary to configure the
# test framework for a given installation.
import os
import logging

class RunConfig(object):
    # So some machines and some environments are going to be slower
    # than others and we will inevitably have to tune timeout parameters
    # that tests need to make sure they complete reliably.
    # This value is applied to ALL timeout constants within the
    # framework to give some crude ability to tailor for the environment
    # people have for testing.
    (TIMEOUT_MULTIPLIER) = int(os.environ.get('TIMEOUT_MULTIPLIER', 8))
    """Scaling factor for all timeouts used throughout ATF CORE"""
    
    def __init__(self):
        r"""
        Setup basic defaults for all configuration information needed for
        a test suite
        """
        self.systemConfigs = {}

    def addSystemConfig(self, name, systemConfig):
        r"""
        Add a SystemConfig to RunConfig under the specified System name
        
        @param name:    
            The index to associate the supplied SystemConfig with
            systemConfig: The SystemConfig to add to the RunConfig
            
        @param systemConfig:
            The L{SystemConfig} object to add to the systemConfigs collection.
            
        @return:
            systemConfig object added to the systemConfigs collection
        """
        self.systemConfigs[name] = systemConfig
        
        return self.systemConfigs[name]
