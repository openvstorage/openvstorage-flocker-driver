'''
Copyright 2015 iNuron NV.  All rights reserved.
Licensed under the Apache v2 License.
'''
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
