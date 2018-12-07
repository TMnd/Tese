$( document ).ready(function() {
    let x = getCookie("cook");

    if(x){
        console.log("Token: " + x);
        let username = x;
        let password = 'unused';
        $.ajax
        ({
            type: "GET",
            url: "http://aal.ieeta.pt/hlt/api/v1/resource",
            async: false,
            headers: {
                "Authorization": "Basic " + btoa(username + ":" + password)
            },
            success: function (response){
                console.log("User_id: " + response["id"]);
            }
        });

    }else{
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
});

function eraseCookie(name) {
    document.cookie = name + '=; expires=Thu, 01 Jan 1970 00:00:01 GMT;';
}

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