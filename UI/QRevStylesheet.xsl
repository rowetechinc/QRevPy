<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
<!--*********This stylesheet is an example of displaying data from the QRev .xml file ********-->
<!--xsl:variable name="UnitConvert" select="1 div 0.3048" /--> <!-- Use for conversion from metric to english units -->
<xsl:variable name="UnitConvert" select="1 div 1" /> <!-- Use for metric units -->
<xsl:template match="/">
<html>
<head>
<style>
table {
	width:100%;
	border-collapse: collapse;
}	

table, td {
	padding: 1px;
	bgcolor:#9acd32;
	font-size:1em;
	font-family: Verdana, sans-serif;
	vertical-align: top;
}
th {
    font-size:1.1em;
	text-align: center;
	vertical-align: center;
	background-color:#9acd32;
	height:25px;
}
td {
	text-align: left;.
	border: 1px solid black;
	
}	
tr:hover{background-color:#f5f5f5}

body {font-family: Verdana, sans-serif; font-size:0.75em;}
header, nav, section, article, footer
{border:0px solid grey; margin:5px; padding:8px;}
nav ul {margin:0; padding:0;}
nav ul li {display:inline; margin:5px;}

</style>
</head>
  <body>
  <header>
  <table style="border:0px">
	<tr style="border:0px">
		<td style="border:0px"><h3>Station Number: <xsl:value-of select="Channel/SiteInformation/SiteID"/></h3>
		</td>
		<td style="border:0px"><h4 align="right">Date (mm/dd/yyyy): <xsl:value-of select="substring(Channel/Transect/StartDateTime, 1, string-length(substring-before(Channel/Transect/StartDateTime, ' ')))"/></h4>
		</td>
	</tr>
	<tr style="border:0px">
		<td colspan="2" style="border:0px"><h3>Station Name: <xsl:value-of select="Channel/SiteInformation/StationName"/></h3>
		</td>
	</tr>
  </table>
 </header>
 <section>
  <article name="Measurement Summary and Setup">
<table>
<td style="width: 50%;border:0px">  
<table name="Measurement Summary">
  <tr>
	<th colspan="2">Measurement Summary</th>
  </tr>
  <tr>
	<td style="width:50%">Discharge (m<sup>3</sup>/s)</td>
	<td><xsl:value-of select="round(Channel/ChannelSummary/Discharge/Total * $UnitConvert * $UnitConvert * $UnitConvert * 1000) div 1000"/></td>
  </tr>
  <tr>
	<td>Mean Velocity (m/s)</td>
	<td><xsl:value-of select="round(Channel/ChannelSummary/Other/MeanQoverA*10000) div 10000"/></td>
  </tr>
  <tr>
	<td>Area (m<sup>2</sup>)</td>
	<td><xsl:value-of select="round(Channel/ChannelSummary/Other/MeanArea*100) div 100"/></td>
  </tr>
  <tr>
	<td>Width (m)</td>
	<td><xsl:value-of select="round(Channel/ChannelSummary/Other/MeanWidth*100) div 100"/></td>
  </tr>
  	  <tr>
		<td>Navigation Reference</td>
		<td><xsl:value-of select="Channel/Processing/Navigation/Reference"/></td>
	  </tr>
  <tr>
	<td>Extrapolation Method (Top/Bottom Exponent):</td>
	<td><xsl:value-of select="Channel/Processing/Extrapolation/TopMethod"/>/<xsl:value-of select="Channel/Processing/Extrapolation/BottomMethod"/> Exp:<xsl:value-of select="Channel/Processing/Extrapolation/Exponent"/></td>
  </tr>  
 </table>
 </td>
<td style="width: 50%;border:0px">
<table name="ADCP Info">
      <tr>
        <th colspan="2">ADCP Info/Settings</th>
	  </tr>

	  <tr>
	  <td style="width:50%">ADCP Model</td>
	  <td><xsl:value-of select="Channel/Instrument/Model"/></td>
	  </tr>
	  <tr>
	  <td>Frequency</td>
	  <td><xsl:value-of select="Channel/Instrument/Frequency"/></td>
	  </tr>
	  <tr>
	  <td>Serial Number</td>
	  <td><xsl:value-of select="Channel/Instrument/SerialNumber"/></td>
	  </tr>
	  <tr>
	  <td>Firmware</td>
	  <td><xsl:value-of select="Channel/Instrument/FirmwareVersion"/></td>
	  </tr>
	  <tr>
	  <td>Configuration</td>
	  <td><xsl:value-of select="Channel/Instrument/InstrumentConfiguration"/></td>
	  </tr>
	  <tr>
		  <td>Software</td>
	  <td><xsl:value-of select="Channel/Processing/SoftwareVersion"/></td>
	  </tr>
	</table>

      </td>
	  </table>

<table>
<td style="width: 50%;border:0px">	  
<table name="Statistics">
<tr>
	<th colspan="2">Measurement Statistics</th>
  </tr>
    <tr>
  <td style="width:50%">Total Duration (s)</td>
  <td><xsl:value-of select="Channel/ChannelSummary/Other/Duration"/></td>
  </tr>
<tr>
<td>Measured Q (%)</td>
<td>
<xsl:value-of select="round((Channel/ChannelSummary/Discharge/Middle * $UnitConvert * $UnitConvert * $UnitConvert) div (Channel/ChannelSummary/Discharge/Total * $UnitConvert * $UnitConvert * $UnitConvert) * 100) div 100 * 100"/>
</td>
</tr>
<tr>
<td>Left Edge Q (%)</td>
<td><xsl:value-of select="Channel/ChannelSummary/Other/LeftQPer"/></td>
</tr>
<tr>
<td>Right Edge Q (%)</td>
<td><xsl:value-of select="Channel/ChannelSummary/Other/RightQPer"/></td>
</tr>
<tr>
<td>Mean Boat Speed (m/s)</td>
<td><xsl:value-of select="Channel/ChannelSummary/Other/MeanBoatSpeed"/></td>
</tr>
<tr>
<td>Invalid Bins (%)</td>
<td><xsl:value-of select="Channel/ChannelSummary/Other/InvalidCellsQPer"/></td>
</tr>
<tr>
<td>Invalid Ensembles (%)</td>
<td><xsl:value-of select="Channel/ChannelSummary/Other/InvalidEnsQPer"/></td>
</tr>
<tr>
<td>Uncertainty - COV</td>
<td><xsl:value-of select="Channel/ChannelSummary/Uncertainty/COV"/></td>
</tr>
<tr>
<td><b>Uncertainty - Total %</b></td>
<td><b><xsl:value-of select="Channel/ChannelSummary/Uncertainty/Total"/></b></td>
</tr>		
<tr>
<td><b>Uncertainty - User Rating %</b></td>
<td><b><xsl:value-of select="Channel/ChannelSummary/Other/UserRating"/></b>
  <xsl:if test="contains(Channel/ChannelSummary/Uncertainty/Total, '*')">
   * Uncertainty based upon user entered values.
</xsl:if></td>
</tr>		
</table>
</td>
<td style="width: 50%;border:0px">
<table name="Measurement Setup">

  <tr>
	<th colspan="2">Measurement Setup / Tests</th>
  </tr>
  <tr>
	<td style="width:50%">Diagnostic Test Results</td>
	<td><xsl:value-of select="Channel/QA/DiagnosticTestResult"/></td>
	</tr>
		  <tr>
	  <td>Compass Calibration Results</td>
	  <td><xsl:value-of select="Channel/QA/CompassCalibrationResult"/></td>
	  </tr>
	  <tr>
	  <td>Magnetic Variation (<sup>o</sup>)</td>
	  <td><xsl:value-of select="Channel/Processing/Navigation/MagneticVariation"/></td>
	  </tr>
	  		  <tr>
	  <td>Moving Bed Test Type</td>
	  <td><xsl:value-of select="Channel/QA/MovingBedTestType"/></td>
	  </tr>
	  		  <tr>
	  <td>Moving Bed Condition</td>
	  <td><xsl:value-of select="Channel/QA/MovingBedTestResult"/></td>
	  </tr>
	  <tr>
		<td>Moving Bed Test Duration (s)</td>
		<td><xsl:value-of select="Channel/QA/MovingBedTest/Duration"/></td>
	  </tr>
	  	  <tr>
	  <td>Moving Bed Percent (%)</td>
	  <td><xsl:value-of select="Channel/QA/MovingBedTest/PercentMovingBed"/></td>
	  </tr>
	  
	  <tr>
	  <td>Moving Bed Correction for Discharge (%)</td>
	  <td><xsl:if test="Channel/ChannelSummary/Discharge/MovingBedPercentCorrection>0"><xsl:value-of select="round(Channel/ChannelSummary/Discharge/MovingBedPercentCorrection*10) div 10"/>  
		</xsl:if></td>
	  </tr>
	  <tr>
	  <td>Moving Bed Message</td>
	  <td><xsl:value-of select="Channel/QA/MovingBedTest/Message"/></td>
	  </tr>
</table>
		
</td>
</table>	
</article>

<article name="Messages">
<h4>Messages</h4>
<p><xsl:value-of select="Channel/UserComment"/></p>
<p><xsl:value-of select="Channel/QA/QRev_Message"/></p>
</article>
<article name="Transect Discharge Summary">
  <h4>Transect Discharge Summary</h4>
   <table>
      <!-- <caption style="text-align:left">Transect Discharge</caption> -->
	  
	  <tr>
        <th>File Name</th>
		<th>Start Edge</th>
		<th>Left Dist</th>
		<th>Right Dist</th>
        <th>Start Time</th>
		<th>End Time</th>
		<th>Top</th>
		<th>Middle</th>
		<th>Bottom</th>
		<th>Left</th>
		<th>Right</th>
		<th>Total Q</th>
      </tr>
   <xsl:for-each select="Channel/Transect">
      <tr>
        <td><xsl:value-of select="Filename"/></td>
		<td><xsl:value-of select="Edge/StartEdge"/></td>
		<td><xsl:value-of select="Edge/LeftDistance"/></td>
		<td><xsl:value-of select="Edge/RightDistance"/></td>
		<!--<td><xsl:value-of select="StartDateTime"/></td>-->
		<!--<td><xsl:value-of select="EndDateTime"/></td>-->
        <td><xsl:value-of select="substring(StartDateTime, 11, string-length(substring-before(StartDateTime, ' ')))"/></td>
		<td><xsl:value-of select="substring(EndDateTime, 11, string-length(substring-before(EndDateTime, ' ')))"/></td>
		<td><xsl:value-of select="round(Discharge/Top * $UnitConvert * $UnitConvert * $UnitConvert * 1000) div 1000"/></td>
		<td><xsl:value-of select="round(Discharge/Middle * $UnitConvert * $UnitConvert * $UnitConvert * 1000) div 1000"/></td>
		<td><xsl:value-of select="round(Discharge/Bottom * $UnitConvert * $UnitConvert * $UnitConvert * 1000) div 1000"/></td>
		<td><xsl:value-of select="round(Discharge/Left * $UnitConvert * $UnitConvert * $UnitConvert * 1000) div 1000"/></td>
		<td><xsl:value-of select="round(Discharge/Right * $UnitConvert * $UnitConvert * $UnitConvert * 1000) div 1000"/></td>
		<td><xsl:value-of select="round(Discharge/Total * $UnitConvert * $UnitConvert * $UnitConvert * 1000) div 1000"/></td>
      </tr>
    </xsl:for-each>
	
    </table>  
	</article>
<article name="Transect Supplementary Data">
<h4>Transect Supplementary Data</h4>
	 <table>
      <tr>
        <th>File Name</th>
		<th>L E Type</th>
        <th>L E Coeff</th>
		<th>R E Type</th>
		<th>R E Coeff</th>
		<th>Width (m)</th>
        <th>Duration (s)</th>
		<th>Invalid Depth Cells (%)</th>
		<th>Invalid Ens (%)</th>
      </tr>
      <xsl:for-each select="Channel/Transect">
      <tr>
        <td><xsl:value-of select="Filename"/></td>
        <td><xsl:value-of select="Edge/LeftType"/></td>
		<td><xsl:value-of select="Edge/LeftEdgeCoefficient"/></td>
		<td><xsl:value-of select="Edge/RightType"/></td>
		<td><xsl:value-of select="Edge/RightEdgeCoefficient"/></td>
		<td><xsl:value-of select="round(Other/Width * $UnitConvert * 1000) div 1000"/></td>
		<td><xsl:value-of select="round(Other/Duration)"/></td>
		<td><xsl:value-of select="round(Other/PercentInvalidBins * 10) div 10"/></td>
		<td><xsl:value-of select="round(Other/PercentInvalidEns * 10) div 10"/></td>
		
		
      </tr>
      </xsl:for-each>
    </table>
</article>

</section>	
<footer>
<p align = "center">QRev Summary File: <xsl:value-of select="Channel/@QRevFilename"/> || QRev Stylesheet Version: WSC v2.0 2017-02-14</p>
 <h3 align="center">QRev Measurement Review - Adapted for Water Survey of Canada</h3>
</footer>
  </body>
  </html>
</xsl:template>
</xsl:stylesheet>