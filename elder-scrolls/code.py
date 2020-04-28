
try:
    import requests
    from bs4 import BeautifulSoup as bsoup
except ImportError:
    import os
    os.system('pip install --user requests bs4 lxml')
    import requests
    from bs4 import BeautifulSoup as bsoup


base_url = "https://skyrimcommands.com"
items = []


def parse_item(row):
    a = row.find("a")
    item_name = a.get_text()
    row_dict = {"item": item_name, "value": 0, "weight": 0.}

    try:

        link = "".join([base_url, a.attrs['href']])
    except AttributeError:
        pass
    else:
        resp = requests.get(link)

        soup_item = bsoup(resp.text, 'lxml')
        rows = soup_item.find_all("tr")
        for rowx in rows:
            cols = rowx.find_all("td")




def parse_items(html_resp):
    soup = bsoup(html_resp.text, 'lxml')
    rows = soup.find_all("tr")
    for row in rows[1:]:
        cols = row.find_all('td')
        print(cols[0])
        parse_item(cols[0])


def get_prices():

    n_pages = 44
    for pg in range(1, n_pages+1):
        if pg == 1:
            url = "https://skyrimcommands.com/items"
        else:
            url = f"https://skyrimcommands.com/items/{pg}"
        resp = requests.get(url)
        parse_items(resp)

get_prices()

