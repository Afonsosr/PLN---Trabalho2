import shutil
from flask import Flask, render_template, request, redirect, url_for
import json
import os
import unicodedata
from collections import defaultdict

app = Flask(__name__)

file = "glossario_por_categoria.json"

with open(file, 'r', encoding='utf-8') as file:
    conceitos = json.load(file)

def guardar_conceitos(conceitos, filename):
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
@app.route("/conceitos")
def listar_conceitos():
    conceitos = carregar_conceitos("glossario_por_categoria.json")

    conceitos_por_letra = defaultdict(list)

    for categoria, lista_conceitos in conceitos.items():
        for item in lista_conceitos:
            conceito = item.get("Conceito")
            if conceito:
                conceito_sem_acentos = unicodedata.normalize("NFD", conceito).encode("ascii", "ignore").decode("utf-8")
                primeira_letra = conceito_sem_acentos[0].upper()
                conceitos_por_letra[primeira_letra].append(conceito)

    for letra in conceitos_por_letra:
        conceitos_por_letra[letra].sort(key=lambda c: unicodedata.normalize("NFD", c).encode("ascii", "ignore").decode("utf-8"))

    # Ordenar as letras
    conceitos_por_letra_ordenado = dict(sorted(conceitos_por_letra.items()))

    return render_template("conceitos.html", conceitos_por_letra=conceitos_por_letra_ordenado)


app.run(host="localhost", port=4001, debug=True)
