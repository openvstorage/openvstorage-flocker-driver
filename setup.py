from setuptools import setup, find_packages
import codecs

setup(
    name="OpenvStorage Flocker driver",
    packages=[
        "openvstorage_flocker_plugin"
    ],
    package_data={
        "openvstorage_flocker_plugin": ["config/*"],
    },
    version="0.1",
    description="OpenvStorage Plugin for ClusterHQ/Flocker.",
    author="Chrysostomos Nanakos",
    author_email="cnanakos@openvstorage.com",
    license='Apache 2.0',

    classifiers=[
    'Development Status :: 4 - Beta',
    'Intended Audience :: System Administrators',
    'Intended Audience :: Developers',
    'Topic :: Software Development :: Libraries :: Python Modules',
    'License :: OSI Approved :: Apache Software License',
    # Python versions supported
    'Programming Language :: Python :: 2.7',
    ],

    keywords='openvstorage, backend, plugin, flocker, docker, python',

    url="https://github.com/openvstorage/openvstorage-flocker-driver",
    install_requires=[]
)
