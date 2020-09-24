# VOLBY SCRAPER PROJECT
# Autor Tomas S

from bs4 import BeautifulSoup as bs
import requests
import codecs


def get_ids_cities(soup):
    cities = []
    links = []
    city_db = {}

    cityA = soup.find_all(headers="t1sa1 t1sb2")
    for i in cityA:
        cities.append(i.string)
    cityB = soup.find_all(headers="t2sa1 t2sb2")
    for i in cityB:
        cities.append(i.string)
    cityC = soup.find_all(headers="t3sa1 t3sb2")
    for i in cityC:
        cities.append(i.string)

    for i in soup.find_all(["a"]):
        if "obec" in str(i):
            if not str(i.string) == "X":
                links.append(i.string)

    for key in cities:
        for value in links:
            # ostrava has a link and causes an issue
            exceptions = {"Ostrava", "Opava", "Ústí nad Labem", "Plzeň"}
            if not value in exceptions:
                city_db[key] = value
                links.remove(value)
                break
    return city_db


def access_and_extract(city_db):
    urls = []
    strany = []
    master = []
    obec = city_db.keys()
    kody = city_db.values()

    # this will generate the individual links
    for i in city_db:
        urls.append("https://volby.cz/pls/ps2017nss/ps311?xjazyk=CZ&xkraj=8&xobec=" + city_db[i])

    # this will get the obec names
    for x, y, z in zip(urls, obec, kody):
        master.append(y)
        master.append(z)
        r = requests.get(x)
        soup = bs(r.text, "html.parser")
        tables = soup.find_all("table")

        # this will get the overall voter numbers etc.
        intro_table = soup.find("table")
        for k in intro_table:
            for l in k:
                tds = soup.find_all("td")
                voters = tds[3].contents[0]
                envelops = tds[4].contents[0]
                valid_votes = tds[7].contents[0]
        master.append(voters)
        master.append(envelops)
        master.append(valid_votes)

        # this will get the votes and political parties
        for j in range(1, len(tables)):
            rows = tables[j].find_all("tr")
            for i in range(2, len(rows)):
                cells = rows[i].find_all("td")
                strana = cells[1].contents[0]
                hlasy = cells[2].contents[0]
                strany.append(strana) if strana not in strany else strany
                master.append(hlasy)
    return master, strany


def format_and_write(master, strany):
    # this will format and write data into csv file
    file_name = str(input("Pojmenuj svůj soubor.")) + ".csv"
    file = codecs.open(file_name, "w+", "utf-8")
    file.write("location;code;registered;envelopes;valid;" + (";".join(map(str, strany))) + "\n")
    n = m = 0
    while m < len(master):
        m = m + 29
        file.write(";".join(master[n:m]) + "\n")
        n = m
    file.close


def vyber_okres():
    nabidka_kraju = """1 - Praha a Středočeský kraj
                  \n2 - Jihočeský a Plzeňský kraj
                  \n3 - Karlovarský a Ústecký kraj
                  \n4 - Liberecký a Královéhradecký
                  \n5 - Pardubciký a Kraj Vysočina
                  \n6 - Jihomoravský a Olomoucký kraj
                  \n7 - Zlínský a Moravskoslezský kraj"""
    print(nabidka_kraju)
    while True:
        kr = input("Vybert ze seznamu kraj z kterého chcete exportovat výsledky")
        if not (kr.isdecimal()) or (0 == int(kr)) or (int(kr) > 7):
            print("Zadej správnou volbu")
            continue
        else:
            break
    kr = int(kr)
    kody = []
    obce = []
    path = "https://volby.cz/pls/ps2017nss/ps3?xjazyk=CZ"
    r = requests.get(path)
    soup = bs(r.text, "html.parser")
    tables_full = []
    # looks only at the tables in the selection
    tables = soup.find_all("table")[((kr - 1) * 2):(kr * 2)]
    for j in range(0, len(tables)):
        rows = tables[j].find_all("tr")
        for i in range(0, len(rows)):
            cells = rows[i].find_all("td")
            for m in cells[1:2]:
                if m not in obce:
                    obce.append(m.contents)
                for k in range(0, len(cells)):
                    kod = cells[k].find_all("a")
                    for l in kod:
                        l = str(l)
                        if "xnumnuts=" in l:
                            start = l.find("xnumnuts=") + 9
                            end = l.find(">", start) - 1
                            l = l[start:end]
                            if l not in kody:
                                kody.append(l)

    flat_obce = [item for sublist in obce for item in sublist]
    # feature zahranici coming soon
    if "Zahraničí" in flat_obce:
        flat_obce.remove("Zahraničí")
    oboje = dict(zip(flat_obce, kody))
    counter = 1
    for x in oboje.keys():
        print(str(counter) + " - " + x)
        counter += 1
    while True:
        vo = input("Vyber kraj.")
        if not (vo.isdecimal()) or (int(vo) == 0) or (int(vo) >= counter):
            print("Zadej správnou volbu.")
            continue
        else:
            break
    vo = int(vo)
    klic = oboje.get(flat_obce[vo - 1])
    return klic


def main():
    klic = vyber_okres()
    path = "https://volby.cz/pls/ps2017nss/ps32?xjazyk=CZ&xkraj=8&xnumnuts=" + klic
    r = requests.get(path)
    soup = bs(r.text, "html.parser")
    city_db = get_ids_cities(soup)
    master, strany = access_and_extract(city_db)
    format_and_write(master, strany)


if __name__ == "__main__":
    main()