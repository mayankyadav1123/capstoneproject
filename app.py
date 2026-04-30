"""
SaafGaadi — Flask Backend (3-Tier Architecture)
================================================
Tier 1  :  Frontend  (HTML / CSS / Vanilla JS)
Tier 2  :  Backend   (This file — Flask REST API)
Tier 3  :  Database  (Supabase / PostgreSQL)

Routes
------
GET   /                → Serve index.html (onboarding page)
GET   /dashboard       → Serve dashboard.html
POST  /api/register    → Register a new user
POST  /api/book        → Create a new booking
GET   /api/bookings    → Fetch all bookings

Run
---
  python app.py
  (Server starts on http://127.0.0.1:8080)
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from supabase import create_client
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("⚠️  Missing SUPABASE_URL or SUPABASE_KEY in .env file!")
          

# APP SETUP

app = Flask(__name__, static_folder=".", static_url_path="")
CORS(app)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


# STATIC PAGE ROUTES


@app.route("/")
def serve_index():
    """Serve the onboarding / login page."""
    return send_from_directory(".", "index.html")


@app.route("/dashboard")
def serve_dashboard():
    """Serve the dashboard page."""
    return send_from_directory(".", "dashboard.html")


# API ROUTES


@app.route("/api/register", methods=["POST"])
def register_user():
    """
    POST /api/register
    Expects JSON body:
      {
        "full_name":     "Mayank",
        "phone_number":  "+919876543210",
        "address":       "123, Street, City"
      }
    Inserts a row into the 'users' table.
    Returns the created user record.
    """
    data = request.get_json()

    if not data:
        return jsonify({"error": "Request body must be JSON"}), 400

    full_name    = data.get("full_name", "").strip()
    phone_number = data.get("phone_number", "").strip()
    address      = data.get("address", "").strip()
    otp          = data.get("otp", "").strip()

    if not full_name or not phone_number or not address or not otp:
        return jsonify({"error": "full_name, phone_number, address, and otp are required"}), 400
        
    if otp != "123456":
        return jsonify({"error": "Invalid OTP. Please use 123456 for this demo."}), 400

    try:
        # Check if user already exists (by phone number)
        existing = (
            supabase
            .table("users")
            .select("*")
            .eq("phone_number", phone_number)
            .execute()
        )

        if existing.data:
            # Update existing user's info
            result = (
                supabase
                .table("users")
                .update({"full_name": full_name, "address": address})
                .eq("phone_number", phone_number)
                .execute()
            )
            return jsonify({"message": "User updated", "data": result.data}), 200

        # Insert new user
        result = (
            supabase
            .table("users")
            .insert({
                "full_name":    full_name,
                "phone_number": phone_number,
                "address":      address
            })
            .execute()
        )
        return jsonify({"message": "User registered successfully", "data": result.data}), 201

    except Exception as e:
        print(f"[ERROR] Supabase user registration failed: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/send-otp", methods=["POST"])
def send_otp():
    """
    POST /api/send-otp
    Expects JSON: { "phone_number": "+91..." }
    """
    data = request.get_json()
    if not data or not data.get("phone_number"):
        return jsonify({"error": "phone_number is required"}), 400
        
    # Simulated OTP logic for demo/capstone
    return jsonify({"message": "OTP sent successfully. Use 123456 for demo.", "demo_otp": "123456"}), 200


@app.route("/api/book", methods=["POST"])
def create_booking():
    """
    POST /api/book
    Expects JSON body:
      {
        "user_name":    "Mayank",
        "phone_number": "+919876543210",
        "service_type": "quick_wash"
      }
    Inserts a row into the 'bookings' table with status = 'pending'.
    """
    data = request.get_json()

    # Basic validation 
    if not data:
        return jsonify({"error": "Request body must be JSON"}), 400

    user_name    = data.get("user_name", "").strip()
    phone_number = data.get("phone_number", "").strip()
    service_type = data.get("service_type", "").strip()

    if not user_name or not phone_number or not service_type:
        return jsonify({"error": "user_name, phone_number, and service_type are required"}), 400

    # Insert into Supabase 
    try:
        result = (
            supabase
            .table("bookings")
            .insert({
                "user_name":    user_name,
                "phone_number": phone_number,
                "service_type": service_type,
                "status":       "pending"
            })
            .execute()
        )
        return jsonify({"message": "Booking created successfully", "data": result.data}), 201

    except Exception as e:
        print(f"[ERROR] Supabase insert failed: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/bookings", methods=["GET"])
def get_bookings():
    """
    GET /api/bookings
    Returns all rows from the 'bookings' table, ordered by newest first.
    Optional query param: ?phone=+919876543210  (filter by phone)
    """
    try:
        query = supabase.table("bookings").select("*").order("created_at", desc=True)

        # Optional: filter by phone number
        phone = request.args.get("phone")
        if phone:
            query = query.eq("phone_number", phone)

        result = query.execute()
        return jsonify({"data": result.data}), 200

    except Exception as e:
        print(f"[ERROR] Supabase select failed: {e}")
        return jsonify({"error": str(e)}), 500


# ──────────────────────────────────────────────
# RUN SERVER
# ──────────────────────────────────────────────
if __name__ == "__main__":
    print("\n🚗  SaafGaadi Flask server running at http://127.0.0.1:8080\n")
    app.run(debug=True, port=8080)
