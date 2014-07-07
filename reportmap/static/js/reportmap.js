/*!
 * Copyright 2014 Fondazione Bruno Kessler
 * Author: Cristian Consonni
 * Released under the MIT license
 *
 */
 
$( document ).ready( function () {

    var geoJsonData = getJsonData();
    var map_id = geoJsonData['id'];

    var osmUrl = 'http://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
        osmAttrib = '&copy; <a href="http://openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        osm = L.tileLayer(osmUrl, {maxZoom: 18, attribution: osmAttrib}),
        map = new L.Map('map', {layers: [osm], center: [175.22, -37.82], zoom: 10 });

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
    map.addControl(drawControl);

    map.on('draw:created', function (e) {
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

    map.on('draw:edited', function (e) {
    console.log('draw:edited');
    });


    map.on('draw:deleted', function (e) {
    console.log('draw:deleted');

    for ( var key in e.layers._layers ){
        var deleted_item = JSON.stringify(e.layers._layers[key].feature);
        deleteItem(deleted_item, map_id);
    }

    });

    map.on('draw:drawstart', function (e) {
        console.log('draw:drawstart');
    });

    map.on('draw:drawstop', function (e) {
        console.log('draw:drawstop');
    });

    map.on('draw:editstart', function (e) {
        console.log('draw:editstart');
    });

    map.on('draw:editstop', function (e) {
        console.log('draw:editstop');
    });

    map.on('draw:deletestart', function (e) {
        console.log('draw:editstop');
    });

    map.on('draw:deletestop', function (e) {
        console.log('draw:deletestop');
    });

    map.addLayer(markers);
    map.fitBounds(markers.getBounds());
});