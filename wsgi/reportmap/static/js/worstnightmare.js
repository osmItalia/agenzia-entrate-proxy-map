/*!
 * Copyright 2014 Fondazione Bruno Kessler
 * Author: Cristian Consonni
 * Released under the MIT license
 *
 */
 
if ( typeof (Number.prototype.toRad) === "undefined" ) {
  Number.prototype.toRad = function() {
    return this * Math.PI / 180;
  };
}

function findWithAttr(layers, attr, value) {

    for ( var layer_id in layers ) {
        if ( layers[layer_id][attr] === value ) {
            return layers[layer_id];
        }
    }
}

function findGeopoiLayer(e, geopoi_url) {
    var geopoi_layer = findWithAttr(e.target._layers, "_url", geopoi_url);

    if ( typeof (geopoi_layer) === "undefined" ) {

        for ( var layer_id in e.target._layers )  {

            var map_layers_array = e.target._layers[layer_id]._map._syncMaps;

            for ( var map_layer_id in map_layers_array ) {
                geopoi_layer = findWithAttr(map_layers_array[map_layer_id]._layers, "_url", geopoi_url);
                if ( typeof (geopoi_layer) !== "undefined" ) {
                    break;
                }
            }

            if ( typeof (geopoi_layer) !== "undefined" ) {
                    break;
            }
        }

    }

    return geopoi_layer;
}

var getTileURL = function(lat, lon, zoom) {
  var xtile = parseInt(Math.floor( (Number(lon) + 180) / 360 * (1<<zoom) ), 10);
  var ytile = parseInt(Math.floor( (1 - Math.log(Math.tan(Number(lat).toRad()) + 1 / Math.cos(Number(lat).toRad())) / Math.PI) / 2 * (1<<zoom) ), 10);
  return [xtile, ytile];
};

var movemarker = function (e) {
    var geopoi_layer = findWithAttr(e.target._layers, "_url", geopoi_url);

    var position = e.target.getCenter();
    lat = Number(position['lat']).toFixed(5);
    lng = Number(position['lng']).toFixed(5);

    if (typeof (marker_center_left) !== 'undefined' ) {
        marker_center_left.setLatLng(position);
        marker_center_right.setLatLng(position);
    }

    tiles = getTileURL(lat, lng, e.target._zoom);
    xtile = tiles[0];
    ytile = tiles[1];

    geopoi_layer.options.xtile_center = xtile;
    geopoi_layer.options.ytile_center = ytile;
    geopoi_layer.setUrl(geopoi_url);
    
    $("#final-lat").text(lat);
    $("#final-lon").text(lng);
    $("#tile-x").text(xtile);
    $("#tile-y").text(ytile);
};

var dragstartmarker = function(e) {
    var geopoi_layer = findGeopoiLayer(e, geopoi_url);

    var position = e.target.getCenter();
    lat = Number(position['lat']).toFixed(5);
    lng = Number(position['lng']).toFixed(5);

    if (typeof (marker_center_left) !== 'undefined' ) {
        marker_center_left.setLatLng(position);
        marker_center_right.setLatLng(position);
    }

    tiles = getTileURL(lat, lng, e.target._zoom);
    xtile = tiles[0];
    ytile = tiles[1];

    geopoi_layer.options.xtile_center = xtile;
    geopoi_layer.options.ytile_center = ytile;
    geopoi_layer.setUrl(geopoi_url);


    $("#final-lat").text(lat);
    $("#final-lon").text(lng);
    $("#tile-x").text(xtile);
    $("#tile-y").text(ytile);
};

