Overview and Table of Contents
==========================

This repository is used for ATF to test docker.
1. [Goal](#linkGoal)
2. [To-Do Items](#linkToDo)
3. [Required Packages](#linkToRequiredPack)
4. [ATF Environment Variables](#atfEV)
5. [Demonstration of usage](#usage)
   * [Build Image](#usage_build)
   * [Launch container](#usage_cont)
   * [Copy in/out file](#usage_copy)
6. [Reference](#ref)

## Goal <a name='linkGoal'></a>
This repo actually is a wrapper on [**Docker SDK for Python**](https://docker-py.readthedocs.io/en/stable/) but provide more flexibly and powerful APIs for QA to write test cases in manipulating docker container/image. The goal of this repo is aimed to be the core/supportive package in testing docker and adopted in any ATF framework. 


## To-Do Items <a name='linkToDo'></a>
So far I will of below features to work on for early implementation:
* Support SSH connection or `docker exec ... bash` to obtain the console of container
* ~~Support log grep function for easily information extraction~~
* ~~Support pdb functionality (breakpoint)~~


## Required Packages <a name='linkToRequiredPack'></a>
* coloredlogs (pip install coloredlogs)
* docker (pip install docker)
* pexpect (pip install pexpect)
* ...

For more, please refer to ['requirements.txt'](https://github.com/jkclee/atf_docker/blob/master/requirements.txt)


## ATF Environment Variables <a name='atfEV'></a>
* ATF_BREAKPOINT: 1 to enable breakpoint
* ATF_LOG_LEVEL: ATF log level. Similar to logging. Ref to [logging doc](https://docs.python.org/2/library/logging.html#logging-levels).
  * RITICAL - 50
  * ERROR - 40
  * WARNING -  30
  * INFO - 20
  * DEBUG - 10
  * NOTSET - 0

## Demonstration of usage <a name='usage'/>
Here will show a few usages on how to automate docker operations by applying this package.

### Build image <a name='usage_build'/>
For API to build image from aspect of [**Docker SDK for Python**](https://docker-py.readthedocs.io/en/stable/), you can refer to below documents:
* [Images - build](https://docker-py.readthedocs.io/en/stable/images.html#docker.models.images.ImageCollection.build)
* [Low-level API - Building images](https://docker-py.readthedocs.io/en/stable/api.html#module-docker.api.build)

This package has wrapped build functionality in package **atf.common.docker.client** and you can refer to example below for how to build a docker image. First, let's check our testing Dockerfile:
```console
// We have testing docker file as below
# ls tests/unit/atf/common/docker/test_data/docker/images/test/
Dockerfile  index.py
```
Then we can use below code to build the testing image:
```python
>>> from atf.common.docker.client import *
>>> da = DockerAgent()
>>> ld_path = 'tests/unit/atf/common/docker/test_data/docker/images/test/'

// Build the image with give tag
>>> build_logs = da.build(path=build_path, tag='atf_docker/demo:latest')
>>> build_logs.grep('Successfully')
['{"stream":"Successfully built 47d13822315d\\n"}\r', '{"stream":"Successfully tagged atf_docker/demo:latest\\n"}\r']

// Retrieve the built image
>>> test_img = da.images('atf_docker/demo:latest')
>>> test_img
[{'Containers': -1, 'Created': 1572233833, 'Id': 'sha256:47d13822315d4145c54c875a36b5e945cd1ac23a31dcc6f7de90e0e0c2aff900', ...}]
>>> from datetime import datetime
>>> datetime.fromtimestamp(test_img[0]['Created'])
datetime.datetime(2019, 10, 28, 11, 37, 13)
```
Then you can double confirmed with command `docker images | grep "atf_docker/demo` from terminal.

### Launch container <a name='usage_cont'/>
For operations on container from aspect of [**Docker SDK for Python**](https://docker-py.readthedocs.io/en/stable/), you can refer to below documents:
* [Containers: Run and manage containers on the server.](https://docker-py.readthedocs.io/en/stable/containers.html)
* [Low-level API - Containers](https://docker-py.readthedocs.io/en/stable/api.html#module-docker.api.container) 

This package has wrapped several functions in package **atf.common.docker.client** to manipulate container and you can refer to example below to lauch the container of image we just built:
```python
// Retrieve testing image
>>> test_img = da.images('atf_docker/demo:latest')[0]

// Launch container of testing image
>>> test_cnt = da.run(image=test_img, name='atf_demo')
>>> test_cnt.status
'running'
>>> test_cnt.id
'9a035313db4af7b7c18175acb8f8bb22c98f76a512f5f349a01948f32d533fe4'
>>> test_cnt.name
'atf_demo'
>>> test_cnt.ip
{'bridge': '172.17.0.2'}
>>> test_cnt.attrs
{'Id': '9a035313db4af7b7c18175acb8f8bb22c98f76a512f5f349a01948f32d533fe4', 'Created': '2019-10-28T05:25:27.956054906Z', ...}

// Search container
>>> da.containers(filters={'name':'atf_demo'})[0].id
'9a035313db4af7b7c18175acb8f8bb22c98f76a512f5f349a01948f32d533fe4'

// Execute command 'ps aux'
>>> rc, logs = test_cnt.exe_command('ps aux')
>>> rc
0
>>> logs
USER       PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
root         1  0.7  0.0 137920 23280 ?        Ss   05:47   0:00 python3 index.p
root        12  0.0  0.0  51740  1732 pts/0    Rs+  05:47   0:00 ps aux

// Stop container
>>> test_cnt.stop()
>>> test_cnt.status
'exited'

// Restart container
>>> test_cnt.restart()
>>> test_cnt.status
'running'


// Remove container
>>> da.remove_container(test_cnt)
...
Stop the container before attempting removal or force remove")

>>> test_cnt.stop()
>>> da.remove_container(test_cnt)
>>> da.containers(filters={'name':'atf_demo'})
[]
```

### Copy in/out file <a name='usage_copy'/>
You can easily copy file in/out from container by below sample user case:
```python
// Launch testing container
>>> from atf.common.docker.client import *
>>> da = DockerAgent()
>>> test_img = da.images(name='atf_docker/test')[0]
>>> test_cnt = da.run(test_img, name='aft_demo')
>>> test_cnt.status
'running'

// Create test file in /tmp/test.txt
>>> import os
>>> os.system('echo "test file copy in/out" > /tmp/test.txt')

// Copy file into container and check the content of file
>>> test_cnt.copy_in('/tmp/test.txt', '/tmp/test_in_cnt.txt')
True
>>> rc, logs = test_cnt.exe_command('cat /tmp/test_in_cnt.txt')
>>> rc
0
>>> logs
test file copy in/out

// Modify /tmp/test_in_cnt.txt and copy it out to host
>>> rc, logs = test_cnt.exe_command('bash -c "echo abcdefg >> /tmp/test_in_cnt.txt"')
>>> rc
0
>>> test_cnt.copy_out('/tmp/test_in_cnt.txt', '/tmp/test_out_cnt.txt')
True

// Confirm the content of file /tmp/test_out_cnt.txt in host
>>> open('/tmp/test_out_cnt.txt', 'r').read()
'test file copy in/out\nabcdefg\n'
```

## Reference <a name='ref'/>
* [Python Debugging With Pdb](https://realpython.com/python-debugging-pdb/)
