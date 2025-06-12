import re
import json

filename = "glossario_neologismos_saude.xml"

#primeiro passo foi retirar manualmente no xml as páginas de introdução que não continham informação relevante para o json
#foi retirado manualmente os indexes e bibliografias

with open(filename, 'r', encoding='utf-8') as file:
    texto = file.read()

texto = re.sub(r'</page>\s*\n?', '', texto) #remove todas as trocas de página do ficheiro
texto = re.sub(r'<text top="\d+" left="\d+" width="\d+" height="\d+" font="23"> </text>*\n?', '',texto)
texto = re.sub(r'<page number="\d+" position="absolute" top="\d+" left="\d+" height="\d+" width="\d+">*\n?', '', texto)
texto = re.sub(r'<text[^>]*?>\((\d+)\)\s*</text>*\n?', '', texto)



padrao_conceito_substantivo = re.compile(
    r'<text[^>]*?>(?P<conceito>.*?)</text>\s*'
    r'<text[^>]*?><i>\s*(?P<substantivo>s\.f\.|s\.m\.)\s*</i></text>\s*'
)

padrao_texto = re.compile(r'<text[^>]*?>(.*?)</text>')

padrao_sigla = re.compile(
    r'(?:<text[^>]*?>Sigla:\s*</text>\s*<text[^>]*?><i>(.*?)</i></text>'  # caso com <i>
    r'|<text[^>]*?>Sigla:\s*(.*?)</text>)',  # caso tudo numa linha
    re.IGNORECASE
)


# Função para extrair tradução
def extrair_traducoes(parte):
    blocos = padrao_texto.findall(parte)
    partes = []

    for bloco in blocos:
        texto_limpo = bloco.strip().lower()

        if "[ing]" in texto_limpo or "[esp]" in texto_limpo:
            partes.append(bloco.strip())
        else:
            break

    if partes:
        return " ".join(partes)
    return None

def extrair_sigla(parte):
    match = padrao_sigla.search(parte)
    if match:
        return (match.group(1) or match.group(2)).strip()
    return ("Sem sigla associada")

def extrair_descricao(parte):
    padrao_bloco = re.finditer(
        r'<text[^>]*?top="\d+" left="(?P<left>\d+)"[^>]*?font="(?P<font>\d+)"[^>]*?>(.*?)</text>',
        parte
    )

    descricao_partes = []
    for m in padrao_bloco:
        left = int(m.group("left"))
        font = int(m.group("font"))
        conteudo = m.group(3).strip()

        if conteudo.startswith("“") or conteudo.startswith('"') or conteudo.startswith("..."):
            break

        if left == 128 and font == 23:
            if re.match(r'^[a-zá-úç\- ]{3,}$', conteudo.lower()):
                break
        if font == 23 and len(conteudo) > 0 and not any(x in conteudo.lower() for x in ['[ing]', '[esp]', 'sigla:']):
            descricao_partes.append(conteudo)

    if descricao_partes:
        return " ".join(descricao_partes)
    return None


def extrair_citacao(parte):
    blocos = re.findall(r'<text[^>]*?font="24"[^>]*?>(.*?)</text>', parte)
    citacao_partes = []
    citando = False

    for linha in blocos:
        texto = re.sub(r'<[^>]+>', '', linha).strip()
        if texto.startswith('“...'):
            citando = True
        if citando:
            citacao_partes.append(texto)
        if texto.endswith('...”') or texto.endswith('...” ') or texto.endswith('...”</i>'):
            break

    if citacao_partes:
        return " ".join(citacao_partes)
    return None


resultado = []

for match in padrao_conceito_substantivo.finditer(texto):
    conceito = match.group("conceito").strip()
    genero = match.group("substantivo")
    fim = match.end()
    parte_pos_termo = texto[fim:fim+6500]

    traducoes = extrair_traducoes(parte_pos_termo)
    sigla = extrair_sigla(parte_pos_termo[:600])
    descricao = extrair_descricao(parte_pos_termo)
    citacao = extrair_citacao(parte_pos_termo)


    resultado.append({
        "Conceito": conceito,
        "Substantivo": genero,
        "Traduções": traducoes,
        "Sigla": sigla,
        "Descrição": descricao,
        "Citação": citacao,
    })


# Exportar o JSON
with open("glossario_neologismos.json", "w", encoding="utf-8") as jsonfile:
    json.dump(resultado, jsonfile, ensure_ascii=False, indent=2)

