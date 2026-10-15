from flask import Flask, render_template, jsonify, request
import mysql.connector
from datetime import datetime, timedelta
import random  # Para simular variaciones suaves en la predicción si hay pocos datos

app = Flask(__name__, template_folder="../front_sima")

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="123456789",
        database="estacionmetereologica_proa"
    )


# 1. Endpoint en tiempo real
@app.route('/api/live')
def api_live():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
    SELECT temperatura, humedad, gas AS calidad_aire,
           fecha_hora AS timestamp
    FROM mediciones
    ORDER BY id_mediciones DESC
    LIMIT 1
""")
    data = cursor.fetchone()
    cursor.close()
    conn.close()

    return jsonify(data)

# 2. Endpoint de históricos según rango de tiempo
@app.route('/api/history')
def api_history():
    hours = request.args.get('hours', default=24, type=int)
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Consulta los registros según el intervalo seleccionado
    query = """
        SELECT temperatura, humedad, gas AS calidad_aire,
               fecha_hora AS timestamp
        FROM mediciones
        WHERE fecha_hora <= NOW() - INTERVAL %s HOUR
        ORDER BY fecha_hora ASC
    """
    cursor.execute(query, (hours,))
    records = cursor.fetchall()
    cursor.close()
    conn.close()
    
    # Formatear timestamps a texto para JS
    for r in records:
        r['timestamp'] = r['timestamp'].strftime('%Y-%m-%d %H:%M')
        
    return jsonify(records)

# 3. Endpoint de predicción estimada (semana próxima)
@app.route('/api/forecast')
def api_forecast():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT AVG(temperatura) as avg_temp, AVG(humedad) as avg_hum FROM mediciones WHERE fecha_hora >= NOW() - INTERVAL 7 DAY")
    avg = cursor.fetchone()
    cursor.close()
    conn.close()
    print(avg)

    base_temp = avg['avg_temp'] if avg and avg['avg_temp'] else 22.0
    base_hum = avg['avg_hum'] if avg and avg['avg_hum'] else 60.0

    forecast = []
    dias = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
    hoy = datetime.now()

    for i in range(1, 8):
        fecha_futura = hoy + timedelta(days=i)
        # Predicción basada en promedios con pequeñas variaciones
        temp_simulada = round(float(base_temp) + random.uniform(-2.5, 2.5), 1)
        hum_simulada = round(float(base_hum) + random.uniform(-5.0, 5.0), 1)
        
        forecast.append({
            "dia": dias[fecha_futura.weekday()],
            "fecha": fecha_futura.strftime('%d/%m'),
            "temperatura": temp_simulada,
            "humedad": hum_simulada,
            "estado": "Soleado" if temp_simulada > 20 else "Nublado"
        })

    return jsonify(forecast)

@app.route('/')
def index():
    return render_template('sima_index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)