#!/usr/bin/env python3.11
# by RinoGeek

#############################################
# Nom du project: Xtranslate

# Description : La pluspart des documents pdf en 
# informatique sont la pluspart du temp rédigés en 
# anglais. Il est donc difficile aux utilisateurs
# ne comprenant pas l'anglais d'accéder au 
# contenu de ces documents. Ce projet est destiné
# remédier à ce problème particulièrement dans le domaine
# informatique. Il permet de traduire entièrement
# le document pdf sans pour autant affecter les éventuels 
# codes informatiques qui s'y trouvent quelque soit le
# langage de programmation de ce dernier.
 
# Temp de réalisation du project : 3Jrs

# Version : v1.0

# Info : La seconde version du projet sera intégrée à 
# une application web codé avec django.
#############################################
import PyPDF2
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.platypus import Paragraph
from reportlab.lib.styles import getSampleStyleSheet
import io
import requests
from tqdm import tqdm
import json
import os

lang = str(input("Langue : "))

def traduire_texte(texte):
    """
    Traduit le texte donné en utilisant une API externe.

    :param texte: Chaîne à traduire.
    :return: Texte traduit en tant que chaîne.
    """
    cle_api = 'VOTRE CLE API'
    url = "https://api.openai.com/v1/chat/completions"
    entetes = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {cle_api}"
    }

    donnees = {
        "model": "gpt-3.5-turbo",
        "messages": [
          {
            "role": "system",
            "content": """Ne produisez que la traduction de la langue d'origine du texte entré vers la """+lang+""" 
            de la Page actuelle, ne produisez aucun contenu en dehors de cela, ne produisez aucun 
            contenu relatif aux Pages précédente et suivante. Ne donnez pas d'indications à 
            l'utilisateur, par exemple : Voici la traduction de la page actuelle : ."""
          },
          {
            "role": "user",
            "content": """
            Suivez attentivement les instructions. Je veux que vous jouiez le rôle d'un traducteur 
            professionnel de la langue d'origine du texte entré vers la """+lang+""". Je fournirai le 
            texte OCR d'une page de livre, votre tâche est de le traduire de la langue d'origine du 
            texte entré vers la """+lang+""". Dans le texte que je vous donnerai, il pourait y avoir du code 
            informatique écrit dans n'importe quel langage de programmation. Vous traduisez les éventuels 
            commentairs présents dans le code ainsi que les noms de variables tout en maintenant la structure 
            et l'intégrité du code informatique. Veuillez ne sortir que la traduction, ne produisez aucun 
            contenu superflu. Supprimez tout caractère non standard tel que des caractères illisibles. 
            Assurez-vous que le titre, les notes de bas de page et le texte conservent le bon format. 
            Vous pouvez vous-même mettre en page, revenir à la ligne avec \n. Vous serez fourni avec Page 
            précédente : 50 derniers caractères. Page actuelle : caractères OCR de la page actuelle. 
            Page suivante : 50 premiers caractères de la page suivante. Ne produisez que la traduction 
            de la Page actuelle, en vous référant au contenu de la Page précédente et de la Page 
            suivante pour assurer la cohérence, mais ne produisez pas de sortie pour celles-ci. Il pourait y 
            dans le texte des mots dont la traduction pourait affecter la compréhension du texte. Ne traduisez 
            ces mots afin de maintenir la cohérence.
            """ + texte
          }
        ]
    }
#json.dumps(response)
    reponse = requests.post(url, headers=entetes, json=donnees)
    donnees_reponse = json.loads(reponse.text)
    contenu = donnees_reponse["choices"][0]["message"]["content"]

    return contenu

def extraire_texte_de_pdf(chemin_pdf, page_debut, page_fin):
    """
    Extrait le texte des pages spécifiées d'un fichier PDF.

    :param chemin_pdf: Chemin vers le fichier PDF.
    :param page_debut: Numéro de la page de début (index zéro).
    :param page_fin: Numéro de la page de fin (index zéro).
    :return: Produit le texte combiné des contenus des pages précédente, actuelle et suivante.
    """
    with open(chemin_pdf, 'rb') as fichier:
        lecteur = PyPDF2.PdfReader(fichier)
        texte_precedent = ''
        for i, page in enumerate(lecteur.pages[page_debut:page_fin+1], page_debut):
            texte_actuel = page.extract_text()
            texte_suivant = lecteur.pages[i + 1].extract_text()[:50] if i < len(lecteur.pages) - 1 else ''
            texte_combine = f"Page précédente : {texte_precedent[-50:]}\nPage actuelle : {texte_actuel}\nPage suivante : {texte_suivant}"
            texte_precedent = texte_actuel
            yield texte_combine

def creer_pdf_avec_texte(texte, nom_fichier, chemin_police='./police.ttf'):
    """
    Crée un fichier PDF avec le texte donné.

    :param texte: Texte à inclure dans le PDF.
    :param nom_fichier: Nom du fichier PDF de sortie.
    :param chemin_police: Chemin vers le fichier de police TTF.
    """
    tampon = io.BytesIO()
    can = canvas.Canvas(tampon, pagesize=letter)
    pdfmetrics.registerFont(TTFont('PoliceChinoise', chemin_police))
    texte = texte.replace('\n', '<br/>')

    styles = getSampleStyleSheet()
    style = styles['Normal']
    style.fontName = 'PoliceChinoise'
    style.fontSize = 12
    style.leading = 15

    para = Paragraph(texte, style=style)
    largeur_texte = letter[0] - 2 * inch
    hauteur_texte = letter[1] - 2 * inch

    largeur, hauteur = para.wrap(largeur_texte, hauteur_texte)
    para.drawOn(can, inch, letter[1] - inch - hauteur)

    can.save()
    tampon.seek(0)
    with open(nom_fichier, 'wb') as fichier:
        fichier.write(tampon.getvalue())

def fusionner_pdfs(liste_pdfs, nom_fichier_sortie):
    """
    Fusionne plusieurs fichiers PDF en un seul.

    :param liste_pdfs: Liste des chemins des fichiers PDF à fusionner.
    :param nom_fichier_sortie: Chemin du fichier PDF fusionné de sortie.
    """
    redacteur_pdf = PyPDF2.PdfWriter()
    for pdf in liste_pdfs:
        lecteur_pdf = PyPDF2.PdfReader(pdf)
        for page in lecteur_pdf.pages:
            redacteur_pdf.add_page(page)

    with open(nom_fichier_sortie, 'wb') as sortie:
        redacteur_pdf.write(sortie)


def retraduire_et_fusionner_pages(numero_pages, pdf_source, pdf_sortie, chemin_police='./police.ttf'):
    """
    Retraduit les pages spécifiées et les fusionne dans un nouveau PDF.

    :param numero_pages: Liste des numéros de page à retraduire.
    :param pdf_source: Chemin vers le fichier PDF source.
    :param pdf_sortie: Chemin du fichier PDF fusionné de sortie.
    :param chemin_police: Chemin vers le fichier de police .ttf prenant en charge les caractères chinois.
    """
    pdfs_traduits = []
    lecteur = PyPDF2.PdfReader(pdf_source)

    for numero_page in tqdm(numero_pages):
        indice_page = numero_page - 1  # Convertir le numéro de page à l'index 0
        texte_page = lecteur.pages[indice_page].extract_text()
        texte_traduit = traduire_texte(texte_page)
        nom_fichier_pdf = f'./pages/page_traduite_{numero_page}.pdf'
        creer_pdf_avec_texte(texte_traduit, nom_fichier_pdf, chemin_police)
        pdfs_traduits.append(nom_fichier_pdf)

    fusionner_pdfs(pdfs_traduits, pdf_sortie)

def nom_pdf():
    nom = str(input("nom pdf : "))
    return nom

def principal():
    """
    Fonction principale pour exécuter le processus de traduction et de création de PDF.
    """
    pdf_source = nom_pdf()
    pdfs_traduits = []
    page_debut = 0
    page_fin = len(PyPDF2.PdfReader(pdf_source).pages) - 1

    for i, texte_combine in enumerate(tqdm(extraire_texte_de_pdf(pdf_source, page_debut, page_fin)), page_debut):
        texte_traduit = traduire_texte(texte_combine)
        nom_fichier_pdf = f'./pages/page_traduite_{i+1}.pdf'
        creer_pdf_avec_texte(texte_traduit, nom_fichier_pdf, chemin_police='./police.ttf')
        pdfs_traduits.append(nom_fichier_pdf)

    fusionner_pdfs(pdfs_traduits, 'document_final_traduit.pdf')

if __name__ == '__main__':
    if not os.path.exists('pages'):
        os.makedirs('pages')

    principal()
    # retraduire_et_fusionner_pages([5, 6], 'source.pdf', 'document_retraduit.pdf')
