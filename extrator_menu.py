import os
import base64
import json
from bs4 import BeautifulSoup
from bs4.element import Comment
import pandas as pd
import requests
import streamlit as st


def get(obj, key):
    value = ''
    try:
        value = obj[key]
    except:
        print("O Elemento " + key + " nao tinha valor definido!")
    return value


# def add_txt(text):
#     text = str(text)
#     try:
#         text = text.replace('"', "'")
#     except:
#         print('A string estava com formato invalido.')
#     text = '"' + text + '",'
#     return text


# Função by-pass, devido a troca da escrita em arquivo para pandas.to_csv
def add_txt(value):
    return value


def get_download_link(data):

    """Generates a link allowing the data in a given panda dataframe to be downloaded
    in:  dataframe
    out: href string
    """
    csv = data.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()  # some strings <-> bytes conversions necessary here
    return f'<a href="data:file/csv;base64,{b64}" download="menu.csv">Download csv file</a>'


# INICIA O FLUXO PRINCIPAL

st.title('iFood')
st.header('Extração do Menu')
st.subheader('Escolha um restaurante do iFood para fazer a extração do menu')
st.text('')
url_input = st.text_input('URL:')
button = st.button('Extrair')

# Realiza a extração do menu
if button:

    # https://www.ifood.com.br/delivery/uberlandia-mg/subway-martins-martins/506d05f6-cee1-4136-b0e0-45da87bf8552
    restaurant_url = url_input
    html = requests.get(restaurant_url).content
    soup = BeautifulSoup(html, 'html.parser')

    contents = soup.find('script', type='application/json').contents
    content = str(contents[0])
    js = json.loads(content)

    # Aqui comeca a salvar o produto
    restaurant = js['props']['initialState']['restaurant']
    details = restaurant['details']

    restaurant_name = details['name']
    restaurant_id = details['shortId']

    menu = restaurant['menu']

    df_header = {'restaurant_id': [], 'category': [], 'category_2': [], 'category_3': [], 'menu': [],
                 'price': [], 'description': [], 'option': [], 'options': [], 'option_item_price': [],
                 'multiple_choice': [], 'order_limit': [], 'photo': []}
    df = pd.DataFrame(df_header)

    count = 0
    for menu_entry in menu:
        code = menu_entry['code']
        category_name = menu_entry['name']
        itens = menu_entry['itens']

        for item in itens:
            count += 1
            description = item['description']
            detail = ''
            try:
                detail = item['details']
            except:
                print("O Elemento " + description + " nao tinha detalhe de escolha!")

            price = str(item['unitPrice'])
            need_choices = str(item['needChoices'])
            logo_url = get(item, 'logoUrl')

            if len(item['choices']) == 0:

                new_row = {'restaurant_id': add_txt(restaurant_id), 'category': add_txt(category_name),
                           'category_2': '', 'category_3': '', 'menu': add_txt(description),
                           'price': add_txt(price), 'description': add_txt(detail),
                           'option': '', 'options': '',
                           'option_item_price': '', 'multiple_choice': add_txt(need_choices),
                           'order_limit': '', 'photo': logo_url}

                df = df.append(new_row, ignore_index=True)
            else:
                # Cria uma linha para cada opção do item do menu
                for choices in item['choices']:

                    choice_description = choices['name']
                    max_items = choices['max']

                    choices_as_text = str()
                    option_values = str()

                    for choice in choices['garnishItens']:
                        if choices_as_text != '':
                            choices_as_text += ', '
                            option_values += ', '
                        choices_as_text += choice['description']
                        option_values += str(choice['unitPrice'])

                    new_row = {'restaurant_id': add_txt(restaurant_id), 'category': add_txt(category_name),
                               'category_2': '', 'category_3': '', 'menu': add_txt(description),
                               'price': add_txt(price), 'description': add_txt(detail),
                               'option': add_txt(choice_description), 'options': add_txt(choices_as_text),
                               'option_item_price': add_txt(option_values), 'multiple_choice': add_txt(need_choices),
                               'order_limit': add_txt(max_items), 'photo': logo_url}

                    df = df.append(new_row, ignore_index=True)

    st.write(df)
    st.text('Foram extraidos {} itens do menu.'.format(count))

    st.markdown(get_download_link(df), unsafe_allow_html=True)
    st.button('Limpar')
