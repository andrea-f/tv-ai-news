var current_video = 0;
var server_url = "http://127.0.0.1:5000"
var maxTestLength = 80;
var timeoutId=null;

function playNext() {
  try {
    clearTimeout(timeoutId);
  } catch (err) {
  }
  var video = document.getElementById("video");
  if (current_video < videos.length) {
    current_video = current_video + 1;
  }
  updateInfo();
}
function playPrev() {
 if (current_video>0) {
    current_video = current_video - 1;
 }
  updateInfo();
}
function updateInfo() {
  let video = videos[current_video];
  setMediaElement(video);
  document.getElementById("group_name").innerHTML = video.group_name;
  document.getElementById("group_participants").innerHTML = video.group_participants;
  document.getElementById("category").innerHTML = video.category;
  document.getElementById("reactions").innerHTML = video.reactions;
  document.getElementById("source_link").innerHTML = video.source_link;
  //document.getElementById("text").innerHTML = video.text;
  document.getElementById("translated_text").innerHTML = video.translated_text.substring(0,maxTestLength*5);
  document.getElementById("message_date").innerHTML = video.message_date;
  document.getElementById("keywords").innerHTML = video.keywords.substring(0,maxTestLength);
  document.getElementById("views").innerHTML = video.views;
  document.getElementById("forwards").innerHTML = video.forwards;
  document.getElementById("duration").innerHTML = video.duration;
  document.getElementById("media_url").innerHTML = "<a href='"+server_url+video.media_url+"' target=_blank>"+server_url+video.media_url+"</a>";
}

function setMediaElement(item) {
      var videoElement = document.getElementById("video");
      if (item.media_url.indexOf(".jpg") !== -1) {
        document.getElementById("media_element_img").style.display="block";
        document.getElementById("media_element_img").src = server_url+item.media_url;
        videoElement.style.display = "none";
        timeoutId = setTimeout(function() { playNext(); }, 5000);
      } else {
        videoElement.style.display="block";
        document.getElementById("media_element").src = server_url+item.media_url;
        document.getElementById("media_element_img").style.display="none";
        videoElement.load();
        videoElement.play();
      }

}