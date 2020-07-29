import os
import sys
sys.path.insert(0, os.getcwd())
from atf.common.docker.client import *


try:
  ATF_CNT_GREP_RETRY = int(os.environ.get('ATF_CNT_GREP_RETRY', 60))
  ''' Retry number while grep log from container '''

  ATF_CNT_GREP_WAIT = int(os.environ.get('ATF_CNT_GREP_WAIT', 1))
  ''' Wait in second while fail in grep log from container '''
except:
  ATF_CNT_GREP_RETRY = 60
  ATF_CNT_GREP_WAIT = 1
  print('Unexpected error while setup ATF_CNT_GREP_RETRY(default={}) or ATF_CNT_GREP_WAIT(default={})!'.format(ATF_CNT_GREP_RETRY, ATF_CNT_GREP_WAIT))


def grep_cnt_logs(container_name, log_pattern, use_match=False, quiet=True, retry=ATF_CNT_GREP_RETRY, wait=ATF_CNT_GREP_WAIT, exit_after=True):
  r'''
  Grep log from target container

  :container_name: Name of container
  :log_pattern: log message to look for
  :use_match: True to use re.match; False to use re.search instead.
  :quite: True to return bool to stand for the matching result; False to return matched line(s) as list
  :retry: Retry number
  :wait: Wait in second for each retry
  '''
  da = DockerAgent()
  matched_containers = da.containers(filters={'name': container_name})
  if len(matched_containers) == 0:
    print("Container={} does not exist!".format(container_name))
    rc = 1

  else:
    cnt = matched_containers[0]
    if cnt.grep_logs(log_pattern, retry=retry, use_match=use_match, quiet=quiet, wait=wait):
      print("Found!")
      rc = 0
    else:
      print("Not Found!")
      rc = 2

  if exit_after:
    sys.exit(rc)
