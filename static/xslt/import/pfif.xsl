<?xml version="1.0"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0"
    xmlns:pfif="http://zesty.ca/pfif/1.2">

    <!-- **********************************************************************

         PFIF 1.2 Import Templates for S3XRC

         Version 0.2 / 2010-07-25 / by nursix

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

    <!-- ****************************************************************** -->
    <xsl:template match="/">
        <xsl:apply-templates select="pfif:pfif"/>
    </xsl:template>

    <xsl:template match="pfif:pfif">
        <s3xrc>
            <xsl:attribute name="domain">
                <xsl:value-of select="$domain"/>
            </xsl:attribute>
            <xsl:apply-templates select="./pfif:person"/>
        </s3xrc>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- pfif:person -->

    <xsl:template match="pfif:person">
        <xsl:if test="./pfif:person_record_id/text()">
            <xsl:variable name="uuid">
                <xsl:value-of select="./pfif:person_record_id/text()"/>
            </xsl:variable>

            <resource name="pr_person">
                <xsl:attribute name="uuid">
                    <xsl:value-of select="$uuid"/>
                </xsl:attribute>
                <data field="last_name">
                    <xsl:value-of select="./pfif:last_name/text()"/>
                </data>
                <data field="first_name">
                    <xsl:value-of select="./pfif:first_name/text()"/>
                </data>
                <data field="gender">
                    <xsl:choose>
                        <xsl:when test="./pfif:sex/text()='female'">
                            <xsl:attribute name="value">2</xsl:attribute>
                        </xsl:when>
                        <xsl:when test="./pfif:sex/text()='male'">
                            <xsl:attribute name="value">3</xsl:attribute>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:attribute name="value">1</xsl:attribute>
                        </xsl:otherwise>
                    </xsl:choose>
                </data>
                <xsl:if test="./pfif:date_of_birth/text()">
                    <data field="date_of_birth">
                        <xsl:value-of select="./pfif:date_of_birth/text()"/>
                    </data>
                </xsl:if>

                <!-- Address -->
                <xsl:if test="./pfif:home_city">
                    <resource name="pr_address">
                        <xsl:attribute name="uuid">
                            <xsl:value-of select="concat($uuid, '_address')"/>
                        </xsl:attribute>
                        <data field="type" value="1">Home Address</data>
                        <data field="street1">
                            <xsl:value-of select="./pfif:home_street/text()"/>
                        </data>
                        <data field="city">
                            <xsl:value-of select="./pfif:home_city/text()"/>
                        </data>
                        <data field="postcode">
                            <xsl:value-of select="./pfif:home_postal_code/text()"/>
                        </data>
                        <data field="state">
                            <xsl:value-of select="./pfif:home_state/text()"/>
                        </data>
                        <data field="country">
                            <xsl:attribute name="value">
                                <xsl:value-of select="./pfif:home_country/text()"/>
                            </xsl:attribute>
                        </data>
                    </resource>
                </xsl:if>

                <!-- PhotoURL: save external URL -->
                <xsl:if test="./pfif:photo_url">
                    <resource name="pr_image">
                        <xsl:attribute name="uuid">
                            <xsl:value-of select="concat($uuid, '_photo')"/>
                        </xsl:attribute>
                        <data field="opt_pr_image_type" value="1">Photograph</data>
                        <data field="title">Photograph</data>
                        <data field="description">external data source</data>
                        <data field="image"/>
                        <data field="url">
                            <xsl:value-of select="./pfif:photo_url/text()"/>
                        </data>
                    </resource>
                </xsl:if>

                <!-- Add notes -->
                <xsl:apply-templates select="./pfif:note"/>

            </resource>
        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- pfif:note -->

    <xsl:template match="pfif:note">
        <resource name="pr_presence">
            <!-- UUID -->
            <xsl:attribute name="uuid">
                <xsl:value-of select="./pfif:note_record_id/text()"/>
            </xsl:attribute>

            <!-- Missing or Found -->
            <xsl:choose>
                <xsl:when test="normalize-space(./pfif:found/text())='false'">
                    <data field="presence_condition">
                        <xsl:attribute name="value">8</xsl:attribute>
                        <xsl:text>Missing</xsl:text>
                    </data>
                </xsl:when>
                <xsl:otherwise>
                    <data field="presence_condition">
                        <xsl:attribute name="value">4</xsl:attribute>
                        <xsl:text>Found</xsl:text>
                    </data>
                </xsl:otherwise>
            </xsl:choose>

            <!-- Date/Time -->
            <data field="time">
                <xsl:call-template name="pfif2datetime">
                    <xsl:with-param name="datetime" select="./pfif:entry_date/text()"/>
                </xsl:call-template>
            </data>

            <!-- Location details -->
            <data field="location_details">
                <xsl:value-of select="./pfif:last_known_location/text()"/>
            </data>

            <data field="proc_desc">
                <xsl:value-of select="./pfif:text/text()"/>
            </data>
            <data field="comment">
                <xsl:value-of select="concat(./pfif:author_name/text(), ' - ', ./pfif:author_email/text(), ' - ', ./pfif:author_phone/text())"/>
            </data>
        </resource>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Tools -->

    <xsl:template name="pfif2datetime">
        <xsl:param name="datetime"/>
        <xsl:value-of select="concat(substring-before($datetime, 'T'),' ',substring-before(substring-after($datetime, 'T'), 'Z'))"/>
    </xsl:template>

</xsl:stylesheet>

