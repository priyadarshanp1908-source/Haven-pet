"""
Pet Breed Classifier Model Training Pipeline
Trains an ensemble Random Forest ML model on pet visual feature representations
and saves the trained artifact to pet_breed_model.joblib.
"""

import io
import os
import sys
import logging
from typing import Tuple, List, Dict
from PIL import Image

import numpy as np
from sklearn.ensemble import RandomForestClassifier, ExtraTreesClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
import joblib

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("train_breed_model")

# Supported Pet Species & Breed Dataset Schema
PET_CLASSES = [
    # Dogs
    ("dog", "Golden Retriever", {"color": (218, 165, 32), "ratio": 1.25, "brightness": 0.65, "texture": 0.35}),
    ("dog", "German Shepherd", {"color": (139, 69, 19), "ratio": 1.30, "brightness": 0.45, "texture": 0.50}),
    ("dog", "French Bulldog", {"color": (160, 160, 160), "ratio": 0.95, "brightness": 0.55, "texture": 0.25}),
    ("dog", "Siberian Husky", {"color": (200, 200, 210), "ratio": 1.20, "brightness": 0.70, "texture": 0.40}),
    ("dog", "Poodle", {"color": (245, 245, 220), "ratio": 1.10, "brightness": 0.80, "texture": 0.60}),
    # Cats
    ("cat", "Persian Cat", {"color": (240, 240, 240), "ratio": 1.05, "brightness": 0.85, "texture": 0.55}),
    ("cat", "Siamese Cat", {"color": (220, 200, 180), "ratio": 1.15, "brightness": 0.75, "texture": 0.30}),
    ("cat", "Maine Coon", {"color": (120, 80, 50), "ratio": 1.35, "brightness": 0.40, "texture": 0.65}),
    ("cat", "Bengal Cat", {"color": (180, 120, 60), "ratio": 1.20, "brightness": 0.58, "texture": 0.70}),
    ("cat", "Domestic Shorthair", {"color": (150, 150, 150), "ratio": 1.10, "brightness": 0.50, "texture": 0.40}),
    # Birds
    ("bird", "Green Macaw", {"color": (34, 139, 34), "ratio": 0.90, "brightness": 0.55, "texture": 0.45}),
    ("bird", "Scarlet Macaw", {"color": (220, 20, 60), "ratio": 0.85, "brightness": 0.60, "texture": 0.50}),
    ("bird", "Cockatiel", {"color": (230, 230, 150), "ratio": 0.95, "brightness": 0.75, "texture": 0.35}),
    ("bird", "Budgerigar (Budgie)", {"color": (127, 255, 0), "ratio": 0.88, "brightness": 0.68, "texture": 0.40}),
    ("bird", "African Grey Parrot", {"color": (128, 128, 128), "ratio": 0.92, "brightness": 0.48, "texture": 0.38}),
    # Lizards & Reptiles
    ("lizard", "Bearded Dragon", {"color": (189, 154, 122), "ratio": 1.40, "brightness": 0.62, "texture": 0.60}),
    ("lizard", "Leopard Gecko", {"color": (240, 210, 110), "ratio": 1.30, "brightness": 0.72, "texture": 0.50}),
    ("lizard", "Green Iguana", {"color": (50, 180, 50), "ratio": 1.45, "brightness": 0.50, "texture": 0.55}),
    ("lizard", "Veiled Chameleon", {"color": (60, 175, 80), "ratio": 1.10, "brightness": 0.52, "texture": 0.65}),
    # Rabbits
    ("rabbit", "Holland Lop", {"color": (210, 180, 140), "ratio": 0.85, "brightness": 0.70, "texture": 0.45}),
    ("rabbit", "Netherland Dwarf", {"color": (160, 130, 100), "ratio": 0.80, "brightness": 0.60, "texture": 0.40}),
    ("rabbit", "Flemish Giant", {"color": (100, 100, 100), "ratio": 1.25, "brightness": 0.42, "texture": 0.50}),
    # Fish
    ("fish", "Betta Splendens", {"color": (0, 102, 204), "ratio": 1.15, "brightness": 0.45, "texture": 0.60}),
    ("fish", "Goldfish", {"color": (255, 140, 0), "ratio": 1.10, "brightness": 0.65, "texture": 0.35}),
    ("fish", "Neon Tetra", {"color": (0, 206, 209), "ratio": 1.20, "brightness": 0.70, "texture": 0.40}),
    # Insects & Arachnids
    ("insect", "Praying Mantis", {"color": (46, 139, 87), "ratio": 0.75, "brightness": 0.48, "texture": 0.50}),
    ("insect", "Rose Hair Tarantula", {"color": (40, 30, 30), "ratio": 1.05, "brightness": 0.20, "texture": 0.75}),
    ("insect", "Rhinoceros Beetle", {"color": (25, 25, 25), "ratio": 1.10, "brightness": 0.15, "texture": 0.60}),
    # Exotic Pets
    ("exotic", "African Pygmy Hedgehog", {"color": (180, 160, 140), "ratio": 0.90, "brightness": 0.58, "texture": 0.80}),
    ("exotic", "Sugar Glider", {"color": (170, 170, 175), "ratio": 0.85, "brightness": 0.62, "texture": 0.35}),
    ("exotic", "Chinchilla", {"color": (190, 190, 195), "ratio": 0.95, "brightness": 0.72, "texture": 0.70}),
]


def extract_features_from_pil_image(img: Image.Image) -> np.ndarray:
    """
    Extract a normalized 16-dimensional feature vector from an image:
    [0-2]: mean RGB
    [3-5]: std RGB
    [6-8]: min/max/median luminance
    [9]: aspect ratio (W/H)
    [10]: red dominance index
    [11]: green dominance index
    [12]: blue dominance index
    [13]: saturation estimate
    [14]: brightness mean
    [15]: texture variance estimate
    """
    img_rgb = img.convert("RGB")
    width, height = img_rgb.size
    aspect_ratio = width / max(height, 1)

    # Downsample for fast feature vector generation
    img_small = img_rgb.resize((32, 32))
    pixels = np.array(img_small.getdata(), dtype=np.float32)

    r_vals, g_vals, b_vals = pixels[:, 0], pixels[:, 1], pixels[:, 2]

    r_mean, r_std = float(np.mean(r_vals)), float(np.std(r_vals))
    g_mean, g_std = float(np.mean(g_vals)), float(np.std(g_vals))
    b_mean, b_std = float(np.mean(b_vals)), float(np.std(b_vals))

    lum = 0.299 * r_vals + 0.587 * g_vals + 0.114 * b_vals
    lum_min, lum_max, lum_med = float(np.min(lum)), float(np.max(lum)), float(np.median(lum))

    total_rgb = r_mean + g_mean + b_mean + 1e-5
    r_dom = r_mean / total_rgb
    g_dom = g_mean / total_rgb
    b_dom = b_mean / total_rgb

    max_c = np.maximum(r_vals, np.maximum(g_vals, b_vals))
    min_c = np.minimum(r_vals, np.minimum(g_vals, b_vals))
    sat = np.mean((max_c - min_c) / (max_c + 1e-5))

    brightness = float(np.mean(lum)) / 255.0
    texture_var = float(np.var(lum)) / 1000.0

    return np.array([
        r_mean, g_mean, b_mean,
        r_std, g_std, b_std,
        lum_min, lum_max, lum_med,
        aspect_ratio,
        r_dom, g_dom, b_dom,
        sat, brightness, texture_var,
    ], dtype=np.float32)


def generate_synthetic_training_dataset(samples_per_class: int = 150) -> Tuple[np.ndarray, np.ndarray, List[Dict]]:
    """Generate synthetic visual feature samples based on pet class profiles."""
    X_list = []
    y_list = []
    class_metadata = []

    np.random.seed(42)

    for idx, (species, breed, traits) in enumerate(PET_CLASSES):
        class_metadata.append({"id": idx, "species": species, "breed": breed})

        r_base, g_base, b_base = traits["color"]
        base_ratio = traits["ratio"]
        base_bright = traits["brightness"]
        base_texture = traits["texture"]

        for _ in range(samples_per_class):
            r = np.clip(r_base + np.random.normal(0, 18), 0, 255)
            g = np.clip(g_base + np.random.normal(0, 18), 0, 255)
            b = np.clip(b_base + np.random.normal(0, 18), 0, 255)

            r_s = np.random.uniform(15, 45)
            g_s = np.random.uniform(15, 45)
            b_s = np.random.uniform(15, 45)

            total_rgb = r + g + b + 1e-5
            r_dom = r / total_rgb
            g_dom = g / total_rgb
            b_dom = b / total_rgb

            ratio = np.clip(base_ratio + np.random.normal(0, 0.12), 0.6, 2.2)
            brightness = np.clip(base_bright + np.random.normal(0, 0.08), 0.05, 0.95)
            texture_var = np.clip(base_texture * 10 + np.random.normal(0, 1.2), 0.1, 15.0)

            sat = np.random.uniform(0.1, 0.8)
            lum_min = np.clip((r + g + b) / 3 - 35 + np.random.normal(0, 10), 0, 255)
            lum_max = np.clip((r + g + b) / 3 + 35 + np.random.normal(0, 10), 0, 255)
            lum_med = (lum_min + lum_max) / 2.0

            vec = np.array([
                r, g, b,
                r_s, g_s, b_s,
                lum_min, lum_max, lum_med,
                ratio,
                r_dom, g_dom, b_dom,
                sat, brightness, texture_var,
            ], dtype=np.float32)

            X_list.append(vec)
            y_list.append(idx)

    return np.array(X_list), np.array(y_list), class_metadata


def train_and_save_model(output_path: str):
    """Train Random Forest Pet Classifier and export compressed joblib file."""
    logger.info("Generating dataset for Pet Breed ML model...")
    X, y, class_metadata = generate_synthetic_training_dataset(samples_per_class=120)

    logger.info(f"Training ensemble model on {len(X)} samples across {len(class_metadata)} pet classes...")
    pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("classifier", ExtraTreesClassifier(n_estimators=50, max_depth=10, random_state=42)),
    ])

    pipeline.fit(X, y)
    score = pipeline.score(X, y)
    logger.info(f"Model training complete. Training accuracy: {score * 100:.2f}%")

    model_data = {
        "pipeline": pipeline,
        "class_metadata": class_metadata,
        "feature_names": [
            "r_mean", "g_mean", "b_mean",
            "r_std", "g_std", "b_std",
            "lum_min", "lum_max", "lum_med",
            "aspect_ratio",
            "r_dom", "g_dom", "b_dom",
            "sat", "brightness", "texture_var",
        ],
    }

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    # Compress joblib artifact (level 3 compression) for lightweight footprint
    joblib.dump(model_data, output_path, compress=3)
    logger.info(f"Successfully saved compressed ML model artifact to: {output_path}")


if __name__ == "__main__":
    out_dir = os.path.dirname(os.path.abspath(__file__))
    model_file = os.path.join(out_dir, "pet_breed_model.joblib")
    train_and_save_model(model_file)
