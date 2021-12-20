
function resizeToMatch(id1, id2) {
    const resize_ob = new ResizeObserver(function(entries) {
        // REFERENCE: https://usefulangle.com/post/319/javascript-detect-element-resize
        let rect = entries[0].contentRect;
        let width = rect.width;
        document.getElementById(id2).setAttribute('style', 'width:' + width + 'px;');
    });
    resize_ob.observe(document.querySelector("#" + id1));
};
// const resize_ob = new ResizeObserver(function(entries) {
//     // REFERENCE: https://usefulangle.com/post/319/javascript-detect-element-resize
// 	let rect = entries[0].contentRect;
// 	let width = rect.width;
//     document.getElementById('topcontrols').setAttribute('style', 'width:' + width + 'px;');
// });
// const reseze_ob = new ResizeObserver(function(entries) {
//     let rect = entries[0].contentRect;
//     let width = rect.width;
//     document.getElementById('bottomcontrols').setAttribute('style', 'width' + width + 'px');
// });

resizeToMatch('camera_feed', 'topcontrols')
resizeToMatch('camera_feed', 'bottomcontrols')


function highlightButton(id) {
    console.log("Highlighting button:", id)
    document.getElementById(id).classList.add('activatedThroughJS')
    function sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
    async function removeTheClass(id) {
        await sleep(150); // sleeps for 150ms, allowing animation to finish, before removing class
        document.getElementById(id).classList.remove('activatedThroughJS')
    }
    removeTheClass(id)
}

function submitfun(e, val, refresh=false) {
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
    if (document.getElementById("powerbutton").classList.contains("poweredon")) {
        $("#powerbutton").addClass('poweredoff');
        $("#powerbutton").removeClass('poweredon');
        console.log("powering off")
        return "poweroff"
    }
    else if (document.getElementById("powerbutton").classList.contains("poweredoff")) {
        $("#powerbutton").addClass('poweredon');
        $("#powerbutton").removeClass('poweredoff')
        console.log("powering on")
        return "poweron"
    }
    else {
        console.log("powerbutton had no poweredon or powerdoff class?!")
    }
}

function powerRestart(){
    if (document.getElementById("powerbutton").classList.contains("poweredon")) {
        console.log('reinitializing')
    }
    else if (document.getElementById("powerbutton").classList.contains("poweredoff")) {
        $("#powerbutton").addClass('poweredon');
        $("#powerbutton").removeClass('poweredoff')
        console.log("powering on")
    }
    else {
        console.log("powerbutton did not have poweredon or powerdoff class?!")
    }
}

$(document).on('submit','#formPower',function(e){
    submitfun(e, powerToggle(), true)
});
$(document).on('submit','#formCalibrate',function(e){
    powerRestart()
    submitfun(e, 'calibrate', true)
});
$(document).on('submit','#form180',function(e){
    powerRestart()
    submitfun(e, 'setto180', true)
});
$(document).on('submit','#form270',function(e){
    powerRestart()
    submitfun(e, 'setto270', true)
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
