import re
import json

filename = "diccionari-multilinguee-de-la-covid-19.xml"

#primeiro passo foi retirar manualmente no xml as páginas de introdução que não continham informação relevante para o json
#foi retirado manualmente os indexes e bibliografias

with open(filename, 'r', encoding='utf-8') as file:
    texto = file.read()

texto = re.sub(r'</page>\s*', '', texto) #remove todas as trocas de página do ficheiro
texto = re.sub(r'<page number="\d+" position="absolute" top="0" left="0" height="1190" width="914">\s*\n?', '', texto) #remove os títulos das páginas e faz com que não fique uma linha em branco entre elas
texto = re.sub(r'<fontspec id="\d+" size="\d+" family="[^"]+" color="#[0-9a-fA-F]{6}"\s*/>*\n?', '', texto) #remove infos da pagina
texto = re.sub(r'<text top="\d+" left="\d+" width="\d+" height="\d+" font="\d+">\d+\s?</text>*\n?', '', texto) #remove o número da definição
texto = re.sub(r'<text top="\d+" left="\d+" width="\d+" height="\d+" font="\d+"><i> n m</i></text>*\n?', '', texto) #remove os n m
texto = re.sub(r'<text top="\d+" left="\d+" width="\d+" height="\d+" font="\d+"><i> n f</i></text>*\n?', '', texto) #remove os n f
texto = re.sub(r'<text top="\d+" left="\d+" width="\d+" height="\d+" font="\d+"><i> n</i></text>*\n?', '', texto) #remove os n
texto = re.sub(r'<text top="\d+" left="\d+" width="\d+" height="\d+" font="\d+">\s+</text>\s*\n?', '', texto) #remove cenas vazias
texto = re.sub(r'<text top="87" left="407" width="118" height="19" font="15"><b>QUADERNS 50 </b></text>*\n?', '', texto)
texto = re.sub(r'<text top="87" left="526" width="327" height="19" font="16"> DICCIONARI MULTILINGÜE DE LA COVID-19</text>*\n?', '', texto)
texto = re.sub(r'<text top="\d+" left="\d+" width="\d+" height="\d+" font="\d+"><b>\s+</b></text>*\n?', '', texto)
texto = re.sub(r'<text top="\d+" left="\d+" width="\d+" height="\d+" font="\d+"><i> adj</i></text>*\n?', '', texto)

#remoção de sinonimos que aparecem descritos de novo

texto = re.sub(
    r'<text top="\d+" left="\d+" width="\d+" height="\d+" font="25"><b>[^<]+</b></text>\s*'
    r'<text top="\d+" left="\d+" width="\d+" height="\d+" font="11+"> veg. </text>\s*'
    r'<text top="\d+" left="\d+" width="\d+" height="\d+" font="25"><b>[^<]+</b></text>\s*',
    '',
    texto,
    flags=re.DOTALL
)

texto = re.sub(
    r'<text top="\d+" left="\d+" width="\d+" height="\d+" font="25"><b>[^<]+</b></text>\s*'
    r'<text top="\d+" left="\d+" width="\d+" height="\d+" font="11+">veg. </text>\s*'
    r'<text top="\d+" left="\d+" width="\d+" height="\d+" font="25"><b>[^<]+</b></text>\s*',
    '',
    texto,
    flags=re.DOTALL
)



with open("teste.xml", 'w', encoding='utf-8') as novo_arquivo:
    novo_arquivo.write(texto)


