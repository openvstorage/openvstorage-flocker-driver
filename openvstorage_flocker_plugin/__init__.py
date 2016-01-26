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
from flocker.node import BackendDescription, DeployerType
from openvstorage_flocker_plugin.openvstorage_blockdevice import (
    openvstorage_from_configuration
)

__author__ = "Chrysostomos Nanakos"
__copyright__ = "Copyright 2015, iNuron NV"
__version__ = "0.1"
__maintainer__ = "Chrysostomos Nanakos"
__email__ = "cnanakos@openvstorage.com"
__status__ = "Development"


def api_factory(cluster_id, **kwargs):

    if "vpool_conf_file" in kwargs:
        vpool_conf_file = kwargs["vpool_conf_file"]
    else:
        raise Exception('No vPool configuration file')
    return openvstorage_from_configuration(vpool_conf_file=vpool_conf_file)

FLOCKER_BACKEND = BackendDescription(
    name=u"openvstorage_flocker_driver",
    needs_reactor=False, needs_cluster_id=True,
    api_factory=api_factory, deployer_type=DeployerType.block)
