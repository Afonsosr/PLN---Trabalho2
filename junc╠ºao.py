import json


ministerio_json = "glossario_ministerio.json"
neologismos_json = "glossario_neologismos.json"
covid_json = "glossario_covid.json"
junçao_conceitos = "glossario_juncao.json"


with open(ministerio_json, "r", encoding="utf-8") as f:
    ministerio = json.load(f)

with open(neologismos_json, "r", encoding="utf-8") as f:
    neologismos = json.load(f)

with open(covid_json, "r", encoding="utf-8") as f:
    covid = json.load(f)

conceitos_unificados = {}


def adicionar_conceito(lista, origem):
    for item in lista:
        nome = item["Conceito"]
        if nome not in conceitos_unificados:
            conceitos_unificados[nome] = {"Conceito": nome, "Fontes": {origem: item}}
        else:
            conceitos_unificados[nome]["Fontes"][origem] = item


adicionar_conceito(ministerio, "ministerio")
adicionar_conceito(neologismos, "neologismo")
adicionar_conceito(covid, "covid")


resultado_final = sorted(conceitos_unificados.values(), key=lambda x: x["Conceito"].lower())

with open(junçao_conceitos, "w", encoding="utf-8") as f:
    json.dump(resultado_final, f, ensure_ascii=False, indent=2)
