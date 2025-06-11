import re
import json

filename = "glossario_ministerio_saude.xml"

with open(filename, 'r', encoding='utf-8') as file:
    texto = file.read()

texto = re.sub(r'</page>\s*\n?', '', texto)
texto = re.sub(r'<page number="\d+" position="absolute" top="\d+" left="\d+" height="\d+" width="\d+">*\n?', '', texto)
texto = re.sub(r'<text top="\d+" left="\d+" width="\d+" height="\d+" font="\d+">\d+</text>*\n?', '', texto)
texto = re.sub(r'<text top="\d+" left="\d+" width="\d+" height="\d+" font="22">.</text>*\n?', '', texto)
texto = re.sub(r"<i>*\n?", "", texto)
texto = re.sub(r"</i>*\n?", "", texto)
texto = re.sub(r'</b>\n<b>(.*?)</b>\n', r' \1</b>\n', texto)
texto = re.sub(r"ü", "u", texto)
texto = re.sub(r"<b>*\n?", "", texto)
texto = re.sub(r"</b>*\n?", "", texto)
texto = re.sub (r"- ", "", texto) #usado para tirar quando é quebra de linha
texto = re.sub (r" – ", "", texto)  
texto = re.sub (r"–*\n?", "", texto)  

def extrair_descricao(texto, inicio, fim_proximo=None):
    """
    Extrai todos os blocos font="14" entre 'inicio' e 'fim_proximo'.
    Se fim_proximo for None, vai até ao fim do texto.
    """
    descricao_partes = []
    limite = fim_proximo if fim_proximo else len(texto)

    for match in re.finditer(r'<text[^>]*font="14"[^>]*>(.*?)</text>', texto):
        if inicio <= match.start() < limite:
            descricao_partes.append(match.group(1).strip())

    descricao = " ".join(descricao_partes)

    descricao = re.sub(r'(\w+)-\s+(\w+)', r'\1\2', descricao)

    return descricao

padrao_conceito_categoria = re.compile(
    r'<text[^>]*font="21"[^>]*>(?P<conceito>.*?)</text>\s*'
    r'<text[^>]*font="16"[^>]*>\s*(<i>)?Categoria:(</i>)?\s*</text>\s*'
    r'<text[^>]*font="14"[^>]*>(?P<categoria>.*?)</text>',
    re.DOTALL
)

resultado = []
matches = list(padrao_conceito_categoria.finditer(texto))

for i, match in enumerate(matches):
    conceito = match.group("conceito").strip()
    categoria = match.group("categoria").strip()
    fim_atual = match.end()

    if i + 1 < len(matches):
        inicio_proximo = matches[i + 1].start()
    else:
        inicio_proximo = None

    descricao = extrair_descricao(texto, fim_atual, inicio_proximo)

    resultado.append({
        "Conceito": conceito,
        "Categoria": categoria,
        "Descrição": descricao
    })

with open("glossario_ministerio.json", "w", encoding='utf-8') as file_out:
    json.dump(resultado, file_out, indent=4, ensure_ascii=False)

