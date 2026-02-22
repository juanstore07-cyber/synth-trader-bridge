import asyncio
import json
import websockets
import requests
from flask import Flask, jsonify
from threading import Thread
import time

app = Flask(__name__)

# Almacén de velas en memoria
velas_boom = []
velas_crash = []

async def conectar_deriv(simbolo, almacen):
    uri = "wss://ws.derivws.com/websockets/v3?app_id=1089"
    while True:
        try:
            async with websockets.connect(uri) as ws:
                print(f"Conectado a Deriv para {simbolo}")
                
                # Solicitar historial de velas
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
                        print(f"{simbolo}: {len(almacen)} velas cargadas")
                    
                    elif "ohlc" in datos:
                        vela_nueva = {
                            "open": float(datos["ohlc"]["open"]),
                            "high": float(datos["ohlc"]["high"]),
                            "low": float(datos["ohlc"]["low"]),
                            "close": float(datos["ohlc"]["close"]),
                            "epoch": datos["ohlc"]["epoch"]
                        }
                        if len(almacen) > 0:
                            almacen[-1] = vela_nueva
                        else:
                            almacen.append(vela_nueva)

        except Exception as e:
            print(f"Error con {simbolo}: {e}. Reconectando en 5s...")
            await asyncio.sleep(5)

@app.route('/boom1000', methods=['GET'])
def get_boom():
    if not velas_boom:
        return jsonify({"error": "Sin datos aun, espera 10 segundos"}), 503
    return jsonify({
        "simbolo": "BOOM1000",
        "total_velas": len(velas_boom),
        "candles": velas_boom[-20:]
    })

@app.route('/crash1000', methods=['GET'])
def get_crash():
    if not velas_crash:
        return jsonify({"error": "Sin datos aun, espera 10 segundos"}), 503
    return jsonify({
        "simbolo": "CRASH1000",
        "total_velas": len(velas_crash),
        "candles": velas_crash[-20:]
    })

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        "status": "ok",
        "boom_velas": len(velas_boom),
        "crash_velas": len(velas_crash)
    })

def correr_websockets():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(asyncio.gather(
        conectar_deriv("BOOM1000", velas_boom),
        conectar_deriv("CRASH1000", velas_crash)
    ))

if __name__ == '__main__':
    # Iniciar WebSocket en hilo separado
    hilo = Thread(target=correr_websockets, daemon=True)
    hilo.start()
    
    # Esperar que carguen datos
    time.sleep(8)
    
    # Iniciar servidor HTTP
    app.run(host='0.0.0.0', port=8080)
