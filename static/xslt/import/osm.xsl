<?xml version="1.0"?>
<xsl:stylesheet
            xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0"
            xmlns:osm="http://openstreetmap.org/osm/0.6">

    <!-- Sahana Eden XSLT Import Template

        Transformation of
            OpenStreetMap Points of Interest
        into
            Sahana Eden GIS Locations
    -->

    <xsl:output method="xml"/>

    <xsl:template match="/">
        <xsl:apply-templates select="./osm"/>
    </xsl:template>

    <xsl:template match="osm">
        <s3xrc>
            <xsl:for-each select="//node" >
                <xsl:if test="./tag">
                    <resource name="gis_location">
                        <xsl:attribute name="uuid">
                            <xsl:text>openstreetmap.org/</xsl:text>
                            <xsl:value-of select="@id"/>
                        </xsl:attribute>
                        <xsl:attribute name="created_on">
                            <xsl:value-of select="@timestamp"/>
                        </xsl:attribute>

                        <data field="gis_feature_type" value="1">Point</data>

                        <data field="lat">
                            <xsl:value-of select="@lat"/>
                        </data>
                        <data field="lon">
                            <xsl:value-of select="@lon"/>
                        </data>

                        <xsl:if test="./tag[@k='name']">
                            <data field="name">
                                <xsl:value-of select="./tag[@k='name']/@v"/>
                            </data>
                        </xsl:if>

                        <xsl:choose>

                            <xsl:when test="./tag[@k='aeroway'] and ./tag[@v='aerodrome']">
                                <reference field="feature_class_id" resource="gis_feature_class">Airport</reference>
                            </xsl:when>
                            <xsl:when test="./tag[@k='amenity'] and ./tag[@v='hospital']">
                                <reference field="feature_class_id" resource="gis_feature_class">Hospital</reference>
                            </xsl:when>
                            <xsl:when test="./tag[@k='amenity'] and ./tag[@v='place_of_worship']">
                                <reference field="feature_class_id" resource="gis_feature_class">Church</reference>
                            </xsl:when>
                            <xsl:when test="./tag[@k='amenity'] and ./tag[@v='school']">
                                <reference field="feature_class_id" resource="gis_feature_class">School</reference>
                            </xsl:when>
                            <xsl:when test="./tag[@k='bridge'] and ./tag[@v='yes']">
                                <reference field="feature_class_id" resource="gis_feature_class">Bridge</reference>
                            </xsl:when>
                            <xsl:when test="./tag[@k='place'] and ./tag[@v='town']">
                                <reference field="feature_class_id" resource="gis_feature_class">Town</reference>
                            </xsl:when>

                        </xsl:choose>
                    </resource>
                </xsl:if>
            </xsl:for-each>
        </s3xrc>
    </xsl:template>

</xsl:stylesheet>
