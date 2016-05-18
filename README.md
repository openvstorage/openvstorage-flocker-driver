# OpenvStorage Plugin for ClusterHQ/flocker

![](https://img.shields.io/badge/build-passing-brightgreen.svg) This an OpenvStorage Block Device driver for Flocker (version: 1.10.1), a container data orchestration system.

## Description
ClusterHQ/Flocker provides an efficient and easy way to connect persistent
store with Docker containers. OpenvStorage's Flocker volume plugin allows the
data nodes to be moved to a new server when the application’s Docker container
and associated OpenvStorage volumes are moved.

## Prerequisites
* The Flocker integration requires the [Blktap Open vStorage Utils](https://openvstorage.gitbooks.io/openvstorage/content/Administration/createvdisk.html#block) to be installed.

## Installation

Make sure you have Flocker already installed. If not visit  [Install Flocker](https://docs.clusterhq.com/en/latest/install/index.html)

**_Be sure to use /opt/flocker/bin/python as this will install the driver into the right python environment_**

Install using python
```bash
git clone https://github.com/openvstorage/openvstorage-flocker-driver
cd openvstorage-flocker-driver/
sudo /opt/flocker/bin/python setup.py install
```

**_Be sure to use /opt/flocker/bin/pip as this will install the driver into the right python environment_**

Install using pip
```
git clone https://github.com/openvstorage/openvstorage-flocker-driver
cd openvstorage-flocker-driver/
/opt/flocker/bin/pip install openvstorage-flocker-driver/
```

##Usage
<pre>
Add the following section to the file '/etc/flocker/agent.yml':
"dataset":
    "backend": "openvstorage_flocker_plugin"
    "vpool_conf_file": "/opt/OpenvStorage/config/storagedriver/storagedriver/<vpool_name>.json"
(This is an example. Use your own values)
</pre>
