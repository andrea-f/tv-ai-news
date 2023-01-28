var currentVideo = 0;
var maxTestLength = 80;
var maxMessageLength = 420; // characters
var timeoutId=null;

function cancelTimeout() {
    try {
        clearTimeout(timeoutId);
        console.log("cancel timeout")
      } catch (err) {}
}

function playNext() {
  cancelTimeout();
  var video = document.getElementById("video");
  if (currentVideo < videos.length) {
    currentVideo = currentVideo + 1;
  }
  updateInfo();
}

function playPrev() {
 cancelTimeout();
 if (currentVideo>0) {
    currentVideo = currentVideo - 1;
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
            timeoutId = setTimeout(function() { playNext(); }, 5000);
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
  document.getElementById("group_name").innerHTML = video.group_name;
  document.getElementById("group_participants").innerHTML = video.group_participants;
  document.getElementById("category").innerHTML = video.category;
  document.getElementById("reactions").innerHTML = video.reactions;
  document.getElementById("source_link").innerHTML = video.source_link;
  document.getElementById("text").innerHTML = formattedText;
  //document.getElementById("translated_text").innerHTML = video.translated_text.substring(0,maxTestLength*5);
  document.getElementById("message_date").innerHTML = video.message_date;
  document.getElementById("keywords").innerHTML = video.keywords.substring(0,maxTestLength);
  document.getElementById("views").innerHTML = video.views;
  document.getElementById("forwards").innerHTML = video.forwards;
  document.getElementById("duration").innerHTML = video.duration;
  document.getElementById("entities").innerHTML = video.entities;
  document.getElementById("sentiment").innerHTML = video.sentiment;
  console.log("sent "+video.sentiment)
  document.getElementById("item_number").innerHTML = currentVideo+"/"+videos.length;
  document.getElementById("media_url").innerHTML = "<a href='"+video.media_url+"' target=_blank>"+video.media_url+"</a>";
}

function setMediaElement(item) {
      var videoElement = document.getElementById("video");
      if (item.media_url.indexOf(".jpg") !== -1) {
        document.getElementById("media_element_img").style.display="block";
        document.getElementById("media_element_img").src = item.media_url;
        videoElement.style.display = "none";
        if (!isChannelPaused) {
            console.log("setting timer")
            timeoutId = setTimeout(function() { playNext(); }, 5000);
        }
      } else if (item.media_url.indexOf(".pdf")==-1) {

        videoElement.style.display="block";
        document.getElementById("media_element").src = item.media_url;
        document.getElementById("media_element_img").style.display="none";
        videoElement.load();
        if (!isChannelPaused) {
            console.log("playing video")
            videoElement.play();
        } else {
            videoElement.pause();
        }

      }
      //isChannelPaused = false;
}


function sortBy(filter) {
    videos.sort(function(a, b) {
        if (filter == "message_date") {
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
    updateInfo();
    console.log(videos[0]);
}

