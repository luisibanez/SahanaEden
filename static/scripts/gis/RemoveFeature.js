/* Copyright (c) 2006 MetaCarta, Inc., published under a modified BSD license.
 * See http://svn.openlayers.org/trunk/openlayers/repository-license.txt 
 * for the full text of the license. */


/**
 * @requires OpenLayers/Control.js
 * @requires OpenLayers/Control/SelectFeature.js
 * @requires OpenLayers/Handler/Keyboard.js
 * 
 * Class: OpenLayers.Control.RemoveFeature
 * Remove a feature with the delete key.  Create a new control with the
 *     <OpenLayers.Control.RemoveFeature> constructor.
 *
 * Inherits From:
 *  - <OpenLayers.Control>
 */
OpenLayers.Control.RemoveFeature = OpenLayers.Class(OpenLayers.Control, {

    /**
     * APIProperty: geometryTypes
     * {Array(String)} To restrict remove to a limited set of geometry types,
     *     send a list of strings corresponding to the geometry class names.
     */
    geometryTypes: null,

    /**
     * APIProperty: onDone
     * {Function} TBD add comment here
     *
     * Parameters:
     * feature - {OpenLayers.Feature.Vector} The feature that was removed.
     */
    onDone: function(feature) {},

    /**
     * Property: layer
     * {OpenLayers.Layer.Vector}
     */
    layer: null,
    
    /**
     * Property: feature
     * {OpenLayers.Feature.Vector}
     */
    feature: null,

    /**
     * Property: selectControl
     * {<OpenLayers.Control.Select>}
     */
    selectControl: null,
    
    /**
     * Property: featureHandler
     * {OpenLayers.Handler.Keyboard}
     */
    keyboardHandler: {},
    
    /**
     * Constructor: OpenLayers.Control.RemoveFeature
     * Create a new control to remove features.
     *
     * Parameters:
     * layer - {OpenLayers.Layer.Vector} The layer containing features to be
     *     dragged.
     * options - {Object} Optional object whose properties will be set on the
     *     control.
     */
    initialize: function(layer, options) {
        OpenLayers.Control.prototype.initialize.apply(this, [options]);
        this.layer = layer;
        
        var control = this;
        this.selectControl = new OpenLayers.Control.SelectFeature(layer,
                                    {geometryTypes: this.geometryTypes,
                                     onSelect: function(feature) {
                                        control.onSelect.apply(control, [feature]);
                                     },
                                     onUnselect: function(feature) {
                                        control.onUnselect.apply(control, [feature]);
                                     }});
        
        this.keyboardHandler = new OpenLayers.Handler.Keyboard( this, { 
                                "keypress": this.defaultKeyPress });
    },
    
    /**
     * APIMethod: destroy
     * Take care of things that are not handled in superclass
     */
    destroy: function() {
        this.layer = null;
        this.selectControl.destroy();
        OpenLayers.Control.prototype.destroy.apply(this, []);
    },

    /**
     * APIMethod: activate
     * Activate the control and the feature handler.
     * 
     * Returns:
     * {Boolean} Successfully activated the control and feature handler.
     */
    activate: function() {
        return (this.selectControl.activate() &&
                OpenLayers.Control.prototype.activate.apply(this, arguments));
    },

    /**
     * APIMethod: deactivate
     * Deactivate the control and all handlers.
     * 
     * Returns:
     * {Boolean} Successfully deactivated the control.
     */
    deactivate: function() {
        // the return from the handler is unimportant in this case
        this.selectControl.deactivate();
        return OpenLayers.Control.prototype.deactivate.apply(this, arguments);
    },
    
    /**
     * Method: onSelect
     * Called when the select feature control selects a feature.
     *
     * Parameters:
     * feature - {OpenLayers.Feature.Vector} The selected feature.
     */
    onSelect: function(feature) {
        this.feature = feature;
        this.keyboardHandler.activate();
    },
    
    /**
     * Method: onUnselect
     * Called when the select feature control unselects a feature.
     *
     * Parameters:
     * feature - {OpenLayers.Feature.Vector} The unselected feature.
     */
    onUnselect: function(feature) {
        this.feature = null;
    },
    
    /**
     * Method: defaultKeyPress
     *
     * Parameters:
     * code - {Integer} 
     */
    defaultKeyPress: function (code) {
        switch(code) {
            case OpenLayers.Event.KEY_DELETE:
                this.remove(this.feature);
                break;
        }
    },
    
    /**
     * Method: remove
     * Removes currently selected feature
     *
     * Parameters:
     * code - {Integer} 
     */
    remove: function(feature) {
        this.layer.removeFeatures([feature]);
        this.onDone(feature);
    },

    /**
     * Method: setMap
     * Set the map property for the control and all handlers.
     *
     * Parameters: 
     * map - {OpenLayers.Map} The control's map.
     */
    setMap: function(map) {
        this.selectControl.setMap(map);
        OpenLayers.Control.prototype.setMap.apply(this, arguments);
    },

    CLASS_NAME: "OpenLayers.Control.RemoveFeature"
});
