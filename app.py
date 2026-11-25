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

# MongoDB connection
MONGO_URI = os.getenv("MONGO_URI")

client = None
collection = None
todo_collection = None

if MONGO_URI:
    try:
        client = MongoClient(
            MONGO_URI,
            serverSelectionTimeoutMS=5000
        )

        db = client["studentdb"]

        # Existing student collection
        collection = db["students"]

        # New To-Do collection
        todo_collection = db["todo_items"]

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

            collection.insert_one({
                "name": name,
                "email": email
            })

            return redirect(url_for("success"))

        except Exception:
            logging.exception("Data submission failed")

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


# ---------------- To-Do Backend Route ----------------
@app.route("/submittodoitem", methods=["POST"])
def submit_todo_item():

    item_name = request.form.get("itemName", "").strip()
    item_description = request.form.get("itemDescription", "").strip()

    if not item_name or not item_description:
        return jsonify({
            "error": "Item Name and Item Description are required."
        }), 400

    if todo_collection is None:
        return jsonify({
            "error": "MongoDB is not configured."
        }), 500

    try:
        todo_collection.insert_one({
            "itemName": item_name,
            "itemDescription": item_description
        })

        return jsonify({
            "message": "To-Do item submitted successfully!",
            "itemName": item_name,
            "itemDescription": item_description
        }), 201

    except Exception:
        logging.exception("To-Do submission failed")

        return jsonify({
            "error": "Unable to save To-Do item."
        }), 500


# ---------------- Run Flask Application ----------------
if __name__ == "__main__":
    app.run(debug=True)
