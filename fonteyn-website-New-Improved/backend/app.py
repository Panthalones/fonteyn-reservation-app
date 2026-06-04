import os
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
import pyodbc
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

FRONTEND_URL = os.getenv("FRONTEND_URL", "*")

CORS(app, resources={
    r"/api/*": {
        "origins": FRONTEND_URL
    }
})


def get_db_connection():
    server = os.getenv("AZURE_SQL_SERVER")
    database = os.getenv("AZURE_SQL_DATABASE")
    username = os.getenv("AZURE_SQL_USER")
    password = os.getenv("AZURE_SQL_PASSWORD")
    driver = os.getenv("AZURE_SQL_DRIVER", "ODBC Driver 18 for SQL Server")

    connection_string = (
        f"DRIVER={{{driver}}};"
        f"SERVER={server};"
        f"DATABASE={database};"
        f"UID={username};"
        f"PWD={password};"
        "Encrypt=yes;"
        "TrustServerCertificate=no;"
        "Connection Timeout=30;"
    )

    return pyodbc.connect(connection_string)


def create_tables():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        IF NOT EXISTS (
            SELECT * FROM sysobjects
            WHERE name='reservations' AND xtype='U'
        )
        CREATE TABLE reservations (
            id INT IDENTITY(1,1) PRIMARY KEY,
            full_name NVARCHAR(255) NOT NULL,
            email NVARCHAR(255) NOT NULL,
            phone NVARCHAR(50),
            park NVARCHAR(255) NOT NULL,
            accommodation NVARCHAR(255) NOT NULL,
            arrival_date DATE NOT NULL,
            departure_date DATE NOT NULL,
            guests INT NOT NULL,
            extras NVARCHAR(MAX),
            total_price DECIMAL(10,2),
            status NVARCHAR(50) DEFAULT 'pending',
            created_at DATETIME2 NOT NULL
        )
    """)

    conn.commit()
    cursor.close()
    conn.close()


def get_value(data, snake_case_key, camel_case_key=None, default=""):
    if snake_case_key in data:
        return data.get(snake_case_key)

    if camel_case_key and camel_case_key in data:
        return data.get(camel_case_key)

    return default


def calculate_price(accommodation, guests):
    prices = {
        "Luxe Cottage": 189,
        "Familiehuis": 149,
        "Kampeerplaats": 49
    }

    base_price = prices.get(accommodation, 0)
    return base_price * guests


@app.route("/")
def home():
    return jsonify({
        "status": "online",
        "message": "Fonteyn Holiday Parks Azure SQL backend is running"
    })


@app.route("/api/health", methods=["GET"])
def health_check():
    try:
        conn = get_db_connection()
        conn.close()

        return jsonify({
            "status": "healthy",
            "database": "azure sql connected",
            "time": datetime.now().isoformat()
        })

    except Exception as error:
        return jsonify({
            "status": "error",
            "database": "not connected",
            "error": str(error)
        }), 500


@app.route("/api/reservations", methods=["POST"])
def create_reservation():
    data = request.get_json()

    if not data:
        return jsonify({"error": "No data received"}), 400

    full_name = get_value(data, "full_name", "fullName")
    email = get_value(data, "email")
    phone = get_value(data, "phone")
    park = get_value(data, "park")
    accommodation = get_value(data, "accommodation")
    arrival_date = get_value(data, "arrival_date", "arrivalDate")
    departure_date = get_value(data, "departure_date", "departureDate")
    guests = get_value(data, "guests")
    extras = get_value(data, "extras")
    total_price = get_value(data, "total_price", "totalPrice", None)

    required_fields = {
        "full_name": full_name,
        "email": email,
        "park": park,
        "accommodation": accommodation,
        "arrival_date": arrival_date,
        "departure_date": departure_date,
        "guests": guests
    }

    for field, value in required_fields.items():
        if value is None or str(value).strip() == "":
            return jsonify({
                "error": f"Field '{field}' is required"
            }), 400

    try:
        guests = int(guests)

        if total_price is None or str(total_price).strip() == "":
            total_price = calculate_price(accommodation, guests)
        else:
            total_price = float(total_price)

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO reservations (
                full_name,
                email,
                phone,
                park,
                accommodation,
                arrival_date,
                departure_date,
                guests,
                extras,
                total_price,
                status,
                created_at
            )
            OUTPUT INSERTED.id
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            full_name,
            email,
            phone,
            park,
            accommodation,
            arrival_date,
            departure_date,
            guests,
            extras,
            total_price,
            "pending",
            datetime.now()
        ))

        reservation_id = cursor.fetchone()[0]

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({
            "message": "Reservation saved successfully",
            "reservation_id": reservation_id
        }), 201

    except Exception as error:
        return jsonify({
            "error": str(error)
        }), 500


@app.route("/api/reservations", methods=["GET"])
def get_reservations():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                id,
                full_name,
                email,
                phone,
                park,
                accommodation,
                arrival_date,
                departure_date,
                guests,
                extras,
                total_price,
                status,
                created_at
            FROM reservations
            ORDER BY created_at DESC
        """)

        rows = cursor.fetchall()
        reservations = []

        for row in rows:
            reservations.append({
                "id": row.id,
                "full_name": row.full_name,
                "email": row.email,
                "phone": row.phone,
                "park": row.park,
                "accommodation": row.accommodation,
                "arrival_date": str(row.arrival_date),
                "departure_date": str(row.departure_date),
                "guests": row.guests,
                "extras": row.extras,
                "total_price": float(row.total_price or 0),
                "status": row.status,
                "created_at": str(row.created_at)
            })

        cursor.close()
        conn.close()

        return jsonify(reservations)

    except Exception as error:
        return jsonify({
            "error": str(error)
        }), 500


@app.route("/api/reservations/<int:reservation_id>", methods=["GET"])
def get_reservation(reservation_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                id,
                full_name,
                email,
                phone,
                park,
                accommodation,
                arrival_date,
                departure_date,
                guests,
                extras,
                total_price,
                status,
                created_at
            FROM reservations
            WHERE id = ?
        """, (reservation_id,))

        row = cursor.fetchone()

        cursor.close()
        conn.close()

        if not row:
            return jsonify({"error": "Reservation not found"}), 404

        return jsonify({
            "id": row.id,
            "full_name": row.full_name,
            "email": row.email,
            "phone": row.phone,
            "park": row.park,
            "accommodation": row.accommodation,
            "arrival_date": str(row.arrival_date),
            "departure_date": str(row.departure_date),
            "guests": row.guests,
            "extras": row.extras,
            "total_price": float(row.total_price or 0),
            "status": row.status,
            "created_at": str(row.created_at)
        })

    except Exception as error:
        return jsonify({
            "error": str(error)
        }), 500


@app.route("/api/reservations/<int:reservation_id>", methods=["DELETE"])
def delete_reservation(reservation_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            DELETE FROM reservations
            WHERE id = ?
        """, (reservation_id,))

        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({
            "message": "Reservation deleted successfully"
        })

    except Exception as error:
        return jsonify({
            "error": str(error)
        }), 500


try:
    create_tables()
except Exception as error:
    print("Database table creation failed:", error)


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )