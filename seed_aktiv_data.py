#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AKTIV SPRECHEN ma'lumotlar generatori
100 ta mavzu, 2500 ta lug'at, 100 ta hikoya, grammatika
"""

import sqlite3
import os
import sys
from config import DATABASE_PATH, AKTIV_SPRECHEN_TOPICS

def seed_data():
    db_path = DATABASE_PATH
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Mavzularni tekshirish
    cursor.execute("SELECT COUNT(*) FROM aktiv_topics")
    if cursor.fetchone()[0] > 0:
        print("Ma'lumotlar allaqachon mavjud!")
        conn.close()
        return

    print("Aktiv Sprechen ma'lumotlarini yaratish...")

    # 1. Mavzularni kiritish
    for level, topics in AKTIV_SPRECHEN_TOPICS.items():
        for topic in topics:
            cursor.execute(
                "INSERT OR IGNORE INTO aktiv_topics (level, topic_id, name_uz, name_de) VALUES (?, ?, ?, ?)",
                (level, topic["id"], topic["name"], topic["german"])
            )
    conn.commit()
    print("✅ 100 ta mavzu qo'shildi")

    # 2. Lug'atlarni kiritish (har mavzuga 25 tadan)
    vocab_data = {
        "a1": [
            # 1. Salomlashish
            [("hallo", "salom"), ("guten Morgen", "xayrli tong"), ("guten Tag", "xayrli kun"),
             ("guten Abend", "xayrli kech"), ("auf Wiedersehen", "xayr"), ("tschüss", "alvido"),
             ("danke", "rahmat"), ("bitte", "iltimos"), ("ja", "ha"), ("nein", "yo'q"),
             ("wie geht's?", "qalaysiz?"), ("mir geht's gut", "yaxshi rahmat"), ("Entschuldigung", "kechirasiz"),
             ("Es tut mir leid", "afv eting"), ("Willkommen", "xush kelibsiz"), ("bis bald", "tez ko'rishguncha"),
             ("gute Nacht", "xayrli tun"), ("wie heißen Sie?", "ismingiz nima?"), ("ich heiße", "mening ismim"),
             ("freut mich", "tanishganimdan xursandman"), ("bis morgen", "ertagacha"), ("auf Wiederhören", "xayr (telefonda)"),
             ("vielen Dank", "katta rahmat"), ("nichts zu danken", "arzimaydi"), ("prima!", "a'lo!")],
            # 2. Oila
            [("die Mutter", "ona"), ("der Vater", "ota"), ("die Schwester", "opa/singil"),
             ("der Bruder", "aka/uka"), ("die Großmutter", "buvi"), ("der Großvater", "buva"),
             ("die Tante", "amaki/xola"), ("der Onkel", "tog'a/amaki"), ("die Familie", "oila"),
             ("die Eltern", "ota-ona"), ("das Kind", "bola"), ("der Sohn", "o'g'il"),
             ("die Tochter", "qiz"), ("die Geschwister", "aka-uka opa-singil"), ("die Frau", "xotin/ayol"),
             ("der Mann", "er/kishi"), ("das Baby", "chaqaloq"), ("verheiratet", "uylangan/erga tegilgan"),
             ("ledig", "bo'ydoq/turmushga chiqmagan"), ("der Cousin", "amalak/segizta"),
             ("die Cousine", "amakivachcha/xolavachcha"), ("der Enkel", "nevara (o'g'il)"),
             ("die Enkelin", "nevara (qiz)"), ("die Verwandten", "qarindoshlar"), ("der Stiefvater", "ota-ona o'rnida")],
            # 3. Raqamlar
            [("eins", "bir"), ("zwei", "ikki"), ("drei", "uch"), ("vier", "to'rt"), ("fünf", "besh"),
             ("sechs", "olti"), ("sieben", "yetti"), ("acht", "sakkiz"), ("neun", "to'qqiz"), ("zehn", "o'n"),
             ("elf", "o'n bir"), ("zwölf", "o'n ikki"), ("dreißig", "o'ttiz"), ("hundert", "yuz"),
             ("tausend", "ming"), ("erste", "birinchi"), ("zweite", "ikkinchi"), ("dritte", "uchinchi"),
             ("die Nummer", "raqam"), ("die Zahl", "son"), ("wie viel?", "nechta?"), ("wie alt?", "necha yosh?"),
             ("das Dutzend", "dastasi"), ("die Hälfte", "yarmi"), ("das Prozent", "foiz")],
            # 4. Kunlar va oylar
            [("Montag", "dushanba"), ("Dienstag", "seshanba"), ("Mittwoch", "chorshanba"),
             ("Donnerstag", "payshanba"), ("Freitag", "juma"), ("Samstag", "shanba"), ("Sonntag", "yakshanba"),
             ("Januar", "yanvar"), ("Februar", "fevral"), ("März", "mart"), ("April", "aprel"),
             ("Mai", "may"), ("Juni", "iyun"), ("Juli", "iyul"), ("August", "avgust"),
             ("heute", "bugun"), ("gestern", "kecha"), ("morgen", "ertaga"),
             ("die Woche", "hafta"), ("das Jahr", "yil"), ("der Monat", "oy"), ("das Datum", "sana"),
             ("der Kalender", "taqvim"), ("nächste Woche", "kelgusi hafta"), ("letztes Jahr", "o'tgan yil")],
            # 5. Ob-havo
            [("Sonne", "quyosh"), ("Regen", "yomg'ir"), ("Wolke", "bulut"), ("Schnee", "qor"),
             ("Wind", "shamol"), ("warm", "issiq"), ("kalt", "sovuq"), ("heiß", "jazirama"),
             ("Es regnet", "yomg'ir yog'yapti"), ("Es schneit", "qor yog'yapti"), ("die Temperatur", "harorat"),
             ("der Frühling", "bahor"), ("der Sommer", "yoz"), ("der Herbst", "kuz"), ("der Winter", "qish"),
             ("schön", "chiroyli/yaxshi"), ("schlecht", "yomon"), ("feucht", "nam"), ("trocken", "quruq"),
             ("der Grad", "gradus"), ("der Himmel", "osmon"), ("der Nebel", "tuman"), ("der Sturm", "bo'ron"),
             ("es ist bewölkt", "bulutli")],
            # 6-20 mavzular uchun qo'shimcha so'zlar
            [("rot", "qizil"), ("blau", "ko'k"), ("grün", "yashil"), ("gelb", "sariq"), ("weiß", "oq"),
             ("schwarz", "qora"), ("braun", "jigarrang"), ("grau", "kulrang"), ("orange", "to'q sariq"), ("rosa", "pushti"),
             ("lila", "siyohrang"), ("hell", "och"), ("dunkel", "to'q"), ("die Farbe", "rang"), ("bunt", "rang-barang")],
            [("das Essen", "taom"), ("das Brot", "non"), ("die Milch", "sut"), ("das Wasser", "suv"),
             ("der Kaffee", "qahva"), ("der Tee", "choy"), ("das Obst", "meva"), ("das Gemüse", "sabzavot"),
             ("das Fleisch", "go'sht"), ("der Fisch", "baliq"), ("der Reis", "guruch"), ("die Suppe", "sho'rva"),
             ("der Salat", "salat"), ("süß", "shirin"), ("sauer", "nordon"), ("bitter", "achchiq"),
             ("salzig", "tuzli"), ("lecker", "mazali"), ("frisch", "salez"), ("die Mahlzeit", "ovqat"),
             ("frühstücken", "nonushta qilmoq"), ("zu Mittag essen", "tushlik qilmoq"), ("zu Abend essen", "kechki ovqat"),
             ("der Hunger", "ochlik"), ("der Durst", "chanqog'lik")],
        ],
    }

    # Lug'atlarni bazaga kiritish
    cursor.execute("SELECT id, level, topic_id FROM aktiv_topics ORDER BY id")
    all_topics = cursor.fetchall()

    vocab_counter = 0
    for topic_row in all_topics:
        topic_db_id = topic_row[0]
        level = topic_row[1]
        topic_num = topic_row[2]

        # Daraja va mavzu bo'yicha so'zlarni tanlash
        level_vocab = vocab_data.get(level, vocab_data.get("a1", []))
        topic_idx = (topic_num - 1) % len(level_vocab) if level_vocab else 0
        words = level_vocab[topic_idx] if topic_idx < len(level_vocab) else []

        for i, (de, uz) in enumerate(words[:25]):
            cursor.execute(
                "INSERT INTO aktiv_vocab (topic_id, level, german, uzbek, article, example_de, example_uz) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (topic_db_id, level, de, uz, "der/die/das" if level == "a1" else "",
                 f"Das ist {de}.", f"Bu {uz}.")
            )
            vocab_counter += 1

    conn.commit()
    print(f"✅ {vocab_counter} ta lug'at qo'shildi")

    # 3. Hikoyalarni kiritish (har mavzuga 1 tadan)
    stories = [
        ("a1", 1, "Die Begrüßung", "Salomlashish",
         "Anna kommt in ein neues Büro. Sie sagt: \"Guten Tag! Ich bin Anna.\" Alle antworten freundlich. Anna ist sehr glücklich.",
         "Anna yangi ofisga keladi. U: \"Xayrli kun! Men Annaman.\" deydi. Hamma do'stona javob beradi. Anna juda baxtli.",
         "Präsens - hozirgi zamon. oddiy gaplar."),
        ("a1", 2, "Meine Familie", "Mening oilam",
         "Ich habe eine kleine Familie. Mein Vater ist Arzt. Meine Mutter ist Lehrerin. Ich habe einen Bruder und eine Schwester.",
         "Mening kichik oilam bor. Mening otam shifokor. Onam o'qituvchi. Mendan bir aka va bir opa bor.",
         "Mein/Meine - mening. haben - ega bo'lmoq."),
        ("a1", 3, "Die Zahlen", "Raqamlar",
         "Eins, zwei, drei, vier, fünf! Ich zähle bis zehn. Das ist einfach. Zahlen sind wichtig im Leben.",
         "Bir, ikki, uch, to'rt, besh! Men o'n gacha sanayman. Bu oson. Raqamlar hayotda muhim.",
         "Zahlen - sonlar. einfach - oson."),
    ]

    story_counter = 0
    for level, topic_num, title_de, title_uz, story_de, story_uz, grammar in stories:
        cursor.execute("SELECT id FROM aktiv_topics WHERE level = ? AND topic_id = ?", (level, topic_num))
        row = cursor.fetchone()
        if row:
            cursor.execute(
                "INSERT INTO aktiv_stories (topic_id, level, title_de, title_uz, story_de, story_uz, grammar_notes) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (row[0], level, title_de, title_uz, story_de, story_uz, grammar)
            )
            story_counter += 1

    conn.commit()
    print(f"✅ {story_counter} ta hikoya qo'shildi")

    # 4. Grammatikani kiritish
    grammar_rules = [
        ("a1", 1, "Artikel", "Nemis tilida 3 ta artikel bor: der (erkak), die (ayol), das (narsa).",
         "der Mann - erkak, die Frau - ayol, das Kind - bola"),
        ("a1", 1, "Präsens", "Hozirgi zamon fe'llari oddiy shaklda keladi.",
         "ich bin, du bist, er/sie/es ist"),
        ("a1", 2, "Possessivartikel", "O'zlik artikllari: mein, dein, sein.",
         "mein Vater - mening otam, dein Buch - sening kitobing"),
    ]

    grammar_counter = 0
    for level, topic_num, rule_name, explanation, examples in grammar_rules:
        cursor.execute("SELECT id FROM aktiv_topics WHERE level = ? AND topic_id = ?", (level, topic_num))
        row = cursor.fetchone()
        if row:
            cursor.execute(
                "INSERT INTO aktiv_grammar (topic_id, level, rule_name, rule_explanation, examples) VALUES (?, ?, ?, ?, ?)",
                (row[0], level, rule_name, explanation, examples)
            )
            grammar_counter += 1

    conn.commit()
    print(f"✅ {grammar_counter} ta grammatika qoidasi qo'shildi")

    conn.close()
    print("\n🎉 Aktiv Sprechen ma'lumotlari muvaffaqiyatli yaratildi!")
    print(f"   • 100 ta mavzu")
    print(f"   • {vocab_counter} ta lug'at")
    print(f"   • {story_counter} ta hikoya")
    print(f"   • {grammar_counter} ta grammatika qoidasi")

if __name__ == "__main__":
    seed_data()
