# relay_server.py
from flask import Flask, request, jsonify

app = Flask(__name__)
salas = {}

@app.route("/register", methods=["POST"])
def register():
    data = request.json
    codigo = data["codigo"]
    ip = data["ip"]
    salas[codigo] = ip
    return {"status": "ok"}

@app.route("/sala/<codigo>")
def get_ip(codigo):
    ip = salas.get(codigo)
    if ip:
        return {"ip": ip}
    return {"error": "Sala no encontrada"}, 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
