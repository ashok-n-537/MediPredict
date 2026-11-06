
from flask import (
    Flask, render_template, request, jsonify,
    redirect, url_for, session, flash
)

import joblib
import pandas as pd
import json
import os
import joblib
import requests
from pathlib import Path

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from db import get_db_connection


app = Flask(__name__)
app.secret_key = "medipredict-development-secret"


# Download the trained model if it is not available locally
MODEL_PATH = Path("model/disease_model.pkl")

if not MODEL_PATH.exists() or MODEL_PATH.stat().st_size < 100_000_000:

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)

    MODEL_URL = os.environ.get("MODEL_URL")

    if not MODEL_URL:
        raise RuntimeError("MODEL_URL is not configured")

    print("Downloading MediPredict model...")

    response = requests.get(
        MODEL_URL,
        stream=True,
        timeout=(30, 600)
    )

    response.raise_for_status()

    content_type = response.headers.get("Content-Type", "")

    if "text/html" in content_type:
        raise RuntimeError("Hugging Face returned HTML instead of the model")

    with open(MODEL_PATH, "wb") as file:
        for chunk in response.iter_content(chunk_size=1024 * 1024):
            if chunk:
                file.write(chunk)

    if MODEL_PATH.stat().st_size < 100_000_000:
        raise RuntimeError("Downloaded model file is incomplete")

    print("Model downloaded successfully!")

saved_data = joblib.load(MODEL_PATH)

model = saved_data["model"]
features = saved_data["features"]

print("MediPredict model loaded successfully!")
# Load the trained model
import hashlib

print("MODEL FILE SIZE:", MODEL_PATH.stat().st_size)

with open(MODEL_PATH, "rb") as f:
    print("MODEL FIRST BYTES:", f.read(20))

h = hashlib.sha256()

with open(MODEL_PATH, "rb") as f:
    for chunk in iter(lambda: f.read(1024 * 1024), b""):
        h.update(chunk)

print("MODEL SHA256:", h.hexdigest())

saved_data = joblib.load(MODEL_PATH)


model = saved_data["model"]
features = saved_data["features"]

print("MediPredict model loaded successfully!")


@app.route('/')
def home():
    return render_template(
        'index.html',
        symptoms=features
    )
# =====================================
# USER REGISTRATION
# =====================================

@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'POST':

        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        if not name or not email or not password:
            flash("Please fill all fields.")
            return redirect(url_for('register'))

        if len(password) < 8:
            flash("Password must contain at least 8 characters.")
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password)

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                INSERT INTO users (name, email, password)
                VALUES (?, ?, ?)
                """,
                (name, email, hashed_password)
            )

            conn.commit()

            flash("Registration successful! Please login.")
            return redirect(url_for('login'))

        except Exception:
            conn.rollback()
            flash("Email already registered or registration failed.")

        finally:
            cursor.close()
            conn.close()

    return render_template('register.html')


# =====================================
# USER LOGIN
# =====================================

@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                "SELECT * FROM users WHERE email = ?",
                (email,)
            )

            user = cursor.fetchone()

            if user and check_password_hash(
                user['password'], password
            ):

                session.clear()

                session['user_id'] = user['id']
                session['user_name'] = user['name']

                return redirect(url_for('home'))

            flash("Invalid email or password.")

        finally:
            cursor.close()
            conn.close()

    return render_template('login.html')


# =====================================
# USER LOGOUT
# =====================================

@app.route('/logout')
def logout():

    session.clear()

    return redirect(url_for('login'))


# =====================================
# AI DISEASE PREDICTION
# =====================================

@app.route('/predict', methods=['POST'])
def predict():

    if 'user_id' not in session:
        return jsonify({
            "error": "Please login first."
        }), 401

    try:

        data = request.get_json()

        if not isinstance(data, dict):
            return jsonify({
                "error": "Invalid input format"
            }), 400

        symptoms = data.get("symptoms")

        if not isinstance(symptoms, list) or not symptoms:
            return jsonify({
                "error": "Select valid symptoms"
            }), 400

        if any(not isinstance(item, str) for item in symptoms):
            return jsonify({
                "error": "Invalid symptoms"
            }), 400

        if len(symptoms) != len(set(symptoms)):
            return jsonify({
                "error": "Duplicate symptoms"
            }), 400

        if not set(symptoms).issubset(set(features)):
            return jsonify({
                "error": "Invalid symptom selected"
            }), 400

        # Convert symptoms into binary values

        input_data = {
            feature: 1 if feature in symptoms else 0
            for feature in features
        }

        input_df = pd.DataFrame(
            [input_data],
            columns=features
        )

        # Generate prediction

        prediction = str(model.predict(input_df)[0])

        # Save prediction in database

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                INSERT INTO predictions
                (user_id, symptoms, predicted_disease)
                VALUES (?, ?, ?)
                """,
                (
                    session['user_id'],
                    json.dumps(symptoms),
                    prediction
                )
            )

            conn.commit()

        finally:
            cursor.close()
            conn.close()

        return jsonify({
            "prediction": prediction,
            "message": "Prediction saved successfully"
        })

    except Exception:

        app.logger.exception("Prediction failed")

        return jsonify({
            "error": "Unable to generate prediction"
        }), 500


# =====================================
# PREDICTION HISTORY
# =====================================

@app.route('/history')
def history():

    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()

    try:

        cursor.execute(
            """
            SELECT id, symptoms, predicted_disease, created_at
            FROM predictions
            WHERE user_id = ?
            ORDER BY created_at DESC
            """,
            (session['user_id'],)
        )

        records = cursor.fetchall()

    finally:
        cursor.close()
        conn.close()

    # Convert database records into dictionaries

    records = [
        {
            'id': record['id'],
            'symptoms': json.loads(record['symptoms']),
            'predicted_disease': record['predicted_disease'],
            'created_at': record['created_at']
        }
        for record in records
    ]

    return render_template(
        'history.html',
        records=records,
        user_name=session['user_name']
    )


# =====================================
# USER DASHBOARD
# =====================================

@app.route('/dashboard')
def dashboard():

    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()

    try:

        # Count total predictions

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM predictions
            WHERE user_id = ?
            """,
            (session['user_id'],)
        )

        total_predictions = cursor.fetchone()[0]

        # Get latest five predictions

        cursor.execute(
            """
            SELECT id, symptoms, predicted_disease, created_at
            FROM predictions
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT 5
            """,
            (session['user_id'],)
        )

        recent_records = cursor.fetchall()

        # Get data for analytics chart

        cursor.execute(
            """
            SELECT predicted_disease, COUNT(*) AS total
            FROM predictions
            WHERE user_id = ?
            GROUP BY predicted_disease
            """,
            (session['user_id'],)
        )

        chart_records = cursor.fetchall()

    finally:
        cursor.close()
        conn.close()

    # Prepare recent records

    recent_records = [
        {
            'id': record['id'],
            'symptoms': json.loads(record['symptoms']),
            'predicted_disease': record['predicted_disease'],
            'created_at': record['created_at']
        }
        for record in recent_records
    ]

    # Prepare chart data

    chart_labels = [
        record['predicted_disease']
        for record in chart_records
    ]

    chart_values = [
        record['total']
        for record in chart_records
    ]

    return render_template(
        'dashboard.html',
        user_name=session['user_name'],
        total_predictions=total_predictions,
        recent_records=recent_records,
        chart_labels=chart_labels,
        chart_values=chart_values
    )


# =====================================
# DELETE INDIVIDUAL PREDICTION
# =====================================

@app.route(
    '/delete_prediction/<int:prediction_id>',
    methods=['POST']
)
def delete_prediction(prediction_id):

    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()

    try:

        cursor.execute(
            """
            DELETE FROM predictions
            WHERE id = ? AND user_id = ?
            """,
            (prediction_id, session['user_id'])
        )

        conn.commit()

    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('history'))


# =====================================
# RUN FLASK APPLICATION
# =====================================

if __name__ == '__main__':
    app.run(debug=True)
