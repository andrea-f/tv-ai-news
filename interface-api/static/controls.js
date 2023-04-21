var currentVideo = 0;
var maxTestLength = 80;
var maxMessageLength = 420; // characters
var timeoutId=null;
var IMAGE_SLIDESHOW_DURATION = 7000; // in millis

function cancelTimeout() {
    try {
        clearTimeout(timeoutId);
        //console.log("cancel timeout")
      } catch (err) {}
}

function playNext() {
  cancelTimeout();
  var video = document.getElementById("video");
  if (currentVideo < videos.length-1) {
    currentVideo += 1;
    currentTotalVideoIndex += 1;
    updateInfo();
  } else {
    // fetch new videos
    window.location.href = nextVideosUrl + refb +"-"+ currentVideo;
  }

}

function fetchNewVideos(url, callback) {
    var xmlHttp = new XMLHttpRequest();
    xmlHttp.onreadystatechange = function() {
        if (xmlHttp.readyState == 4 && xmlHttp.status == 200)
            callback(xmlHttp.responseText);
    }
    xmlHttp.open("GET", url, true); // true for asynchronous
    xmlHttp.send(null);
}

function playPrev() {
 cancelTimeout();
 if (currentVideo>0) {
    currentVideo -= 1;
    currentTotalVideoIndex -= 1;
 }
  updateInfo();
}

var isChannelPaused = false;
function pause() {
    var videoElement = document.getElementById("video");
    if (isChannelPaused==false) {
        cancelTimeout();
        videoElement.pause();
        isChannelPaused=true;
        document.getElementById("pause_button").innerHTML = "Play";
    } else {
        if (videos[currentVideo].media_url.indexOf(".jpg")==-1) {
            videoElement.play();
        } else {
            timeoutId = setTimeout(function() { playNext(); }, IMAGE_SLIDESHOW_DURATION);
        }

        isChannelPaused = false;

        document.getElementById("pause_button").innerHTML = "Pause";
    }


}

function updateInfo() {
  let video = videos[currentVideo];
  setMediaElement(video);
  var formattedText = video.text;

  if (video.text.length > maxMessageLength) {
    formattedText = video.text.substring(0,maxMessageLength)+"...";
  }

  var entities = video.entities;
  if (video.entities.length > maxMessageLength) {
    entities = video.entities.substring(0,maxMessageLength)+"...";
  } else if (video.entities.length==0) {
    entities = "None detected";
  }

  var keywords = video.keywords;
  if (video.keywords.length >maxMessageLength) {
    keywords = video.keywords.substring(0,maxMessageLength)+"...";
  } else if (video.keywords.length==0) {
    keywords = "None detected";
  }

  document.getElementById("group_name").innerHTML = video.group_name;
  document.getElementById("group_participants").innerHTML = video.group_participants;
  //document.getElementById("category").innerHTML = video.category;
  document.getElementById("reactions").innerHTML = video.reactions;
  document.getElementById("source_link").innerHTML = video.source_link;
  document.getElementById("text").innerHTML = formattedText;
  //document.getElementById("translated_text").innerHTML = video.translated_text.substring(0,maxTestLength*5);
  document.getElementById("message_date").innerHTML = video.message_date;
  document.getElementById("keywords").innerHTML = keywords;
  document.getElementById("views").innerHTML = video.views;
  document.getElementById("forwards").innerHTML = video.forwards;
  //document.getElementById("duration").innerHTML = video.duration;
  document.getElementById("entities").innerHTML = video.entities;
  document.getElementById("sentiment").innerHTML = video.sentiment;
  //console.log("sent "+video.sentiment)
  document.getElementById("item_number").innerHTML = currentTotalVideoIndex+"/"+totalItems;
  //document.getElementById("media_url").innerHTML = "<a href='"+video.media_url+"' target=_blank>"+video.media_url+"</a>";
}

function setMediaElement(item) {
      var videoElement = document.getElementById("video");
      if (item.media_url.indexOf(".jpg") !== -1) {
        document.getElementById("media_element_img").style.display="block";
        document.getElementById("media_element_img").src = item.media_url;
        videoElement.style.display = "none";
        if (!isChannelPaused) {
            //console.log("setting timer")
            timeoutId = setTimeout(function() { playNext(); }, IMAGE_SLIDESHOW_DURATION);
        }
      } else if (item.media_url.indexOf(".pdf")==-1) {

        videoElement.style.display="block";
        document.getElementById("media_element").src = item.media_url;
        document.getElementById("media_element_img").style.display="none";
        var isPlaying = videoElement.currentTime > 0 && !videoElement.paused && !videoElement.ended
                        && videoElement.readyState > videoElement.HAVE_CURRENT_DATA;
        try {
            videoElement.load();
        } catch (err) {
            videoElement.play();
        }
        if (!isChannelPaused && !isPlaying) {
            videoElement.play();
        } else {
            videoElement.pause();
        }

      }
}


function sortBy(filter) {
    cancelTimeout();
    videos.sort(function(a, b) {
        if (filter == "timestamp") {
            return new Date(b[filter]) - new Date(a[filter]);
        } else {
            if (a[filter] < b[filter]) {
                return 1;
            }
            if (a[filter] > b[filter]) {
                return -1;
            }
            return 0;
        }
    });
    currentVideo=0;
    currentTotalVideoIndex=0;
    updateInfo();
}

