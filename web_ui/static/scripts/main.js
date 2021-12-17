function highlightButton(id) {
    console.log("Highlighting button:", id)
    document.getElementById(id).childNodes[0].classList.add('activatedThroughJS')
    function sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
    async function removeTheClass(id) {
        await sleep(150); // sleeps for 150ms, allowing animation to finish, before removing class
        document.getElementById(id).childNodes[0].classList.remove('activatedThroughJS')
    }
    removeTheClass(id)
}



function submitfun(e, val) {
    // REFERENCE: form submission without page reload: https://www.geeksforgeeks.org/flask-form-submission-without-page-reload/
    console.log("Submitting: ", val)
    e.preventDefault();
    $.ajax({
        type:'POST',
        url:'/',
        data:{button:val},
        // success:function()
        // {
        // 	//alert('saved');
        // }
    })
}

document.getElementById("camera_feed").addEventListener('wheel', (e) => {
    if (e.deltaY > 0) {
        highlightButton("formZoomOut")
        submitfun(e, "zoomout")
    }
    else if (e.deltaY < 0) {
        highlightButton("formZoomIn")
        submitfun(e, "zoomin")
    }
})
document.onkeydown = checkKey;
function checkKey(e) {
    e = e || window.event;
    if (e.keyCode == '38') {
        console.log("UP")
        highlightButton("formPanUp")
        submitfun(e, "panup")
    }
    else if (e.keyCode == '40') {
        console.log("DOWN")
        highlightButton("formPanDown")
        submitfun(e, "pandown")
    }
    else if (e.keyCode == '37') {
        console.log("LEFT")
        highlightButton("formPanLeft")
        submitfun(e, "panleft")
    }
    else if (e.keyCode == '39') {
        console.log("RIGHT")
        highlightButton("formPanRight")
        submitfun(e, "panright")
    }
}
function powerToggle(buttonAction){
    // buttonaction = False if not powerbutton (=> other buttons can only turn on stream)
    if (buttonAction) {
        if (document.getElementById("powerbutton").classList.contains("poweredon")) {
            $("#powerbutton").addClass('poweredoff');
            $("#powerbutton").removeClass('poweredon');
            console.log("powering off")
            sendstr = "power_off"
        }
        else if (document.getElementById("powerbutton").classList.contains("poweredoff")) {
            $("#powerbutton").addClass('poweredon');
            $("#powerbutton").removeClass('poweredoff')
            console.log("powering on")
            sendstr = "power_on"
        }
        else {
            $("#powerbutton").addClass('poweredon');
            console.log("powering on")
            sendstr = "power_on"
        }
    }
    else {
        if (document.getElementById("powerbutton").classList.contains("poweredon")) {
            console.log('powering on again')
        }
        else if (document.getElementById("powerbutton").classList.contains("poweredoff")) {
            $("#powerbutton").addClass('poweredon');
            $("#powerbutton").removeClass('poweredoff')
            console.log("powering on")
        }
        else {
            $("#powerbutton").addClass('poweredon');
            console.log("powering on")
        }
    }
    return sendstr
}

$(document).on('submit','#formPower',function(e){
    sendstr = powerToggle(true)
    submitfun(e, sendstr)
});
$(document).on('submit','#formCalibrate',function(e){
    powerToggle(false)
    submitfun(e, 'calibrate')
});
$(document).on('submit','#form180',function(e){
    powerToggle(false)
    submitfun(e, 'setto180')
});
$(document).on('submit','#form270',function(e){
    powerToggle(false)
    submitfun(e, 'setto270')
});

$(document).on('submit','#formFullView',function(e){
    submitfun(e, "fullview")
});
$(document).on('submit','#fromCroppedView',function(e){
    submitfun(e, "fillview")
});
$(document).on('submit','#formZoomIn',function(e){
    submitfun(e, "zoomin")
});
$(document).on('submit','#formZoomOut',function(e){
    submitfun(e, "zoomout")
});
$(document).on('submit','#formPanUp',function(e){
    submitfun(e, "panup")
});
$(document).on('submit','#formPanLeft',function(e){
    submitfun(e, "panleft")
});
$(document).on('submit','#formPanDown',function(e){
    submitfun(e, "pandown")
});
$(document).on('submit','#formPanRight',function(e){
    submitfun(e, "panright")
});
