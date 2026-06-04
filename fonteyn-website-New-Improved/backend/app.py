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

    required_fields = [
        "full_name",
        "email",
        "park",
        "accommodation",
        "arrival_date",
        "departure_date",
        "guests"
    ]

    for field in required_fields:
        if field not in data or str(data[field]).strip() == "":
            return jsonify({
                "error": f"Field '{field}' is required"
            }), 400

    try:
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
            data["full_name"],
            data["email"],
            data.get("phone", ""),
            data["park"],
            data["accommodation"],
            data["arrival_date"],
            data["departure_date"],
            int(data["guests"]),
            data.get("extras", ""),
            float(data.get("total_price", 0)),
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