function sendData(){
    let username =  $("#username").val();
    let password =  $("#password").val();
    let jsondata = [];
    let data = {};
    data.username = username
    data.password = password
    jsondata.push(data);
    let sendjson = JSON.stringify(jsondata);

    console.log(sendjson)

    $.ajax({
        type: "POST",
        headers: {'X-Requested-With': 'XMLHttpRequest'},
        url: "http://127.0.0.1:5000/api/users",
        contentType: "application/json",
        dataType: "text",
        data: sendjson,
        success: function (result) {
            console.log(result);
        },
        error: function (result) {
            console.log("nao funcionou - initUser");
        }
    });
}