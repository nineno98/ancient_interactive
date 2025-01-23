
const map = new ol.Map({
    target: 'map',
    layers: [
        new ol.layer.Tile({
            source: new ol.source.OSM() 
        })
    ],
    view: new ol.View({
        center: ol.proj.fromLonLat([0, 0]), 
        zoom: 2
    })
});


const vectorSource = new ol.source.Vector({
    format: new ol.format.GeoJSON(),
    url: 'http://127.0.0.1:8000/territories/' 
});

const styleFunction = (feature) => {
    
    let color = ol.color.asArray(feature.get('color')).slice();
    color[3] = 0.5;
    let strokeColor = color
    if(feature.get('hidden')){
        color[3] = 0.0;
        strokeColor = 'rgba(0, 0, 0, 0.0)'
    }
    return new ol.style.Style({
        stroke: new ol.style.Stroke({
            color: strokeColor, 
            width: 1
        }),
        fill: new ol.style.Fill({
            color: color
        })
    });
};


const vectorLayer = new ol.layer.Vector({
    source: vectorSource,
    style: styleFunction,
    
});

map.addLayer(vectorLayer);

document.getElementById('date-slider').addEventListener('input', function (event){
    let selectedDate = parseInt(event.target.value)
    document.getElementById('slider-value').textContent = selectedDate;

    vectorSource.forEachFeature((feature) => {
        let stard_date = feature.get('start_date')
        let end_date = feature.get('end_date')
        if(selectedDate < stard_date || selectedDate >= end_date){
            feature.set('hidden', true);
        }else{
            feature.set('hidden', false);
        }

        feature.changed()
    })
})
