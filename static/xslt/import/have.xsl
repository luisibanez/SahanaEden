<?xml version="1.0"?>
<xsl:stylesheet
            xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0"
            xmlns:have="urn:oasis:names:tc:emergency:EDXL:HAVE:1.0"
            xmlns:gml="http://www.opengis.net/gml"
            xmlns:xnl="urn:oasis:names:tc:ciq:xnl:3"
            xmlns:xal="urn:oasis:names:tc:ciq:xal:3"
            xmlns:xpil="urn:oasis:names:tc:ciq:xpil:3">

    <!-- **********************************************************************

         EDXL-HAVE Import Templates

         Version 0.2 / 2010-06-10 / by nursix

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

    <!-- ****************************************************************** -->
    <xsl:param name="domain"/>
    <xsl:param name="base_url"/>

    <!-- ****************************************************************** -->
    <xsl:template match="/">
        <xsl:apply-templates select="./have:HospitalStatus"/>
    </xsl:template>

    <xsl:template match="have:HospitalStatus">
        <s3xrc>
            <xsl:apply-templates select="./have:Hospital"/>
        </s3xrc>
    </xsl:template>


    <!-- ****************************************************************** -->
    <xsl:template match="have:Hospital">
        <xsl:if test="./have:Organization/have:OrganizationInformation/xnl:OrganisationName/@xnl:ID">
            <resource name="hms_hospital">
                <xsl:call-template name="HospitalUUID"/>
            </resource>
        </xsl:if>
    </xsl:template>


    <!-- ****************************************************************** -->
    <xsl:template name="HospitalUUID">
        <xsl:variable name="uuid_provided">
            <xsl:value-of select="./have:Organization/have:OrganizationInformation/xnl:OrganisationName/@xnl:ID"/>
        </xsl:variable>
        <xsl:if test="$uuid_provided">
            <xsl:attribute name="uuid">
                <xsl:value-of select="$uuid_provided"/>
            </xsl:attribute>
        </xsl:if>
    </xsl:template>


    <!-- ****************************************************************** -->

</xsl:stylesheet>
