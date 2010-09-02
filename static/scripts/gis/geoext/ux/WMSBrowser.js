/**
 * Copyright (c) 2008-2010 The Open Source Geospatial Foundation
 * 
 * Published under the BSD license.
 * See http://svn.geoext.org/core/trunk/geoext/license.txt for the full text
 * of the license.
 */

Ext.namespace("GeoExt.ux")

/*
 * @requires GeoExt/widgets/Action.js
 */

/** api: (define)
 *  module = GeoExt.ux
 *  class = WMSBrowser
 */

/** api: constructor
 *  .. class:: WMSBrowser
 */
GeoExt.ux.WMSBrowser = Ext.extend(Ext.Panel, {

    layout: 'absolute',

    minWidth: 300,

    minHeight: 200,

    plain:true,

    bodyStyle:'padding:5px;',

    buttonAlign:'center',

    useIcons: false,

    layerStore: null,

    serverStore: null,

    serverStoreDisplayField: 'url',

    capabilitiesParams: {},

    defaultCapabilitiesParams: {
       'service': "WMS",
       'request': "GetCapabilities",
       'version': '1.1.1'
    },

    gridPanelOptions: {
        'height': 200
    },

    /** api: config[layerOptions]
     * ``Object`` optional object passed as default options                                                           
     * ``OpenLayers.Layer.WMS`` constructor
     */
    layerOptions: null,

    zoomOnLayerAdded: false,

    closeOnLayerAdded: false,

    allowInvalidUrl: false,

    currentUrl: null,

    /** private: method[constructor]
     */
    constructor: function(config) {
        this.serverStore = config.serverStore || null;
        this.gridPanelOptions = config.gridPanelOptions || this.gridPanelOptions;
        this.layerOptions = config.layerOptions || this.layerOptions;
        
        OpenLayers.Util.applyDefaults(
            this.capabilitiesParams, this.defaultCapabilitiesParams);

        this.initMyItems();
        this.initMyToolbar();

        arguments.callee.superclass.constructor.call(this, config);

        this.on("afterrender", this.onAfterRender, this);
    },

    initMyItems: function() {
        var oItems;

        oItems = [];

        // Top panel
        oTopPanel = {
            style:'padding:2px;margin:2px;',
            region: 'north',
            id: "wms_field_group",
            xtype: 'fieldset',
            layout: 'form',
            border: false,
            collapsible: false,
	    anchor: '100%',
            defaults: {width: '100%'},
            defaultType: 'textfield',
            buttonAlign:'center',
            items: [],
            buttons: []
        };

        // URL panel
        var oURLField;
        if(this.serverStore) {
            oURLField = {
            style:'padding:0px;margin:0px;',
                columnWidth: 0.85,
                'name': 'wms_url',
                'id': 'wms_url',
                xtype: 'combo',
                store: this.serverStore,
                displayField: this.serverStoreDisplayField,
                typeAhead: true,
                mode: 'local',
                forceSelection: false,
                triggerAction: 'all',
                allowBlank: false,
                validator:this.urlValidator,
                invalidText: OpenLayers.i18n('The url address entered is not valid.'),
                emptyText:OpenLayers.i18n('Select or input a server address (URL)'),
                selectOnFocus:true
            };
        } else {
            oURLField = {
            style:'padding:0px;margin:0px;',
                xtype: "textfield",
                columnWidth: 0.85,
                layout: 'fit',
                'name': 'wms_url',
                'id': 'wms_url',
                border: false,
                allowBlank: false,
                validator:this.urlValidator,
                invalidText: OpenLayers.i18n('The url address entered is not valid.'),
                'emptyText': OpenLayers.i18n('Input the server address (URL)')
            };
        }

        // Top panel - URL and Connect
        oTopPanel.items.push({
            style:'padding:0px;margin:0px;',
            xtype: 'fieldset',
            layout: 'column',
            border: false,
            collapsible: false,
            collapsed: false,
            items: [
                oURLField,
                {
                    style:'padding:0px;margin:0px;',
                    columnWidth: 0.15,
                    border: false,
                    items: [{
			width: 'auto',
 			autoWidth: 'true',
                        style:'padding:0px;margin:0px;',
                        xtype: 'button',
                        text:  OpenLayers.i18n('Connect'),
                        scope: this,
                        handler: function(b, e){this.triggerGetCapabilities();}
                    }]
                }
            ]
        });


        // Top panel - Username and Password
	// currenty not used at all...
	/*
        oTopPanel.items.push({
            style:'padding:10px;margin:2px;',
            xtype: 'fieldset',
            title: OpenLayers.i18n('Login information (optional)'),
            layout: 'form',
            collapsible: true,
            collapsed: true,
            autoHeight: true,
            autoWidth: true,
            defaults: {width: '100%'},
            defaultType: 'textfield',
            items: [{
                name: 'wms_username',
                id: 'wms_username',
                fieldLabel: OpenLayers.i18n('Username')
            },{
                name: 'wms_password',
                id: 'wms_password',
                inputType: 'password',
                fieldLabel: OpenLayers.i18n('Password')
            }]
        });
        */
        oItems.push(oTopPanel);

        // Center Panel
        oCenterPanel = {
            style:'padding:2px;margin:2px;',
	    x: 0,
	    y: 25,
            xtype: 'form',
            region: 'center',
            id: "wms_capabilities_panel",
            layout: 'column',
            border: false,
            collapsible: false,
            anchor: '100% 100%',
            defaults: {width: '100%', hideLabel: true},
            defaultType: 'textfield',
            buttonAlign:'center',
            items: []
        };

        // WMSCapabilitiesStore on blank url on start
        this.capStore = new GeoExt.data.WMSCapabilitiesStore({'url': "", layerOptions: this.layerOptions});
        this.capStore.on('load', this.onWMSCapabilitiesStoreLoad, this);

        oCenterPanel.items.push(this.createGridPanel(this.capStore));
        oCenterPanel.items.push(this.createFormPanel());
        
        oItems.push(oCenterPanel);

        Ext.apply(this, {items: oItems});
    },

    triggerGetCapabilities: function() {
        var urlField = Ext.getCmp('wms_url');
        var url = urlField.getValue();

        // if url in not valid
        if(!urlField.isValid()) {
            // if url is blank, throw error
            if(!url) {
                alert(OpenLayers.i18n('Please, enter an url in the textbox first'));
                return;
            }
            // if url is not blank and the widget don't allow invalid urls, 
            // throw error
            else if (!this.allowInvalidUrl){
                alert( OpenLayers.i18n('The url address entered is not valid.'));
                return;
            }
        }

        // keep the inputed url in order to add it to the url store later if
        // it was valid
        this.currentUrl = url;

        // add the GetCapabilities parameters to the url
        var params = OpenLayers.Util.getParameterString(this.capabilitiesParams);        
        url = OpenLayers.Util.urlAppend(url, params);

        if (OpenLayers.ProxyHost && OpenLayers.String.startsWith(url, "http")) {
            url = OpenLayers.ProxyHost + encodeURIComponent(url);
        }

        // change the url of the capability store proxy
        this.capStore.proxy.setUrl(url);
        this.capStore.proxy.setApi(Ext.data.Api.actions.read, url);

        this.capStore.load();
    },

    removeAllItemsFromObject: function(object){
        while(object.items.length != 0){
            var oItem = object.items.items[0];
            object.remove(oItem, true);
            oItem.destroy();
        }
    },

    createWMSCapabilitiesStore: function(url) {
        var store = new GeoExt.data.WMSCapabilitiesStore({'url': url});
        store.on('load', this.onWMSCapabilitiesStoreLoad, this);
        return store;
    },

    createGridPanel: function(store) {
        var columns = [
            { header: OpenLayers.i18n('Add'),
              dataIndex: "srsCompatible", hidden: false,
              renderer: this.boolRenderer, width: 30},
            { header: OpenLayers.i18n('Title'), 
              dataIndex: "title", id: "title", sortable: true},
            { header: OpenLayers.i18n('Name'), 
              dataIndex: "name", sortable: true},
            { header: OpenLayers.i18n('Queryable'), 
              dataIndex: "queryable", sortable: true, hidden: true, 
              renderer: this.boolRenderer},
            { header: OpenLayers.i18n('Description'),
              dataIndex: "abstract", hidden: true}
        ];

        // In order to have a scrollbar, a GridPanel must have a 'height' set,
        // it can't be left with 'autoHeight': true...
        var options = {
            id: 'wms_capabilities_grid_panel',
            columnWidth: 0.5,
            layout: 'fit',
            store: store,
            columns: columns,
            // SelectionModel
            sm: new Ext.grid.RowSelectionModel({
                singleSelect: true,
                listeners: {
                    rowselect: function(sm, row, rec) {
                        Ext.getCmp("wms_capabilities_panel").getForm().loadRecord(rec);
                    }
                }
            }),
            autoExpandColumn: "title",
            width: 'auto',
            autoWidth: true,
            listeners: {
                rowdblclick: this.mapPreview
            }
        };

        options = OpenLayers.Util.applyDefaults(this.gridPanelOptions, options);

        return new Ext.grid.GridPanel(options);
    },

    createFormPanel: function() {
        var nDescHeight = parseInt(this.gridPanelOptions['height']) - 115;

        var options = {
            style:'padding:0px;margin:0px;',
            columnWidth: 0.5,
            xtype: 'fieldset',
            //layout: 'anchor',
            labelWidth: 80,
            defaults: Ext.isIE6 ? {width: '150px', border:false, readOnly: true} : {width: '100%', border:false, readOnly: true},
            defaultType: 'textfield',
            autoHeight: true,
            bodyStyle: Ext.isIE ? 'padding:0 0 0px 0px;' : 'padding:5px 0px;',
            border: false,
            style: {
                "margin-left": "10px",
                "margin-right": Ext.isIE6 ? (Ext.isStrict ? "-10px" : "-13px") : "0"
            },
            items: [{
                fieldLabel: OpenLayers.i18n('Title'),
                name: 'title'
            },{
                fieldLabel: OpenLayers.i18n('Name'),
                name: 'name'
            },{
                xtype: 'radiogroup',
                columns: 'auto',
                fieldLabel: OpenLayers.i18n('Queryable'),
                name: 'queryable',
                defaults: {readOnly: true},
                items: [{
                    name: 'queryableBox',
                    inputValue: "true",
                    boxLabel: OpenLayers.i18n("Yes")
                }, {
                    name: 'queryableBox',
                    inputValue: "",
                    boxLabel: OpenLayers.i18n("No")
                }]
            },{
                xtype: 'radiogroup',
                columns: 'auto',
                fieldLabel: OpenLayers.i18n('Can add ?'),
                name: 'srsCompatible',
                defaults: {readOnly: true},
                items: [{
                    name: 'srsCompatibleBox',
                    inputValue: "true",
                    boxLabel: OpenLayers.i18n("Yes")
                }, {
                    name: 'srsCompatibleBox',
                    inputValue: "false",
                    boxLabel: OpenLayers.i18n("No")
                }]
            },{
                xtype: 'textarea',
                fieldLabel: OpenLayers.i18n('Description'),
                name: 'abstract',
	        height: nDescHeight	
            }]
        };

        return options;

    },

    mapPreview: function(grid, index) {
        var record = grid.getStore().getAt(index);
        var layer = record.get("layer").clone();
        
        var win = new Ext.Window({
            title: OpenLayers.i18n('Preview') + ": " + record.get("title"),
            width: 512,
            height: 256,
            layout: "fit",
            items: [{
                xtype: "gx_mappanel",
                layers: [layer],
                extent: record.get("llbbox")
            }]
        });
        win.show();
    },

    initMyToolbar: function() {
        var items = [];

        items.push('->');

        // AddLayer action
        var actionOptions = {
            handler: this.addLayer,
            scope: this,
            tooltip: OpenLayers.i18n('Add currently selected layer')
        };

        if (this.useIcons === true) {
            actionOptions.iconCls = "gx-wmsbrowser-addlayer";
        } else {
            actionOptions.text = OpenLayers.i18n('Add Layer');
        }

        var action = new Ext.Action(actionOptions);
        items.push(action);

        // Cancel/Close action... todo


        Ext.apply(this, {bbar: new Ext.Toolbar(items)});
    },

    addLayer: function() {
        var grid = Ext.getCmp('wms_capabilities_grid_panel');
        var record = grid.getSelectionModel().getSelected();
        if(record) {
            // check the projection of the map is supported by the layer
            if (record.get("srsCompatible") === false) {
                var error = "This layer can't be added to the current map" + 
                            " because it doesn't support its projection.";
                alert(OpenLayers.i18n(error));
                return;
            }

            var copy = record.clone();

            // the following line gives a "too much recursion" error.
            //copy.set("layer", record.get("layer"));
            copy.data.layer = record.data.layer.clone();

            copy.get("layer").mergeNewParams({
                format: "image/png",
                transparent: "true"
            });
            this.layerStore.add(copy);

            if(this.zoomOnLayerAdded) {
                // zoom to added layer extent (in the current map projection)
                this.layerStore.map.zoomToExtent(
                    OpenLayers.Bounds.fromArray(copy.get("llbbox")).transform(
                        new OpenLayers.Projection("EPSG:4326"),
                        new OpenLayers.Projection(
                            this.layerStore.map.getProjection()))
                );
            }

            if(this.closeOnLayerAdded && 
               this.ownerCt.getXType() == Ext.Window.xtype) {
                this.closeWindow();
            }

        } else {
            // means no record was selected
            if(grid.store.getTotalCount() > 0) {
                var error = "Please, select a layer from the grid first.";
                alert(OpenLayers.i18n(error));
            } else {
                var error = "Please, enter an url in the textbox " + 
                            "then click \'Connect\'.";
                alert(OpenLayers.i18n(error));
            }
        }
    },

    onWMSCapabilitiesStoreLoad: function(store, records, options) {
        var srs = this.layerStore.map.getProjection();
        var grid = Ext.getCmp('wms_capabilities_grid_panel');
        var urlField = Ext.getCmp('wms_url');

        // loop through all records (layers) to see if they contain the current
        // map projection
        for(var i=0; i<records.length; i++) {
            var record = records[i];

            // Check if the 'srs' contains a 'key' named by the srs OR
            // Check if the 'srs' is an array and contains the srs
            if(record.get('srs')[srs] === true ||
               OpenLayers.Util.indexOf(record.get('srs'), srs) >= 0) {
                record.set("srsCompatible", true);
            } else {
                record.set("srsCompatible", false);
            }
        }

        if(grid.store.getCount() > 0) {
            // select the first element of the list on load end
            grid.getSelectionModel().selectRow(0);

            // the url that was used was a valid WMS server, keep it if the
            // url field is a combobox and if it's not already added
            if(urlField.getXType() == Ext.form.ComboBox.xtype) {
                var aszUrls = urlField.store.getValueArray('url');
                if(OpenLayers.Util.indexOf(aszUrls, this.currentUrl) == -1) {
                    var record = new Ext.data.Record({'url': this.currentUrl});
                    urlField.store.add([record]);
                }
            }
        }
    },

    boolRenderer: function(bool) {
        return (bool)
            ? '<span style="color:green;">' + OpenLayers.i18n("Yes") + '</span>'
            : '<span style="color:red;">' + OpenLayers.i18n("No") + '</span>';
    },

    /** private: method[onAfterRender]
     *  Called after this element was rendered.
     *  If the owner is a window, add a 'close' button.
     */
    onAfterRender : function() {
        if(this.ownerCt.getXType() == Ext.Window.xtype) {
            this.addCloseButton();
        }
    },

    addCloseButton : function() {
        var actionOptions = {
            handler: this.closeWindow,
            scope: this,
            tooltip: OpenLayers.i18n('Close this window')
        };

        if (this.useIcons === true) {
            actionOptions.iconCls = "gx-wmsbrowser-close";
        } else {
            actionOptions.text = OpenLayers.i18n('Close');
        }

        var action = new Ext.Action(actionOptions);

        this.getBottomToolbar().add(action);
    },

    closeWindow: function() {
        this.ownerCt.hide();
    },

    urlValidator: function(url) {
        var result = Ext.form.VTypes.url(url);

        return result;
    }
});
