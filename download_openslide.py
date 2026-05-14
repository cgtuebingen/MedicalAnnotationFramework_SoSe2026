"""
This file is there to download the latest version of openslide from their website.
Only works for windows currently
"""
import os
import platform
import requests
from bs4 import BeautifulSoup
import zipfile
import tarfile
import shutil

# Check for Openslide Installation
continueInstalling = True
if(os.path.isdir("openslide")):
    userAnswer = input("There is already an Openslide installation. Do you want to continue and overwrite it? [Y/N] ")
    if not (userAnswer.lower() in ["y","yes", "j", "ja"]):
        continueInstalling = False


if continueInstalling:
    # Determine OS to choose openslide version
    operatingSystem:str = ""
    operatingSystemInformation = platform.uname()
    if operatingSystemInformation.system == "Windows":
        operatingSystem = "windows-x64" if "64" in operatingSystemInformation.machine else "win32"
    elif operatingSystemInformation.system == "Linux":
        if "x86_64" in operatingSystemInformation.machine: 
            operatingSystem = "linux-x86_64"
        elif "aarch64" in operatingSystemInformation.machine:
            operatingSystem = "linux-aarch64"
    elif operatingSystemInformation.system == "Darwin":
        operatingSystem = "macos"
    if operatingSystem == "":
        raise Exception("Can't determin Operating System, therefore no openslide installation is possible")

    # Download Openslide
    openslide_url = "https://openslide.org/download/"

    response = requests.get(openslide_url)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')

        download_link = None
        for link in soup.find_all('a'):
            if link.get('href') and operatingSystem in link.get('href'):
                download_link = link.get('href')
                break

        if download_link:
            filename = os.path.basename(download_link)

            response = requests.get(download_link)
            if response.status_code == 200:
                with open(filename, 'wb') as file:
                    file.write(response.content)

                ending:str = filename.split(".")[-1]
                if ending == "zip":
                    with zipfile.ZipFile(filename) as zip_ref:
                        zip_ref.extractall("tmp_unpackfolder")
                elif ending == "xz":
                    with tarfile.TarFile.xzopen(filename) as tar_ref:
                        tar_ref.extractall("tmp_unpackfolder")
                else:
                    raise Exception("Unknown compression format, can't unpack")

                os.remove(filename)
                if(os.path.isdir("openslide")): shutil.rmtree("openslide", ignore_errors=True) # Remove existing installation
                extractedFolder =  os.listdir("tmp_unpackfolder")[0]
                os.rename("tmp_unpackfolder/"+extractedFolder, "openslide")
                shutil.rmtree("tmp_unpackfolder", ignore_errors=True)
                print(f"Openslide has been successfully downloaded.")
            else:
                print("Failed to download OpenSlide library.")
        else:
            print("Download link not found on the page.")
    else:
        print("Failed to access the OpenSlide download page.")