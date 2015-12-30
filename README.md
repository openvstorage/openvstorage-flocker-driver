# OpenvStorage Plugin for ClusterHQ/flocker

This an OpenvStorage Block Device driver for Flocker, a container data orchestration system.

## Description
ClusterHQ/Flocker provides an efficient and easy way to connect persistent
store with Docker containers. OpenvStorage's Flocker volume plugin allows the
data nodes to be moved to a new server when the application’s Docker container
and associated OpenvStorage volumes are moved.

## Installation

Make sure you have Flocker already installed. If not visit  [Install Flocker](https://docs.clusterhq.com/en/latest/using/installing/index.html)

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
    "vpool_conf_file": "/path/to/volumedriverfs.json"
(This is an example. Use your own values)
</pre>
