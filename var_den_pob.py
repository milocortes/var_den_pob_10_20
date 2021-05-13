# Cargamos la librerías
import geopandas as gpd
import pandas as pd
from shapely.geometry import Polygon, Point
import matplotlib.pyplot as plt
from tqdm import tqdm
import shapely
import shapely.ops as ops
from functools import partial
import pyproj
import warnings
import os

## Nos cambiamos al directorio /datos
os.chdir("datos")

## Desactivamos los future warnings
warnings.simplefilter(action='ignore', category=Warning)
### Cargamos geojson de municipios de la zona metropolitana del valle de méxico
municipios= gpd.read_file("muni_metro.geojson")
### Cargamos geojson de las agebs de la CDMX
agebs_cdmx = gpd.read_file('09agebs.geojson')
### Cargamos datos del censo a nivel ageb del censo de 2010
censo_ageb = pd.read_csv("resultados_ageb_urbana_09_cpv2010.csv.gz", compression='gzip')
### Cargamos datos del censo a nivel ageb del censo de 2020
censo_ageb_2020 = pd.read_csv("resageburb_0920.csv.gz", compression='gzip')

### Generamos la cvegeo de la ageb en los datos del censo de 2010 y hacemos merge con la geometría
censo_ageb["cvegeo"]= censo_ageb["entidad"].apply("{0:0=2d}".format)+censo_ageb["mun"].apply("{0:0=3d}".format)+censo_ageb["loc"].apply("{0:0=4d}".format)+censo_ageb["ageb"]
censo_ageb =censo_ageb[censo_ageb.mza==0]
agebs_cdmx_2010=pd.merge(left=agebs_cdmx, right=censo_ageb, how='left', left_on='cvegeo', right_on='cvegeo')

### Generamos la cvegeo de la ageb en los datos del censo de 2020 y hacemos merge con la geometría
censo_ageb_2020["cvegeo"]= censo_ageb_2020["ENTIDAD"].apply("{0:0=2d}".format)+censo_ageb_2020["MUN"].apply("{0:0=3d}".format)+censo_ageb_2020["LOC"].apply("{0:0=4d}".format)+censo_ageb_2020["AGEB"]
censo_ageb_2020 =censo_ageb_2020[censo_ageb_2020.MZA==0]
agebs_cdmx_2020=pd.merge(left=agebs_cdmx, right=censo_ageb_2020, how='left', left_on='cvegeo', right_on='cvegeo')

### Haceos merge con los datos de los censos de 2010 y 2020 y nos quedamos con la población total
cambio_densidad =pd.merge(left= agebs_cdmx_2010[["cvegeo","cve_mun","geometry","pobtot"]], right=agebs_cdmx_2020[["cvegeo","POBTOT"]], how='left', left_on='cvegeo', right_on='cvegeo')

### Definimos una función para calcular el área de la ageb
def obten_area(poligono):
    geom_area = ops.transform(
        partial(
            pyproj.transform,
            pyproj.Proj(init='EPSG:4326'),
            pyproj.Proj(
                proj='aea',
                lat_1=poligono.bounds[1],
                lat_2=poligono.bounds[3])),
        poligono)

    return geom_area.area/1000000

### Calculamos el áreb de cada ageb
cambio_densidad["area"]=cambio_densidad["geometry"].apply(lambda x:  obten_area(Polygon(x)))

### Calculamos la densidad poblacional para la población en 2010 y 2020
cambio_densidad["densidad_2010"]=cambio_densidad["pobtot"]/cambio_densidad['area']
cambio_densidad["densidad_2020"]=cambio_densidad["POBTOT"]/cambio_densidad['area']
cambio_densidad.loc[cambio_densidad.densidad_2010==0,"densidad_2010"]=1
cambio_densidad.loc[cambio_densidad.densidad_2020==0,"densidad_2020"]=1
### Calculamos la variación porcentual
cambio_densidad["var_10_20"]= ((cambio_densidad["densidad_2020"]/cambio_densidad["densidad_2010"])-1)*100

### Removemos aquellas agebs que tuvieron una variación porcentual mayor a 100 y graficamos
cambio_densidad["var_10_20_imp"]=cambio_densidad["var_10_20"]
cambio_densidad.loc[cambio_densidad["var_10_20"]>100,"var_10_20_imp"]=0
cambio_densidad.plot(column='var_10_20_imp',ax=municipios[municipios.CVE_ENT=="09"].boundary.plot(figsize=(15, 15),color ='red'), legend=True)
plt.show()
