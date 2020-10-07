# QRev 4

**QRev** version 4 is a Python port of the Matlab code QRev developed by the USGS to to compute the discharge from a moving-boat ADCP measurement using data collected with any of the Teledyne RD Instrument (TRDI) or SonTek bottom tracking ADCPs. QRev improves the consistency and efficiency of processing streamflow measurements by providing:

* Automated data quality checks with feedback to the user
* Automated data filtering
* Automated application of extrap, LC, and SMBA algorithms
* Consistent processing algorithms independent of the ADCP used to collect the data
* Improved handing of invalid data
* An estimated uncertainty to help guide the user in rating the measurement


**For a full description and instructions on the use of QRev click** **[HERE](https://hydroacoustics.usgs.gov/movingboat/QRev.shtml)** **to view the QRev web page.**

***

# Development
**QRevPy** has been approved for release (IP-118174) and has been assigned a digital object identifier of 10.5066/P9OZ8QDL. Additional development of features in QRev are expected. Versions available in the master branch of this repository are currently in use by the USGS, however, no warranty, expressed or implied, is made by the USGS or the U.S. Government as to the functionality of the software and related material nor shall the fact of release constitute any such warranty. If you would like to contribute, please use the pull request process to provide new or improved code. 

## Requirements and Dependencies
### Source Code

QRevPy is currently being developed using Python 3.6.6 and makes use of the following packages:

PyInstaller==3.5	
PyQt5==5.13.1
PyQt5-sip==4.19.19
PyQt5-stubs==5.13.1.3
altgraph==0.16.1
atomicwrites==1.3.0
attrs==19.1.0
colorama==0.4.1
cycler==0.10.0
future==0.17.1
importlib-metadata==0.23
kiwisolver==1.1.0
macholib==1.11
matplotlib==3.1.1
more-itertools==7.2.0
numpy==1.17.2
packaging==19.2
pandas==0.25.1
patsy==0.5.1
pefile==2019.4.18
pip==20.1
pluggy==0.13.0
py==1.8.0
pyparsing==2.4.2
pyqt5-tools==5.12.1.1.5rc4
pytest==5.1.3
python-dateutil==2.8.0
python-dotenv==0.10.3
pytz==2019.2
pywin32-ctypes==0.2.0
scipy==1.3.1
setuptools==41.2.0
sip==4.19.8
six==1.12.0
utm==0.5.0
wcwidth==0.1.7
xmltodict==0.12.0
zipp==0.6.0
simplekml==1.3.1


## Bugs
Please report all bugs with appropriate instructions and files to reproduce the issue and add this to the issues tracking feature in this repository.

# [Disclaimer](https://code.usgs.gov/QRev/QRevPy/-/blob/master/DISCLAIMER.md)

# [License](https://code.usgs.gov/QRev/QRevPy/-/blob/master/LICENSE.md)


# Suggested citation
Mueller, D.S., 2020, QRev, U.S. Geological Survey software release, https://doi.org/10.5066/P9OZ8QDL.

# Author
David S Mueller  
U.S. Geological Survey  
9818 Bluegrass Parkway  
Louisville, KY  
<dmueller@usgs.gov>