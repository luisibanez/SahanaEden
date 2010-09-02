<?xml version="1.0"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">
    
    <!-- **********************************************************************

         GeoJSON Export Templates for Sahana-Eden

         Version 0.1 / 2010-07-25 / by nursix

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
    <xsl:output method="xml"/>

    <xsl:param name="prefix"/>
    <xsl:param name="name"/>
    
    <xsl:template match="/">
        <GeoJSON>
            <xsl:apply-templates select="s3xrc"/>
        </GeoJSON>
    </xsl:template>
    
    <xsl:template match="s3xrc">
        <xsl:variable name="resource">
            <xsl:value-of select="concat($prefix,'_',$name)"/>
        </xsl:variable>
        <xsl:choose>
            <xsl:when test="count(./resource[@name=$resource])=1">
                <xsl:apply-templates select="./resource[@name=$resource]"/>
            </xsl:when>
            <xsl:otherwise>
                <type>FeatureCollection</type>
                <xsl:for-each select="./resource[@name=$resource]">
                    <features>
                        <xsl:apply-templates select="."/>
                    </features>
                </xsl:for-each>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    
    <xsl:template match="resource">
        <xsl:choose>
            <xsl:when test="@name='gis_location'">
                <type>Feature</type>
                <id>
                    <xsl:value-of select="@uuid"/>
                </id>
                <geometry>
                    <type>
                        <xsl:value-of select="data[@field='gis_feature_type']"/>
                    </type>
                    <coordinates>
                        <xsl:value-of select="data[@field='lat']"/>
                    </coordinates>
                    <coordinates>
                        <xsl:value-of select="data[@field='lon']"/>
                    </coordinates>
                </geometry>
            </xsl:when>
        </xsl:choose>
    </xsl:template>
    
</xsl:stylesheet>
