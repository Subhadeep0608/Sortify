// Handle camera
const video = document.getElementById('camera');
navigator.mediaDevices.getUserMedia({ video: true })
  .then(stream => { video.srcObject = stream; })
  .catch(err => console.error("Camera Error: ", err));

function captureImage() {
  const canvas = document.getElementById('canvas');
  const ctx = canvas.getContext('2d');
  canvas.width = video.videoWidth;
  canvas.height = video.videoHeight;
  ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

  const dataUrl = canvas.toDataURL('image/png');
  document.getElementById('preview').src = dataUrl;

  fetch('/predict', {
    method: 'POST',
    body: dataURItoFormData(dataUrl)
  })
  .then(res => res.json())
  .then(data => {
    document.getElementById('result').innerText = "Result: " + data.prediction;
  });
}

function uploadImage() {
  const fileInput = document.getElementById('fileInput');
  if (fileInput.files.length === 0) {
    alert("Please select an image");
    return;
  }

  const formData = new FormData();
  formData.append("file", fileInput.files[0]);

  fetch('/predict', {
    method: 'POST',
    body: formData
  })
  .then(res => res.json())
  .then(data => {
    document.getElementById('preview').src = data.file_path;
    document.getElementById('result').innerText = "Result: " + data.prediction;
  });
}

// Convert base64 image to FormData
function dataURItoFormData(dataURI) {
  const byteString = atob(dataURI.split(',')[1]);
  const ab = new ArrayBuffer(byteString.length);
  const ia = new Uint8Array(ab);
  for (let i = 0; i < byteString.length; i++) {
    ia[i] = byteString.charCodeAt(i);
  }
  const file = new Blob([ab], { type: 'image/png' });
  const formData = new FormData();
  formData.append("file", file, "capture.png");
  return formData;
}
