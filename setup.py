from distutils.core import setup
from setuptools import find_packages


setup(
    name='ponyadmin',
    version='1.0',
    description='an admin with a pony',
    url='http://github.com/yeago/ponyadmin/tree/master',
    packages=find_packages(),
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Framework :: Django',
    ],
    package_data={
    },
    zip_safe=False
)
