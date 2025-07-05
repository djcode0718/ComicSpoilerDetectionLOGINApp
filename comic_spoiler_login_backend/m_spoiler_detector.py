import cv2
import numpy as np
import pytesseract
from transformers import pipeline
from ultralytics import YOLO
import joblib
from deepface.DeepFace import represent
from sklearn.cluster import DBSCAN
from scipy.spatial.distance import cosine

# OCR setup
pytesseract.pytesseract.tesseract_cmd = r"/opt/homebrew/bin/tesseract"

# Load all models
caption_generator = pipeline("summarization", model="facebook/bart-large-cnn")
genre_classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")
character_detector = YOLO("models/yolov8_comic_characters_detect.pt")
xgboost_model = joblib.load("models/xgboost_spoiler_classifier.pkl")
tfidf_vectorizer = joblib.load("models/tfidf_vectorizer.pkl")
genre_encoder = joblib.load("models/genre_encoder.pkl")

# Genre labels used during training
genre_labels = ["Sports", "Crime", "Action", "Fantasy", "Sci-Fi", "Romance", "Horror", "Comedy", "Drama", "Mystery", "Superhero"]

def extract_text_from_image(image_path):
    image = cv2.imread(image_path)
    if image is None:
        return ""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return pytesseract.image_to_string(gray).strip()

def generate_caption(text):
    if not text.strip():
        return "No caption available"
    try:
        summary = caption_generator(text, max_length=50, min_length=10, do_sample=False)
        return summary[0]['summary_text']
    except Exception:
        return "Error generating caption"

def predict_genre(text):
    if not text.strip():
        return "Unknown"
    result = genre_classifier(text, genre_labels)
    predicted = result['labels'][0]
    return predicted if predicted in genre_labels else "Unknown"

def get_face_embedding(face):
    try:
        emb = represent(face, model_name="Facenet", enforce_detection=False)
        return emb[0]['embedding']
    except Exception:
        return None

def detect_unique_characters(image_path):
    image = cv2.imread(image_path)
    if image is None:
        return 0
    results = character_detector(image)
    face_embeddings = []

    for result in results:
        for box in result.boxes.xyxy:
            x1, y1, x2, y2 = map(int, box)
            face = image[y1:y2, x1:x2]
            if face.size == 0:
                continue
            embedding = get_face_embedding(face)
            if embedding is not None:
                face_embeddings.append(embedding)

    if not face_embeddings:
        return 0

    clustering = DBSCAN(metric=cosine, eps=0.5, min_samples=1)
    labels = clustering.fit_predict(face_embeddings)
    return len(set(labels))

def run_pipeline(image_path):
    # 1. Extract text
    extracted_text = extract_text_from_image(image_path)

    # 2. Generate caption
    caption = generate_caption(extracted_text)

    # 3. Predict genre
    genre = predict_genre(extracted_text)

    # 4. Count unique characters
    unique_character_count = detect_unique_characters(image_path)

    # 5. Encode genre
    if genre in genre_encoder.classes_:
        genre_encoded = genre_encoder.transform([genre])[0]
    else:
        genre_encoded = -1  # fallback for unknown genre

    # 6. TF-IDF on caption
    caption_features = tfidf_vectorizer.transform([caption]).toarray()

    # 7. Combine features
    numeric_features = np.array([[unique_character_count, genre_encoded]])
    X_input = np.hstack((numeric_features, caption_features)).reshape(1, -1)

    # 8. Predict
    prediction = xgboost_model.predict(X_input)[0]
    label_mapping = {0: "Unknown", 1: "Non-Spoiler", 2: "Spoiler"}
    prediction_label = label_mapping.get(prediction, "Unknown")

    return {
        "text": extracted_text,
        "caption": caption,
        "genre": genre,
        "character_count": unique_character_count,
        "result": prediction_label
    }
