# Librerías a utilizar.
import nltk # Eliminación de stop words.
import pandas as pd # Manejo de archivos xlsx.
from os import listdir # Manejo de archivos.
import json # Almacenamiento de archivo JSON.

# Se descarga el conjunto (se puede comentar luego de la primera ejecución).
nltk.download("stopwords")

# Se importa el conjunto de palabras.
from nltk.corpus import stopwords

# Lista de palabras adicional.
#additional_words = []

# Se utilizan las stopwords en español, al ser el idioma del texto a procesar.
stop_words = stopwords.words("spanish") #+ []

# Función de limpieza
def clean_text(text):
    # Se pasa a minúscula.
    clean = text.lower()
    # Se eliminan comas, puntos y guiones.
    clean = clean.replace(',','').replace('.','').replace('-','')
    # Se eliminan las stopwords del español y se retorna.
    return ' '.join([w for w in clean.split() if w not in stop_words])

# A continuación, se obtienen las rutas de los archivos.
destiny_path = "../d3-concept-map"
base_path = "../../dataset/ELA JULIO 2017 CEAR UDP/ELA"
files_path = {}

for file in listdir(base_path):
    # Nos quedamos con los archivos de la extensión correcta.
    if ".xlsx" in file:
        # Se guardan las rutas en un diccionario.
        name = file.split(" - ")[-1].split(".")[0]
        files_path[name] = "{0}/{1}".format(base_path, file)

# Lectura de datos.
data = pd.read_excel(files_path["Valores2"], "Hoja1", index_col = None)

# Eliminamos las filas sin contenido en la columna correspondiente.
data = data[(data['normalizacion'].notnull()) & (data['normalizacion'] != '–') &
            (data["region"].notnull())]

# Obtenemos las categorías
categories = list(data.categoria.unique())

# Obtenemos las regiones.
regions = data.region.unique()

# Mapeo de id de región a su nombre
region_name = {
    1: "Arica y Parinacota",
    2: "Tarapacá",
    3: "Antofagasta",
    4: "Atacama",
    5: "Coquimbo",
    6: "Valparaíso",
    7: "Metropolitana",
    8: "Libertador B. O.",
    9: "Maule",
    10: "Biobío",
    11: "La Araucanía",
    12: "Los Ríos",
    13: "Los Lagos",
    14: "Aisén",
    15: "Mag. y Antártica"
}

# Mapeo de nombre de categoría a su versión corta, si corresponde.
category_short = {
    "Respeto / Conservación de la naturaleza o medio ambiente": "Medio ambiente",
    "Bien Común / Comunidad": "Bien común",
    "Transparencia y publicidad": "Transp. y publicidad",
    "Paz / Convivencia pacífica": "Paz"
}

# JSON global.
data_json = {}

# Límite de palabras a considerar.
word_limit = 20

# Para cada región y para cada categoría...
for category in categories:
    for region in regions:
        # Selección de los fundamentos normalizados.
        text_set = data[(data.categoria == category) &
                        (data.region == region)]
        # Realizamos el siguiente procedimiento solo si el dataframe no está
        # vacío.
        if not text_set.empty:
            # Se crea la llave del diccionario.
            if category in category_short.keys():
                json_key = "{0}-{1}".format(region_name[int(region)],
                                            category_short[category])
            else:
                json_key = "{0}-{1}".format(region_name[int(region)], category)
            # Diccionario de palabras.
            word_dict = {}
            # Diccionario de co-ocurrencias.
            word_coocurrence = {}
            for index, row in text_set.iterrows():
                # Aplicamos la limpieza del texto, separamos las palabras y
                # eliminamos posibles repeticiones.
                row_words = list(set(clean_text(row["normalizacion"]).split()))
                # Vemos todas las combinaciones.
                #print(row_words)
                for i in range(len(row_words)):
                    # Aumentamos la cantidad de ocurrencias.
                    if row_words[i] not in word_dict.keys():
                        word_dict[row_words[i]] = 1
                    else:
                        word_dict[row_words[i]] += 1
                    # Aumentamos la cantidad de co-ocurrencias de forma que un
                    # par de palabras se encuentre una única vez.
                    for j in range(i+1,len(row_words)):
                        coocurrence_key1 = "{0}-{1}".format(row_words[i],
                                                            row_words[j])
                        coocurrence_key2 = "{0}-{1}".format(row_words[j],
                                                            row_words[i])
                        if coocurrence_key1 not in word_coocurrence.keys():
                            if coocurrence_key2 not in word_coocurrence.keys():
                                word_coocurrence[coocurrence_key1] = 1
                            else:
                                word_coocurrence[coocurrence_key2] += 1
                        else:
                            word_coocurrence[coocurrence_key1] += 1
            # Añadimos un atributo que indica si es la palabra más mencionada
            # o no.       
            sorted_dict = sorted(word_dict.items(), key = lambda x: x[1],
                                 reverse = True)
            max_freq = sorted_dict[0][1] # Frecuencia máxima.
            sorted_dict[0] = (sorted_dict[0][0], (sorted_dict[0][1], True))
            for i in range(1, len(sorted_dict)):
                if sorted_dict[i][0] == max_freq:
                    sorted_dict[i] = (sorted_dict[i][0], (sorted_dict[i][1],
                                                          True))
                else:
                    sorted_dict[i] = (sorted_dict[i][0], (sorted_dict[i][1],
                                                          False))
            # Ahora, si corresponde, nos quedamos con las 20 palabras más
            # mencionadas.
            if len(sorted_dict) > word_limit:
                word_dict = dict(sorted_dict[:word_limit])
            else:
                word_dict = dict(sorted_dict)
            # Finalmente, procedemos a hacer el JSON.
            word_list = word_dict.keys()
            node_list, link_list = [],[]
            for key, value in word_dict.items():
                #print(value)
                word_hash = {"word": key, "freq": value[0], "maxval": value[1]}
                node_list.append(word_hash)
            for key, value in word_coocurrence.items():
                word1, word2 = key.split('-')
                # Nos quedamos solo con las co-ocurrencias no filtradas.
                if word1 in word_list and word2 in word_list:
                    pair_hash = {"source": word1, "target": word2,
                                 "freq": value}
                    link_list.append(pair_hash)
            # Finalmente, se guarda el hash final en el JSON global.
            graph_json = {"nodes": node_list, "links": link_list}
            data_json[json_key] = graph_json

# Para terminar, se guarda el resultado en la carpeta de origen.
file_name = "valores_word_graph.json"
with open("{}/{}".format(destiny_path, file_name), 'w', encoding='utf-8') as f:
    json.dump(data_json, f, indent = 2, ensure_ascii = False)
