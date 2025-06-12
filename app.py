import shutil
from flask import Flask, render_template, request, redirect, url_for
import json
import os
from collections import defaultdict

app = Flask(__name__)

file = "glossario_por_categoria.json"

with open(file, 'r', encoding='utf-8') as file:
    conceitos = json.load(file)

def guardar_conceitos(doencas, filename):
    with open(filename, 'w', encoding='utf-8') as file:
        json.dump(conceitos, file, ensure_ascii=False, indent=4)
        
def carregar_conceitos(file):
    with open(file, 'r', encoding='utf-8') as file:
        conceitos = json.load(file)
    return conceitos

@app.route("/")
def home():
    tamanho = len(conceitos)
    return render_template("home.html", tamanho = tamanho)

app.run(host="localhost", port=4001, debug=True)
