import asyncio
import json
import websockets
from flask import Flask, jsonify
import os

app = Flask(__name__)

async def pedir_velas(simbolo):
    uri = "wss://ws.derivws.com/websockets/v3?app_id=1089"
    try:
        async with websockets.connect(uri) as ws:
            peticion = {
                "ticks_history": simbolo,
                "end": "latest",
                "start": 1,
                "count": 101,
                "style": "candles",
                "granularity": 60
            }
            await ws.send(json.dumps(peticion))
            async for mensaje in ws:
                datos = json.loads(mensaje)
                if "candles" in datos:
                    return datos["candles"]
    except Exception as e:
        print("Error: " + str(e))
        return None

@app.route("/boom1000")
def boom():
    velas = asyncio.run(pedir_velas("BOOM1000"))
    if not velas:
        return jsonify({"error": "Sin datos"}), 503
    return jsonify({
        "simbolo": "BOOM1000",
        "total_velas": len(velas),
        "candles": velas
    })

@app.route("/crash1000")
def crash():
    velas = asyncio.run(pedir_velas("CRASH1000"))
    if not velas:
        return jsonify({"error": "Sin datos"}), 503
    return jsonify({
        "simbolo": "CRASH1000",
        "total_velas": len(velas),
        "candles": velas
    })

@app.route("/health")
def health():
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
