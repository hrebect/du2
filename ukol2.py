import json, sys, math, statistics
from pyproj import CRS, Transformer


#priprava prevodu mezi wgs a jtsk
crs_wgs = CRS.from_epsg(4326)
crs_jtsk = CRS.from_epsg(5514)
wgs2jtsk= Transformer.from_crs(crs_wgs,crs_jtsk)



def verejne_kont(kontejnery_data):#vyber souradnic  verejnych kontejneru
    kontejnery = []
    container_features = kontejnery_data["features"]

    for container in container_features: #projde vsechny kontejnery
        properties = container["properties"]
        pristup = properties["PRISTUP"]
     
        if pristup == 'volně': #souradnice volnych kontejneru ulozi do listu 'kontejnery'
            coordinates = container["geometry"]['coordinates']
            kontejnery.append(coordinates)
    return kontejnery

def adresy(adresy_data):
    adresy_jmena = []
    adresy_coord =[]
    adresy_features = adresy_data["features"] 

    for buliding in adresy_features:  #projede vsechny budovy 
        properties = buliding["properties"]
        coordinates = buliding["geometry"]['coordinates']
        address = str(properties["addr:street"] + ' ' + properties["addr:housenumber"])
        y,x = wgs2jtsk.transform(coordinates[1],coordinates[0]) #prevod souradnic
        coord_build = [y,x] #ulozeni souradnic jako list, aby byly stejný typ jako souradnice kontejneru
        adresy_jmena.append(address)
        adresy_coord.append(coord_build)

    return adresy_jmena, adresy_coord


def vzdalenosti(adresy_jmena, adresy_coord, kontejnery):
    list_minim = [] #list minim
        
    for build_coord in adresy_coord:
        minimum = 10001 #horní hranice minima, podle zadani nepracujeme se vzdalenostmi nad 10 km
        for cont_coord in kontejnery: #vypocet vzdalenosti od kazdeho kontejneru
            x_vzdalenost = build_coord[1]-cont_coord[1]
            y_vzdalenost = build_coord[0]-cont_coord[0]
            vzdalenost = math.sqrt(x_vzdalenost * x_vzdalenost + y_vzdalenost *y_vzdalenost) #phytagoras
            if vzdalenost < minimum: #hledani minima pro adresu v ramci kontejneru
                minimum = vzdalenost
            
        if minimum > 10000: #ukonceni programu, kdyz je u jednoho konejnery minimum vice nez 10 km
            sys.exit('CHYBA, u jedné adresy je nejbližší kontejner vzdálen více než 10 km')  
        list_minim.append(minimum) #list vsech minim
        max_minimum = max(list_minim) 
        max_pos = list_minim.index(max(list_minim))
        max_adresa = adresy_jmena[max_pos]
    return list_minim, max_minimum, max_adresa

#nacteni souboru
try:
    with open('adresy.geojson',encoding='utf-8') as f:
        adresy_data = json.load(f)
except FileNotFoundError: #ukonceni programu, kdyz soubor nebude nalezen
    sys.exit('Soubor s adresami nenalezen')
except PermissionError:
    sys.exit('Program nemá oprávnění číst soubor s adresami')

try:
    with open('kontejnery.geojson',encoding='utf-8') as e:   
        kontejnery_data = json.load(e)
except FileNotFoundError: #ukonceni programu, kdyz soubor nebude nalezen
    sys.exit('Soubor s kontejnery nenalezen')
except PermissionError:
    sys.exit('Program nemá oprávnění číst soubor s kontejnery')

#spusteni funkci a ulozeni do promennych
kontejnery=verejne_kont(kontejnery_data)
adresy_jmena, adresy_coord=adresy(adresy_data)
list_minim, max_minimum, max_adresa = vzdalenosti(adresy_jmena, adresy_coord, kontejnery)

prumer = statistics.mean(list_minim)
median = statistics.median(list_minim)

print(f'Načteno {len(adresy_jmena)} adresních bodů')
print(f'Načteno {len(kontejnery)} kontejnerů\n')
print(f'Pruměrná vzdálenost ke kontejneru je {prumer:.0f} m.')
print(f'Nejdále ke kontejneru je z adresy {max_adresa} a to {max_minimum:.0f} m.')
print(f'Medián vzdáleností je {median:.0f} m.') 