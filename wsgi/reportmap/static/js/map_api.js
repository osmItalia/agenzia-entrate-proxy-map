function getJsonData() {
    var geoJsonData;

    $.ajax({
        dataType: "json",
        url: "/rmap/errors",
        async: false,
        success: function( data ) {
          geoJsonData = data;
        }
    });

    return geoJsonData;
}

function deleteItem(deleted_item, map_id) {
    $.ajax({
        type: 'POST',
        dataType: "json",
        url: "/rmap/error/delete",
        data: {'item': deleted_item, 'map_id': map_id},
        success: function(data){
          alert(JSON.stringify(data));
        },
        failure: function(err) {
          alert(err);
        }
    });
}

function insertItem(lat, lon, map_id, id) {
    $.ajax({
        type: 'POST',
        dataType: "json",
        url: "/rmap/error/insert",
        data: {'lat': lat, 'lon': lon, 'map_id': map_id, 'id': id},
        success: function(data){
            alert(JSON.stringify(data));
        },
        failure: function(err) {
            alert(err);
        }
    });
}