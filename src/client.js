// peer connection
var pc = null;

// data channel
var dataChannelLog = document.getElementById("objects-log");
var dc = null,
  dcInterval = null;

function createPeerConnection() {
  var config = {
    sdpSemantics: "unified-plan",
  };

  pc = new RTCPeerConnection(config);

  // connect audio / video
  pc.addEventListener("track", function (evt) {
    if (evt.track.kind == "video")
      document.getElementById("video").srcObject = evt.streams[0];
  });

  return pc;
}

function negotiate() {
  return pc
    .createOffer()
    .then(function (offer) {
      return pc.setLocalDescription(offer);
    })
    .then(function () {
      // wait for ICE gathering to complete
      return new Promise(function (resolve) {
        if (pc.iceGatheringState === "complete") {
          resolve();
        } else {
          function checkState() {
            if (pc.iceGatheringState === "complete") {
              pc.removeEventListener("icegatheringstatechange", checkState);
              resolve();
            }
          }
          pc.addEventListener("icegatheringstatechange", checkState);
        }
      });
    })
    .then(function () {
      var offer = pc.localDescription;

      return fetch("/offer", {
        body: JSON.stringify({
          sdp: offer.sdp,
          type: offer.type,
        }),
        headers: {
          "Content-Type": "application/json",
        },
        method: "POST",
      });
    })
    .then(function (response) {
      console.log("First response: ", response);
      return response.json();
    })
    .then(function (answer) {
      console.log("First answer: ", answer);
      return pc.setRemoteDescription(answer);
    })
    .catch(function (e) {
      console.log("Error");
      alert(e);
    });
}

function start() {
  pc = createPeerConnection();

  var time_start = null;

  function current_stamp() {
    if (time_start === null) {
      time_start = new Date().getTime();
      return 0;
    } else {
      return new Date().getTime() - time_start;
    }
  }

  dc = pc.createDataChannel("chat", { ordered: false, maxRetransmits: 0 });
  dc.onclose = function () {
    clearInterval(dcInterval);
    dataChannelLog.textContent += "- close\n";
  };
  dc.onopen = function () {
    dataChannelLog.textContent += "- open\n";
    dcInterval = setInterval(function () {
      var message = "bed|cell phone|person";
      dc.send(message);
    }, 1000);
  };
  dc.onmessage = function (evt) {
    console.log("Received message", evt.data);
    dataChannelLog.textContent += "< " + evt.data + "\n";
  };

  var constraints = {
    video: true,
  };

  if (constraints.video) {
    navigator.mediaDevices.getUserMedia(constraints).then(
      function (stream) {
        stream.getTracks().forEach(function (track) {
          pc.addTrack(track, stream);
        });
        return negotiate();
      },
      function (err) {
        alert("Could not acquire media: " + err);
      }
    );
  } else {
    negotiate();
  }
}

start();
