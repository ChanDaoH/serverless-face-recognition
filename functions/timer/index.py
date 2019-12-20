# -*- coding: utf-8 -*-
import logging
import json

from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.auth.credentials import StsTokenCredential
from aliyunsdkfnf.request.v20190315.StartExecutionRequest import StartExecutionRequest

"""
This function will be invoked by FC time trigger.
time trigger payload example:
{"flowName": "YourFlowName", "input": "{\"bucket\": \"YourBucketName\",\"prefix\":\"\"}"}
"""

def handler(event, context):
  logger = logging.getLogger()
  evt = json.loads(event)
  logger.info("Handling event: %s", evt)
  creds = context.credentials
  endpoint = '{}-internal.fnf.aliyuncs.com'.format(context.region)
  if creds.security_token != None:
    sts_creds = StsTokenCredential(creds.access_key_id, creds.access_key_secret, creds.security_token)
    fnf_client = AcsClient(credential=sts_creds, region_id=context.region)
  else:
    # for local testing
    fnf_client = AcsClient(creds.access_key_id, creds.access_key_secret, context.region)
    endpoint = str.replace(endpoint, "-internal", "")
  payload = evt.get('payload', '{}')
  data = json.loads(payload)
  logger.info(json.loads(data.get('input', '')))
  request = StartExecutionRequest()
  request.set_FlowName(data.get('flowName', ''))
  request.set_Input(data.get('input', ''))
  request.set_endpoint(endpoint)
  fnf_client.do_action_with_exception(request)
