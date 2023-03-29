# This is a sample Python script.
import csv
import unicodedata
import re
from typing import List, AnyStr, Dict

RANK_MIN = 1

RANK_MAX = 10

""" 
Función que sirve para convertir un texto a su versión slug,
esto hace más facil el manejo del producto como una llave, ya que
esta función reemplaza los espacios en blanco por "-", remueve las tildes, dieresis.

Esta función la saque del código del framework django.
"""


def slugify(value, allow_unicode=False):
    """
    Convert to ASCII if 'allow_unicode' is False. Convert spaces to hyphens.
    Remove characters that aren't alphanumerics, underscores, or hyphens.
    Convert to lowercase. Also strip leading and trailing whitespace.
    """
    value = str(value)
    if allow_unicode:
        value = unicodedata.normalize('NFKC', value)
    else:
        value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
    value = re.sub(r'[^\w\s-]', '', value.lower()).strip()
    return re.sub(r'[-\s]+', '-', value)


def read_csv():
    """
    Función que lee el archivo datos.csv, y extrae la información en una variable de tipo lista
    """
    file = open('./datos.csv', 'r', encoding='utf-8-sig')
    data = list(csv.reader(file, delimiter=';'))
    file.close()
    return data


def calculate_total_ranking(data: List[List[AnyStr]], dic_data: Dict):
    """
    Esta función se encarga de calcular el ranking total por producto,
    donde se calcula la cantidad de respuestas por producto, y el peso de la respuesta segun la posición,
    luego, esto lo sumamos, y dividamos sobre 10 (cantidad de respuestas), y tenemos el ranking total

    :param data Lista que contiene otras listas con la data de los productos.
    :param dic_data Dict que contiene los productos con la cantidad de respuestas por peso (inicialmente este valor estara en 0)
    :return: Devuelve "dic_data" con los calculos de los ranking totales por producto
    """

    product_names_index = {}

    """
    Este iterador, se encarga de crear un diccionario donde
    el key es el index de la posición del producto, y el value es el nombre del producto en tipo slug,
    esto, me sirve para realizar los calculos del ranking total, de una manera mas rapida, ya que al
    iterar la data del csv solo con saber la posición (index), ya podria saber nombre del producto
    sin hacer algun "filter" o función que encuentre en una lista ese nombre, la idea es tener una buena perforamance
    si en algun momento esos datos se vuelven millones de datos. 
    """
    for index, key in enumerate(dic_data.keys()):
        product_names_index[dic_data[key]['index']] = key

    """
    Aqui iteramos valor por valor la data del csv, esta data es una lista y en esta lista hay mas listas
    con los valores por columna, donde cada columna equivale a un producto, 
    por ejemplo si es la columna 0, es el producto 'armarios-para-ropa-y-vestidores'
    y como ya tenemos un diccionario con esta equivalencia dentro de la variable "product_names_index",
    solo tenemos que referencias de esta manera "product_names_index[index]"
    Ahora dic_data tiene una estructura de esta manera:
    
    {'armarios-para-ropa-y-vestidores':
     {'index': 0, 'ranks': {'1': 5, '2': 11, '3': 6, '4': 10, '5': 9, '6': 7, '7': 3, '8': 3, '9': 1, '10': 3},
      'total': 26.6}}
      
    Como vemos en esta estructura, tenemos la llave que es el nombre del producto en tipo slug, y otro dict donde
    tenemos el index de la posición de ese producto, y los pesos (ranks) que al principio estaran en 0
    Aqui vemos, para que realmente nos serviria el "product_names_index", ya que teniendo la llave del producto,
    podemos referenciar segun el nombre del producto y realizar los calculos, esto, sin hacer alguna operación para
    buscar en que "key" se encuentra el producto, asi, mejoramos la performance. 
    """
    for product_values in data:
        for index_product, value in enumerate(product_values):
            product_name = product_names_index[
                index_product]  # buscamos el nombre del producto segun el index del valor a calcular
            actual_value = dic_data[product_name]['ranks'][
                value]  # obtenemos el valor del ranking actual del producto segun el peso
            dic_data[product_name]['ranks'][value] = actual_value + 1  # Aumentamos en 1 el peso de la respuesta

    """
    Como ya tenemos la cantidad de respuestas por peso de cada producto,
    ahora, tenemos que calcular el ranking total, donde se aplica la formula 
    ranking_total = (x_1w_1 + x_2w_2 + x_3w_3 ... + x_nw_n) / total_de_respuestas
    """
    for key in dic_data.keys():
        total = 0  # por cada producto a iterar, comenzamos con un total de 0
        for key_rank in dic_data[key]['ranks'].keys():  # iteramos todos los pesos de cada producto
            value_key_rank = dic_data[key]['ranks'][key_rank]  # cantidad de respuestas por peso
            weight = RANK_MAX - int(
                key_rank) - 1  # Aqui ponemos el valor real del peso, donde 1 pesa 10, 2 pesa 9, 3 pesa 8, etc
            total = total + (
                    value_key_rank * weight)  # sumamos el total actual mas las respuestas por peso * peso real
        dic_data[key][
            'total'] = total / RANK_MAX  # dividimos la suma de todas las respuestas sobre numero de respuestas (10)
    return dic_data


def build_product_rankings(csv_data: List):
    """
    :param csv_data: data de tipo lista que contiene los valores por cada producto
    :return: lista de productos ordenadas de mayor a menor por el ranking total segun las respuestas y el peso de cada respuesta
    """
    slugify_headers = list(map(lambda header: slugify(header), csv_data[0]))  # Convertimos los textos a un tipo slug
    data: List[int] = csv_data[1: -1]  # quitamos las cabeceras de la data, para que solo tenga los valores
    dict_headers = {}
    for index, header in enumerate(slugify_headers):  # iteramos las cabeceras, y las enumeramos para obtener su index
        """
        Le creamos esta estructura a cada producto, donde la llave es el nombre del producto de tipo slug
        """
        dict_headers[header] = {'index': index, 'ranks': {}, 'total': 0}

        """
        Aqui, creamos cada peso como un diccionario en cada producto, donde el peso es la llave del diccionario,
        y su valor inicial sera 0, ya que aun no se hace los calculos 
        """
        for n in range(RANK_MIN, RANK_MAX + 1):
            rank_string = '{}'.format(n)
            dict_headers[header]['ranks'][rank_string] = 0
    dict_headers_with_total = calculate_total_ranking(data, dict_headers)  # calculamos el ranking total
    product_with_total = [{'product': key, 'total': dict_headers_with_total[key]['total']} for key in
                          dict_headers_with_total.keys()]  # iteramos para solo obtener el producto y su total
    product_with_total.sort(key=lambda x: x['total'], reverse=True)  # ordenamos de mayor a menor
    return product_with_total


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    csv_data = read_csv()
    build_product_rankings(csv_data)
