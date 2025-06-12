import shutil
from flask import Flask, render_template, request, redirect, url_for
import json
import os
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
                primeira_letra = conceito[0].upper()

                # Junta as letras com acento à letra normal
                if primeira_letra in ["Á", "Â"]:
                    conceitos_por_letra["A"].append(conceito)
                elif primeira_letra == "É":
                    conceitos_por_letra["E"].append(conceito)
                elif primeira_letra == "Í":
                    conceitos_por_letra["I"].append(conceito)
                elif primeira_letra == "Ó":
                    conceitos_por_letra["O"].append(conceito)
                elif primeira_letra == "Ú":
                    conceitos_por_letra["U"].append(conceito)
                else:
                    conceitos_por_letra[primeira_letra].append(conceito)

    return render_template("conceitos.html", conceitos_por_letra=conceitos_por_letra)


app.run(host="localhost", port=4001, debug=True)
