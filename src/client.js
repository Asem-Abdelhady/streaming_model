// // data channel
// var dataChannelLog = document.getElementById("objects-log");

// function createPeerConnection() {
//   var config = {
//     sdpSemantics: "unified-plan",
//   };

//   pc = new RTCPeerConnection(config);

//   // connect audio / video
//   pc.addEventListener("track", function (evt) {
//     if (evt.track.kind == "video")
//       document.getElementById("video").srcObject = evt.streams[0];
//   });

//   return pc;
// }

// function negotiate(pc) {
//   return pc
//     .createOffer()
//     .then(function (offer) {
//       return pc.setLocalDescription(offer);
//     })
//     .then(function () {
//       // wait for ICE gathering to complete
//       return new Promise(function (resolve) {
//         if (pc.iceGatheringState === "complete") {
//           resolve();
//         } else {
//           function checkState() {
//             if (pc.iceGatheringState === "complete") {
//               pc.removeEventListener("icegatheringstatechange", checkState);
//               resolve();
//             }
//           }
//           pc.addEventListener("icegatheringstatechange", checkState);
//         }
//       });
//     })
//     .then(function () {
//       var offer = pc.localDescription;

//       return fetch("/offer", {
//         body: JSON.stringify({
//           sdp: offer.sdp,
//           type: offer.type,
//         }),
//         headers: {
//           "Content-Type": "application/json",
//         },
//         method: "POST",
//       });
//     })
//     .then(function (response) {
//       console.log("First response: ", response);
//       return response.json();
//     })
//     .then(function (answer) {
//       console.log("First answer edited2: ", answer);
//       return pc.setRemoteDescription(answer);
//     })
//     .catch(function (e) {
//       console.log("Error");
//       alert(e);
//     });
// }

// function start() {
//   pc = createPeerConnection();
//   var dcInterval = null;

//   dc = pc.createDataChannel("chat", { ordered: false, maxRetransmits: 0 });
//   dc.onclose = function () {
//     clearInterval(dcInterval);
//     dataChannelLog.textContent += "- close\n";
//   };
//   dc.onopen = function () {
//     dataChannelLog.textContent += "- open\n";
//     dcInterval = setInterval(function () {
//       var message = "bed|cell phone|person";
//       dc.send(message);
//     }, 1000);
//   };
//   dc.onmessage = function (evt) {
//     console.log("Received message", evt.data);
//     dataChannelLog.textContent += "< " + evt.data + "\n";
//   };

//   var constraints = {
//     video: true,
//   };

//   if (constraints.video) {
//     navigator.mediaDevices
//       .getUserMedia(constraints)iceGatheringState
//       .then((stream) => {
//         pc.addStream(stream);
//         negotiate(pc).then((res) => console.log("res: ", res));
//       })
//       .catch((e) => console.log("Error: ", e));
//   } else {
//     negotiate(pc).then((res) => console.log("Res in else: ", res));
//   }
// }

// start();

function createPeerConnection() {
  var config = {
    sdpSemantics: "unified-plan",
  };

  pc = new RTCPeerConnection(config);
  return pc;
}

async function fetch_stream(offer) {
  const res = await fetch("/offer", {
    body: JSON.stringify({
      sdp: offer.sdp,
      type: offer.type,
    }),
    headers: {
      "Content-Type": "application/json",
    },
    method: "POST",
  });
  const data = await res.json();
  return data;
}

async function settleIce(pc) {
  if (pc.iceGatheringState !== "complete") {
    let checkState = () => {
      if (pc.iceGatheringState === "complete") {
        pc.removeEventListener("icegatheringstatechange", checkState);
        resolve();
      }
    };
    pc.addEventListener("icegatheringstatechange", checkState);
  }
}

async function addStream(stream) {
  document.getElementById("video").srcObject = stream;
  return pc.addStream(stream);
}

async function handleOffer(msg) {
  let pc = createPeerConnection();
  let constraints = {
    video: true,
  };

  let offer = await pc.createOffer();
  await pc.setLocalDescription(offer);
  await settleIce(pc);

  let answer = await fetch_stream(offer);
  console.log("Answer: ", answer);

  // let remoteDescriptor = await pc.setRemoteDescription(answer);

  let stream = await navigator.mediaDevices.getUserMedia(constraints);
  await addStream(stream);
}

handleOffer();
