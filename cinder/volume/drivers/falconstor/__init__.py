# Copyright (c) 2016 FalconStor, Inc.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.


from oslo_config import cfg
from oslo_log import log as logging

FSS_OPTS = [
    cfg.StrOpt('san_ip',
               default='127.0.0.1',
               help='FSS server ip.'),
    cfg.StrOpt('san_login',
               default='username',
               help='FSS login account.'),
    cfg.StrOpt('san_password',
               default='password',
               help='FSS login password.'),
    cfg.IntOpt('fss_pool',
               default='',
               help='FSS pool id in which FalconStor volumes are stored.'),
    cfg.StrOpt('additional_retry_list',
               default='',
               help='FSS additional retry list, separate by ;')
]

CONF = cfg.CONF
CONF.register_opts(FSS_OPTS)

LOG = logging.getLogger(__name__)


RETRY_LIST = ['107', '2147680512']
RETRY_CNT = 5
RETRY_INTERVAL = 15
OPERATION_TIMEOUT = 60 * 60


class FSSHTTPError(Exception):

    def __init__(self, target, response):
        super(FSSHTTPError, self).__init__()
        self.target = target
        self.code = response['code']
        self.text = response['text']
        self.reason = response['reason']

    def __str__(self):
        msg = ("FSSHTTPError code {0} returned by REST at {1}: {2}\n{3}")
        return msg.format(self.code, self.target,
                          self.reason, self.text)
