import logging
import pexpect
import signal
import subprocess
import json
import sys
import os

import atf.common.Common as Common
import docker

from atf.framework.device.state.DockerImgState import *
from datetime import datetime
from atf.framework.FrameworkBase import *
from atf.common.docker.client import *
from ProxyDevice import *
from ProxyContainer import *
from ProxyEmulator import *
from dep_docker import Client
from dep_docker.utils import dspawn


class DockerConfig(ContainerConfig):
    r"""
    Encapsulate the QEMU specific configuration information needed
    to set up a QEMU hosted Device.
    """
    def __init__(self, image, run_config, host='tcp://localhost:2375', host_user='root', host_passwd='realsecure'):
        r"""
        Save all arguments internally and construct base class.
         
        @param image:
            Docker image related information.

        @param run_config:
            dict object to hold argument(s) to run the container
 
        @param host:
            Docker daemon host 

        @param host_user:
            Host user account

        @param host_passwd:
            Password of `host_user`
        """
        ContainerConfig.__init__(self, image, run_config)
        self.host = os.environ.get('ATF_DOCKER_HOST', host)
        self.host_user = os.environ.get('ATF_DOCKER_HOST_USER', host_user)
        self.host_passwd = os.environ.get('ATF_DOCKER_HOST_PASSWD', host_passwd)

 
class ProxyDocker(ProxyContainer):
    r"""
    The ProxyDocker class supports the ProxyDevice interface to control the Virtual Machine.
    """    
    
    (CONTAINER_STATUS_PATH) = '/tmp/CONTAINER_STATUS'
    """ Path to file which will hold service status from container (0:Ready, 1:Starting, 2:Stopping, 3:Stopped) """
    
    def __init__(self,  dkConfig=None, diagLevel=logging.WARNING, dkClient=None):
        r"""
        Refer base class for a description of this interface method.
        
        @param dkConfig:
            A pre-constructed EmulatorConfig object
            
        @param diagLevel:
            What debug level to run this object in.
            
        @param dkClient:
            Docker client 
        """
        ProxyContainer.__init__(self, dkConfig, diagLevel)
        if dkClient is None:
            dkClient = DockerAgent(diagLevel=diagLevel)

        self.dkClient = dkClient
        self.container = None
        # self.hostJail = '/hostfs'
        """chroot to host jail is an alternative to ssh localhost"""

    def __del__(self):
        r"""
        Try and make sure that qrun gets a chance to cleanup by
        sending it a signal before exit.
        """
        if (hasattr(self, "container") and self.container) :
            self.stop()
        
        self.config = None
        
    def start(self, productPackage=None, entrypoint=None):
        r"""
        Start the container from image indicated by self.config.getImagePath()

        @return:
            None, Can raise L{FrameworkError} exceptions
        """                
        self.start_begin=datetime.now()
        imgs = self.dkClient.images(self.config.image)
        if len(imgs) != 1:
            raise (FrameworkError(ProxyDevice.ERR_FAILED_DOCKER_IMG,
                                  "Fail to retrieve image='%s'!" % (self.config.image)))
        else:
            img = imgs[0]

        self.logger.debug("Using image: %s" % img['RepoTags'])
        self.hostShell = self.dkClient.cons

        # Start container from image
        try:
            if 'environment' in self.config.run_config:
                self.config.run_config['environment']['PPID'] = os.getpid()
            else:
                self.config.run_config['environment'] = {'PPID': os.getpid()}

            self.config.run_config['image'] = img['Id']
            self.container = self.dkClient.run(**self.config.run_config)
        except docker.errors.APIError as e:
            raise (FrameworkError(ProxyDevice.ERR_FAILED_DOCKER_RUN,
                                      "Fail to start container from image='%s':\n%s\n" % (img, e)))
        except KeyboardInterrupt as ke:
            if hasattr(self.dkClient, '_container') and self.dkClient._container:
                self.logger.debug("Remove temporal container=%s..." % self.dkClient._container)
                self.dkClient.remove(container=self.dkClient._container['Id'], sh=self.hostShell)
            raise (FrameworkError(ProxyDevice.ERR_FAILED_DOCKER_RUN,
                                  "Interrupt while starting container from image='%s'!" % (img)))
        except:            
            if hasattr(self.dkClient, '_container') and self.dkClient._container:
                self.logger.debug("Remove temporal container=%s..." % self.dkClient._container)
                self.dkClient.remove(container=self.dkClient._container['Id'], sh=self.hostShell)

            raise (FrameworkError(ProxyDevice.ERR_FAILED_DOCKER_RUN,
                                  "Fail to start container from image='%s'!" % (img)))
        self.logger.debug("Launched Container: %s" % self.container['Id'])

        # This is necessary until we can figure out why attaching to container does not always succeed in a nested jail
        cnt = 0
        maxTry = 10
        while cnt < maxTry:
            cnt += 1
            self.logger.debug("%d: docker exec: %s" % (cnt, self.container['Id']))
            try:
                self.cons=self.dkClient.spawn_container_shell(self.container)
                break
            except:
                time.sleep(2)
                continue

        if cnt >= maxTry:
            self.fail("Failed to attach to container: %s" % self.container['Id'])

        if (self.logger.getEffectiveLevel() <= logging.DEBUG):
                self.cons.logfile_read = sys.stdout

        r'''
        TBD
        # Determine the networking setup
        self.logger.debug("Setting up networks ...")
        self.cons.sendline('ip link del eth0')
        self.cons.prompt()

        if (self.config.networks != None):
            for (bridge, sysIFs) in sorted(self.config.networks.items()):
                self.dkClient.network_add_link(container=self.container['Id'], bridge=bridge, ifname=sysIFs.interfaces.keys()[0], sh=self.hostShell)

                # Look for any bridge that needs to be assigned an address 
                # so that it can act as a GW to the real world.
                for (gw, ips) in self.config.guestGWs.items():
                    if (gw == bridge):
                        if type(ips) is not types.ListType:
                            ips = [ips]
                        separator = '='
                        for ip in ips:
                            if hasattr(ip, 'netmaskLength'):
                                self.hostShell.sendline('ip a a dev %s %s/%s' % (bridge, ip.address, ip.netmaskLength))
                                self.hostShell.prompt()        
                            elif(hasattr(ip, 'prefixLength')):
                                self.hostShell.sendline('ip -6 a a dev %s %s/%s' % (bridge, ip.address, ip.prefixLength))
                                self.hostShell.prompt()        
                            separator = ','
                        break
        '''           
  
        self.start_end=datetime.now()
        self.state = ProxyDevice.STATE_RUNNING
        
    def stop(self):
        r"""
        Refer base class for a description of this interface method.
        """
        try:
            self.state = ProxyDevice.STATE_STOPPING

            # if self.dockerDaemon != None:
            #     self.dockerDaemon.cons.sendcontrol('c') # stop daemon
            #     self.dockerDaemon.sendline('rm -f /var/run/docker.%d' % os.getpid())
            #     self.dockerDaemon.prompt()
            #     self.dockerDaemon.cons.sendcontrol('d') # exit host jail
            #     self.dockerDaemon.close()
            # elif self.container:            
            if self.container:
                if self.cons:
                    # removing network links can be destructive if not carried out inside container
                    self.cons.sendline("if test ! -d /var/cache/build; then  for i in $(ip l | grep ' eth[0-9]:' | awk '{print $2}' | sed 's/://') ; do ip link del ${i} ; done  ; fi")
                    self.cons.sendcontrol('d') # exit container
                    self.cons.sendcontrol('d') # exit host jail
                    self.cons.close()
                    self.cons = None
                
                #self.hostShell.sendline('export DOCKER_HOST=tcp://127.0.0.1:2375 docker; docker rm -f $(docker ps -qa)')
                #self.hostShell.sendcontrol('d') # exit host jail                
                #self.dkClient.kill(container=self.container['Id'], signal='KILL')
                #self.dkClient.remove(container=self.container['Id'], sh=self.hostShell)
                self.dkClient.remove_container(container=self.container['Id'], force=True)                
                self.hostShell.close()
                self.container = None

            
            self.state = ProxyDevice.STATE_STOPPED
        except BaseException, failure:
            self.state = ProxyDevice.STATE_UNKNOWN
            self.logger.error('Failed to stop() Container : %s' % str(failure))
            # Output whatever was sent to the console during the attempt.
            self.logger.debug(str(self.cons))
            raise (FrameworkError(ProxyDevice.ERR_FAILED_DEVICE_STOP,
                                  'Unexpected failure to stop, see log')) 

