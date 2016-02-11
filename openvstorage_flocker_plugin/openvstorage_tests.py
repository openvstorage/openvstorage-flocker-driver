# Copyright 2015 iNuron NV
#
# Licensed under the Open vStorage Modified Apache License (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.openvstorage.org/license
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import yaml

from twisted.trial.unittest import SkipTest

from flocker.node.agents.test.test_blockdevice import (
    make_iblockdeviceapi_tests)
from openvstorage_flocker_plugin.openvstorage_blockdevice import (
    OpenvStorageBlockDeviceAPI)


def read_config():
    config_file = os.getenv('VPOOL_FLOCKER_CONFIG_FILE',
                            '/etc/flocker/agent.yml')
    with open(config_file) as fh:
        config = yaml.load(fh.read())
        return config['dataset']['vpool_conf_file']

    raise SkipTest('Could not open config file')


def openvstorageblockdeviceapi_for_test(test_case):
    conf = read_config()
    ovsapi = OpenvStorageBlockDeviceAPI(conf)
    test_case.addCleanup(ovsapi.destroy_all_flocker_volumes)
    return ovsapi


class OpenvStorageBlockDeviceAPIInterfaceTests(
    make_iblockdeviceapi_tests(
        blockdevice_api_factory=(
            lambda test_case: openvstorageblockdeviceapi_for_test(
                test_case=test_case,
            )
        ),
        minimum_allocatable_size=int(1024*1024*1024),
        device_allocation_unit=int(1024 * 1024),
        unknown_blockdevice_id_factory=lambda test: u"voldrv-00000000",
    )
):
    """
    Acceptance tests for the OpenvStorage driver.
    """
