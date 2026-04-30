import gzip
import os
import pathlib
import time
from concurrent.futures import ThreadPoolExecutor
import requests
import numpy as np

# Enter year, starting doy and number of doys to process
YEAR = 2024
DOYINI = 47
NUMBER = 9

template_url = "https://cddis.nasa.gov/archive/gnss/data/daily/{ano}/brdc/{nomearquivo}"
DESTINO_LOCAL_GZIP_ARQUIVOS = "C:\\Users\\Fernando\\CALIBRA\\GZIP"
nameConvention = "BRDC00IGS_R_{}{:03d}0000_01D_MN.rnx.gz"
global deCompressedFilename


def download_file(url):
    print("Processando a URL: {}".format(url))
    response = requests.get(url)

    if "content-disposition" in response.headers:
        content_disposition = response.headers["content-disposition"]
        filename = content_disposition.split("filename=")[1]
    else:
        filename = os.path.join(DESTINO_LOCAL_GZIP_ARQUIVOS, url.split("/")[-1])

    with open(filename, mode="wb") as file:
        file.write(response.content)
        file.close()
        print(f"=> Salvando localmente o arquivo compactado: {filename}")

        try:
            # compressedfilename = pathlib.Path(localfilename).name
            folderToSaveUncompressed = pathlib.Path(DESTINO_LOCAL_GZIP_ARQUIVOS).parent
            deCompressedFilename = os.path.join(folderToSaveUncompressed, pathlib.Path(filename).stem)
            # print(f"{deCompressedFilename}")
            fp = open(deCompressedFilename, "wb")
            with gzip.open(filename, "rb") as f:
                bindata = f.read()
                fp.write(bindata)
                fp.close()
                print("=> Salvando localmente o arquivo descomprimido: {}".format(deCompressedFilename))
        except:
            print("Erro salvando o arquivo: {}".format(deCompressedFilename))


def formatFilePaths(year, doy):
    rinexEphemeridesFilename = nameConvention.format(year, doy)
    urlx = template_url.format(ano=year, nomearquivo=rinexEphemeridesFilename)
    return urlx


# Formats the DOYLIST and the YEARLIST
DOYLIST = range(DOYINI, DOYINI + NUMBER)
YEARLIST = list(np.ones(len(DOYLIST), dtype=int) * YEAR)

# Cria uma lista com os caminhos completos dos arquivos
urls = list(map(formatFilePaths, YEARLIST, DOYLIST))

# Executa o download dos arquivos
with ThreadPoolExecutor() as executor:
    executor.map(download_file, urls)
