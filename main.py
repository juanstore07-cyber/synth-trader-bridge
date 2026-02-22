import asyncio
import json
import websockets
from flask import Flask, jsonify
import threading
import os

app = Flask(__name__)

velas_boom = []
velas_crash = []

async def conectar(simbolo, almacen):
    uri = "wss://ws.derivws.com/websockets/v3?app_id=1089"
    while True:
        try:
            print("Conectando a " + simbolo)
            async with websockets.connect(uri) as ws:
                print("Conectado a " + simbolo)
                peticion = {
                    "ticks_history": simbolo,
                    "end": "latest",
                    "start": 1,
                    "count": 50,
                    "style": "candles",
                    "granularity": 60,
                    "subscribe": 1
                }
                await ws.send(json.dumps(peticion))
                async for mensaje in ws:
                    datos = json.loads(mensaje)
                    if "candles" in datos:
                        almacen.clear()
                        almacen.extend(datos["candles"])
                        print(simbolo + ": " + str(len(almacen)) + " velas")
                    elif "ohlc" in datos:
                        vela = {
                            "open": float(datos["ohlc"]["open"]),
                            "high": float(datos["ohlc"]["high"]),
                            "low": float(datos["ohlc"]["low"]),
                            "close": float(datos["ohlc"]["close"]),
                            "epoch": datos["ohlc"]["epoch"]
                        }
                        if almacen:
                            almacen[-1] = vela
                        else:
                            almacen.append(vela)
        except Exception as e:
            print("Error: " + str(e))
            await asyncio.sleep(5)

def iniciar():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(asyncio.gather(
        conectar("BOOM1000", velas_boom),
        conectar("CRASH1000", velas_crash)
    ))

t = threading.Thread(target=iniciar, daemon=True)
t.start()

@app.route("/health")
def health():
    return jsonify({
        "status": "ok",
        "boom_velas": len(velas_boom),
        "crash_velas": len(velas_crash)
    })

@app.route("/boom1000")
def boom():
    if not velas_boom:
        return jsonify({"error": "Sin datos"}), 503
    return jsonify({
        "simbolo": "BOOM1000",
        "total_velas": len(velas_boom),
        "candles": velas_boom[-20:]
    })

@app.route("/crash1000")
def crash():
    if not velas_crash:
        return jsonify({"error": "Sin datos"}), 503
    return jsonify({
        "simbolo": "CRASH1000",
        "total_velas": len(velas_crash),
        "candles": velas_crash[-20:]
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
