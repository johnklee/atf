#!/usr/bin/env python3
import os
import sys
sys.path.insert(0, os.getcwd())
import unittest
import tempfile
import shutil
import time
import requests
import pytest
import subprocess
from datetime import datetime
from atf.common.docker.client import DockerAgent, ContainerWP
from atf.framework.FrameworkBase import FrameworkError


CUR_TEST_DIR = os.path.dirname(os.path.realpath(__file__))
''' The directory of current py'''
REPO_ROOT_PATH = os.path.realpath(os.path.join(CUR_TEST_DIR, '../../../../'))
''' The path of repo root '''
CUR_TESTDATA_DIR = os.path.join(CUR_TEST_DIR, 'test_data')
''' The directory to hold testing data '''


class DockerAgentTest(unittest.TestCase):
    def setUp(self):
        da = DockerAgent(auto_clean_cnt=False)
        self.test_dir = tempfile.mkdtemp()
        self.test_img_name = 'atf_docker/test:latest'
        self.test_img_name2 = 'johnklee/atf_docker_test2:latest'
        self.hello_img_name = 'hello-world'
        self.test_build_path = os.path.join(CUR_TESTDATA_DIR, 'docker/images/test/')
        self.test_dockerfile_path = os.path.join(self.test_build_path, 'Dockerfile')
        test_image_list = da.images(name=self.test_img_name)
        if len(test_image_list) == 0:
            logs = da.build(path=self.test_build_path,
                            dockerfile=self.test_dockerfile_path,
                            tag=self.test_img_name,
                            pull=True)

            self.assertTrue(len(logs.grep('Successfully tagged atf_docker/test:latest')) > 0,
                            'Unexpected logs:\n{}\n'.format(logs))

        self.test_img = da.images(name=self.test_img_name)[0]
        self.test_img_id = self.test_img['Id']

        hello_image_list = da.images(name=self.hello_img_name)
        if len(hello_image_list) > 0:
            logs = da.remove_image(hello_image_list[0], force=True)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    @pytest.mark.image
    def test_api_remove_image(self):
        build_path = os.path.join(CUR_TESTDATA_DIR, 'docker/images/test/')
        dockerfile_path = os.path.join(build_path, 'Dockerfile')
        da = DockerAgent()

        # 0) Confirm that test image exist
        test_image_list = da.images(name=self.test_img_name)
        self.assertTrue(len(test_image_list) > 0, 'Test image={} does not exist!'.format(self.test_img_name))

        # 1) Remove test image
        da.remove_image(test_image_list[0], force=True)

        test_image_list = da.images(name=self.test_img_name)
        self.assertTrue(len(test_image_list) == 0, 'Test image={} should be removed!'.format(self.test_img_name))

    @pytest.mark.image
    def test_api_images(self):
        da = DockerAgent()
        # 1) Positive test case(s)

        # 1.1) Query test image
        image_list = da.images(name=self.test_img_name)
        self.assertTrue(len(image_list) == 1, 'Expect at least one image (testing image)!')
        img_test = image_list[0]
        self.assertTrue(isinstance(img_test, dict), 'Unexpected image type={}!'.format(img_test.__class__))
        self.assertTrue('Id' in img_test and img_test['Id'] == self.test_img_id, 'Unexpected test image={}!'.format(img_test))

        # 1.2) Query with parameter quiet
        img_id = da.images(name=self.test_img_name, quiet=1)[0]
        self.assertTrue(img_id == self.test_img_id)
        img_names = da.images(name=self.test_img_name, quiet=2)[0]
        self.assertTrue(self.test_img_name in img_names, 'Unexpected img_names={}'.format(img_names))
        img_tup = da.images(name=self.test_img_name, quiet=3)[0]
        self.assertTrue(img_tup[0] == self.test_img_id, 'Unexpected img_tup={}'.format(img_tup))
        self.assertTrue(self.test_img_name in img_tup[1], 'Unexpected img_tup={}'.format(img_tup))
        with pytest.raises(FrameworkError):
            da.images(name=self.test_img_name, quiet=4)

        # 1.3) Query name as function type
        def get_atf(name):
            return True if name.startswith('atf_') else False

        img_id = da.images(name=get_atf, quiet=1)[0]
        self.assertTrue(img_id == self.test_img_id)

        # 1.4) Query name as unexpected type. (e.g.: dict)
        with pytest.raises(FrameworkError):
            da.images(name={})

    @pytest.mark.image
    def test_api_pull(self):
        da = DockerAgent()
        image_list = da.images(name=self.hello_img_name)
        self.assertTrue(len(image_list) == 0, 'Unexpect hello-world image!')
        logs = da.pull(self.hello_img_name, tag='latest')
        self.assertTrue(len(logs.grep('Pull complete')) > 0, 'Unexpected logs:\n{}\n'.format(logs))
        image_list = da.images(name=self.hello_img_name)
        self.assertTrue(len(image_list) > 0, 'Expect hello-world image!')

    @pytest.mark.image
    def test_api_img2id(self):
        da = DockerAgent()
        self.assertEqual(self.test_img_id, da.img2id(self.test_img), 'Mismatch in test image id!')  
        self.assertEqual(self.test_img_id, da.img2id(self.test_img_name), 'Mismatch in test image id!')

    @pytest.mark.container
    def test_api_cn2id(self):
        # 1) Start container
        da = DockerAgent()
        cnt_name = 'atf_test'
        cnt_test = da.run(self.test_img_name, name=cnt_name)

        # 2) Get container ID and check API:cn2id
        cnt_test_id = da.cn2id(cnt_name)
        self.assertEqual(cnt_test.id, cnt_test_id,
                         'Unexpected container ID1={} (exp={})'.format(cnt_test_id, cnt_test.id))

        # 3) Stop container and then call API:cn2id with all=(True,False)
        cnt_test.stop()
        cnt_test_id = da.cn2id(cnt_name)
        self.assertEqual(cnt_test.id, cnt_test_id,
                         'Unexpected container ID2={} (exp={})'.format(cnt_test_id, cnt_test.id))

        cnt_test_id = da.cn2id(cnt_name, all=False)
        self.assertIsNone(cnt_test_id, 'Unexpected containerID3={}'.format(cnt_test_id))

    @pytest.mark.container
    def test_api_run(self):
        # 1) Start container
        da = DockerAgent()
        cnt_test = da.run(self.test_img_name, name='atf_test')
        self.assertTrue(isinstance(cnt_test, ContainerWP), 'Returned container object should be class ContainerWP')
        self.assertTrue(cnt_test.status == 'running', 'Unexpected container status={}'.format(cnt_test.status))

        # 2) Test container service
        time.sleep(3)
        test_url = 'http://{}:5000/'.format(cnt_test.ip['bridge'])
        print('access url={}'.format(test_url))
        resp = requests.get(test_url)
        self.assertTrue(resp.status_code==200, 'Unexpected status code={} to access test container'.format(resp.status_code))
        self.assertEqual(resp.text, 'Hello World!', 'Unexpected returned data={}!'.format(resp.text))

    @pytest.mark.container
    def test_host_config(self):
        # 1) Test volumes
        da = DockerAgent()
        mark_msg = datetime.now().strftime('%y%m%d%H%M%S')
        host_test_dir = os.path.join(self.test_dir, mark_msg)
        os.makedirs(host_test_dir)
        test_txt_name = 'test.txt'
        with open(os.path.join(host_test_dir, test_txt_name), 'w') as fw:
            fw.write(mark_msg)
        
        #   1.1) Create volume maping host test dir to /tmp/test in container
        #               port binding from 5000(cnt)->1234(host)
        cnt_bind_path = '/tmp/test'
        cnt_port = 5000
        host_port = 1234
        cnt_test = da.run(self.test_img_name, name='atf_test',
                          binds={host_test_dir:{'bind':cnt_bind_path, 'mode':'rw'}},
                          port_bindings={cnt_port: host_port})

        self.assertTrue(cnt_test.status == 'running', 'Unexpected container status={}'.format(cnt_test.status))
        #   1.2) Confirmed the volume is mounted in container
        rc, logs = cnt_test.exe_command('cat {}'.format(os.path.join(cnt_bind_path, test_txt_name)))
        self.assertTrue(rc == 0, 'Unexpected rc={} to check mounted volume!'.format(rc))
        #   1.3) Create another test file in container in mounted path and check host for it
        cnt_test_txt_name = 'test_cnt.txt'
        rc, logs = cnt_test.exe_command('bash -c "echo just4fun > {}"'.format(os.path.join(cnt_bind_path, cnt_test_txt_name)))
        self.assertTrue(rc == 0, 'Unexpected rc={} with logs:\n{}\n'.format(rc, logs))
        new_file_from_cnt = os.path.join(host_test_dir, cnt_test_txt_name)
        self.assertTrue(os.path.isfile(new_file_from_cnt), 'Missing file from container')
        with open(new_file_from_cnt, 'r') as fh:
            file_content = fh.read()
            self.assertTrue('just4fun' in file_content, 'Unexpected file_content=\'{}\''.format(file_content))

        # 2) Test port binding
        # rc, out = subprocess.getstatusoutput('lsof -i :1234')
        # self.assertTrue(rc == 0, 'Unexpected rc={}:\n{}\n'.format(rc, out))

        # Build server won't allow us to do it
        # test_url = 'http://localhost:{}/'.format(host_port)
        # print('access url={}'.format(test_url))
        # resp = requests.get(test_url)
        # self.assertTrue(resp.status_code==200, 'Unexpected status code={} to access test container'.format(resp.status_code))
        # self.assertEqual(resp.text, 'Hello World!', 'Unexpected returned data={}!'.format(resp.text))

    @pytest.mark.container
    def test_cnt_apis(self):
        # 1) Start container
        da = DockerAgent()
        cnt_test = da.run(self.test_img_name, name='atf_test')
        self.assertTrue(isinstance(cnt_test, ContainerWP), 'Returned container object should be class ContainerWP')
        self.assertTrue(cnt_test.status == 'running', 'Unexpected container status={}'.format(cnt_test.status))
        time.sleep(3)

        # 2) Test container APIs
        r'''
         * Serving Flask app "index" (lazy loading)
         * Environment: production
         WARNING: This is a development server. Do not use it in a prod         n deployment.
         Use a production WSGI server instead.
         * Debug mode: off
         * Running on http://0.0.0.0:5000/ (Press CTRL+C to quit)
        '''
        self.assertTrue(cnt_test.grep_logs('Running on http://0.0.0.0:5000/'), 'Unexpected logs:\n{}\n'.format(cnt_test.logs))
        self.assertTrue(hasattr(cnt_test, 'last_matched_line_num') and cnt_test.last_matched_line_num == 5)
        self.assertFalse(cnt_test.grep_logs('Serving Flask app'), 'grep should start from last success line!')
        cnt_test.last_matched_line_num = -1
        self.assertTrue(cnt_test.grep_logs('Serving Flask app'), 'Reset should let grep to start from first line!')

        #   2.1) Test API:exe_command
        rc, logs = cnt_test.exe_command('ls -hl', workdir='/app')
        self.assertTrue(rc == 0, 'Unexpected return code={}'.format(rc))
        self.assertTrue(logs.grep('index.py', quiet=True), 'Unexpected logs:\n{}\n'.format(logs))

        #   2.2) Test API:copy_in, API:copy_out
        test_txt = os.path.join(CUR_TESTDATA_DIR, 'test.txt')
        rt = cnt_test.copy_in(test_txt, '/tmp') 
        self.assertTrue(rt, 'Fail to copy file={} into container!'.format(test_txt))
        rc, logs = cnt_test.exe_command('cat /tmp/test.txt')
        self.assertTrue(rc == 0, 'Unexpected return code={}:\n{}\n'.format(rc, logs))
        self.assertTrue(logs.grep('This is for testing', quiet=True), 'Unexpected logs:\n{}\n'.format(logs))
        mark = 'abcdefg'
        rc, logs = cnt_test.exe_command('bash -c "echo {} >> /tmp/test.txt"'.format(mark))
        self.assertTrue(rc == 0, 'Unexpected return code={}:\n{}\n'.format(rc, logs))
        test_out_txt = os.path.join(self.test_dir, 'test_out.txt')
        rt = cnt_test.copy_out('/tmp/test.txt', test_out_txt)
        self.assertTrue(rt, 'Fail to copy file={} out of container!'.format(test_txt))
        content_of_test_out_txt = ''
        with open(test_out_txt) as fh:
            content_of_test_out_txt = fh.read()

        self.assertTrue(mark in content_of_test_out_txt,
                        'Unexpected content of out file:\n{}\n'.format(content_of_test_out_txt))

    @pytest.mark.container
    def test_feat_continuous_log_grepping(self):
        # 1) Start container
        da = DockerAgent()
        cnt_test = da.run(self.test_img_name2, name='atf_test')
        self.assertTrue(isinstance(cnt_test, ContainerWP), 'Returned container object should be class ContainerWP')
        self.assertTrue(cnt_test.status == 'running', 'Unexpected container status={}'.format(cnt_test.status))
        time.sleep(3)

        # 2) Grep logs
        # e.g.: [(0, 'Hi 0'), (1, 'Hi 1'), (2, 'Hi 2'), (3, 'Hi 3')]
        logs = cnt_test.grep_logs("Hi \d", quiet=False)
        self.assertTrue(len(logs) > 0, 'Unexpected empty logs')
        self.assertTrue(logs[0][0] == 0, 'Unexpected line number')
        self.assertTrue(logs[0][1] == 'Hi 0', 'Unexpected line number')
        time.sleep(2)
        # e.g.: [(4, 'Hi 4'), (5, 'Hi 5')]
        next_logs = cnt_test.grep_logs("Hi \d", quiet=False)
        self.assertTrue(next_logs[0][0] == logs[-1][0] + 1, f'Unexpected next logs={next_logs}')

    @pytest.mark.network
    def test_network_api(self):
        # 1) Start container
        da = DockerAgent()
        atf_net = da.create_network('atf_net')
        self.assertTrue('name' in atf_net and atf_net['name'] == 'atf_net',
                        'Unexpected atf_net={}!'.format(atf_net))

        # 2) Create two containers to connect same network
        cnt_test1 = da.run(self.test_img_name, name='atf_test1', nets=[atf_net])
        ip_setting1 = cnt_test1.ip
        self.assertTrue('bridge' in ip_setting1 and 'atf_net' in ip_setting1,
                        'Unexpected IP setting={}'.format(ip_setting1))

        cnt_test2 = da.run(self.test_img_name, name='atf_test2', nets=[atf_net])
        ip_setting2 = cnt_test2.ip
        self.assertTrue('bridge' in ip_setting2 and 'atf_net' in ip_setting2,
                        'Unexpected IP setting={}'.format(ip_setting2))

        # 3) Make sure two containers can ping each other through created network
        rc, out = cnt_test1.exe_command('ping -c 3 {}'.format(ip_setting2['atf_net']))
        self.assertTrue(rc == 0, 'Unexpected rc={} with out:\n{}\n'.format(rc, out))
