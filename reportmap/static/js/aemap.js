/*!
 * Copyright 2014 Fondazione Bruno Kessler
 * Author: Cristian Consonni
 * Released under the MIT license
 *
 */
 
$( document ).ready( function() {

    var center = [41.89032, 12.49422];

    var map = L.map('map').setView(center, 18);

    var center_tiles = getTileURL(center[0], center[1], 18);

    var geopoi = L.tileLayer(geopoi_url, {
        attribution: geopoi_attribution,
        tms: true,
        minZoom: 18,
        xtile_center: center_tiles[0],
        ytile_center: center_tiles[1]
    }).addTo(map);

    var osm_classic = L.tileLayer(osmclassic_url, {
        maxZoom: 18,
        attribution: osmclassic_attribution
    });
    
    // minimappa
    var osm_minimap = new L.TileLayer(osmclassic_url, {
        minZoom: 0,
        maxZoom: 13
    });

    var miniMap = new L.Control.MiniMap(osm_minimap, {
        toggleDisplay: true
    }).addTo(map);

    // hash
    var hash = new L.Hash(map);

    var baseLayers = {
        "Geopoi": geopoi,
        "OSM classic": osm_classic,
    };

    L.control.layers(baseLayers).addTo(map);

    // Use move event of map for update map center position
    map.on('move', movemarker);

    // Use dragstart event of map for update map center position
    map.on('dragstart', dragstartmarker);
    

});
