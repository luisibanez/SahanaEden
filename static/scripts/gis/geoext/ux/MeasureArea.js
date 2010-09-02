/**
 * Copyright (c) 2008-2009 The Open Source Geospatial Foundation
 * 
 * Published under the BSD license.
 * See http://svn.geoext.org/core/trunk/geoext/license.txt for the full text
 * of the license.
 */

Ext.namespace("GeoExt.ux")

/*
 * @requires GeoExt.ux/Measure.js
 */

/** api: (define)
 *  module = GeoExt.ux.MeasureArea
 *  class = MeasureArea
 */

/** api: constructor
 *  .. class:: MeasureArea(config)
 *
 *      Creates a GeoExt.Action for area measurements.
 * 
 *  JSBuild: OpenLayers/Handler/Polygon.js must be included.
 */
GeoExt.ux.MeasureArea = Ext.extend(GeoExt.ux.Measure, {

    /** api: config[handlerClass]
     *  ``Function`` The handler class to pass to the measure control,
     *  Defaults to ``OpenLayers.Handler.Polygon``. 
     */

    /** api: config[iconCls]
     *  ``String`` The CSS class selector that specifies a background image 
     *  to be used as the header icon for all components using this action 
     *  Defaults to 'gx-map-measurearea'. 
     */
    
    /** api: config[template]
     *  ``String`` | ``Ext.XTemplate`` HTML template, or Ext.XTemplate used
     *  to display the measure. Optional.
     */
     
    /** private: method[constructor]
     */
    constructor: function(config) {
        config = Ext.apply({
            handlerClass: OpenLayers.Handler.Polygon,
            iconCls: 'gx-map-measurearea',
            tooltip: "Area measurement",
            template: '<p>{[values.measure.toFixed(this.decimals)]}&nbsp;'+
                '{units}<sup>2</sup></p>'
        }, config);
        arguments.callee.superclass.constructor.call(this, config);
    }
});
