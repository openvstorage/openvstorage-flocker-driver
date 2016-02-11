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
import time
import os
import platform
import uuid
from uuid import UUID
import logging
import requests
import json
import sys

import blktap as Blktap
import volumedriver.storagerouter.storagerouterclient as src

from subprocess import check_output

from bitmath import Byte, GiB, MiB, KiB

from eliot import Message, Logger
from zope.interface import implementer, Interface
from twisted.python.filepath import FilePath
from characteristic import attributes

from flocker.node.agents.blockdevice import (
    AlreadyAttachedVolume, IBlockDeviceAPI,
    BlockDeviceVolume, UnknownVolume, UnattachedVolume
)

__author__ = "Chrysostomos Nanakos"
__copyright__ = "Copyright 2015, iNuron NV"
__version__ = "0.1"
__maintainer__ = "Chrysostomos Nanakos"
__email__ = "cnanakos@openvstorage.com"
__status__ = "Development"

_logger = Logger()


class VolumeExists(Exception):
    """
    An OpenvStorage volume with the request name already exists.
    """
    def __init__(self, blockdevice_id):
        Exception.__init__(self, blockdevice_id)
        self.blockdevice_id = blockdevice_id


class ExternalBlockDeviceId(Exception):
    """
    The ``blockdevice_id`` was not a Flocker-controlled volume.
    """
    def __init__(self, blockdevice_id):
        Exception.__init__(self, blockdevice_id)
        self.blockdevice_id = blockdevice_id


def _blockdevice_id(dataset_id):
    """
    A blockdevice_id is the unicode representation of a Flocker dataset_id
    according to the storage system.
    """
    return u"flocker-%s" % (dataset_id,)


def _dataset_id(blockdevice_id):
    if not blockdevice_id.startswith(b"flocker-"):
        raise ExternalBlockDeviceId(blockdevice_id)
    return UUID(blockdevice_id[8:])


@implementer(IBlockDeviceAPI)
class OpenvStorageBlockDeviceAPI(object):
    """
    A ``IBlockDeviceAPI`` which uses OpenvStorage Block Devices.
    """

    def __init__(self, vpool_conf_file):
        self.vpool_conf_file = vpool_conf_file
        self.client = src.LocalStorageRouterClient(self.vpool_conf_file)

    def _check_exists(self, blockdevice_id):
        all_volumes = [os.path.splitext(x)[0].lstrip("/")
                       for x in self.client.list_volumes_by_path()]
        if blockdevice_id not in all_volumes:
            raise UnknownVolume(unicode(blockdevice_id))

    def _list_maps(self):
        """
        Return a ``dict`` mapping unicode OpenvStorage volumes to mounted block
        device ``FilePath``s for the active pool only.
        This information only applies to this host.
        """
        maps = dict()
        list_output = Blktap.Tapdisk.list()
        if not len(list_output):
            return maps
        for i in list_output:
            try:
                _dataset_id(i.volume)
            except ExternalBlockDeviceId:
                continue
            maps[i.volume] = FilePath(i.device)
        return maps

    def _is_already_mapped(self, blockdevice_id):
        """
        Return ``True`` or ``False`` if requested blockdevice_id is already
        mapped.
        """
        mapped = self._list_maps()
        for volume in mapped:
            if volume == blockdevice_id:
                return True
        return False

    def allocation_unit(self):
        return 1024 * 1024

    def compute_instance_id(self):
        """
        Get the hostname for this node.
        :returns: A ``unicode`` object representing this node.
        """
        return unicode(platform.node())

    def create_volume(self, dataset_id, size):
        """
        Create a new OpenvStorage volume.
        :param UUID dataset_id: The Flocker dataset ID of the dataset on this
            volume.
        :param int size: The size of the new volume in bytes.
        :returns: A ``BlockDeviceVolume``.
        """
        blockdevice_id = _blockdevice_id(dataset_id)
        try:
            self.client.info_volume(str(blockdevice_id))
            raise VolumeExists(blockdevice_id)
        except src.ObjectNotFoundException:
            self.client.create_volume("/%s.raw" % str(blockdevice_id),
                                      None,
                                      "%d KiB" % Byte(size).to_KiB().value)
            return BlockDeviceVolume(blockdevice_id=blockdevice_id,
                                     size=size,
                                     dataset_id=dataset_id)

    def destroy_volume(self, blockdevice_id):
        """
        Destroy an existing OpenvStorage volume.
        :param unicode blockdevice_id: The unique identifier for the volume to
            destroy.
        :raises UnknownVolume: If the supplied ``blockdevice_id`` does not
            exist.
        :return: ``None``
        """
        ascii_blockdevice_id = blockdevice_id.encode()
        self._check_exists(ascii_blockdevice_id)
        self.client.unlink(str("/%s.raw" % ascii_blockdevice_id))

    def attach_volume(self, blockdevice_id, attach_to):
        """
        Attach ``blockdevice_id`` to the node indicated by ``attach_to``.

        :param unicode blockdevice_id: The unique identifier for the block
            device being attached.
        :param unicode attach_to: An identifier like the one returned by the
            ``compute_instance_id`` method indicating the node to which to
            attach the volume.

        :raises UnknownVolume: If the supplied ``blockdevice_id`` does not
            exist.
        :raises AlreadyAttachedVolume: If the supplied ``blockdevice_id`` is
            already attached.
        :returns: A ``BlockDeviceVolume`` with a ``attached_to`` attribute set
            to ``attach_to``.
        """
        ascii_blockdevice_id = blockdevice_id.encode()
        self._check_exists(ascii_blockdevice_id)

        if self._is_already_mapped(blockdevice_id):
            raise AlreadyAttachedVolume(blockdevice_id)

        if attach_to != self.compute_instance_id():
            return

        Blktap.Tapdisk.create(blockdevice_id)
        object_id = self.client.get_object_id(str("/%s.raw" % blockdevice_id))
        size = self.client.info_volume(object_id).volume_size
        return BlockDeviceVolume(blockdevice_id=blockdevice_id,
                                 size=size,
                                 attached_to=self.compute_instance_id(),
                                 dataset_id=_dataset_id(blockdevice_id))

    def detach_volume(self, blockdevice_id):
        """
        Detach ``blockdevice_id`` from whatever host it is attached to.

        :param unicode blockdevice_id: The unique identifier for the block

            device being detached.
        :raises UnknownVolume: If the supplied ``blockdevice_id`` does not
            exist.
        :raises UnattachedVolume: If the supplied ``blockdevice_id`` is
            not attached to anything.
        :returns: ``None``
        """
        self._check_exists(blockdevice_id)
        device_path = self.get_device_path(blockdevice_id).path
        Blktap.Tapdisk.destroy(str(device_path))

    def list_volumes(self):
        """
        List all the block devices available via the back end API.
        :returns: A ``list`` of ``BlockDeviceVolume``s.
        """
        volumes = []
        all_volumes = [os.path.splitext(x)[0].lstrip("/")
                       for x in self.client.list_volumes_by_path()]
        all_maps = self._list_maps()
        for blockdevice_id in all_volumes:
            blockdevice_id = blockdevice_id.decode()
            try:
                dataset_id = _dataset_id(blockdevice_id)
            except ExternalBlockDeviceId:
                continue
            object_id = \
                self.client.get_object_id(str("/%s.raw" % blockdevice_id))
            size = self.client.info_volume(object_id).volume_size
            if blockdevice_id in all_maps:
                attached_to = self.compute_instance_id()
            else:
                attached_to = None
            volumes.append(BlockDeviceVolume(blockdevice_id=
                                             unicode(blockdevice_id),
                                             size=size, attached_to=
                                             attached_to,
                                             dataset_id=dataset_id))
        return volumes

    def get_device_path(self, blockdevice_id):
        """
        Return the device path that has been allocated to the block device on
        the host to which it is currently attached.

        :param unicode blockdevice_id: The unique identifier for the block
            device.
        :raises UnknownVolume: If the supplied ``blockdevice_id`` does not
            exist.
        :raises UnattachedVolume: If the supplied ``blockdevice_id`` is
            not attached to a host.
        :returns: A ``FilePath`` for the device.
        """
        self._check_exists(blockdevice_id)
        maps = self._list_maps()
        try:
            return maps[blockdevice_id]
        except KeyError:
            raise UnattachedVolume(blockdevice_id)

    def destroy_all_flocker_volumes(self):
        """
        Search for and destroy all Flocker volumes.
        """
        maps = self._list_maps()
        for blockdevice_id in maps:
            self.detach_volume(blockdevice_id)
        for blockdevicevolume in self.list_volumes():
            self.destroy_volume(blockdevicevolume.blockdevice_id)


def openvstorage_from_configuration(vpool_conf_file):
    return OpenvStorageBlockDeviceAPI(vpool_conf_file)


def main():
    if len(sys.argv) != 2:
        print "Please provide vPool configuration file"
        return
    vpool_config_file = sys.argv[1]
    vs = openvstorage_from_configuration(vpool_conf_file=vpool_config_file)
    volume = vs.create_volume(dataset_id=uuid.uuid4(), size=21474836480)
    vs.list_volumes()
    vm = vs.compute_instance_id()
    vs.attach_volume(blockdevice_id=volume.blockdevice_id, attach_to=vm)
    vs.list_volumes()
    vs.get_device_path(volume.blockdevice_id)
    vs.detach_volume(volume.blockdevice_id)
    vs.list_volumes()
    vs.destroy_volume(volume.blockdevice_id)
    vs.list_volumes()

if __name__ == '__main__':
    main()
