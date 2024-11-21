# src/utils.py

import pandas as pd
from langdetect import detect
from googletrans import Translator

def load_qa_pairs(filepath):
    df = pd.read_excel(filepath)
    qa_dict = dict(zip(df['Question'], df['Answer']))
    return qa_dict

def detect_language(text):
    try:
        return detect(text)
    except:
        return 'tr'  # Varsayılan dil Türkçe

translator = Translator()

def translate_text(text, dest_language):
    try:
        translation = translator.translate(text, dest=dest_language)
        return translation.text
    except Exception as e:
        print(f"Çeviri hatası: {e}")
        return text