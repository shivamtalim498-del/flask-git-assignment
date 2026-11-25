
from flask import Flask, render_template, request, redirect, url_for, jsonify
from pymongo import MongoClient
from dotenv import load_dotenv
from pathlib import Path
import os
import json
import logging

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Project directory
BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "data.json"

# Logging
logging.basicConfig(level=logging.INFO)

# MongoDB Atlas Connection
MONGO_URI = os.getenv("MONGO_URI")

client = None
collection = None

if MONGO_URI:
    try:
        client = MongoClient(
            MONGO_URI,
            serverSelectionTimeoutMS=5000
        )

        db = client["studentdb"]
        collection = db["students"]

    except Exception:
        logging.exception("MongoDB configuration error")


# ---------------- API Route ----------------
@app.route("/api")
def api():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)

        return jsonify(data), 200

    except FileNotFoundError:
        return jsonify({"error": "data.json file not found"}), 404

    except json.JSONDecodeError:
        return jsonify({"error": "Invalid JSON format"}), 500

    except Exception:
        logging.exception("API error")
        return jsonify({"error": "Unable to load API data"}), 500


# ---------------- Home Page ----------------
@app.route("/", methods=["GET", "POST"])
def home():

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()

        try:
            if not name or not email:
                return render_template(
                    "index.html",
                    error="Please enter both name and email."
                ), 400

            if collection is None:
                raise RuntimeError("MongoDB is not configured.")

            # Insert form data into MongoDB
            collection.insert_one({
                "name": name,
                "email": email
            })

            # Redirect after successful submission
            return redirect(url_for("success"))

        except Exception:
            logging.exception("Data submission failed")

            # Display error on the same page
            return render_template(
                "index.html",
                error="Data submission failed. Please check your MongoDB connection and try again.",
                name=name,
                email=email
            ), 500

    return render_template("index.html")


# ---------------- Success Page ----------------
@app.route("/success")
def success():
    return render_template("success.html")


# ---------------- Run Flask Application ----------------
if __name__ == "__main__":
    app.run(debug=True)
