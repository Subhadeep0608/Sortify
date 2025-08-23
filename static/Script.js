// Camera setup
const video = document.getElementById('camera');
const preview = document.getElementById('preview');
const resultBox = document.getElementById('result');

function enableCamera() {
  video.classList.remove('hidden');
  navigator.mediaDevices.getUserMedia({ video: true })
    .then(stream => { video.srcObject = stream; })
    .catch(err => alert("Camera access denied: " + err));
}

function captureImage() {
  const canvas = document.getElementById('canvas');
  const ctx = canvas.getContext('2d');
  canvas.width = video.videoWidth;
  canvas.height = video.videoHeight;
  ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

  // Preview captured frame
  const dataUrl = canvas.toDataURL('image/png');
  preview.src = dataUrl;
  preview.classList.remove('hidden');

  // Send to backend
  fetch('/predict', {
    method: 'POST',
    body: dataURItoFormData(dataUrl)
  })
  .then(res => res.json())
  .then(data => {
    if (data.error) {
      showResult("❌ Error: " + data.error, "bg-red-500/40");
      return;
    }
    showResult(`${data.prediction} <br>(confidence: ${(data.confidence * 100).toFixed(1)}%)`, 
               data.prediction.includes("Recyclable") ? "bg-green-500/40" : "bg-red-500/40");
  })
  .catch(err => showResult("⚠️ Upload failed: " + err, "bg-red-500/40"));
}

function uploadImage() {
  const fileInput = document.getElementById('fileInput');
  if (fileInput.files.length === 0) {
    alert("Please select an image");
    return;
  }

  const file = fileInput.files[0];
  const formData = new FormData();
  formData.append("file", file);

  // Show preview immediately
  preview.src = URL.createObjectURL(file);
  preview.classList.remove('hidden');

  fetch('/predict', {
    method: 'POST',
    body: formData
  })
  .then(res => res.json())
  .then(data => {
    if (data.error) {
      showResult("❌ Error: " + data.error, "bg-red-500/40");
      return;
    }
    showResult(`${data.prediction} <br>(confidence: ${(data.confidence * 100).toFixed(1)}%)`, 
               data.prediction.includes("Recyclable") ? "bg-green-500/40" : "bg-red-500/40");
  })
  .catch(err => showResult("⚠️ Upload failed: " + err, "bg-red-500/40"));
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

// Show result with animation + color
function showResult(message, bgClass) {
  resultBox.innerHTML = message;
  resultBox.className = `text-2xl font-bold mt-6 p-4 rounded-xl border border-white/20 ${bgClass}`;
  resultBox.classList.remove("hidden");
  resultBox.style.animation = "fadeIn 1s ease forwards";
}
