# -*- coding: utf-8 -*-

# Learn more: https://github.com/kennethreitz/setup.py

from setuptools import setup, find_packages


with open('README.md') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

setup(
    name='qrevpy',
    version='0.1.0',
    description='QRev port to python',
    long_description=readme,
    author='David S. Mueller',
    author_email='dmueller@usgs.gov',
    url='https://hydroacoustics.usgs.gov/movingboat/QRev.shtml',
    license=license,
	REQUIRES_PYTHON = '>=3.6.6',
	packages=['QRev', 'QRev.Classes', 'QRev.MiscLibs', 'QRev.UI'],
	 install_requires=[
						"PyQt5==5.13.1",
						"PyQt5-sip==4.19.19",
						"altgraph==0.16.1",
						"atomicwrites==1.3.0",
						"attrs==19.1.0",
						"colorama==0.4.1",
						"cycler==0.10.0",
						"future==0.17.1",
						"importlib-metadata==0.23",
						"kiwisolver==1.1.0",
						"macholib==1.11",
						"matplotlib==3.1.1",
						"more-itertools==7.2.0",
						"numpy==1.17.2",
						"packaging==19.2",
						"pandas==0.25.1",
						"patsy==0.5.1",
						"pefile==2019.4.18",
						"pip==19.2.3",
						"pluggy==0.13.0",
						"py==1.8.0",
						"pyparsing==2.4.2",
						"pyqt5-tools==5.12.1.1.5rc4",
						"pytest==5.1.3",
						"python-dateutil==2.8.0",
						"python-dotenv==0.10.3",
						"pytz==2019.2",
						"pywin32-ctypes==0.2.0",
						"scipy==1.3.1",
						"setuptools==65.5.1",
						"sip==4.19.8",
						"six==1.12.0",
						"statsmodels==0.10.1",
						"utm==0.5.0",
						"wcwidth==0.1.7",
						"xmltodict==0.12.0",
						"zipp==0.6.0"
					  ],
)