"""
SaafGaadi — Vercel Serverless Flask API
========================================
This file runs as a Vercel serverless function.
All /api/* requests are routed here.

Routes
------
POST  /api/register    → Register a new user
POST  /api/book        → Create a new booking
GET   /api/bookings    → Fetch all bookings
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from supabase import create_client
import os


# ── Supabase credentials (set in Vercel Dashboard → Settings → Environment Variables) ──
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")


# ── App Setup ──
app = Flask(__name__)
CORS(app)

# Lazy init — avoids crash if env vars are missing at import time
supabase = None
if SUPABASE_URL and SUPABASE_KEY:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


def _check_supabase():
    """Return an error response if Supabase is not configured."""
    if supabase is None:
        return jsonify({"error": "Supabase is not configured. Set SUPABASE_URL and SUPABASE_KEY in Vercel environment variables."}), 503
    return None


# ── ROUTES ──


@app.route("/api/register", methods=["POST"])
def register_user():
    """
    POST /api/register
    Expects JSON: { "full_name", "phone_number", "address" }
    """
    err = _check_supabase()
    if err:
        return err

    data = request.get_json()

    if not data:
        return jsonify({"error": "Request body must be JSON"}), 400

    full_name    = data.get("full_name", "").strip()
    phone_number = data.get("phone_number", "").strip()
    address      = data.get("address", "").strip()

    if not full_name or not phone_number or not address:
        return jsonify({"error": "full_name, phone_number, and address are required"}), 400

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


@app.route("/api/book", methods=["POST"])
def create_booking():
    """
    POST /api/book
    Expects JSON: { "user_name", "phone_number", "service_type" }
    """
    err = _check_supabase()
    if err:
        return err

    data = request.get_json()

    if not data:
        return jsonify({"error": "Request body must be JSON"}), 400

    user_name    = data.get("user_name", "").strip()
    phone_number = data.get("phone_number", "").strip()
    service_type = data.get("service_type", "").strip()

    if not user_name or not phone_number or not service_type:
        return jsonify({"error": "user_name, phone_number, and service_type are required"}), 400

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
    Optional query param: ?phone=+919876543210
    """
    err = _check_supabase()
    if err:
        return err

    try:
        query = supabase.table("bookings").select("*").order("created_at", desc=True)

        phone = request.args.get("phone")
        if phone:
            query = query.eq("phone_number", phone)

        result = query.execute()
        return jsonify({"data": result.data}), 200

    except Exception as e:
        print(f"[ERROR] Supabase select failed: {e}")
        return jsonify({"error": str(e)}), 500
