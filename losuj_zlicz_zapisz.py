# -*- coding: utf-8 -*-
"""
Created on Tue Dec  4 20:43:41 2018

@author: Adi
"""

#%% ### BIBLIOTEKI



import os
from osgeo import ogr
from osgeo import osr
import random
import pandas as pd
import datetime
import numpy as np

#%%


#%% ### ŚCIEŻKI i PLIKI




os.getcwd()
sciezka1="C:\\Users\\Adi\\Desktop\Praca magisterska\\TESTY" #pliki wynikowe, punkty losowe, granica próbkowania
sciezka2=sciezka1 + "\\Bufory" #bufory
os.chdir(sciezka1)
os.listdir(sciezka2)

lista_plikow=[x for x in os.listdir(sciezka2) if x.endswith('.shp')]

lista_sciezek=[]

for i in range(len(lista_plikow)):
    lista_sciezek.append(sciezka2+'\\'+lista_plikow[i])


#%%
    
    
#%% ### FUNKCJA PRÓBKUJĄCO - ZLICZAJĄCA
    
# Wariant II - nie wymaga zagregowanych geometrii - dopuszcza nakładające się bufory


def losuj_zlicz_2(liczba_losowan, liczba_punktow,  warstwa_zasiegu="powiat_nt.shp"): 
    """
    Funkcja generuje zadaną ilosć punktów o rozkładzie losowym, podaną ilosć razy, na wybranym obszarze. 
    Po każdorazowym wygenerowaniu kompletnego rozkładu - zlicza ilosć wystąpień punktów we wskazanych strefach buforowych.  
    """
    time1=datetime.datetime.now().time() #sprawdzenie ile czasu zajmie wykonanie funkcji...
    
    warstwa_zasiegu = ogr.Open(warstwa_zasiegu,0)
    wzasiegu_layr = warstwa_zasiegu.GetLayer()
    
    proj = osr.SpatialReference()
    proj.ImportFromEPSG(2180)
    driver = ogr.GetDriverByName("ESRI Shapefile")
        
    losowe = driver.CreateDataSource("losowe.shp")
    losowe_layr= losowe.CreateLayer("layer", proj,ogr.wkbPoint)
    
    minX, maxX, minY, maxY = wzasiegu_layr.GetExtent()
    print(minX, maxX, minY, maxY)

    wspolne=[] # wspólne punkty w poszczególnych przejściach
    [wspolne.append([]) for i in range(len(lista_plikow))]
    for j in range(liczba_losowan):
        i=1
        while i<=liczba_punktow:
            try:
                przeciecie = driver.CreateDataSource("punkty_przeciecie.shp") #warstwa przechowująca intersect (dla warstw: punkt i powiat)
                przeciecie_layr= przeciecie.CreateLayer("layer", proj,ogr.wkbPoint)    
                punkt = driver.CreateDataSource("punkt.shp")
                punkt_layr= punkt.CreateLayer("layer", proj,ogr.wkbPoint)
                feature = ogr.Feature(punkt_layr.GetLayerDefn())
                point = ogr.Geometry(ogr.wkbPoint)
                a,b=(random.uniform(minX, maxX), random.uniform(minY, maxY))
                point.AddPoint(a,b)
                feature.SetGeometry(point) 
                punkt_layr.CreateFeature(feature)
                feature=None
                punkt_layr.Intersection(wzasiegu_layr, przeciecie_layr)
                
                if  przeciecie_layr.GetFeatureCount() > 0 or przeciecie_layr == None:
                    feature2 = ogr.Feature(losowe_layr.GetLayerDefn())
                    feature2.SetGeometry(point)
                    losowe_layr.CreateFeature(feature2)
                    punkt.DeleteLayer(0)
                    przeciecie=None
                    i=i+1
                else:
                    punkt.DeleteLayer(0)
                    przeciecie=None
            except AttributeError:
                print('Wystapil rzadko powtarzajacy sie, ale na razie blizej nieokreslony problem')
                punkt.DeleteLayer(0)
                przeciecie=None

        print("wygenerowano losowy rozkład punktów po raz:",j+1)

        for k in range(len(lista_plikow)):
            tymczasowy= driver.CreateDataSource("punkty_tymczasowy.shp")
            tymczasowy_layr= tymczasowy.CreateLayer("layer", proj,ogr.wkbPoint)
            bufor = ogr.Open(lista_sciezek[k],0)
            bufor_layr = bufor.GetLayer()
            losowe_layr.Intersection(bufor_layr, tymczasowy_layr)
            tymczasowy_fea = [tymczasowy_layr.GetFeature(i) for i in range(len(tymczasowy_layr))]
            tymczasowy_geom=[tymczasowy_fea[i].geometry() for i in range(len(tymczasowy_fea))]
            tymczasowy_geom_wkt = [tymczasowy_geom[i].ExportToWkt() for i in range(len(tymczasowy_geom))]
            liczba_oryginalnych = len(np.unique(tymczasowy_geom_wkt))
            wspolne[k].append(liczba_oryginalnych)
            tymczasowy=None 
            bufor = None 
        punkt=None
        losowe=None
        losowe = driver.CreateDataSource("losowe.shp")
        losowe_layr= losowe.CreateLayer("layer", proj,ogr.wkbPoint)
    wzasiegu_layr = None
    time2=datetime.datetime.now().time()
    print("Czas działania funkcji wyniósł: ",time2.hour-time1.hour,"godzin +",time2.minute-time1.minute," minut + ",time2.second-time1.second, "sekund")
    return dict(zip(lista_plikow,wspolne))

#%%

#%%

# Aby przetestować funkcję na dowolnych danych należy:

#1. Wskazać katalog przechowujący granicę próbkowania (zmienna: sciezka1) 
#2. Wskazać katalog zawierający bufory, w obrębie których będą zliczane punkty losowe (sciezka2)
#3. Wywołać funkcję losuj_zlicz_2 podając jako argumenty: 
    ## liczba_losowan - okresla ilosć różniących się od siebie rozkładów punktów losowych
    ## liczba_punktow - ilosc punktów losowych
    ## warstwa_zasiegu - granica próbkowania - domyslnie powiat_nt
    

slownik=losuj_zlicz_2(10,378)


## KONWERSJA DO DATA FRAME + ZAPIS DO PLIKU 


df = pd.DataFrame(slownik)
df.to_excel('bufory_statystyki.xlsx', sheet_name='arkusz_z_wynikami') #zapis danych do pliku


#%%

