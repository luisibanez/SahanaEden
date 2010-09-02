<?xml version="1.0"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0"
    xmlns:pfif="http://zesty.ca/pfif/1.2">

    <!-- **********************************************************************

         PFIF 1.2 Export Templates for Sahana-Eden

         Version 0.2 / 2010-07-26 / by nursix

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
        <xsl:apply-templates select="./s3xrc"/>
    </xsl:template>

    <xsl:template match="/s3xrc">
        <pfif:pfif>
            <xsl:apply-templates select="./resource[@name='pr_person' and not(@ref)]"/>
        </pfif:pfif>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="resource[@name='pr_person']">
        <pfif:person>

            <!-- Record ID -->
            <pfif:person_record_id>
                <xsl:value-of select="./@uuid" />
            </pfif:person_record_id>

            <!-- Entry date and Author -->
            <pfif:entry_date>
                <xsl:call-template name="datetime2pfif">
                    <xsl:with-param name="datetime" select="./@modified_on" />
                </xsl:call-template>
            </pfif:entry_date>
            <pfif:author_name>
                <xsl:value-of select="./@modified_by" />
            </pfif:author_name>

            <!-- Source Information -->
            <pfif:source_name>
                <xsl:value-of select="/s3xrc/@domain"/>
            </pfif:source_name>
            <pfif:source_date>
                <xsl:call-template name="datetime2pfif">
                    <xsl:with-param name="datetime" select="./@created_on" />
                </xsl:call-template>
            </pfif:source_date>
            <pfif:source_url>
                <xsl:value-of select="./@url"/>
            </pfif:source_url>

            <!-- Person names -->
            <pfif:first_name>
                <xsl:value-of select="./data[@field='first_name']/text()" />
            </pfif:first_name>
            <pfif:last_name>
                <xsl:value-of select="./data[@field='last_name']/text()" />
            </pfif:last_name>

            <!-- Sex, Date of Birth -->
            <xsl:choose>
                <xsl:when test="./data[@field='gender']/@value='2'">
                    <pfif:sex>female</pfif:sex>
                </xsl:when>
                <xsl:when test="./data[@field='gender']/@value='3'">
                    <pfif:sex>male</pfif:sex>
                </xsl:when>
            </xsl:choose>
            <xsl:if test="./data[@field='date_of_birth']">
                <pfif:date_of_birth>
                    <xsl:value-of select="./data[@field='date_of_birth']"/>
                </pfif:date_of_birth>
            </xsl:if>

            <!-- other Elements -->
            <xsl:apply-templates select="./resource[@name='pr_address' and ./data[@field='type']/@value=1][1]" />
            <xsl:apply-templates select="./resource[@name='pr_image']"/>
            <xsl:apply-templates select="./resource[@name='pr_presence']"/>
        </pfif:person>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="resource[@name='pr_presence']">
        <pfif:note>

            <pfif:note_record_id>
                <xsl:value-of select="@uuid"/>
            </pfif:note_record_id>

            <pfif:entry_date>
                <xsl:call-template name="datetime2pfif">
                    <xsl:with-param name="datetime" select="./data[@field='time']/@value" />
                </xsl:call-template>
            </pfif:entry_date>
            <pfif:author_name>
                <xsl:value-of select="./reference[@field='reporter']/text()" />
            </pfif:author_name>

            <pfif:source_date>
                <xsl:call-template name="datetime2pfif">
                    <xsl:with-param name="datetime" select="./@created_on" />
                </xsl:call-template>
            </pfif:source_date>

            <pfif:found>
                <xsl:choose>
                    <xsl:when test="./data[@field='presence_condition']/@value=8">
                        <xsl:text>false</xsl:text>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:text>true</xsl:text>
                    </xsl:otherwise>
                </xsl:choose>
            </pfif:found>

            <pfif:last_known_location>
                <xsl:if test="./data[@field='location']/text()">
                    <xsl:value-of select="./data[@field='location']/text()"/>
                    <xsl:if test="string-length(./data[@field='location_details']/text())&gt;0">
                        <xsl:text> / </xsl:text>
                    </xsl:if>
                </xsl:if>
                <xsl:if test="string-length(./data[@field='location_details']/text())&gt;0">
                    <xsl:value-of select="./data[@field='location_details']/text()"/>
                </xsl:if>
            </pfif:last_known_location>

            <pfif:text>
                <xsl:value-of select="./data[@field='presence_condition']/text()"/>
                <xsl:if test="string-length(./data[@field='procedure']/text())&gt;0">
                    <xsl:text> : </xsl:text>
                    <xsl:value-of select="./data[@field='procedure']/text()"/>
                </xsl:if>
                <xsl:if test="string-length(./data[@field='comment']/text())&gt;0">
                    <xsl:text> - Info: </xsl:text>
                    <xsl:value-of select="./data[@field='comment']/text()"/>
                </xsl:if>
            </pfif:text>

        </pfif:note>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="resource[@name='pr_person']/resource[@name='pr_address']">
        <pfif:home_street>
            <xsl:value-of select="./data[@field='street1']/text()"/>
        </pfif:home_street>

        <!-- Neighborhood not supported
        <pfif:home_neighborhood>
        </pfif:home_neighborhood>
        -->

        <pfif:home_city>
            <xsl:value-of select="./data[@field='city']/text()"/>
        </pfif:home_city>
        <pfif:home_state>
            <xsl:value-of select="./data[@field='state']/text()"/>
        </pfif:home_state>
        <pfif:home_postal_code>
            <xsl:value-of select="./data[@field='postcode']/text()"/>
        </pfif:home_postal_code>

        <!-- ISO 3166-1 Country Codes -->
        <pfif:home_country>
            <xsl:value-of select="./data[@field='country']/@value"/>
        </pfif:home_country>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="resource[@name='pr_person']/resource[@name='pr_image']">
        <pfif:photo_url>
            <xsl:choose>
                <xsl:when test="./data[@field='url']/@value">
                    <xsl:value-of select="./data[@field='url']/@value"/>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:value-of select="./data[@field='image']/text()"/>
                </xsl:otherwise>
            </xsl:choose>
        </pfif:photo_url>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="datetime2pfif">
        <xsl:param name="datetime"/>
        <xsl:value-of select="concat(substring-before($datetime, ' '), 'T', substring-after($datetime, ' '), 'Z')"/>
    </xsl:template>

    <!-- deprecated -->
    <xsl:template name="name2pfif">
        <xsl:param name="name"/>
        <xsl:value-of select="translate($name,
            'abcdefghijklmnopqrstuvwxyzáéíóúàèìòùäöüåâêîôûãẽĩõũø',
            'ABCDEFGHIJKLMNOPQRSTUVWXYZÁÉÍÓÚÀÈÌÒÙÄÖÜÅÂÊÎÔÛÃẼĨÕŨØ')"/>
    </xsl:template>

</xsl:stylesheet>
