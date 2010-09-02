<xsl:stylesheet version="1.0"
  xmlns="http://www.opengis.net/kml/2.2"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

    <!-- **********************************************************************

         KML Export Templates for S3XRC

         Copyright (c) 2010 Sahana Software Foundation

         Permission is hereby granted, free of charge, to any person
         obtaining a copy of this software and associated documentation
         files (the "Software"), to deal in the Software without
         restriction, including without limitation the rights to use,
         copy, modify, merge, publish, distribute, sublicense, and/or sell
         copies of the Software, and to permit persons to whom the
         Software is furnished to do so, subject to the following
         conditions:

         The above copyright notice and this permission notice shall be
         included in all copies or substantial portions of the Software.

         THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
         EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
         OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
         NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
         HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
         WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
         FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
         OTHER DEALINGS IN THE SOFTWARE.

    *********************************************************************** -->
    <xsl:output method="xml" indent="yes"/>

    <!-- ****************************************************************** -->
    <xsl:template match="/">
        <kml xmlns="http://www.opengis.net/kml/2.2">
            <Document>
                <xsl:apply-templates select="s3xrc"/>
            </Document>
        </kml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="s3xrc">
        <Folder>
            <name>Sahana Eden Locations</name>
            <xsl:apply-templates select=".//resource[@name='gis_location']"/>
        </Folder>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="resource[@name='gis_location']">
        <xsl:variable name="uid">
            <xsl:value-of select="@uuid"/>
        </xsl:variable>
        <xsl:choose>
            <xsl:when test="//reference[@resource='gis_location' and @uuid=$uid]">
                <!-- This can render multiple markers for the same point, where
                     some KML clients (like GoogleEarth) will resolve such stacks
                     (GE does a nice stack explosion widget here), others won't.
                -->
                <xsl:for-each select="//reference[@resource='gis_location' and @uuid=$uid]">
                    <xsl:apply-templates select=".."/>
                </xsl:for-each>
            </xsl:when>
            <xsl:otherwise>
                <Style>
                    <xsl:attribute name="id"><xsl:value-of select="@uuid"/></xsl:attribute>
                    <IconStyle>
                        <Icon>
                            <href><xsl:value-of select="@marker"/></href>
                        </Icon>
                    </IconStyle>
                </Style>
                <Placemark>
                    <name><xsl:value-of select="data[@field='name']"/></name>
                    <styleUrl>#<xsl:value-of select="@uuid"/></styleUrl>
                    <description><xsl:value-of select="@url"/></description>
                    <Point>
                        <coordinates>
                            <xsl:value-of select="data[@field='lon']"/>
                            <xsl:text>,</xsl:text>
                            <xsl:value-of select="data[@field='lat']"/>
                        </coordinates>
                    </Point>
                </Placemark>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="resource[@name='hms_hospital']">
        <Style id="hospital">
            <IconStyle>
                <Icon>
                    <href>http://demo.eden.sahanafoundation.org/eden/default/download/gis_marker.image.E_Med_Hospital_S1.png</href>
                </Icon>
            </IconStyle>
        </Style>
        <Placemark>
            <name><xsl:value-of select="data[@field='name']"/></name>
            <styleUrl>#hospital</styleUrl>
            <!-- <description><xsl:value-of select="@url"/></description> -->
            <description>
                &lt;table&gt;
                    &lt;tr&gt;
                        &lt;td&gt;EMS Status: &lt;/td&gt;
                        &lt;td&gt;<xsl:value-of select="./data[@field='ems_status']/text()"/>&lt;/td&gt;
                    &lt;/tr&gt;
                    &lt;tr&gt;
                        &lt;td&gt;Facility Status: &lt;/td&gt;
                        &lt;td&gt;<xsl:value-of select="./data[@field='facility_status']/text()"/>&lt;/td&gt;
                    &lt;/tr&gt;
                    &lt;tr&gt;
                        &lt;td&gt;Clinical Status: &lt;/td&gt;
                        &lt;td&gt;<xsl:value-of select="./data[@field='clinical_status']/text()"/>&lt;/td&gt;
                    &lt;/tr&gt;
                    &lt;tr&gt;
                        &lt;td&gt;Beds total: &lt;/td&gt;
                        &lt;td&gt;<xsl:value-of select="./data[@field='total_beds']/text()"/>&lt;/td&gt;
                    &lt;/tr&gt;
                    &lt;tr&gt;
                        &lt;td&gt;Beds available: &lt;/td&gt;
                        &lt;td&gt;<xsl:value-of select="./data[@field='available_beds']/text()"/>&lt;/td&gt;
                    &lt;/tr&gt;
                    &lt;tr&gt;
                        &lt;td&gt;Details: &lt;/td&gt;
                        &lt;td&gt;&lt;a href=<xsl:value-of select="@url"/>&gt;<xsl:value-of select="@url"/>&lt;/a&gt;&lt;/td&gt;
                    &lt;/tr&gt;
                &lt;/table&gt;
                <xsl:if test="./resource[@name='hms_shortage']/data[@field='status']/@value='1' or ./resource[@name='hms_shortage']/data[@field='status']/@value='2'">
                    &lt;ul&gt;
                    <xsl:apply-templates select="./resource[@name='hms_shortage']"/>
                    &lt;/ul&gt;
                </xsl:if>
            </description>
            <Point>
                <coordinates>
                    <xsl:value-of select="reference[@field='location_id']/@lon"/>
                    <xsl:text>,</xsl:text>
                    <xsl:value-of select="reference[@field='location_id']/@lat"/>
                </coordinates>
            </Point>
        </Placemark>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="resource">
        <xsl:if test="./reference[@field='location_id']">
            <Style><xsl:attribute name="id"><xsl:value-of select="reference[@field='location_id']/@uuid"/></xsl:attribute>
                <IconStyle>
                    <Icon>
                        <href><xsl:value-of select="reference[@field='location_id']/@marker"/></href>
                    </Icon>
                </IconStyle>
            </Style>
            <Placemark>
                <name><xsl:value-of select="data[@field='name']"/></name>
                <styleUrl>#<xsl:value-of select="reference[@field='location_id']/@uuid"/></styleUrl>
                <description><xsl:value-of select="@url"/></description>
                <Point>
                    <coordinates>
                        <xsl:value-of select="reference[@field='location_id']/@lon"/>
                        <xsl:text>,</xsl:text>
                        <xsl:value-of select="reference[@field='location_id']/@lat"/>
                    </coordinates>
                </Point>
            </Placemark>
        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="resource[@name='hms_shortage']">
        <xsl:if test="./data[@field='status']/@value='1' or ./data[@field='status']/@value='2'">
            &lt;li&gt;Shortage [<xsl:value-of select="./data[@field='priority']/text()"/>/<xsl:value-of select="./data[@field='impact']/text()"/>/<xsl:value-of select="./data[@field='type']/text()"/>]: <xsl:value-of select="./data[@field='description']/text()"/>&lt;/li&gt;
        </xsl:if>
    </xsl:template>

</xsl:stylesheet>
