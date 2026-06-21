#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DEUTSCH MEISTER PRO - Markaziy Konfiguratsiya
To'liq yangilangan versiya
"""

import os
import logging

# ==================== LOGGING ====================
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ==================== ENVIRONMENT ====================
TOKEN = os.environ.get("BOT_TOKEN", "")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
ADMIN_IDS = [int(x.strip()) for x in os.environ.get("ADMIN_IDS", "").split(",") if x.strip()]
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_WHISPER_URL = "https://api.groq.com/openai/v1/audio/transcriptions"
WHISPER_MODEL = "whisper-large-v3"
DEFAULT_AI_MODEL = "llama3-70b-8192"
DATABASE_PATH = os.environ.get("DATABASE_PATH", "deutsch_meister.db")

# ==================== TTS VOICES (Edge TTS) ====================
TTS_VOICES = {
    "female": "de-DE-KatjaNeural",
    "male": "de-DE-ConradNeural",
}

# ==================== XP SYSTEM ====================
XP_REWARDS = {
    "flashcard_correct": 10,
    "flashcard_complete": 50,
    "ai_conversation": 50,
    "mistake_corrected": 20,
    "pomodoro_25min": 30,
    "level_up_bonus": 100,
    "daily_mission_complete": 100,
    "voice_practice": 25,
    "roleplay_complete": 40,
    "quiz_perfect": 75,
    "vorstellen": 30,
    "vocab_test_correct": 5,
    "vocab_sprechen": 30,
    "aktiv_sprechen": 35,
    "daily_word": 15,
    "test_complete": 40,
}

# ==================== LEVEL LABELS ====================
LEVEL_LABELS = {
    "a1": "A1 - Beginner",
    "a2": "A2 - Elementary",
    "b1": "B1 - Intermediate",
    "b2": "B2 - Upper-Intermediate",
    "c1": "C1 - Advanced",
}

# ==================== AKTIV SPRECHEN TOPICS (100 topics, 20 per level) ====================
AKTIV_SPRECHEN_TOPICS = {
    "a1": [
        {"id": 1, "name": "Salomlashish", "german": "Begrüßung"},
        {"id": 2, "name": "Oila", "german": "Familie"},
        {"id": 3, "name": "Raqamlar", "german": "Zahlen"},
        {"id": 4, "name": "Kunlar va oylar", "german": "Wochentage und Monate"},
        {"id": 5, "name": "Ob-havo", "german": "Wetter"},
        {"id": 6, "name": "Ranglar", "german": "Farben"},
        {"id": 7, "name": "Taomlar", "german": "Essen und Trinken"},
        {"id": 8, "name": "Uy hayvoni", "german": "Haustiere"},
        {"id": 9, "name": "Maktab", "german": "Schule"},
        {"id": 10, "name": "Kasblar", "german": "Berufe"},
        {"id": 11, "name": "Transport", "german": "Verkehrsmittel"},
        {"id": 12, "name": "Shahar", "german": "Stadt"},
        {"id": 13, "name": "Uy", "german": "Zuhause"},
        {"id": 14, "name": "Kiyimlar", "german": "Kleidung"},
        {"id": 15, "name": "Badan", "german": "Körper"},
        {"id": 16, "name": "Hobbylar", "german": "Hobbys"},
        {"id": 17, "name": "Musiqa", "german": "Musik"},
        {"id": 18, "name": "Sport", "german": "Sport"},
        {"id": 19, "name": "Sayohat", "german": "Reisen"},
        {"id": 20, "name": "Xarid qilish", "german": "Einkaufen"},
    ],
    "a2": [
        {"id": 21, "name": "O'zini taqdim etish", "german": "Sich vorstellen"},
        {"id": 22, "name": "Oilaviy munosabatlar", "german": "Familienbeziehungen"},
        {"id": 23, "name": "Kundalik hayot", "german": "Tagesablauf"},
        {"id": 24, "name": "Ta'lim", "german": "Bildung"},
        {"id": 25, "name": "Ish joyi", "german": "Arbeitsplatz"},
        {"id": 26, "name": "Sayohat rejalari", "german": "Reisepläne"},
        {"id": 27, "name": "Restoran", "german": "Im Restaurant"},
        {"id": 28, "name": "Sog'liq", "german": "Gesundheit"},
        {"id": 29, "name": "Havo va fasl", "german": "Wetter und Jahreszeiten"},
        {"id": 30, "name": "Xabarlar", "german": "Nachrichten"},
        {"id": 31, "name": "Texnologiya", "german": "Technologie"},
        {"id": 32, "name": "Madaniyat", "german": "Kultur"},
        {"id": 33, "name": "Ta'til", "german": "Urlaub"},
        {"id": 34, "name": "Mashina haydash", "german": "Autofahren"},
        {"id": 35, "name": "Bank xizmatlari", "german": "Bankdienstleistungen"},
        {"id": 36, "name": "Poytaxt va davlatlar", "german": "Hauptstädte und Länder"},
        {"id": 37, "name": "Tabiat", "german": "Natur"},
        {"id": 38, "name": "Hayvonlar", "german": "Tiere"},
        {"id": 39, "name": "Oziq-ovqat", "german": "Lebensmittel"},
        {"id": 40, "name": "Uy ishlari", "german": "Hausarbeit"},
    ],
    "b1": [
        {"id": 41, "name": "Shaxsiy rivojlanish", "german": "Persönliche Entwicklung"},
        {"id": 42, "name": "Kasbiy faoliyat", "german": "Berufliche Tätigkeit"},
        {"id": 43, "name": "Ta'lim tizimi", "german": "Bildungssystem"},
        {"id": 44, "name": "Sayohat tajribasi", "german": "Reiseerfahrungen"},
        {"id": 45, "name": "Sog'liqni saqlash", "german": "Gesundheitspflege"},
        {"id": 46, "name": "Sport turlari", "german": "Sportarten"},
        {"id": 47, "name": "San'at va madaniyat", "german": "Kunst und Kultur"},
        {"id": 48, "name": "Oshxona an'analari", "german": "Kulinarische Traditionen"},
        {"id": 49, "name": "Media va axborot", "german": "Medien und Information"},
        {"id": 50, "name": "Atrof-muhit", "german": "Umwelt"},
        {"id": 51, "name": "Ilm-fan", "german": "Wissenschaft"},
        {"id": 52, "name": "Tarix", "german": "Geschichte"},
        {"id": 53, "name": "Ijtimoiy hayot", "german": "Soziales Leben"},
        {"id": 54, "name": "Moda va uslub", "german": "Mode und Stil"},
        {"id": 55, "name": "Xalqaro munosabatlar", "german": "Internationale Beziehungen"},
        {"id": 56, "name": "Transport va kommunikatsiya", "german": "Verkehr und Kommunikation"},
        {"id": 57, "name": "Muzey va teatr", "german": "Museum und Theater"},
        {"id": 58, "name": "Mamlakatlar taqqoslash", "german": "Ländervergleich"},
        {"id": 59, "name": "Kelajak rejalari", "german": "Zukunftspläne"},
        {"id": 60, "name": "Xotiralar", "german": "Erinnerungen"},
    ],
    "b2": [
        {"id": 61, "name": "Global muammolar", "german": "Globale Probleme"},
        {"id": 62, "name": "Iqtisodiyot", "german": "Wirtschaft"},
        {"id": 63, "name": "Siyosat va jamiyat", "german": "Politik und Gesellschaft"},
        {"id": 64, "name": "Psixologiya", "german": "Psychologie"},
        {"id": 65, "name": "Filosofiya", "german": "Philosophie"},
        {"id": 66, "name": "Arxitektura", "german": "Architektur"},
        {"id": 67, "name": "Etnografiya", "german": "Ethnografie"},
        {"id": 68, "name": "Tibbiyot", "german": "Medizin"},
        {"id": 69, "name": "Qonunchilik", "german": "Gesetzgebung"},
        {"id": 70, "name": "Menejment", "german": "Management"},
        {"id": 71, "name": "Marketing", "german": "Marketing"},
        {"id": 72, "name": "Ta'lim siyosati", "german": "Bildungspolitik"},
        {"id": 73, "name": "Muhojirlik", "german": "Migration"},
        {"id": 74, "name": "Energetika", "german": "Energie"},
        {"id": 75, "name": "Aloqa texnologiyalari", "german": "Kommunikationstechnologie"},
        {"id": 76, "name": "Aviatsiya", "german": "Luftfahrt"},
        {"id": 77, "name": "Me'morchilik", "german": "Baukunst"},
        {"id": 78, "name": "Qishloq xo'jaligi", "german": "Landwirtschaft"},
        {"id": 79, "name": "Sanoat", "german": "Industrie"},
        {"id": 80, "name": "T_ijorat", "german": "Handel"},
    ],
    "c1": [
        {"id": 81, "name": "Diplomatiya", "german": "Diplomatie"},
        {"id": 82, "name": "Strategik rejalashtirish", "german": "Strategische Planung"},
        {"id": 83, "name": "Neyrofan va sun'iy intelekt", "german": "Neurowissenschaft und KI"},
        {"id": 84, "name": "Kosmik tadqiqotlar", "german": "Raumfahrtforschung"},
        {"id": 85, "name": "Genetika", "german": "Genetik"},
        {"id": 86, "name": "Kibernetika xavfsizligi", "german": "Cybersicherheit"},
        {"id": 87, "name": "Ijtimoiy tarmoqlar ta'siri", "german": "Social Media Einfluss"},
        {"id": 88, "name": "Globalizatsiya ta'siri", "german": "Globalisierungsauswirkungen"},
        {"id": 89, "name": "Barqaror rivojlanish", "german": "Nachhaltige Entwicklung"},
        {"id": 90, "name": "Bioxilma-xillik", "german": "Biodiversität"},
        {"id": 91, "name": "Klimat o'zgarishi", "german": "Klimawandel"},
        {"id": 92, "name": "Startap ekotizimi", "german": "Startup-Ökosystem"},
        {"id": 93, "name": "Zamonaviy san'at", "german": "Zeitgenössische Kunst"},
        {"id": 94, "name": "Interkultural dialog", "german": "Interkultureller Dialog"},
        {"id": 95, "name": "Ta'lim inovatsiyalari", "german": "Bildungsinnovationen"},
        {"id": 96, "name": "Tibbiyot etikasi", "german": "Medizinethik"},
        {"id": 97, "name": "Huquqiy tizimlar taqqoslash", "german": "Rechtssystemvergleich"},
        {"id": 98, "name": "Zamonaviy adabiyot", "german": "Moderne Literatur"},
        {"id": 99, "name": "Mashhur shaxslar", "german": "Berühmte Persönlichkeiten"},
        {"id": 100, "name": "Kelajat texnologiyalari", "german": "Zukunftstechnologien"},
    ],
}

# ==================== VORSTELLEN QUESTIONS ====================
VORSTELLEN_QUESTIONS = [
    {"num": 1, "de": "Stellen Sie sich vor! Wie heißen Sie und wie alt sind Sie?", "uz": "O'zingizni taqdim eting! Ismingiz va yoshingiz?", "topic": "Name und Alter"},
    {"num": 2, "de": "Woher kommen Sie? Erzählen Sie von Ihrem Heimatland.", "uz": "Qayerdansiz? Vataningiz haqida gapiring.", "topic": "Herkunft"},
    {"num": 3, "de": "Wo wohnen Sie? Beschreiben Sie Ihre Wohnung/Ihr Haus.", "uz": "Qayerda yashaysiz? Uy/apartamentingizni tavsiflang.", "topic": "Wohnort"},
    {"num": 4, "de": "Erzählen Sie von Ihrer Familie.", "uz": "Oilangiz haqida gapiring.", "topic": "Familie"},
    {"num": 5, "de": "Wo haben Sie Deutsch gelernt? Wie lange lernen Sie schon?", "uz": "Qayerda nemis tilini o'rgandingiz? Qancha vaqtdan beri o'rganasiz?", "topic": "Deutsch lernen"},
    {"num": 6, "de": "Was machen Sie? (Studium, Beruf, Schule...)", "uz": "Nima ish qilasiz? (O'qish, ish, maktab...)", "topic": "Studium/Beruf"},
    {"num": 7, "de": "Welche Sprachen sprechen Sie? Warum lernen Sie Deutsch?", "uz": "Qaysi tillarni bilasiz? Nima uchun nemis tilini o'rganasiz?", "topic": "Sprachen"},
]
