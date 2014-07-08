/*!
 * Copyright 2014 Fondazione Bruno Kessler
 * Author: Cristian Consonni
 * Released under the MIT license
 *
 */

$( document ).ready( function() {

    var geoJsonData = getJsonData();
    var map_id = geoJsonData['id'];

    var targetIcon = new L.icon({
        iconUrl: '/static/img/target_32x32.png',
        iconSize:     [32, 32],
        shadowSize:   [50, 64],
        iconAnchor:   [12, 41],
        shadowAnchor: [4, 62],
        popupAnchor:  [3, -33]
    });

    var center = [46.0718, 11.1199];

    var center_tiles = getTileURL(center[0], center[1], 18);

    var markers = L.markerClusterGroup();

    var geoJsonLayer = L.geoJson(geoJsonData, {
        onEachFeature: function (feature, layer) {
            markers.addLayer(layer);
            layer.bindPopup(feature.properties.address);
        }
    });

    var drawControl = new L.Control.Draw({
        draw: {
            position: 'topleft',
            polygon : false,
            polyline : false,
            rectangle : false,
            circle : false
        },
        edit: {
            featureGroup: markers
        }
    });

    var geopoi = L.tileLayer(geopoi_url, {
        attribution: geopoi_attribution,
        tms: true,
        minZoom: 18,
        xtile_center: center_tiles[0],
        ytile_center: center_tiles[1]
    });

    var mapbox = L.tileLayer(mapbox_url, {
        maxZoom: 18,
        minZoom: 18,
        attribution: mapbox_attribution,
        id: 'examples.map-9ijuk24y'
    });

    var grayscale   = L.tileLayer(mapbox_url, {
        maxZoom: 18,
        minZoom: 18,
        attribution: mapbox_attribution,
        id: 'examples.map-20v6611k'
    });

    var osm_classic = L.tileLayer(osmclassic_url, {
        maxZoom: 18,
        minZoom: 18,
        attribution: osmclassic_attribution
    });

    var map1 = L.map('map1', {
        layers: [osm_classic],
        center: center,
        zoom: 18
    });

    var map2 = L.map('map2', {
        layers: [geopoi],
        center: center,
        zoom: 18
    });

    var baseLayers = {
        "OSM oggi": osm_classic,
        "Mapbox": mapbox,
        "Grigio": grayscale,
    };

    map1.addControl(drawControl);

    L.control.layers(baseLayers).addTo(map1);

    var marker_center_left = new L.marker(center,
        {icon: targetIcon}
        ).addTo(map1);
    var marker_center_right = new L.marker(center,
        {icon: targetIcon}
        ).addTo(map2);

    $("#final-lat").text(center[0]);
    $("#final-lon").text(center[1]);
    $("#tile-x").text(center_tiles[0]);
    $("#tile-y").text(center_tiles[1]);


    // minimappa
    var osm_minimap = new L.TileLayer(osmclassic_url, {
        minZoom: 0,
        maxZoom: 13
    });
    var miniMap = new L.Control.MiniMap(osm_minimap, {
        toggleDisplay: true
    }).addTo(map1);

    // hash
    var hash = new L.Hash(map1);

    map2.sync(map1);
    map1.sync(map2);

    var movemarker = function () {
        var position = map2.getCenter();
        lat = Number(position['lat']).toFixed(5);
        lng = Number(position['lng']).toFixed(5);

        marker_center_left.setLatLng(position);
        marker_center_right.setLatLng(position);

        tiles = getTileURL(lat, lng, 18);
        xtile = tiles[0];
        ytile = tiles[1];


        geopoi.options.xtile_center = xtile;
        geopoi.options.ytile_center = ytile;
        geopoi.setUrl(geopoi_url);
        
        $("#final-lat").text(lat);
        $("#final-lon").text(lng);
        $("#tile-x").text(xtile);
        $("#tile-y").text(ytile);
    };

    // Use move event of map for update map center position
    map1.on('move', movemarker);
    map2.on('move', movemarker);

    // Use dragstart event of map for update map center position
    map1.on('dragstart', dragstartmarker);
    map2.on('dragstart', dragstartmarker);

    /*
    * Draw events on map1:
    * * draw:created is fired on node creation
    * * draw:deleted is fired on node deletion (when saving)
    */
    map1.on('draw:created', function (e) {
        console.log('draw:created');

        var type = e.layerType,
            layer = e.layer;

        if (type === 'marker') {
          layer.bindPopup('A popup!');
        }

        // drawnItems.addLayer(layer);
        markers.addLayer(layer);

        var lat = layer._latlng.lat;
        var lon = layer._latlng.lng;
        var id = layer._leaflet_id;

        insertItem(lat, lon, map_id, id);
    });

    map1.on('draw:deleted', function (e) {
        console.log('draw:deleted');

        for ( var key in e.layers._layers ){
          var deleted_item = JSON.stringify(e.layers._layers[key].feature);
          deleteItem(deleted_item, map_id);
        }
    });

    map1.addLayer(markers);
    map1.fitBounds(markers.getBounds());

});
