import os
import logging
import requests
import numpy as np
import pandas as pd
import tensorflow as tf
import gdown
from PIL import Image
from flask import Flask, request, jsonify, render_template, send_from_directory
from werkzeug.utils import secure_filename

# -------------------------------------------------
# Paths & Constants
# -------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
MODEL_PATH = os.path.join(BASE_DIR, "art_style_classifier_with_inceptionv3.h5")
CSV_PATH = os.path.join(BASE_DIR, "updated_classes_with_genres.csv")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}

# 🔥 Your Google Drive direct download URL
GOOGLE_DRIVE_MODEL_URL = (
    "https://drive.google.com/uc?export=download&id=10qkDnVU8f6d4xQRmPzqliMx6nsjHhqTS"
)

# -------------------------------------------------
# Flask App Setup
# -------------------------------------------------
app = Flask(
    __name__,
    static_folder=os.path.join(BASE_DIR, "static"),
    template_folder=os.path.join(BASE_DIR, "templates"),
)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret")

# -------------------------------------------------
# Logging Setup
# -------------------------------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# -------------------------------------------------
# Utility Functions
# -------------------------------------------------
def allowed_file(filename):
    """Check allowed file extension."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def process_image(image_path):
    """Resize and normalize image for model."""
    img = Image.open(image_path).convert("RGB")
    img = img.resize((224, 224))
    arr = np.array(img) / 255.0
    return np.expand_dims(arr, axis=0)


MODEL_PATH = os.path.join(BASE_DIR, "art_style_classifier_with_inceptionv3.h5")
GOOGLE_DRIVE_MODEL_URL = "https://drive.google.com/uc?id=10qkDnVU8f6d4xQRmPzqliMx6nsjHhqTS"
logger = logging.getLogger(__name__)

def download_model_if_needed():
    """Download model from Google Drive if not found."""
    if os.path.exists(MODEL_PATH):
        logger.info("Model already exists — skipping download.")
        return

    try:
        logger.info("Downloading model from Google Drive...")
        gdown.download(GOOGLE_DRIVE_MODEL_URL, MODEL_PATH, quiet=False)
        logger.info("Model downloaded successfully.")
    except Exception as e:
        logger.exception(f"Failed to download model: {e}")
        raise RuntimeError("Model download failed.") from e



# -------------------------------------------------
# Load Metadata CSV
# -------------------------------------------------
try:
    df = pd.read_csv(CSV_PATH)
    if "image_path" in df.columns:
        df["image_path"] = df["image_path"].apply(lambda x: os.path.basename(str(x)))
    logger.info("CSV loaded successfully.")
except Exception as e:
    logger.exception(f"Failed to load CSV: {e}")
    df = pd.DataFrame()

# -------------------------------------------------
# Load Model
# -------------------------------------------------
try:
    download_model_if_needed()
    model = tf.keras.models.load_model(MODEL_PATH)
    logger.info("Model loaded successfully.")
except Exception as e:
    logger.exception(f"Model load failed: {e}")
    model = None

# -------------------------------------------------
# Class Labels (make sure matches model outputs)
# -------------------------------------------------
class_labels = [
    "Abstract Expressionism", "Baroque", "Cubism", "Expressionism",
    "High Renaissance", "Impressionism", "Minimalism", "Realism",
    "Rococo", "Ukiyo_e"
]

# -------------------------------------------------
# Routes
# -------------------------------------------------
@app.route("/")
def home():
    return render_template("index.html")


@app.route("/result")
def result():
    return render_template("result.html")


@app.route("/predict", methods=["POST"])
def predict():
    if model is None:
        return jsonify({"error": "Model not loaded"}), 500

    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "Invalid file type"}), 400

    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)

    try:
        # Save file
        file.save(file_path)

        # Run prediction
        processed = process_image(file_path)
        preds = model.predict(processed)[0]
        logger.info(f"Predictions: {preds}")

        # Metadata lookup
        painting_title = "Unknown Title"
        artist_name = "Unknown Artist"

        if not df.empty and "image_path" in df.columns:
            row = df[df["image_path"] == filename]
            if not row.empty:
                painting_title = row["description"].values[0] if "description" in row.columns else "Unknown Title"
                artist_name = row["artist"].values[0] if "artist" in row.columns else "Unknown Artist"

        # Top 2 predictions
        sorted_idx = np.argsort(preds)[::-1]
        top1, top2 = sorted_idx[:2]

        total = preds[top1] + preds[top2] if preds[top1] + preds[top2] > 0 else 1
        pct1 = (preds[top1] / total) * 100
        pct2 = (preds[top2] / total) * 100

        result = {
            "image_url": f"/uploads/{filename}",
            "prediction": {
                "style1_percentage": round(float(pct1), 2),
                "style2_percentage": round(float(pct2), 2),
                "style1_name": class_labels[top1],
                "style2_name": class_labels[top2],
                "painting_title": painting_title,
                "artist_name": artist_name,
            },
        }

        return jsonify(result)

    except Exception as e:
        logger.exception(f"Prediction failed: {e}")
        return jsonify({"error": "Prediction error — check logs"}), 500


@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


# -------------------------------------------------
# Local Dev Run
# -------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5001)
