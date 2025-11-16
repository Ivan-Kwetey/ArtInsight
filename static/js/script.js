const fileInput = document.getElementById('file-upload');
const previewImage = document.getElementById('preview-image');

// Listen for file selection
fileInput.addEventListener('change', (event) => {
  const file = event.target.files[0];

  if (file) {
    // Display the image preview
    const reader = new FileReader();
    reader.onload = (e) => {
      previewImage.src = e.target.result;
      previewImage.style.display = 'block';
    };
    reader.readAsDataURL(file);

    // Send the file to the server for prediction
    sendFileToServer(file);
  }
});

// Function to send the file to the server
function sendFileToServer(file) {
  const formData = new FormData();
  formData.append('file', file);

  fetch('/predict', {  // Make sure this path matches Flask's route
    method: 'POST',
    body: formData,
  })
  .then(response => response.json())
  .then(data => {
    // Redirect to result page with image URL and prediction data
    if (data.image_url && data.prediction) {
      const params = new URLSearchParams();
      params.append('image_url', data.image_url);
      params.append('prediction', JSON.stringify(data.prediction));
      window.location.href = `/result?${params.toString()}`;
    } else {
      alert('Prediction failed. Please try again.');
    }
  })
  .catch((error) => {
    console.error('Error uploading file:', error);
    alert('Error uploading file. Please try again.');
  });

  function resetToHome() {
    window.location.href = '/';  // Redirects to the home route served by Flask
  }
  
}
/*real*/

