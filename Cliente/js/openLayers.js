var map, customDelete;
var vectorSourceinit;
var iconStyleinit = '';
var actualPOIS= [];
var count = 0;
//Trajecto Mapa
var trajectoformat, trajectoVectorSource, trajectoVectorLayer, trajectoiconFeatureinitIcon, trajectoiconStyleinitIcon, trajectoiconFeatureinitIcon, trajectovectorSourceinitIcon, trajectovectorLayerinitIcon;
//Solo Trajecto Mapa
var soloroutegeojson, solotrajectoformat, solotrajectoVectorSource, solotrajectoVectorLayer, trajectoiconStyleinitIcon, trajectoiconFeatureinitIcon, trajectovectorSourceinitIcon, trajectovectorLayerinitIcon;

//Custom POI ADD
var customPoiArray={};
var iconFeatureinitCustomAddPoi, iconStyleinitCustomAddPoi, vectorSourceCustomAddPoi, vectorLayerinitCustomAddPoi;
var contPois = 0;
//Unwanted POI
var unwantedPointiconFeatureinit, unwantedPointiconStyleinit, unwantedpointvectorSourceinit, unwantedpointvectorLayerinit;
var unwantedpoiroadformat, unwantedpoiroadvectorSource, unwantedpoiroadvectorLayer;
//BlockerRoads blockerList=> é os unwantedpois e as estradas
var blockerList = {};
//roadblock
var blockerRoadList = {};
//User ID
var userid = 15;

$( document ).ready(function() {
    let x = getCookie("cook");

    if(x){
        /** Adquirir o id do utilizador em função do token*/
        let username = x;
        let password = 'unused';
        $.ajax({
            type: "GET",
            url: "http://aal.ieeta.pt/hlt/api/v1/resource",
            async: false,
            headers: {
                "Authorization": "Basic " + btoa(username + ":" + password)
            },
            success: function (response){
                console.log(response);
                $("#name_user").html(response["username"]);
                userid = response["id"];
            }
        });

        $("#logout").click(function() {
            delete_cookie("cook");
            self.location = "http://aal.ieeta.pt/hlt/apiteste/";
        });

        mapa();

        /**Ao arrancar com a inicialização da pagina*/
        $.ajax({
            type: "POST",
            headers: {'X-Requested-With': 'XMLHttpRequest'},
            url: "http://aal.ieeta.pt/hlt/api/v1/initUser/", //Iniciar as tabelas auxiliares por utilizador
            dataType: "text",
            data: {id: userid},
            success: function(result){
                console.log(result);
                $.ajax({
                    type: "GET",
                    url: "http://aal.ieeta.pt/hlt/api/v1/showBlockedRoad/", //Depois da criação correcta das tabelas verifica-se os bloqueios relativos ao utilizador
                    data: {id: userid},
                    success: function(result){
                        let arrayUnwantedPoi = result[0];
                        let arrayBlockRoads = result[1];
                        /** unwantedPOI */
                        for (var key in arrayUnwantedPoi) {
                            let auxarrayRemoveInfo = [];
                            let auxarray = arrayUnwantedPoi[key]; //0 => unwantedpoiID || 1 => COORD || 2 => GEOJSON
                            auxarrayRemoveInfo.push('unwantedpointvectorSourceinit_' + auxarray[0]);
                            auxarrayRemoveInfo.push('unwantedpointroadvectorSource_' + auxarray[0]);

                            let coord = auxarray[1].split(" ")

                            let PointiconFeatureinit = new ol.Feature({
                                geometry: new ol.geom.Point([coord[0], coord[1]]),
                                long_Original: coord[0],
                                lat_Original: coord[1],
                                type: 2,
                                id: auxarray[0]
                            });

                            let PointiconStyleinit = new ol.style.Style({
                                image: new ol.style.Icon(
                                    ({
                                        anchor: [0.5, 46],
                                        anchorXUnits: 'fraction',
                                        anchorYUnits: 'pixels',
                                        src: './images/unwanted.png',
                                        scale: 0.6
                                    }))
                            });

                            PointiconFeatureinit.setStyle(PointiconStyleinit);

                            auxarrayRemoveInfo[0] = new ol.source.Vector({
                                features: [PointiconFeatureinit]
                            });

                            let pointvectorLayerinit = new ol.layer.Vector({
                                source: auxarrayRemoveInfo[0]
                            });

                            map.addLayer(pointvectorLayerinit);

                            let format = new ol.format.GeoJSON({
                                featureProjection: "EPSG:4326"
                            });
                            auxarrayRemoveInfo[1] = new ol.source.Vector({
                                features: format.readFeatures(auxarray[2])
                            });

                            let vectorLayer = new ol.layer.Vector({
                                source: auxarrayRemoveInfo[1],
                                style: new ol.style.Style({
                                    stroke: new ol.style.Stroke({
                                        color: 'red',
                                        width: 3,
                                        lineDash: [.1, 5]
                                    })
                                })
                            });

                            map.addLayer(vectorLayer);

                            blockerList[auxarray[0]] = auxarrayRemoveInfo;
                        }

                        /** caminhos */
                        let cont=0;
                        var format;
                        for (var key in arrayBlockRoads) {
                            let aux = arrayBlockRoads[key];
                            let roadif = aux[0];
                            let roadGeojson = aux[1];
                            let auxarrayRemoveInfo = [];

                            auxarrayRemoveInfo.push('roadvector_' + roadif);

                            format = new ol.format.GeoJSON({
                                featureProjection:"EPSG:4326",
                            });

                            auxarrayRemoveInfo[0] = new ol.source.Vector({
                                features:format.readFeatures(roadGeojson)
                            });

                            let vectorLayer = new ol.layer.Vector({
                                source: auxarrayRemoveInfo[0],
                                style: new ol.style.Style({
                                    stroke: new ol.style.Stroke({
                                        color: 'red',
                                        width: 5
                                    }),
                                    zIndex: cont,
                                })
                            });

                            map.addLayer(vectorLayer);

                            blockerRoadList[roadif] = auxarrayRemoveInfo;
                        }
                    },
                    error: function(jqXHR, exception){
                        console.log("nao funcionou - showBlockedRoad");
                        let msg = '';
                        if (jqXHR.status === 0) {
                            msg = 'Not connect.\n Verify Network.';
                        } else if (jqXHR.status == 404) {
                            msg = 'Requested page not found. [404]';
                        } else if (jqXHR.status == 500) {
                            msg = 'Internal Server Error [500].';
                        } else if (exception === 'parsererror') {
                            msg = 'Requested JSON parse failed.';
                        } else if (exception === 'timeout') {
                            msg = 'Time out error.';
                        } else if (exception === 'abort') {
                            msg = 'Ajax request aborted.';
                        } else {
                            msg = 'Uncaught Error.\n' + jqXHR.responseText;
                        }
                        console.log("Erro: " + msg);
                    }
                });
            },
            error: function(jqXHR, exception){
                console.log("nao funcionou - initUser");
                let msg = '';
                if (jqXHR.status === 0) {
                    msg = 'Not connect.\n Verify Network.';
                } else if (jqXHR.status == 404) {
                    msg = 'Requested page not found. [404]';
                } else if (jqXHR.status == 500) {
                    msg = 'Internal Server Error [500].';
                } else if (exception === 'parsererror') {
                    msg = 'Requested JSON parse failed.';
                } else if (exception === 'timeout') {
                    msg = 'Time out error.';
                } else if (exception === 'abort') {
                    msg = 'Ajax request aborted.';
                } else {
                    msg = 'Uncaught Error.\n' + jqXHR.responseText;
                }
                console.log("Erro: " + msg);
            }
        });
        //INFORMAÇÃO SOBRE A FUNÇÃO DE CUSTO
        $.ajax({
            type: "GET",
            headers: {'X-Requested-With': 'XMLHttpRequest'},
            url: "http://aal.ieeta.pt/hlt/api/v1/readdata/", //Carregar a informação das preferencias da função de custo para o menu
            contentType: "application/json",
            dataType: "text",
            data: {id: userid},
            success: function(result){
                var obj = JSON.parse(result);
                for (let key in obj) {
                    if(key == "cover" || key == "incli" || key == "security") {
                        for (let key2 in obj[key]) {
                            let option = key2 + "-" + key;
                            if (obj[key][key2]) {
                                document.getElementById(option).checked = true;
                            }
                        }
                    }else{
                        for (let key2 in obj[key]) {
                            let option = key2+"-"+key;
                            document.getElementById(option).value = obj[key][key2];
                        }
                    }
                }
            },
            error: function(jqXHR, exception){
                console.log("nao funcionou - readdata");
                let msg = '';
                if (jqXHR.status === 0) {
                    msg = 'Not connect.\n Verify Network.';
                } else if (jqXHR.status == 404) {
                    msg = 'Requested page not found. [404]';
                } else if (jqXHR.status == 500) {
                    msg = 'Internal Server Error [500].';
                } else if (exception === 'parsererror') {
                    msg = 'Requested JSON parse failed.';
                } else if (exception === 'timeout') {
                    msg = 'Time out error.';
                } else if (exception === 'abort') {
                    msg = 'Ajax request aborted.';
                } else {
                    msg = 'Uncaught Error.\n' + jqXHR.responseText;
                }
                console.log("Erro: " + msg);
            }
        });
    }else{ //Quando o cookie não é detectado
        alert("No user detected");
        self.location = "http://aal.ieeta.pt/hlt/apiteste/";
    }

    function delete_cookie(name) {
        document.cookie = name +'=; Path=/; Expires=Thu, 01 Jan 1970 00:00:01 GMT;';
    }

    $("#logout").click(function() {
        delete_cookie("cook");
        self.location = "http://aal.ieeta.pt/hlt/apiteste/";
    });

    $("#sendDataButton").click(function() {
        let Calcadaportuguesa_Cimento = $("#portugueswalkway_concrete-roadMultiplier").val();
        let Alcatrao = $("#tarmac-roadMultiplier").val();
        let Pistabicicleta = $("#cicleway-roadMultiplier").val();
        let Terra = $("#dirt-roadMultiplier").val();
        let Passadicomadeira_metal = $("#woodenway_metalway-roadMultiplier").val();
        let escadas = $('#stairs-incli:checkbox:checked').length > 0;
        let ajudamovimento = $('#helpmovement-incli:checkbox:checked').length > 0;
        let coverageshape_cover = $('#coverage_shape-cover:checkbox:checked').length > 0;
        let coveragerainprotected_cover = $('#coverage_rainprotected-cover:checkbox:checked').length > 0;
        let allowcars_security = $('#allowcars-security:checkbox:checked').length > 0;
        let allowbikes_security = $('#allowbikes-security:checkbox:checked').length > 0;
        $.ajax({
            type: "POST",
            headers: {'X-Requested-With': 'XMLHttpRequest'},
            url: "http://aal.ieeta.pt/hlt/api/v1/updateData/", //Actualizar as preferencias do utilizador na base de dados
            dataType: "text",
            data: {
                id: userid,
                Calcadaportuguesa_Cimento: Calcadaportuguesa_Cimento,
                Alcatrao: Alcatrao,
                Pistabicicleta: Pistabicicleta,
                Terra: Terra,
                escadas:escadas,
                ajudamovimento:ajudamovimento,
                Passadicomadeira_metal: Passadicomadeira_metal,
                coverageshape_cover: coverageshape_cover,
                coveragerainprotected_cover: coveragerainprotected_cover,
                allowcars_security: allowcars_security,
                allowbikes_security: allowbikes_security
            },
            success: function(result){
                console.log(result);
                location.reload(); //Para colocar em função os novos custos
            },
            error: function(jqXHR, exception){
                console.log("nao funcionou");
                let msg = '';
                if (jqXHR.status === 0) {
                    msg = 'Not connect.\n Verify Network.';
                } else if (jqXHR.status == 404) {
                    msg = 'Requested page not found. [404]';
                } else if (jqXHR.status == 500) {
                    msg = 'Internal Server Error [500].';
                } else if (exception === 'parsererror') {
                    msg = 'Requested JSON parse failed.';
                } else if (exception === 'timeout') {
                    msg = 'Time out error.';
                } else if (exception === 'abort') {
                    msg = 'Ajax request aborted.';
                } else {
                    msg = 'Uncaught Error.\n' + jqXHR.responseText;
                }
                console.log("Erro: " + msg);
            }
        });
    });
});

function getCookie(name) {
    var nameEQ = name + "=";
    var ca = document.cookie.split(';');
    for(var i=0;i < ca.length;i++) {
        var c = ca[i];
        while (c.charAt(0)==' ') c = c.substring(1,c.length);
        if (c.indexOf(nameEQ) == 0) return c.substring(nameEQ.length,c.length);
    }
    return null;
}

function mapa(){
    map = new ol.Map({
        layers: [
            new ol.layer.Tile({
                source: new ol.source.OSM()
            })
        ],
        target: 'map',
        controls: ol.control.defaults({
            attributionOptions: {
                collapsible: false
            }
        }),
        view: new ol.View({
            projection: 'EPSG:4326',
            center: [-8.445590, 40.574180],
            zoom: 16
        })
    });

    $.ajax({
        url: "http://aal.ieeta.pt/hlt/api/v1/loadPois/", //Para carregar os pois inseridos por utilizador
        type: "get",
        data: {
            userid: userid,
        },
        success: function (response) {
            if(response.length == 0){
                console.log("No POIs detected in the database");
            }
            else{
                for(var i=0; i<response.length; i++){
                    let id = response[i]["id"]
                    let nome = response[i]["nome"]
                    let geom = response[i]["geom"];
                    let selecionado = response[i]["selecionado"];
                    let lat = response[i]["latitude"];
                    let long = response[i]["longitude"];
                    let cv_lat = response[i]["cv_lat"];
                    let cv_long = response[i]["cv_long"];
                    let tipo = response[i]["tipo"];
                    let actual = response[i]["tipo"];

                    //Icons
                    let iconFeatureinit = new ol.Feature({
                        geometry: new ol.geom.Point([cv_long, cv_lat]),
                        geom: geom,
                        id: id,
                        selecionado: selecionado,
                        cv_lat: cv_lat,
                        cv_lon: cv_long,
                        lat_Original: lat,
                        long_Original: long,
                        nome: nome,
                        type: 1,
                        tipo: tipo
                    });

                    if (!selecionado) {
                        iconStyleinit = new ol.style.Style({
                            image: new ol.style.Icon(
                                ({
                                    anchor: [0.5, 46],
                                    anchorXUnits: 'fraction',
                                    anchorYUnits: 'pixels',
                                    src: './images/icon_'+tipo+'-mini.png'
                                    //src: 'https://openlayers.org/en/v4.6.5/examples/data/icon.png'
                                }))
                        });
                    }else {
                        iconStyleinit = new ol.style.Style({
                            image: new ol.style.Icon(
                                ({
                                    anchor: [0.5, 46],
                                    anchorXUnits: 'fraction',
                                    anchorYUnits: 'pixels',
                                    src: './images/icon_'+tipo+'_selected-mini.png'
                                    //src: 'https://openlayers.org/en/v4.6.5/examples/data/icon.png'
                                }))
                        });
                    }

                    iconFeatureinit.setStyle(iconStyleinit);

                    vectorSourceinit = new ol.source.Vector({
                        features: [iconFeatureinit]
                    });

                    let vectorLayerinit = new ol.layer.Vector({
                        source: vectorSourceinit
                    });

                    map.addLayer(vectorLayerinit);
                }
            }
        },
        error: function(jqXHR, exception) {
            console.log("nao funcionou - loadPois");
            let msg = '';
            if (jqXHR.status === 0) {
                msg = 'Not connect.\n Verify Network.';
            } else if (jqXHR.status == 404) {
                msg = 'Requested page not found. [404]';
            } else if (jqXHR.status == 500) {
                msg = 'Internal Server Error [500].';
            } else if (exception === 'parsererror') {
                msg = 'Requested JSON parse failed.';
            } else if (exception === 'timeout') {
                msg = 'Time out error.';
            } else if (exception === 'abort') {
                msg = 'Ajax request aborted.';
            } else {
                msg = 'Uncaught Error.\n' + jqXHR.responseText;
            }
            console.log("Erro: " + msg);
        }
    });

    map.on('singleclick', function(evt) {
        customDelete = ('#deletepoi:checkbox:checked').length > 0;
        let feature = map.forEachFeatureAtPixel(evt.pixel, function (feature, layer) {
            return feature;
        });
        if (feature) {
            let id = feature["values_"]["id"];
            let nome = feature["values_"]["nome"];
            let geom = feature["values_"]["geom"];
            let selec = feature["values_"]["selecionado"];
            let lat = feature["values_"]["lat_Original"];
            let long = feature["values_"]["long_Original"]
            let cv_lat = feature["values_"]["cv_lat"];
            let cv_lon = feature["values_"]["cv_lon"];
            let type = feature["values_"]["type"];
            let pointID = feature["values_"]["idPoint_vertex"];
            let tipo = feature["values_"]["tipo"];

            if (type == 2) //Para selecionar o antiPOI
            {
                $.ajax({
                    type: "get",
                    url: "http://aal.ieeta.pt/hlt/api/v1/unwantedPois/", //Carregar os anti-pois em função do utilizador
                    data: {
                        long: long,
                        lat: lat,
                        userid: userid,
                        poiid: id
                    },
                    success: function (response) {
                        for(let i=0;i<blockerList[id].length;i++){
                            blockerList[id][i].clear();
                        }
                    },
                    error: function(jqXHR, exception){
                        console.log("Nao funcionou - unwantedPois");
                        let msg = '';
                        if (jqXHR.status === 0) {
                            msg = 'Not connect.\n Verify Network.';
                        } else if (jqXHR.status == 404) {
                            msg = 'Requested page not found. [404]';
                        } else if (jqXHR.status == 500) {
                            msg = 'Internal Server Error [500].';
                        } else if (exception === 'parsererror') {
                            msg = 'Requested JSON parse failed.';
                        } else if (exception === 'timeout') {
                            msg = 'Time out error.';
                        } else if (exception === 'abort') {
                            msg = 'Ajax request aborted.';
                        } else {
                            msg = 'Uncaught Error.\n' + jqXHR.responseText;
                        }
                        console.log("Erro: " + msg);
                    }
                });
            }
            else if(type == 1){
                if ((tipo == "custom" || tipo == "custom_add") && document.getElementById('deletepoi').checked){
                    //apagar o icon ja inserido
                    map.forEachFeatureAtPixel(evt.pixel, function (feature, layer) {
                        feature.setStyle(null);
                    });
                    $.ajax({
                        type: "POST",
                        headers: {'X-Requested-With': 'XMLHttpRequest'},
                        url: "http://aal.ieeta.pt/hlt/api/v1/removeallpoi/", //Remover os custompois em função do utilizador
                        data: {
                            long: long,
                            lat: lat,
                            option: 0,
                            userid: userid
                        },
                        success: function (response) {
                            console.log(response);
                        },
                        error: function (jqXHR, exception) {
                            console.log("nao funciona - removeAllPois");
                            let msg = '';
                            if (jqXHR.status === 0) {
                                msg = 'Not connect.\n Verify Network.';
                            } else if (jqXHR.status == 404) {
                                msg = 'Requested page not found. [404]';
                            } else if (jqXHR.status == 500) {
                                msg = 'Internal Server Error [500].';
                            } else if (exception === 'parsererror') {
                                msg = 'Requested JSON parse failed.';
                            } else if (exception === 'timeout') {
                                msg = 'Time out error.';
                            } else if (exception === 'abort') {
                                msg = 'Ajax request aborted.';
                            } else {
                                msg = 'Uncaught Error.\n' + jqXHR.responseText;
                            }
                            console.log("Erro: " + msg);
                        }
                    });
                }
                else{
                    let iconStyleinit;
                    if (!selec) {
                        if(tipo == "custom_add"){
                            let xy = evt.coordinate;

                            iconFeatureinitCustomAddPoi = new ol.Feature({
                                geometry: new ol.geom.Point([cv_lon, cv_lat]),
                                cv_lon: cv_lon,
                                cv_lat: cv_lat,
                                long_Original: xy[0],
                                lat_Original: xy[1],
                                selecionado: true,
                                tipo: "custom_add",
                                type: 1
                            });

                            iconStyleinitCustomAddPoi = new ol.style.Style({
                                image: new ol.style.Icon(
                                    ({
                                        anchor: [0.5, 46],
                                        anchorXUnits: 'fraction',
                                        anchorYUnits: 'pixels',
                                        src: './images/icon_custom_selected-mini.png'
                                    }))
                            });

                            iconFeatureinitCustomAddPoi.setStyle(iconStyleinitCustomAddPoi);

                            vectorSourceCustomAddPoi = new ol.source.Vector({
                                features: [iconFeatureinitCustomAddPoi]
                            });

                            vectorLayerinitCustomAddPoi = new ol.layer.Vector({
                                source: vectorSourceCustomAddPoi
                            });

                            map.addLayer(vectorLayerinitCustomAddPoi);
                        }
                        else{
                            iconFeatureinit = new ol.Feature({
                                geometry: new ol.geom.Point([cv_lon, cv_lat]),
                                geom: geom,
                                id: id,
                                selecionado: true,
                                cv_lat: cv_lat,
                                cv_lon: cv_lon,
                                lat_Original: lat,
                                long_Original: long,
                                nome: nome,
                                type: 1,
                                tipo: tipo
                            });

                            iconStyleinit = new ol.style.Style({
                                image: new ol.style.Icon(
                                    ({
                                        anchor: [0.5, 46],
                                        anchorXUnits: 'fraction',
                                        anchorYUnits: 'pixels',
                                        src: './images/icon_'+tipo+'_selected-mini.png'
                                    }))
                            });

                            iconFeatureinit.setStyle(iconStyleinit);

                            vectorSourceinit = new ol.source.Vector({
                                features: [iconFeatureinit]
                            });

                            vectorLayerinit = new ol.layer.Vector({
                                source: vectorSourceinit
                            });

                            map.addLayer(vectorLayerinit);
                        }
                    } else {
                        if(tipo == "custom_add"){
                            let xy = evt.coordinate;

                            vectorSourceCustomAddPoi.clear();

                            let iconFeatureinitCustomAddPoi2 = new ol.Feature({
                                geometry: new ol.geom.Point([cv_lon, cv_lat]),
                                cv_lon: cv_lon,
                                cv_lat: cv_lat,
                                long_Original: xy[0],
                                lat_Original: xy[1],
                                selecionado: false,
                                tipo: "custom_add",
                                type: 1
                            });

                            let iconStyleinitCustomAddPoi2 = new ol.style.Style({
                                image: new ol.style.Icon(
                                    ({
                                        anchor: [0.5, 46],
                                        anchorXUnits: 'fraction',
                                        anchorYUnits: 'pixels',
                                        src: './images/icon_custom-mini.png'
                                    }))
                            });

                            iconFeatureinitCustomAddPoi2.setStyle(iconStyleinitCustomAddPoi2);

                            let vectorSourceCustomAddPoi2 = new ol.source.Vector({
                                features: [iconFeatureinitCustomAddPoi2]
                            });

                            let vectorLayerinitCustomAddPoi2 = new ol.layer.Vector({
                                source: vectorSourceCustomAddPoi2
                            });

                            map.addLayer(vectorLayerinitCustomAddPoi2);
                        }
                        else{
                            iconFeatureinit = new ol.Feature({
                                geometry: new ol.geom.Point([cv_lon, cv_lat]),
                                geom: geom,
                                id: id,
                                selecionado: false,
                                cv_lat: cv_lat,
                                cv_lon: cv_lon,
                                lat_Original: lat,
                                long_Original: long,
                                nome: nome,
                                type: 1,
                                tipo: tipo
                            });

                            iconStyleinit = new ol.style.Style({
                                image: new ol.style.Icon(
                                    ({
                                        anchor: [0.5, 46],
                                        anchorXUnits: 'fraction',
                                        anchorYUnits: 'pixels',
                                        src: './images/icon_'+tipo+'-mini.png'
                                    }))
                            });

                            iconFeatureinit.setStyle(iconStyleinit);

                            vectorSourceinit = new ol.source.Vector({
                                features: [iconFeatureinit]
                            });

                            vectorLayerinit = new ol.layer.Vector({
                                source: vectorSourceinit
                            });

                            map.addLayer(vectorLayerinit);
                        }
                    }
                }
            }
            else { //Estradas bloquedas
                let id = feature.getId();
                $.ajax({
                    type: "get",
                    url: "http://aal.ieeta.pt/hlt/api/v1/removeBlockedRoads/", //remover a estrada individualmente
                    data: {
                        userid: userid,
                        roadid: id
                    },
                    success: function (response) {
                        console.log(response);
                        blockerRoadList[id][0].clear();
                    },
                    error: function(jqXHR, exception){
                        console.log("Nao funcionou - remove blockedroad");
                        let msg = '';
                        if (jqXHR.status === 0) {
                            msg = 'Not connect.\n Verify Network.';
                        } else if (jqXHR.status == 404) {
                            msg = 'Requested page not found. [404]';
                        } else if (jqXHR.status == 500) {
                            msg = 'Internal Server Error [500].';
                        } else if (exception === 'parsererror') {
                            msg = 'Requested JSON parse failed.';
                        } else if (exception === 'timeout') {
                            msg = 'Time out error.';
                        } else if (exception === 'abort') {
                            msg = 'Ajax request aborted.';
                        } else {
                            msg = 'Uncaught Error.\n' + jqXHR.responseText;
                        }
                        console.log("Erro: " + msg);
                    }
                });
            }
            $.ajax({
                type: "POST",
                headers: {'X-Requested-With': 'XMLHttpRequest'},
                url: "http://aal.ieeta.pt/hlt/api/v1/selectPOI/", //Selecionar o poi no mapa (custom ou standard)
                data: {
                    long: long,
                    lat: lat,
                    selec: selec,
                    userid: userid
                },
                error: function(jqXHR, exception){
                    console.log("Nao funcionou - selectPOI");
                    let msg = '';
                    if (jqXHR.status === 0) {
                        msg = 'Not connect.\n Verify Network.';
                    } else if (jqXHR.status == 404) {
                        msg = 'Requested page not found. [404]';
                    } else if (jqXHR.status == 500) {
                        msg = 'Internal Server Error [500].';
                    } else if (exception === 'parsererror') {
                        msg = 'Requested JSON parse failed.';
                    } else if (exception === 'timeout') {
                        msg = 'Time out error.';
                    } else if (exception === 'abort') {
                        msg = 'Ajax request aborted.';
                    } else {
                        msg = 'Uncaught Error.\n' + jqXHR.responseText;
                    }
                    console.log("Erro: " + msg);
                }
            });
        }
        else{
            //clicar no mapa
            var xy = evt.coordinate;
            $.ajax({
                url: "http://aal.ieeta.pt/hlt/api/v1/closedPoints/", //Selecionar o vertice mais proximo
                type: "get",
                data:{
                    long: xy[0],
                    lat: xy[1]
                },
                success: function (response) {
                    console.log(response);
                    let coord = response.split(" ");

                    if(trajectovectorSourceinitIcon != undefined){
                        trajectovectorSourceinitIcon.clear();
                    }

                    //Icons
                    trajectoiconFeatureinitIcon = new ol.Feature({
                        geometry: new ol.geom.Point([coord[0], coord[1]]),
                    });

                    trajectoiconStyleinitIcon = new ol.style.Style({
                        image: new ol.style.Icon(
                            ({
                                anchor: [0.5, 46],
                                anchorXUnits: 'fraction',
                                anchorYUnits: 'pixels',
                                src: './images/pin.png'
                            }))
                    });

                    trajectoiconFeatureinitIcon.setStyle(trajectoiconStyleinitIcon);

                    trajectovectorSourceinitIcon = new ol.source.Vector({
                        features: [trajectoiconFeatureinitIcon]
                    });

                    trajectovectorLayerinitIcon = new ol.layer.Vector({
                        source: trajectovectorSourceinitIcon
                    });

                    map.addLayer(trajectovectorLayerinitIcon);

                    $.ajax({
                        url: "http://aal.ieeta.pt/hlt/api/v1/teseSolucao/",
                        type: "get",
                        data: {
                            long: coord[0],
                            lat: coord[1],
                            userid: userid
                        },
                        success: function (response) {
                            console.log(response);
                            let TypeRoute = response["TypeRoute"];
                            let routegeojson = response["geojson"];

                            if(TypeRoute == "SoloPoint"){
                                let distancia = prompt("Insira a distancia do raio (em metros)", "50");
                                Pace.track(function(){
                                    $.ajax({
                                        url: "http://aal.ieeta.pt/hlt/api/v1/soloteseSolucao/",
                                        type: "get",
                                        data: {
                                            long: coord[0],
                                            lat: coord[1],
                                            userid: userid,
                                            distancia: distancia
                                        },
                                        success: function (response) {
                                            console.log("solo");
                                            console.log(solotrajectoVectorSource);
                                            console.log(trajectoVectorSource);
                                            /*if(solotrajectoVectorSource != undefined){
                                                alert("tinha solo");
                                                solotrajectoVectorSource.clear();
                                            }else if(trajectoVectorSource != undefined){
                                                alert("tinha multi");

                                            }*/
                                            try {
                                                solotrajectoVectorSource.clear();
                                            }
                                            catch(err) {
                                                //console.log("Falha ao apagar o trajecto solo");
                                            }
                                            try {
                                                trajectoVectorSource.clear();
                                            }
                                            catch(err) {
                                                //console.log("Falha ao apagar o trajecto multi");
                                            }
                                            //solotrajectoVectorSource.clear();
                                            //trajectoVectorSource.clear();
                                            soloroutegeojson = response["geojson"];

                                            solotrajectoformat = new ol.format.GeoJSON({
                                                featureProjection:"EPSG:4326"
                                            });

                                            solotrajectoVectorSource = new ol.source.Vector({
                                                features:solotrajectoformat.readFeatures(soloroutegeojson)
                                            });

                                            solotrajectoVectorLayer = new ol.layer.Vector({
                                                source: solotrajectoVectorSource,
                                                style: new ol.style.Style({
                                                    stroke: new ol.style.Stroke({
                                                        color: 'green',
                                                        width: 3
                                                    })
                                                })
                                            });

                                            map.addLayer(solotrajectoVectorLayer);
                                        },
                                        error: function (jqXHR, exception) {
                                            console.log("Erro to create a solo solution.")
                                            let msg = '';
                                            if (jqXHR.status === 0) {
                                                msg = 'Not connect.\n Verify Network.';
                                            } else if (jqXHR.status == 404) {
                                                msg = 'Requested page not found. [404]';
                                            } else if (jqXHR.status == 500) {
                                                msg = 'Internal Server Error [500].';
                                            } else if (exception === 'parsererror') {
                                                msg = 'Requested JSON parse failed.';
                                            } else if (exception === 'timeout') {
                                                msg = 'Time out error.';
                                            } else if (exception === 'abort') {
                                                msg = 'Ajax request aborted.';
                                            } else {
                                                msg = 'Uncaught Error.\n' + jqXHR.responseText;
                                            }
                                            console.log("Erro: " + msg);
                                        }
                                    });
                                });
                            }else if(TypeRoute == "MultiPoint"){
                                console.log("multi");
                                /*if (trajectoVectorSource != undefined) {
                                    alert("tinha multi");
                                    trajectoVectorSource.clear();
                                }else if(solotrajectoVectorSource != undefined){
                                    alert("tinha solo");
                                    solotrajectoVectorSource.clear();
                                }*/
                                try {
                                    solotrajectoVectorSource.clear();
                                }
                                catch(err) {
                                    //console.log("Falha ao apagar o trajecto solo");
                                }
                                try {
                                    trajectoVectorSource.clear();
                                }
                                catch(err) {
                                    //console.log("Falha ao apagar o trajecto multi");
                                }

                                trajectoformat = new ol.format.GeoJSON({
                                    featureProjection:"EPSG:4326"
                                });

                                trajectoVectorSource = new ol.source.Vector({
                                    features:trajectoformat.readFeatures(routegeojson)
                                });

                                trajectoVectorLayer = new ol.layer.Vector({
                                    source: trajectoVectorSource,
                                    style: new ol.style.Style({
                                        stroke: new ol.style.Stroke({
                                            color: 'green',
                                            width: 3
                                        })
                                    })
                                });

                                map.addLayer(trajectoVectorLayer);
                            }
                        },
                        error: function (jqXHR, exception) {
                            console.log("nao funcionou - teseSolucao");
                            let msg = '';
                            if (jqXHR.status === 0) {
                                msg = 'Not connect.\n Verify Network.';
                            } else if (jqXHR.status == 404) {
                                msg = 'Requested page not found. [404]';
                            } else if (jqXHR.status == 500) {
                                msg = 'Internal Server Error [500].';
                            } else if (exception === 'parsererror') {
                                msg = 'Requested JSON parse failed.';
                            } else if (exception === 'timeout') {
                                msg = 'Time out error.';
                            } else if (exception === 'abort') {
                                msg = 'Ajax request aborted.';
                            } else {
                                msg = 'Uncaught Error.\n' + jqXHR.responseText;
                            }
                            console.log("Erro: " + msg);
                        }
                    });
                },
                error: function (jqXHR, exception) {
                    console.log("nao funcionou - closedPoints");
                    let msg = '';
                    if (jqXHR.status === 0) {
                        msg = 'Not connect.\n Verify Network.';
                    } else if (jqXHR.status == 404) {
                        msg = 'Requested page not found. [404]';
                    } else if (jqXHR.status == 500) {
                        msg = 'Internal Server Error [500].';
                    } else if (exception === 'parsererror') {
                        msg = 'Requested JSON parse failed.';
                    } else if (exception === 'timeout') {
                        msg = 'Time out error.';
                    } else if (exception === 'abort') {
                        msg = 'Ajax request aborted.';
                    } else {
                        msg = 'Uncaught Error.\n' + jqXHR.responseText;
                    }
                    console.log("Erro: " + msg);
                }
            });
        }
    });

    var contextmenu_items = [
        {
            text: 'Select road to block',
            callback: soloBlockRoad
        },
        {
            text: 'Unwanted Poi',
            callback: insertblock
        },
        {
            text: 'Add Poi',
            callback: addPoints
        },
        {
            text: "-------------"
        },
        {
            text: 'Remove block roads',
            callback: removeallblocks
        },
        {
            text: 'Remove all custom Pois',
            callback: removeAllCustomPois
        },
        {
            text: 'ShowPoints',
            callback: showPoints
        }
    ];

    var contextmenu = new ContextMenu({
        width: 180,
        items: contextmenu_items
    });
    map.addControl(contextmenu);

    var removeMarkerItem = {
        text: 'Remove this Marker',
        classname: 'marker',
        callback: removeMarker
    };

    contextmenu.on('open', function (evt) {
        var feature =	map.forEachFeatureAtPixel(evt.pixel, ft => ft);

        if (feature && feature.get('type') === 'removable') {
            contextmenu.clear();
            removeMarkerItem.data = { marker: feature };
            contextmenu.push(removeMarkerItem);
        } else {
            contextmenu.clear();
            contextmenu.extend(contextmenu_items);
        }
    });
}

function icon(option){
    switch(option) {
        case 1:
            iconStyleinit = new ol.style.Style({
                image: new ol.style.Icon(
                    ({
                        anchor: [0.5, 46],
                        anchorXUnits: 'fraction',
                        anchorYUnits: 'pixels',
                        src: './images/icon_cafe_selected-mini.png'
                    }))
            });
            break;
        case 2:
            iconStyleinit = new ol.style.Style({
                image: new ol.style.Icon(
                    ({
                        anchor: [0.5, 46],
                        anchorXUnits: 'fraction',
                        anchorYUnits: 'pixels',
                        src: './images/icon_cafe-mini.png'
                    }))
            });
            break;
    }


    iconFeatureinit.setStyle(iconStyleinit);

    vectorSourceinit = new ol.source.Vector({
        features: [iconFeatureinit]
    });

    vectorLayerinit = new ol.layer.Vector({
        source: vectorSourceinit
    });

    map.addLayer(vectorLayerinit);
}

function removeMarker(obj) {
    vectorLayer.getSource().removeFeature(obj.data.marker);
}
idcaminho = 0;

function coord(evt) {
    console.log(evt.coordinate);
}

function showPoints(evt){
    let input = prompt("Insert o par de coordenadas ,ex: -8.449817161407472 40.57785999076844,-8.435547809448243 40.5701996018219");
    let coord = input.split(",");
    let singlecoord1 = coord[0].split(" ");
    let singlecoord2 = coord[1].split(" ");
    $.ajax({
        url: "http://aal.ieeta.pt/hlt/api/v1/showPoints/", //Mostrar os vertices do grafo
        type: "get",
        data: {
            userid: userid,
            long1: singlecoord1[0],
            lat1: singlecoord1[1],
            long2: singlecoord2[0],
            lat2: singlecoord2[1]
        },
        success: function (response) {
            let data = JSON.parse(response);
            for (var key in data) {
                iconFeatureinit = new ol.Feature({
                    geometry: new ol.geom.Point([data[key][0], data[key][1]]),
                    lat: data[key][1],
                    long: data[key][0],
                    idPoint_vertex: key,
                    type: 2, //2 significa o tipo de icon [vertice do grafo] (nao é poi(1) nem ponto de interação(0))
                });

                iconStyleinit = new ol.style.Style({
                    image: new ol.style.Icon(
                        ({
                            anchor: [0.5, 0.5],
                            anchorXUnits: 'fraction',
                            anchorYUnits: 'pixels',
                            scale: 0.5,
                            color: '#8959A8',
                            src: 'images/dot.png'
                        }))
                });

                iconFeatureinit.setStyle(iconStyleinit);

                vectorSourceinit = new ol.source.Vector({
                    features: [iconFeatureinit]
                });

                vectorLayerinit = new ol.layer.Vector({
                    source: vectorSourceinit
                });

                map.addLayer(vectorLayerinit);
            }
        },
        error: function(jqXHR, exception){
            console.log("nao funciona - showPoints");
            let msg = '';
            if (jqXHR.status === 0) {
                msg = 'Not connect.\n Verify Network.';
            } else if (jqXHR.status == 404) {
                msg = 'Requested page not found. [404]';
            } else if (jqXHR.status == 500) {
                msg = 'Internal Server Error [500].';
            } else if (exception === 'parsererror') {
                msg = 'Requested JSON parse failed.';
            } else if (exception === 'timeout') {
                msg = 'Time out error.';
            } else if (exception === 'abort') {
                msg = 'Ajax request aborted.';
            } else {
                msg = 'Uncaught Error.\n' + jqXHR.responseText;
            }
            console.log("Erro: " + msg);
        }
    });
}

function soloBlockRoad(evt) {
    var xy = evt.coordinate;
    $.ajax({
        url: "http://aal.ieeta.pt/hlt/api/v1/blockRoad/", //Bloquear uma escrada individualmente
        type: "get",
        data:{
            long: xy[0],
            lat: xy[1],
            id: userid
        },
        success: function (response) {
            console.log(response);
            let roadid = response[0];
            let roadGeojson = response[1];
            let auxarrayRemoveInfo = [];

            auxarrayRemoveInfo.push('roadvector_' + roadid);

            format = new ol.format.GeoJSON({
                featureProjection:"EPSG:4326",
            });

            auxarrayRemoveInfo[0] = new ol.source.Vector({
                features:format.readFeatures(roadGeojson)
            });

            let vectorLayer = new ol.layer.Vector({
                source: auxarrayRemoveInfo[0],
                style: new ol.style.Style({
                    stroke: new ol.style.Stroke({
                        color: 'red',
                        width: 5
                    }),
                })
            });

            map.addLayer(vectorLayer);

            blockerRoadList[roadid] = auxarrayRemoveInfo;
        },
        error: function(jqXHR, exception){
            console.log("nao funciona - blockRoad");
            let msg = '';
            if (jqXHR.status === 0) {
                msg = 'Not connect.\n Verify Network.';
            } else if (jqXHR.status == 404) {
                msg = 'Requested page not found. [404]';
            } else if (jqXHR.status == 500) {
                msg = 'Internal Server Error [500].';
            } else if (exception === 'parsererror') {
                msg = 'Requested JSON parse failed.';
            } else if (exception === 'timeout') {
                msg = 'Time out error.';
            } else if (exception === 'abort') {
                msg = 'Ajax request aborted.';
            } else {
                msg = 'Uncaught Error.\n' + jqXHR.responseText;
            }
            console.log("Erro: " + msg);
        }
    });
}

//unwantedpo
function insertblock(evt){
    var xy = evt.coordinate;;
    $.ajax({
        type: "get",
        url: "http://aal.ieeta.pt/hlt/api/v1/Insertblock/", //Inserir um anti-poi
        data: {
            long: xy[0],
            lat: xy[1],
            userid: userid
        },
        success: function (response) {
            console.log(response);
            let auxarrayRemoveInfo=[];

            auxarrayRemoveInfo.push('unwantedpointvectorSourceinit_'+response[0]);
            auxarrayRemoveInfo.push('unwantedpointroadvectorSource_'+response[0]);

            //Ponto
            let coord = response[1].split(" ");

            unwantedPointiconFeatureinit = new ol.Feature({
                geometry: new ol.geom.Point([coord[0], coord[1]]),
                long_Original: coord[0],
                lat_Original: coord[1],
                type: 2,
                id: response[0]
            });

            unwantedPointiconStyleinit = new ol.style.Style({
                image: new ol.style.Icon(
                    ({
                        anchor: [0.5, 46],
                        anchorXUnits: 'fraction',
                        anchorYUnits: 'pixels',
                        src: './images/unwanted.png',
                        scale: 0.6
                    }))
            });

            unwantedPointiconFeatureinit.setStyle(unwantedPointiconStyleinit);

            auxarrayRemoveInfo[0] = new ol.source.Vector({
                features: [unwantedPointiconFeatureinit]
            });

            unwantedpointvectorLayerinit = new ol.layer.Vector({
                source: auxarrayRemoveInfo[0]
            });

            map.addLayer(unwantedpointvectorLayerinit);

            //geojson
            let geojson = response[2].replace("\\","");
            unwantedpoiroadformat = new ol.format.GeoJSON({
                featureProjection:"EPSG:4326"
            });
            auxarrayRemoveInfo[1] = new ol.source.Vector({
                features:unwantedpoiroadformat.readFeatures(geojson)
            });

            unwantedpoiroadvectorLayer = new ol.layer.Vector({
                source: auxarrayRemoveInfo[1],
                style: new ol.style.Style({
                    stroke: new ol.style.Stroke({
                        color: 'red',
                        width: 3,
                        lineDash: [.1, 5]
                    })
                })
            });

            map.addLayer(unwantedpoiroadvectorLayer);

            blockerList[response[0]]=auxarrayRemoveInfo
        },
        error: function (jqXHR, exception) {
            console.log("nao funciona - Insertblock");
            let msg = '';
            if (jqXHR.status === 0) {
                msg = 'Not connect.\n Verify Network.';
            } else if (jqXHR.status == 404) {
                msg = 'Requested page not found. [404]';
            } else if (jqXHR.status == 500) {
                msg = 'Internal Server Error [500].';
            } else if (exception === 'parsererror') {
                msg = 'Requested JSON parse failed.';
            } else if (exception === 'timeout') {
                msg = 'Time out error.';
            } else if (exception === 'abort') {
                msg = 'Ajax request aborted.';
            } else {
                msg = 'Uncaught Error.\n' + jqXHR.responseText;
            }
            console.log("Erro: " + msg);
        }
    });
}

function removeallblocks(){
    $.ajax({
        type: "get",
        url: "http://aal.ieeta.pt/hlt/api/v1/removeallBlockedRoad/", //Remover todas as estradas bloqueadas
        data: {
            userid: userid
        },
        success: function (response) {
            if(response){
                console.log("reload page");
                location.reload();
            }
        },
        error: function (jqXHR, exception) {
            console.log("nao funciona - removeBlockedRoad");
            let msg = '';
            if (jqXHR.status === 0) {
                msg = 'Not connect.\n Verify Network.';
            } else if (jqXHR.status == 404) {
                msg = 'Requested page not found. [404]';
            } else if (jqXHR.status == 500) {
                msg = 'Internal Server Error [500].';
            } else if (exception === 'parsererror') {
                msg = 'Requested JSON parse failed.';
            } else if (exception === 'timeout') {
                msg = 'Time out error.';
            } else if (exception === 'abort') {
                msg = 'Ajax request aborted.';
            } else {
                msg = 'Uncaught Error.\n' + jqXHR.responseText;
            }
            console.log("Erro: " + msg);
        }
    });
}

function removeAllCustomPois(){
    $.ajax({
        type: "POST",
        headers: {'X-Requested-With': 'XMLHttpRequest'},
        url: "http://aal.ieeta.pt/hlt/api/v1/removeallpoi/",
        data: {
            userid: userid,
            option: 1
        },
        success: function (response) {
            if(response){
                location.reload();
            }
        },
        error: function (jqXHR, exception) {
            console.log("nao funciona - removeAllPois");
            let msg = '';
            if (jqXHR.status === 0) {
                msg = 'Not connect.\n Verify Network.';
            } else if (jqXHR.status == 404) {
                msg = 'Requested page not found. [404]';
            } else if (jqXHR.status == 500) {
                msg = 'Internal Server Error [500].';
            } else if (exception === 'parsererror') {
                msg = 'Requested JSON parse failed.';
            } else if (exception === 'timeout') {
                msg = 'Time out error.';
            } else if (exception === 'abort') {
                msg = 'Ajax request aborted.';
            } else {
                msg = 'Uncaught Error.\n' + jqXHR.responseText;
            }
            console.log("Erro: " + msg);
        }
    });
}

function addPoints(evt){
    let xy = evt.coordinate;
    let jsondata = [];
    let data = {};
    data.userid = userid; /** ID DO UTILIZADOR */
    data.nome = "unknown";
    data.tipo = "custom";
    data.latitude = xy[1].toString();
    data.longitude = xy[0].toString();
    jsondata.push(data);
    let sendjson = JSON.stringify(jsondata);
    count = count+1;
    let vs = "vectorSource_"+count;
    actualPOIS.push(vs);
    let auxpois=[];
    $.ajax({
        type: "POST",
        headers: {'X-Requested-With': 'XMLHttpRequest'},
        url: "http://aal.ieeta.pt/hlt/api/v1/addPois/", //Adicionar custom pois
        contentType: "application/json",
        dataType: "text",
        data: sendjson,
        success: function (response) {
            console.log(response);
            $.ajax({
                type: "GET",
                url: "http://aal.ieeta.pt/hlt/api/v1/closedPoints/", // Selecionar o vertice mais proximo para o antipoi
                data: {
                    long: xy[0],
                    lat: xy[1]
                },
                success: function (response) {
                    let coord = response.split(" ");

                    auxpois.push('iconFeatureinitCustomAddPoi'+contPois);
                    auxpois.push('iconStyleinitCustomAddPoi'+contPois);
                    auxpois.push('vectorSourceCustomAddPoi'+contPois);
                    auxpois.push('vectorLayerinitCustomAddPoi'+contPois);
                    customPoiArray[contPois]=auxpois;

                    iconFeatureinitCustomAddPoi = new ol.Feature({
                        id: contPois,
                        geometry: new ol.geom.Point([coord[0], coord[1]]),
                        cv_lon: coord[0],
                        cv_lat: coord[1],
                        long_Original: xy[0],
                        lat_Original: xy[1],
                        selecionado: true,
                        tipo: "custom_add",
                        type: 1
                    });

                    iconStyleinitCustomAddPoi = new ol.style.Style({
                        image: new ol.style.Icon(
                            ({
                                anchor: [0.5, 46],
                                anchorXUnits: 'fraction',
                                anchorYUnits: 'pixels',
                                src: './images/icon_custom_selected-mini.png'
                            }))
                    });

                    iconFeatureinitCustomAddPoi.setStyle(iconStyleinitCustomAddPoi);

                    vectorSourceCustomAddPoi = new ol.source.Vector({
                        features: [iconFeatureinitCustomAddPoi]
                    });

                    vectorLayerinitCustomAddPoi = new ol.layer.Vector({
                        source: vectorSourceCustomAddPoi
                    });

                    map.addLayer(vectorLayerinitCustomAddPoi);

                    contPois+=1;
                    location.reload();
                },
                error: function(jqXHR, exception) {
                    console.log("nao funciona - closedPoints(addpoi)");
                    let msg = '';
                    if (jqXHR.status === 0) {
                        msg = 'Not connect.\n Verify Network.';
                    } else if (jqXHR.status == 404) {
                        msg = 'Requested page not found. [404]';
                    } else if (jqXHR.status == 500) {
                        msg = 'Internal Server Error [500].';
                    } else if (exception === 'parsererror') {
                        msg = 'Requested JSON parse failed.';
                    } else if (exception === 'timeout') {
                        msg = 'Time out error.';
                    } else if (exception === 'abort') {
                        msg = 'Ajax request aborted.';
                    } else {
                        msg = 'Uncaught Error.\n' + jqXHR.responseText;
                    }
                    console.log("Erro: " + msg);
                }
            });
        },
        error: function(jqXHR, exception){
            console.log("nao funciona - addpoi");
            let msg = '';
            if (jqXHR.status === 0) {
                msg = 'Not connect.\n Verify Network.';
            } else if (jqXHR.status == 404) {
                msg = 'Requested page not found. [404]';
            } else if (jqXHR.status == 500) {
                msg = 'Internal Server Error [500].';
            } else if (exception === 'parsererror') {
                msg = 'Requested JSON parse failed.';
            } else if (exception === 'timeout') {
                msg = 'Time out error.';
            } else if (exception === 'abort') {
                msg = 'Ajax request aborted.';
            } else {
                msg = 'Uncaught Error.\n' + jqXHR.responseText;
            }
            console.log("Erro: " + msg);
        }
    });
}