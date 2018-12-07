document.getElementById('fileinput').addEventListener('change', readSingleFile, false);

var fileContents = [];

function readSingleFile(evt) {
    //Retrieve the first (and only!) File from the FileList object
    var f = evt.target.files[0];
    var jsondata;
    if (f) {
        var r = new FileReader();
        r.onload = function(e) {
            jsondata = parseCSV(e.target.result,'\n',',') //OU \r
            $.ajax({
                type: "POST",
                headers: {'X-Requested-With': 'XMLHttpRequest'},
                url: "http://aal.ieeta.pt/hlt/api/v1/addPois/",
                contentType: "application/json",
                dataType: "text",
                data: jsondata/*,
                success: function(result){
                    alert(result)
                },
                error: function(result){
                    console.log("nao funcionou");
                }*/
            });
        }
        r.readAsText(f);
    } else {
        alert("Failed to load file");
    }
}

function parseCSV(texto,splitLinha,separadorLinha){
    var info = texto.split(splitLinha);
    for(var i=1;i<info.length;i++){
        var conteudos = info[i].split(separadorLinha);
        var filtrarUltCoordenada = conteudos[3].replace('\r',''); //Para tirar o \r pq o csv que criei vinha com \r e \n no fim
        fileContents.push({
            nome: conteudos[0],
            tipo: conteudos[1],
            latitude: conteudos[2],
            longitude: filtrarUltCoordenada
        });
    }
    return JSON.stringify(fileContents);
}

function chooseOrder(evt){
    alert(evt)
}