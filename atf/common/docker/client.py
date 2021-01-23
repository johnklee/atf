import os
import re
import sys
import time
import types
import docker
import logging
from atf.common.utils.dspawn import dspawn
from atf.framework.FrameworkBase import *  # noqa


################################
# Constants
################################
MODU_PATH = os.path.dirname(__file__) if os.path.dirname(__file__) else './'
''' Path of current module '''


################################
# Class Definition
################################
class LogOutput(object):
    r'''
    Wrapper of output from logs/exe_command
    '''
    def __init__(self, bin_output, encoding='utf8'):
        self.raw_data = bin_output
        self.encoding = encoding

    def __str__(self):
        if isinstance(self.raw_data, bytes):
            return self.raw_data.decode(self.encoding)
        else:
            return str(self.raw_data)

    def __repr__(self):
        return self.__str__()

    def grep(self, ptn, use_match=False, quiet=False, start_line_num=-1):
        '''grep the log message

        Parameters
        ----------
        ptn : string
            pattern to match line(s) from log

        use_match : bool
            True to use re.match to match line; otherwise re.search will be used

        quiet : bool
            True to return bool as matching result (True: Matched; False: Miss)
            False to return list of all matched line

        start_line_num : int
            Number of line to start grepping. (-1 or 0 means to grep from first line)

        Returns
        -------
        if `quiet` is True:
            bool as grepping result (True: match; False: miss)
        else:
            list of matched line(s)
        '''
        lines = str(self).split('\n')

        matched = []
        grep_method = re.match if use_match else re.search
        for line_num, line in enumerate(lines):
            if start_line_num > 0 and line_num < start_line_num:
                continue

            if grep_method(ptn, line):
                matched.append((line_num, line.strip()))

        if quiet:
            return len(matched) > 0
        else:
            return matched


class ContainerWP:
    r'''
    Wrapper of docker.models.containers.Container
    '''
    def __init__(self, container, da):
        self.c = container
        self.da = da
        for attr in ['id', 'labels', 'image', 'name', 'short_id']:
            setattr(self, attr, getattr(self.c, attr))

        self.last_matched_line_num = -1

    @property
    def attrs(self):
        return self.da.apiClient.inspect_container(self.id)

    @property
    def status(self):
        return self.attrs['State']['Status']

    @property
    def ip(self):
        attrs = self.da.apiClient.inspect_container(self.id)
        ip_setting = {}
        for net_name, net_setting in attrs['NetworkSettings']['Networks'].items():
            ip_setting[net_name] = net_setting['IPAddress']

        # return self.attrs['NetworkSettings']['IPAddress']
        return ip_setting

    @property
    def gateway(self):
        attrs = self.da.apiClient.inspect_container(self.id)
        gw_setting = {}
        for net_name, net_setting in attrs['NetworkSettings']['Networks'].items():
            gw_setting[net_name] = net_setting['Gateway']

        return gw_setting

    @property
    def mac(self):
        # return self.attrs['NetworkSettings']['MacAddress']
        attrs = self.da.apiClient.inspect_container(self.id)
        mac_setting = {}
        for net_name, net_setting in attrs['NetworkSettings']['Networks'].items():
            mac_setting[net_name] = net_setting['MacAddress']

        return mac_setting

    def top(self):
        return self.c.top()

    @property
    def logs(self):
        _logs = self.c.logs()
        log_output = LogOutput(_logs)
        return log_output

    def grep_logs(self, ptn, use_match=False, quiet=True, retry=5, wait=1):
        r'''Grep logs collected from container

        Parameters
        ----------
        ptn : str
            Pattern to search in logs

        use_match : bool
            True to use re.match to match line; otherwise re.search will be used

        quiet : bool
            True to return bool as matching result (True: Matched; False: Miss)
            False to return list of all matched line

        retry : int
            How many times to retry grepping

        wait : int
            How many seconds to wait for next round in searching when miss.
        '''
        retry_count = 0

        def _post_poc_grep_rst(grep_rst):
            if len(grep_rst) > 0:
                self.last_matched_line_num = grep_rst[-1][0]

            if quiet:
                return len(grep_rst) > 0
            else:
                return grep_rst

        while True:
            grep_rst = self.logs.grep(ptn, use_match, quiet=False, start_line_num=self.last_matched_line_num + 1)
            if grep_rst:
                return _post_poc_grep_rst(grep_rst)

            retry_count += 1
            if retry_count >= retry:
                return _post_poc_grep_rst(grep_rst)

            time.sleep(wait)

    def exe_command(self, cmd, stdout=True, stderr=True, stdin=False, tty=True, privileged=True, user='', environment=None,
                    workdir=None, detach_keys=None, detach=False, stream=False, socket=False, demux=False):
        r'''
        exe_obj = self.da.apiClient.exec_create(self.id, cmd=cmd, stdout=stdout, stderr=stderr, stdin=stdin, tty=tty,
                                                privileged=privileged, user=user, environment=environment, workdir=workdir,
                                                detach_keys=detach_keys)

        exe_out = self.da.apiClient.exec_start(exe_obj, detach=detach, tty=tty, stream=stream, socket=socket, demux=demux)
        '''
        exit_code, exe_out = self.c.exec_run(cmd=cmd, stdout=stdout, stderr=stderr, stdin=stdin, tty=tty, privileged=privileged,
                                             user=user, detach=detach, stream=stream, socket=socket, environment=environment,
                                             workdir=workdir, demux=demux)

        return (exit_code, LogOutput(exe_out))

    def copy_in(self, from_path, to_path, depress_except=False):
        r'''
        Copy file from host into container
        '''
        return self.da.copy2cont(self.id, from_path, to_path, depressExcept=depress_except)

    def copy_out(self, from_path, to_path, depress_except=False):
        r'''
        Copy file from container out to host
        '''
        return self.da.copy_from_cnt(self.id, from_path, to_path, depressExcept=depress_except)

    def start(self):
        r'''
        Start a container. Similar to the `docker start command`, but doesn't support attach options.
        '''
        self.da.apiClient.start(container=self.id)

    def stop(self, timeout=10):
        r'''
        Stops a container. Similar to the 'docker stop' command.

        @param timeout (int):
            Timeout in seconds to wait for the container to stop before sending a SIGKILL. Default: 10
        '''
        self.da.apiClient.stop(container=self.id, timeout=timeout)

    def restart(self, timeout=10):
        r'''
        Restart a container. Similar to the 'docker restart' command.

        @parm timeout (int):
            Number of seconds to try to stop for before killing the container.
            Once killed it will then be restarted. Default is 10 seconds.
        '''
        self.da.apiClient.restart(container=self.id, timeout=timeout)


class DockerAgent(FrameworkBase):
    ###
    # Class error definitions
    ###
    (CMD_TIMEOUT) = FrameworkError.ERR_DOCKER
    (API_ERROR) = FrameworkError.ERR_DOCKER + 1

    ###
    # Common Commands
    ###
    (DOCKER_ENV) = ''
    (CMD_DOCKER) = DOCKER_ENV + "docker"
    """ BASH interpreter """
    (CMD_DOCKER_EXEC) = CMD_DOCKER + " exec -t -i %s %s"
    """ The 'docker exec' command runs a new command in a running container. """
    (CMD_DOCKER_INSPECT_PID) = CMD_DOCKER + "  inspect -f '{{.State.Pid}}' %s"
    """ Obtain process ID corresponding to container """
    (CMD_DOCKER_VERSION) = CMD_DOCKER + " --version"
    (CMD_DOCKER_PS) = CMD_DOCKER + " ps"
    (CMD_DOCKER_CP) = CMD_DOCKER + " cp "

    def __init__(self, base_url='unix://var/run/docker.sock', diagLevel=logging.WARNING,
                 auto_clean_cnt=True, auto_clean_net=True):
        FrameworkBase.__init__(self, diagLevel=diagLevel)
        self.cons = dspawn('bash')
        self.client = docker.from_env()
        self.apiClient = docker.APIClient(base_url)
        self.created_container_ids = set()
        self.created_network_ids = set()
        self.auto_clean_cnt = auto_clean_cnt
        self.auto_clean_net = auto_clean_net

    @property
    def networks(self):
        r'''
        Create and manage networks on the server.

        @see:
            https://docker-py.readthedocs.io/en/stable/networks.html#
            https://docs.docker.com/engine/userguide/networking/
        '''
        return self.client.networks

    @property
    def version(self, short=True):
        r'''
        Show version of current docker daemon

        @param short(bool):
            True to show Version only
        '''
        if not hasattr(self, '_version'):
            self._version = self.client.version()

        if short:
            return self._version['Version']
        else:
            return self._version

    def _wgen(self, gen):
        r'''
        Wrap generator into {LogOutput} object
        '''
        if isinstance(gen, str):
            return LogOutput(gen)

        out_msg = ''
        for msg in gen:
            self.logger.debug(msg)
            if isinstance(msg, bytes):
                out_msg += msg.decode('utf8')
            else:
                for k, v in msg.items():
                    out_msg += v

        return LogOutput(out_msg)

    def build(self, **kwargs):
        r'''
        Build an image and return it. Similar to the 'docker build' command.
        Either path or fileobj must be set.

        @param path (str):
            Path to the directory containing the Dockerfile

        @param fileobj:
            A file object to use as the Dockerfile. (Or a file-like object)

        @param tag (str):
            A tag to add to the final image

        @param quiet (bool):
            Whether to return the status

        @param nocache (bool):
            Don't use the cache when set to True

        @param rm (bool):
            Remove intermediate containers. The 'docker build' command now defaults to --rm=true,
            but we have kept the old default of False to preserve backward compatibility

        @param stream (bool):
            Deprecated for API version > 1.8 (always True).
            Return a blocking generator you can iterate over to retrieve build output as it happens

        @param timeout (int):
            HTTP timeout

        @param custom_context (bool):
            Optional if using fileobj

        @param encoding (str):
            The encoding for a stream. Set to gzip for compressing

        @param pull (bool):
            Downloads any updates to the FROM image in Dockerfiles

        @param forcerm (bool):
            Always remove intermediate containers, even after unsuccessful builds

        @param dockerfile (str)
            path within the build context to the Dockerfile

        @param buildargs (dict):
            A dictionary of build arguments

        @param container_limits (dict):
            A dictionary of limits applied to each container created by the build process.

        @param decode (bool):
            If set to True, the returned stream will be decoded into dicts on the fly. Default False.

        @param cache_from (list):
            A list of images used for build cache resolution.

        @return:
            The built logs

        @see:
            https://docker-py.readthedocs.io/en/stable/images.html#docker.models.images.ImageCollection.build
        '''
        if 'path' in kwargs:
            kwargs['path'] = os.path.abspath(kwargs['path'])

        if 'dockerfile' in kwargs:
            kwargs['dockerfile'] = os.path.abspath(kwargs['dockerfile'])
        elif 'dockerfile' not in kwargs and 'path' in kwargs:
            kwargs['dockerfile'] = os.path.join(kwargs['path'], 'Dockerfile')

        if 'forcerm' not in kwargs:
            kwargs['forcerm'] = True

        if 'rm' not in kwargs:
            kwargs['rm'] = True

        gen = self.apiClient.build(**kwargs)
        return self._wgen(gen)

    def containers(self, all=False, quiet=0, limit=-1, filters=None, name=None):
        r'''
        List containers. Mapping to command 'docker ps'.

        @param all(bool):
            True to show all containers. Only running containers are shown by default

        @param quiet(int):
            quiet=0: Show all information
            quiet=1: Only display numeric Ids
            quiet=2: Only display the name of container(s)

        @param limit (int):
            Show limit last created containers, include non-running ones

        @param filters (dict):
            Filters to be processed on the image list. Available filters:
            - exited (int): Only containers with specified exit code
            - status (str): One of restarting, running, paused, exited
            - label (str): format either "key" or "key=value"
            - id (str): The id of the container.
            - name (str): The name of the container.
            - ancestor (str): Filter by container ancestor. Format of
              <image-name>[:tag], <image-id>, or <image@digest>.
            - before (str): Only containers created before a particular
              container. Give the container name or id.
            - since (str): Only containers created after a particular
              container. Give container name or id.

            A comprehensive list can be found in the documentation for docker ps.

        @param name(re|lambda):
            Name of container(s) to filter out

        @return
            List of container
        '''
        cns = self.client.containers.list(limit=limit, filters=filters, all=all)

        if name:
            if isinstance(name, types.FunctionType):
                # Lambda object
                cns = [cn for cn in cns if name(cn.name)]
            elif isinstance(name, type(re.compile('.'))):
                # Regular expression object
                cns = [cn for cn in cns if name.match(cn.name)]
            else:
                # Unknown object
                raise (FrameworkError(DockerAgent.API_ERROR, 'Illegal parameter type (name={})'.format(type(name))))

        if quiet == 1:
            # Show ID of container(s) only
            return [cnt.id for cnt in cns]
        elif quiet == 2:
            # Show Name of container(s) only
            return [cnt.name for cnt in cns]
        else:
            return list(map(lambda cnt: ContainerWP(cnt, self), cns))
            # return cns

    def copy_from_cnt(self, container_id, from_path, to_path, depressExcept=False):
        r'''
        Identical to the "docker cp" command. Copy file/folders out of container to host.

        @see:
            https://docs.docker.com/engine/reference/commandline/cp/

        @param from_path (str):
            File/Folder path inside container
        @param to_path (str):
            Destination path from host of copy action
        @param container_id (str):
            The id of target container to copy into.

        @return:
            (str): The contents of the file as a string
        '''
        self.cons.sendline("%s %s:%s %s" % (DockerAgent.CMD_DOCKER_CP, container_id, from_path, to_path))
        expect_resp = [
            'must specify at least one container source',
            'No such container',
            'no such file or directory',
            self.cons.PROMPT
        ]
        rt = self.cons.expect(expect_resp)
        if depressExcept:
            if rt + 1 < len(expect_resp):
                return False
            else:
                return True
        else:
            if rt == 0:
                raise (FrameworkError(DockerAgent.CMD_TIMEOUT, 'Must specify at least one container source (docker cp)'))
            elif rt == 1:
                raise (FrameworkError(DockerAgent.CMD_TIMEOUT, 'No such container (docker cp)'))
            elif rt == 2:
                raise (FrameworkError(DockerAgent.CMD_TIMEOUT, 'No such file or directory (docker cp)'))
            else:
                return True

    def copy2cont(self, container_id, from_path, to_path, depressExcept=False):
        r'''
        Identical to the "docker cp" command. Copy files/folders from local to the container.

        @see:
            https://docs.docker.com/engine/reference/commandline/cp/

        @param from_path (str):
            File/Folder path from local
        @param to_path (str):
            Destination path inside container of copy action
        @param container_id (str):
            The id of target container to copy into.

        @return:
            (str): The contents of the file as a string
        '''
        self.cons.sendline("%s %s %s:%s" % (DockerAgent.CMD_DOCKER_CP, from_path, container_id, to_path))
        expect_resp = [
            'must specify at least one container source',
            'No such container',
            'no such file or directory',
            self.cons.PROMPT
        ]

        rt = self.cons.expect(expect_resp)
        if depressExcept:
            if rt + 1 < len(expect_resp):
                return False
            else:
                return True
        else:
            if rt == 0:
                raise (FrameworkError(DockerAgent.CMD_TIMEOUT, 'Must specify at least one container source (docker cp)'))
            elif rt == 1:
                raise (FrameworkError(DockerAgent.CMD_TIMEOUT, 'No such container (docker cp)'))
            elif rt == 2:
                raise (FrameworkError(DockerAgent.CMD_TIMEOUT, 'No such file or directory (docker cp)'))
            else:
                return True

    def cn2id(self, container_name, all=True):
        r'''
        Translate name of container into corresponding container id

        @param container_name(str):
            Name of container
        @param all(bool):
            True to search all container(s); False to search only container in running status.

        @return
            Container id or None if the input container name doesn't exist.
        '''
        cnts = self.containers(filters={'name': container_name}, all=all)
        if len(cnts) == 1:
            return cnts[0].id
        else:
            return None

    def create_container(self, image, command=None, hostname=None, user=None, detach=False, stdin_open=False, tty=False,
                         ports=None, environment=None, volumes=None, network_disabled=False, name=None, entrypoint=None,
                         working_dir=None, domainname=None, host_config=None, mac_address=None, labels=None, stop_signal=None,
                         networking_config=None, healthcheck=None, stop_timeout=None, runtime=None, use_config_proxy=True):
        r'''
        Creates a container. Parameters are similar to those for the
        docker run command except it doesn't support the attach options (-a).

        @param image (str):
            The image to run
        @param command (str or list):
            The command to be run in the container
        @param hostname (str):
            Optional hostname for the container
        @param user (str or int):
            Username or UID
        @param detach (bool):
            Detached mode: run container in the background and return container ID
        @param stdin_open (bool):
            Keep STDIN open even if not attached
        @param tty (bool):
            Allocate a pseudo-TTY
        @param mem_limit (float or str):
            Memory limit. Accepts float values (which represent the memory
            limit of the created container in bytes) or a string with a
            units identification char (100000b, 1000k, 128m, 1g). If a
            string is specified without a units character, bytes are
            assumed as an intended unit.
        @param ports (list of ints):
            A list of port numbers opened inside container
        @param environment (dict or list):
            A dictionary or a list of strings in the following
            format ["PASSWORD=xxx"] or {"PASSWORD": "xxx"}.
        @param volumes (str or list):
            List of paths inside the container to use as volumes.
        @param network_disabled (bool):
            Disable networking
        @param name (str):
            A name for the container
        @param entrypoint (str or list):
            An entrypoint
        @param working_dir (str):
            Path to the working directory
        @param domainname (str or list):
            Set custom DNS search domains
        @param host_config (dict):
            A dictionary created with create_host_config()
        @param mac_address (str):
            The Mac Address to assign the container
        @param labels (dict or list):
            A dictionary of name-value labels (e.g. {"label1": "value1", "label2": "value2"})
            or a list of names of labels to set with empty values (e.g. ["label1", "label2"])
        @param stop_signal (str):
            The stop signal to use to stop the container (e.g. SIGINT).
        @param stop_timeout (int):
            Timeout to stop the container, in seconds. Default: 10
        @param networking_config (dict):
            A networking configuration generated by create_networking_config().
        @param runtime (str):
            Runtime to use with this container.
        @param healthcheck (dict):
            Specify a test to perform to check that the container is healthy.
        @param use_config_proxy (bool):
            If True, and if the docker client configuration file (~/.docker/config.json by default) contains a proxy configuration,
            the corresponding environment variables will be set in the container being created.

        @return:
            A dictionary with an image 'Id' key and a 'Warnings' key.

        @see
            https://docker-py.readthedocs.io/en/stable/api.html#docker.api.container.ContainerApiMixin.create_container
        '''
        if name is None:
            name = 'atf_' + str(int(time.time()))

        # e.g. {u'Id': u'57974c7820aa1e7da661930064c56032a7788f748d101831929a0ad6df615407', u'Warnings': None}
        if not image:
            raise (FrameworkError(DockerAgent.API_ERROR, 'Illegal image name=\'{}\''.format(image)))

        if isinstance(image, dict):
            image = image['Id']

        try:
            return self.apiClient.create_container(image=image, command=command, hostname=hostname, user=user, detach=detach,
                                                   stdin_open=stdin_open, tty=tty, ports=ports, environment=environment,
                                                   volumes=volumes, network_disabled=network_disabled, name=name,
                                                   entrypoint=entrypoint, working_dir=working_dir, domainname=domainname,
                                                   host_config=host_config, mac_address=mac_address, labels=labels,
                                                   stop_signal=stop_signal, networking_config=networking_config,
                                                   healthcheck=healthcheck, stop_timeout=stop_timeout, runtime=runtime)
        except docker.errors.APIError as err:
            raise (FrameworkError(DockerAgent.API_ERROR, 'Fail in creating container: {}'.format(str(err))))
        except:
            raise (FrameworkError(DockerAgent.API_ERROR, 'Unexpected error: {}'.format(sys.exc_info()[0])))

    def images(self, name=None, quiet=0, all=False, filters=None):
        r'''
        List images. Similar to the "docker images" command.

        @param name (str):
            Only show images belonging to the repository name (e.g. 'neuromancer/function_test:latest')
        @param quiet (int):
            0. Return the complete list
            1. Only return numeric IDs as a list.
            2. Only return name(s) as a list.
            3. Only return tuple of (id, name list)
        @param all (bool):
            Show intermediate image layers. By default, these are filtered out.
        @param filters (dict):
            Filters to be processed on the image list. Available filters:
                - dangling (bool)
                - label (str): format either key or key=value
        @return:
            A list if quiet=True, otherwise a dict.

        @see:
            https://docker-py.readthedocs.io/en/stable/api.html#docker.api.image.ImageApiMixin.images
        '''
        # Querying
        if name is None or isinstance(name, str):
            rt_list = self.apiClient.images(name=name, quiet=False, all=all, filters=filters)
        elif isinstance(name, types.FunctionType):
            rt_list = self.apiClient.images(quiet=False, all=all, filters=filters)
            tp_list = []
            for img in rt_list:
                if img['RepoTags']:
                    for n in img['RepoTags']:
                        if name(n):
                            tp_list.append(img)
                            break

            rt_list = tp_list
        else:
            # Unexpected argument type
            raise (FrameworkError(DockerAgent.API_ERROR, 'Illegal parameter type (name={})'.format(name)))

        # Selection of output
        if quiet == 0:
            return rt_list
        elif quiet == 1:
            # image id only
            return [e['Id'] for e in rt_list]
        elif quiet == 2:
            # name only
            return [e['RepoTags'] for e in rt_list]
        elif quiet == 3:
            # (id, name list)
            return [(e['Id'], e['RepoTags']) for e in rt_list]
        else:
            # Unexpected argument value
            raise (FrameworkError(DockerAgent.API_ERROR, 'Illegal parameter value (quiet={})'.format(quiet)))

    def img2id(self, image_name):
        r'''
        Translate image name into corresponding image id

        @param image_name:
            Name of image
        '''
        if isinstance(image_name, dict) and 'Id' in image_name:
            return image_name['Id']

        img_list = self.images(image_name, quiet=1)
        if not len(img_list) == 1:
            raise (FrameworkError(DockerAgent.API_ERROR, 'The image name=\'{}\' does not exist!'.format(image_name)))

        return img_list[0]

    def kill(self, container, signal=None):
        r'''
        Kill a container or send a signal to a container.

        @param container (str):
            The id of container to kill
        @param signal (str or int):
            The signal to send. Defaults to SIGKILL

        @see:
            https://docker-py.readthedocs.io/en/stable/api.html#docker.api.container.ContainerApiMixin.kill
        '''
        self.apiClient.kill(container=container, signal=signal)

    def pause(self, container):
        r'''
        Pauses all processes within a container.

        @param container (str):
            The container to pause

        @see:
            https://docker-py.readthedocs.io/en/stable/api.html#docker.api.container.ContainerApiMixin.pause
        '''
        self.apiClient.pause(container)

    def prune_containers(self, filters=None):
        r'''
        Delete stopped containers

        @param filters (dict):
            Filters to process on the prune list.

        @return
            A dict containing a list of deleted container IDs and
            the amount of disk space reclaimed in bytes.

        @see:
            https://docker-py.readthedocs.io/en/stable/api.html#docker.api.container.ContainerApiMixin.prune_containers
        '''
        self.apiClient.prune_containers(filters=filters)

    def pull(self, repository, tag=None, stream=False, auth_config=None, decode=False, platform=None):
        r'''
        Pulls an image. Similar to the "docker pull" command.

        @param repository (str):
            The repository to pull
        @param tag (str):
            The tag to pull
        @param stream (bool):
            Stream the output as a generator
        @param auth_config (dict):
            Override the credentials that login() has set for this request.
            auth_config should contain the 'username' and 'password' keys to be valid.
        @param decode (bool):
            Decode the JSON data from the server into dicts. Only applies with stream=True
        @param platform (str):
            Platform in the format os[/arch[/variant]]

        @return:
            {LogOutput} object

        @see:
            https://docker-py.readthedocs.io/en/stable/api.html#docker.api.image.ImageApiMixin.pull
        '''
        try:
            gen = self.apiClient.pull(repository=repository, tag=tag, stream=stream, auth_config=auth_config,
                                      decode=decode, platform=platform)

            return self._wgen(gen)
        except docker.errors.ImageNotFound:
            raise (FrameworkError(DockerAgent.API_ERROR, 'Image Not Found ({})'.format(repository)))
        except:
            raise (FrameworkError(DockerAgent.API_ERROR, 'Unexpected error: {}'.format(sys.exc_info()[0])))

    def remove_container(self, container, v=False, link=False, force=False):
        r'''
        Remove a container. Similar to the 'docker rm' command.

        @param container (str|lambda|re):
            The container to remove
        @parm v (bool):
            Remove the volumes associated with the container
        @param link (bool):
            Remove the specified link and not the underlying container
        @param force (bool):
            Force the removal of a running container (uses SIGKILL)
        '''
        if isinstance(container, str):
            return self.apiClient.remove_container(container=container, v=v, link=link, force=force)
        elif isinstance(container, type(re.compile('.'))) or isinstance(container, types.FunctionType):
            # re/lambda object to match name of container(s)
            rcnt = 0
            for cnt_id in self.containers(quiet=1, all=True, name=container):
                self.logger.debug('Remove container with id={}...'.format(cnt_id))
                self.apiClient.remove_container(container=cnt_id, v=v, link=link, force=force)
                rcnt = rcnt + 1
            return rcnt
        elif isinstance(container, dict):
            return self.apiClient.remove_container(container=container['Id'], v=v, link=link, force=force)
        elif isinstance(container, docker.models.containers.Container) or isinstance(container, ContainerWP):
            return self.apiClient.remove_container(container=container.id, v=v, link=link, force=force)
        else:
            # Unknown object
            raise (FrameworkError(DockerAgent.API_ERROR, 'Illegal parameter type (name={})'.format(type(container))))

    def remove_image(self, image, force=False, noprune=False, ignoreINF=True):
        r'''
        Remove an image. Similar to the 'docker rmi' command.

        @param image (str):
            The image to remove
        @param force (bool):
            Force removal of the image
        @param noprune (bool):
            Do not delete untagged parents
        @param ignoreINF (bool):
            Ignore exception of image not found.

        @see:
            https://docker-py.readthedocs.io/en/stable/api.html#docker.api.image.ImageApiMixin.remove_image
        '''
        try:
            if isinstance(image, dict) and 'Id' in image:
                image = image['Id']

            logs = self.apiClient.remove_image(image=image, force=force, noprune=noprune)
            return self._wgen(logs)
        except docker.errors.ImageNotFound:
            if ignoreINF:
                pass
            else:
                raise (FrameworkError(DockerAgent.API_ERROR, 'Image Not Found ({})'.format(image)))
        except:
            raise (FrameworkError(DockerAgent.API_ERROR, 'Unexpected error: {}'.format(sys.exc_info()[0])))

    def rename(self, container, name):
        r'''
        Rename a container. Similar to the docker rename command.

        @param container (str):
            ID of the container to rename
        @param name (str):
            New name for the container
        '''
        self.apiClient.rename(container=container, name=name)

    def restart(self, container, timeout=10):
        r'''
        Restart a container. Similar to the 'docker restart' command.

        @param container (str or dict):
            The container to restart. If a dict, the Id key is used.
        @parm timeout (int):
            Number of seconds to try to stop for before killing the container.
            Once killed it will then be restarted. Default is 10 seconds.
        '''
        self.apiClient.restart(container=container, timeout=timeout)

    def run(self, image, command=None, hostname=None, user=None, detach=False, stdin_open=False, tty=False,
            ports=None, environment=None, volumes=None, network_disabled=False, name=None, entrypoint=None, working_dir=None,
            domainname=None, host_config=None, mac_address=None, labels=None, stop_signal=None, networking_config=None,
            healthcheck=None, stop_timeout=None, nets=None, binds=None, port_bindings=None):
        r'''
        Create the container and run it as well.

        @param net(str/dict):
            Network to connect by created container
        @param binds(dict):
            A dictionary to configure volumes mounted inside the container.
            The key is either the host path or a volume name, and the value is a dictionary with the keys:
            * bind: The path to mount the volume inside the container
            * mode: Either rw to mount the volume read/write, or ro to mount it read-only.

            For example:
            >>> binds={'/home/user1/': {'bind': '/mnt/vol2', 'mode': 'rw'}, '/var/www': {'bind': '/mnt/vol1', 'mode': 'ro'}}

        @param port_bindings(dict):
            Port binding is done in two parts:
            first, provide a list of ports to open inside the container with the ports parameter,
            then declare bindings with the host_config parameter. For example:

            For example:
            port_bindings={5000: 1234} will map port 5000 inside container to host port 1234

        @return:
            dict with key 'Id' with value as container id;
                      key 'Warnings' with value as warning message.
        '''
        if (binds or port_bindings) and host_config is None:
            chc_kargs = {}
            if binds:
                chc_kargs['binds'] = binds
            if port_bindings:
                chc_kargs['port_bindings'] = port_bindings
                ports = list(port_bindings.keys())

            host_config = self.apiClient.create_host_config(**chc_kargs)

        cont_dict = self.create_container(image=image, command=command, hostname=hostname, user=user, detach=detach, stdin_open=stdin_open,
                                          tty=tty, ports=ports, environment=environment, volumes=volumes, network_disabled=network_disabled,
                                          name=name, entrypoint=entrypoint, working_dir=working_dir, domainname=domainname,
                                          host_config=host_config, mac_address=mac_address, labels=labels, stop_signal=stop_signal,
                                          networking_config=networking_config, healthcheck=healthcheck, stop_timeout=stop_timeout)

        self.start(cont_dict)
        cont_obj = self.containers(filters={'id': cont_dict['Id']})[0]
        self.created_container_ids.add(cont_obj.id)
        if nets:
            for net in nets:
                if isinstance(net, str):
                    net_id = net
                elif isinstance(net, dict) and 'Id' in net:
                    net_id = net['Id']
                else:
                    self.logger.warn('Unknown net={}!'.format(net))
                    continue

                if net_id:
                    self.logger.debug('Connecting container({}) to network({})...'.format(cont_obj.id, net_id))
                    self.apiClient.connect_container_to_network(cont_obj.id, net_id)

        # return ContainerWP(cont_obj, self)
        return cont_obj

    def create_network(self, name, driver="bridge", options=None, ipam=None, check_duplicate=None, internal=False, labels=None,
                       enable_ipv6=False, attachable=None, scope=None, ingress=None):
        r'''
        Create a network. Similar to the `docker network create`.

        @param name (str):
            Name of the network
        @param driver (str):
            Name of the driver used to create the network
        @param options (dict):
            Driver options as a key-value dictionary
        @param ipam (IPAMConfig):
            Optional custom IP scheme for the network.
        @param check_duplicate (bool):
            Request daemon to check for networks with same name. Default: None.
        @param internal (bool):
            Restrict external access to the network. Default False.
        @param labels (dict):
            Map of labels to set on the network. Default None.
        @param enable_ipv6 (bool):
            Enable IPv6 on the network. Default False.
        @param attachable (bool):
            If enabled, and the network is in the global scope, non-service containers on worker nodes will be able to connect to the network.
        @param scope (str):
            Specify the network’s scope ('local', 'global' or 'swarm')
        @param ingress (bool):
            If set, create an ingress network which provides the routing-mesh in swarm mode.

        @return:
            The created network reference object

        @see:
            https://docker-py.readthedocs.io/en/stable/api.html#docker.api.network.NetworkApiMixin.create_network
        '''
        net_dict = self.apiClient.create_network(name=name, driver=driver, options=options, ipam=ipam, check_duplicate=check_duplicate,
                                                 internal=internal, labels=labels, enable_ipv6=enable_ipv6, attachable=attachable,
                                                 scope=scope, ingress=ingress)

        self.created_network_ids.add(net_dict['Id'])
        net_dict['name'] = name
        return net_dict

    def prune_networks(self, filters=None):
        r'''
        Delete unused networks

        @param  filters (dict):
            Filters to process on the prune list.

        @return (dict):
            A dict containing a list of deleted network names and
            the amount of disk space reclaimed in bytes.
        '''
        return self.apiClient.prune_networks(filters=filters)

    def inspect_network(net_id, verbose=None, scope=None):
        r'''
        Get detailed information about a network.

        @param net_id (str):
            ID of network
        @param verbose (bool):
            Show the service details across the cluster in swarm mode.
        @param scope (str):
            Filter the network by scope (swarm, global or local).
        '''
        return self.apiClient.inspect_network(net_id=net_id, verbose=verbose, scope=scope)

    def remove_network(self, net_id):
        r'''
        Remove a network. Similar to the `docker network rm` command.

        @param net_id (str):
            The network’s id
        '''
        return self.apiClient.remove_network(net_id)

    def __del__(self):
        if self.cons is not None:
            self.cons.close(force=True)
            self.cons = None

        if self.auto_clean_cnt:
            for cid in self.created_container_ids:
                cnt_list = self.containers(filters={'id': cid}, all=True)
                for cnt in cnt_list:
                    self.logger.debug('Remove container with id={}...'.format(cnt.id))
                    self.remove_container(cnt.id, force=True)

                for cnt in self.containers(all=True):
                    if cnt.status == 'created':
                        self.logger.debug('Remove container with id={}...'.format(cnt.id))
                        self.remove_container(cnt.id, force=True)

        if self.auto_clean_net:
            for nid in self.created_network_ids:
                self.logger.debug('Remove network with id={}...'.format(nid))
                self.remove_network(nid)

    def start(self, container):
        r'''
        Start a container. Similar to the docker start command, but doesn't support attach options.

        @param container (str):
            The container to start
        '''
        self.apiClient.start(container=container)

    def stop(self, container, timeout=10):
        r'''
        Stops a container. Similar to the 'docker stop' command.

        @param container (str):
            The container to stop
        @param timeout (int):
            Timeout in seconds to wait for the container to stop before sending a SIGKILL. Default: 10
        '''
        self.apiClient.stop(container=container, timeout=timeout)

    def exit(self):
        if self.cons is not None:
            self.cons.close(force=True)
            self.cons = None
