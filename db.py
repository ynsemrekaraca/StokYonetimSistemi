import mysql.connector
from getpass import getpass

MYSQL_SIFRE = getpass("MySQL sifreni gir: ")

def veritabani_baglantisi():
    baglanti = mysql.connector.connect(
        host="localhost",
        user="root",
        password=MYSQL_SIFRE,
        database="stok_yonetim"
    )

    return baglanti