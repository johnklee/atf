import docker
import json


from abc import ABCMeta, abstractmethod


class ImgState:
    __metaclass__ = ABCMeta
        
    def getImage(self):
        return self.img
        
    def getErrMsg(self):
        return self.errMsg
    
    @abstractmethod
    def next(self):
        pass
    
    
class StartState(ImgState):
    r'''
    Search locally with command 'docker images'
    
                  |Found--> DoneState
    StartState----|
                  |Not Found--> PullRemoteState
    '''
    def __init__(self, imgPath, dkClient, config, logger):
        self.imgPath = imgPath
        self.dkClient = dkClient
        self.config = config
        self.logger = logger        
        
    def next(self):
        self.logger.debug("Searching for image: %s" % self.imgPath)
        imgs = self.dkClient.images(cfilters={'RepoTags':self.imgPath})
        if len(imgs) == 0:
            return PullRemteState(self.imgPath, self.dkClient, self.config, self.logger)   
        return DoneState(imgs[0])
    
class PullRemteState(ImgState):
    r'''
    Pull from remote repository
    
                       |Success -> DoneState
    PullRemoteState----|
                       |Fail -> LocalDImageState
    '''
    def __init__(self, imgPath, dkClient, config, logger):
        self.imgPath = imgPath
        self.dkClient = dkClient
        self.config = config
        self.logger = logger
        
    def next(self):
        self.logger.debug("Pull images for '%s'..." % self.imgPath)
        for line in self.dkClient.pull(self.config.imgInfo.repository, self.config.imgInfo.tag, stream=True):
                print(json.dumps(json.loads(line), indent=4))       
        imgs = self.dkClient.images(cfilters={'RepoTags':self.imgPath})
        if len(imgs) == 0:
            return LocalDImageState(self.config.imgInfo.getImagePath(isDft=True), self.dkClient, self.config, self.logger) 
        return DoneState(imgs[0])
    
class LocalDImageState(ImgState):
    r'''
    Use default image locally
    
                        |Found -> DoneState
    LocalDImageState----|
                        |Not Found -> RemoteDImageState
    ''' 
    def __init__(self, imgPath, dkClient, config, logger):
        self.imgPath = imgPath
        self.dkClient = dkClient
        self.config = config
        self.logger = logger
        
    def next(self):        
        self.logger.debug("Use default images as '%s' locally..." % self.imgPath)
        imgs = self.dkClient.images(cfilters={'RepoTags':self.imgPath})
        if len(imgs) == 0:
            return RemoteDImageState(self.imgPath, self.dkClient, self.config, self.logger) 
        return DoneState(imgs[0])
    
class RemoteDImageState(ImgState):
    r'''
    Pull default Image from remote repository
    
                         |Success -> DoneState
    RemoteDImageState----|
                         |Fail -> ErrorState
    '''
    def __init__(self, imgPath, dkClient, config, logger):
        self.imgPath = imgPath
        self.dkClient = dkClient
        self.config = config
        self.logger = logger
        
    def next(self):
        self.logger.debug("Pull default images for '%s'..." % self.imgPath)
        for line in self.dkClient.pull(self.config.imgInfo.drepository, self.config.imgInfo.tag, stream=True):
                print(json.dumps(json.loads(line), indent=4))       
        imgs = self.dkClient.images(cfilters={'RepoTags':self.imgPath})
        if len(imgs) == 0:
            return ErrorState("Fail to retrieve Image Path='%s'!" % self.imgPath) 
        return DoneState(imgs[0])
        
 
class ErrorState(ImgState):
    def __init__(self, errMsg):
        self.errMsg = errMsg
        
    def next(self):
        return self
    
class DoneState(ImgState):
    def __init__(self, img):
        self.img = img
        
    def next(self):
        return self
