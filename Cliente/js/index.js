$( document ).ready(function() {
    // Get the modal
    var modal = document.getElementById('id01');
    var register = document.getElementById('register');

    // When the user clicks anywhere outside of the modal, close it
    window.onclick = function(event) {
        if(event.target === register){
            modal.style.display = "block";
        }
        else if (event.target === modal) {
            modal.style.display = "none";
        }

    }
});

function logata(){
    let username =  $("#log_username").val();
    let password =  $("#log_password").val();

    var fd = new FormData();
    fd.append("username", username);
    fd.append("password", password);


    $.ajax
    ({
        type: "GET",
        url: "http://aal.ieeta.pt/hlt/api/v1/token",
        async: false,
        headers: {
            "Authorization": "Basic " + btoa(username + ":" + password)
        },
        success: function (response){
            console.log(response["token"]);
            setCookie("cook",response["token"],1);
            self.location = "http://aal.ieeta.pt/hlt/apiteste/apiClient.html";
        }
    });
}

function setCookie(name,value,days) {
    var expires = "";
    if (days) {
        var date = new Date();
        date.setTime(date.getTime() + (days*24*60*60*1000));
        expires = "; expires=" + date.toUTCString();
    }
    document.cookie = name + "=" + (value || "")  + expires + "; path=/";
}

function registerData(){
    let username =  $("#reg_username").val();
    let password =  $("#reg_password").val();

    $.ajax({
        type: "POST",
        headers: {'X-Requested-With': 'XMLHttpRequest'},
        url: "http://aal.ieeta.pt/hlt/api/v1/users",
        contentType: 'application/json;charset=UTF-8',
        data: JSON.stringify({
            username: username,
            password: password
        }),
        success: function (result) {
            document.getElementById('id01').style.display = "none";
            $("#log_username").val(username);
            $("#log_password").val(password);
        },
        error: function (result) {
            console.log("nao funcionou - initUser");
        }
    });
}