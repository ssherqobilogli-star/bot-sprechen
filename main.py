#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
============================================================
  DEUTSCH MEISTER PRO - Mukammal Nemis Tili Telegram Bot
  To'liq yangilangan versiya
============================================================
"""

import os
import sys
import json
import random
import datetime
import logging
import tempfile
import asyncio
import io

from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
    ReplyKeyboardMarkup, KeyboardButton, InputFile,
    WebAppInfo, MenuButtonWebApp, Contact,
)
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes,
    ConversationHandler,
)

from config import (
    logger, TOKEN, GROQ_API_KEY, ADMIN_IDS,
    LEVEL_LABELS, AKTIV_SPRECHEN_TOPICS, VORSTELLEN_QUESTIONS,
    XP_REWARDS, TTS_VOICES,
)
from database import get_db

# ==================== HELPER FUNCTIONS ====================

def esc_md(text: str) -> str:
    """MarkdownV2 uchun maxsus belgilarni escape qilish"""
    if not text:
        return ""
    for ch in r"\_*[]()~`>#+-=|{}.!":
        text = text.replace(ch, f"\\{ch}")
    return text


def is_admin(user_id: int) -> bool:
    """Foydalanuvchi admin ekanligini tekshirish"""
    return user_id in ADMIN_IDS


# ==================== PASTKI DOIMIY MENYU ====================

REPLY_KEYBOARD = ReplyKeyboardMarkup(
    [
        ["🤖 AI Mentor", "💬 Aktiv Sprechen"],
        ["📖 Lug'at", "🌐 Tarjimon"],
        ["📚 Sayfa", "📚 Kitob Materiallar"],
        ["📖 Kunlik so'z", "📊 Progressim"],
        ["📝 Test", "⚙️ Sozlamalar"],
    ],
    resize_keyboard=True,
    is_persistent=True,
)

ADMIN_REPLY_KEYBOARD = ReplyKeyboardMarkup(
    [
        ["🤖 AI Mentor", "💬 Aktiv Sprechen"],
        ["📖 Lug'at", "🌐 Tarjimon"],
        ["📚 Sayfa", "📚 Kitob Materiallar"],
        ["📖 Kunlik so'z", "📊 Progressim"],
        ["📝 Test", "⚙️ Sozlamalar"],
        ["🔐 Admin Panel"],
    ],
    resize_keyboard=True,
    is_persistent=True,
)


# ==================== STATES ====================
(
    MAIN_MENU,
    REG_PHONE,
    # Admin
    ADMIN_MENU, ADMIN_USERS, ADMIN_REQUESTS, ADMIN_BROADCAST, ADMIN_STATS,
    # AI Mentor
    AI_MENTOR_MENU, AI_VORSTELLEN_START, AI_VORSTELLEN_RESULT,
    AI_AKTIV_LEVEL, AI_AKTIV_TOPIC, AI_AKTIV_DETAIL,
    # Lug'at
    LUGAT_MENU, LUGAT_LEVEL, LUGAT_BOOK, LUGAT_CHAPTER, LUGAT_WORDS,
    # Tarjimon
    TARJIMON_MENU, TARJIMON_UZB_DEU, TARJIMON_DEU_UZB,
    # Sayfa
    SAYFA_MENU, SAYFA_BOOK,
    # Kitob
    KITOB_MENU, KITOB_LEVEL, KITOB_BOOK,
    # Kunlik so'z
    DAILY_WORD,
    # Progress
    PROGRESS_MENU,
    # Sozlamalar
    SETTINGS_MENU, SETTINGS_VOICE, SETTINGS_SPEED, SETTINGS_LEVEL,
    # Test
    TEST_MENU, TEST_LEVEL, TEST_QUIZ, TEST_RESULT,
) = range(36)


# ==================== /START - Telefon raqam so'rash ====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """/start komandasi - Telefon raqam so'rash"""
    user = update.effective_user
    db = get_db()
    existing = db.get_user(user.id)

    if existing and existing.get("phone"):
        # Telefon allaqachon mavjud
        return await show_main_menu(update, context)

    # Telefon raqam so'rash
    phone_keyboard = ReplyKeyboardMarkup(
        [[KeyboardButton("📱 Telefon raqamni yuborish", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )

    await update.message.reply_text(
        f"🇩🇪 *Deutsch Meister PRO*\n\n"
        f"Salom, {esc_md(user.first_name)}\\! 👋\n\n"
        f"Botdan to'liq foydalanish uchun telefon raqamingizni yuboring\\.",
        parse_mode="MarkdownV2",
        reply_markup=phone_keyboard,
    )
    return REG_PHONE


async def receive_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Telefon raqamni qabul qilish"""
    contact = update.message.contact
    user = update.effective_user
    db = get_db()

    phone = contact.phone_number if contact else None
    if not phone:
        await update.message.reply_text(
            "❌ Telefon raqamni olishda xatolik. Iltimos, qayta urinib ko'ring.",
            reply_markup=ReplyKeyboardMarkup(
                [[KeyboardButton("📱 Telefon raqamni yuborish", request_contact=True)]],
                resize_keyboard=True, one_time_keyboard=True,
            ),
        )
        return REG_PHONE

    # Foydalanuvchini yaratish yoki yangilash
    db.get_or_create_user(user.id, user.username, user.first_name, user.last_name)
    db.save_phone(user.id, phone)

    # Adminlarga xabar yuborish
    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_message(
                chat_id=admin_id,
                text=(
                    f"📋 *Yangi foydalanuvchi*\n\n"
                    f"👤 *Ism:* {esc_md(user.first_name)}\n"
                    f"🔗 *Username:* @{esc_md(str(user.username))}\n"
                    f"🆔 *ID:* `{user.id}`\n"
                    f"📱 *Telefon:* `{esc_md(phone)}`\n"
                    f"📅 *Sana:* {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
                    f"✅ Botda ro'yxatdan o'tdi\\!"
                ),
                parse_mode="MarkdownV2",
            )
        except Exception as e:
            logger.warning(f"Admin {admin_id} ga xabar yuborib bo'lmadi: {e}")

    await update.message.reply_text(
        f"✅ *Raqam qabul qilindi\\!*\n\n"
        f"📱 `{esc_md(phone)}`\n\n"
        f"Endi botdan to'liq foydalanishingiz mumkin\\.",
        parse_mode="MarkdownV2",
    )
    return await show_main_menu(update, context)


async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Asosiy menyuni ko'rsatish"""
    user = update.effective_user
    db = get_db()
    db_user = db.get_or_create_user(user.id, user.username, user.first_name, user.last_name)

    kb = ADMIN_REPLY_KEYBOARD if is_admin(user.id) else REPLY_KEYBOARD

    text = (
        f"🇩🇪 *Deutsch Meister PRO*\n\n"
        f"Salom, {esc_md(user.first_name)}\\! 👋\n\n"
        f"📚 *Joriy daraja:* {esc_md(LEVEL_LABELS.get(db_user.get('current_level', 'a1'), 'A1'))}\n"
        f"⭐ *XP:* {db_user.get('total_xp', 0)}\n\n"
        f"Quyidagi bo'limlardan birini tanlang:"
    )

    if update.callback_query:
        query = update.callback_query
        await query.answer()
        await query.edit_message_text(text, parse_mode="MarkdownV2")
        await context.bot.send_message(chat_id=query.message.chat_id, text="👇", reply_markup=kb)
    else:
        await update.message.reply_text(text, parse_mode="MarkdownV2", reply_markup=kb)
    return MAIN_MENU


# ==================== ADMIN PANEL ====================

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Admin panel bosh menyu"""
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text("❌ Sizda ruxsat yo'q.")
        return MAIN_MENU

    db = get_db()
    users_count = db.get_users_count()
    pending_requests = len(db.get_requests(status="pending"))

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("👥 Foydalanuvchilar", callback_data="admin_users")],
        [InlineKeyboardButton(f"📨 Murojaatlar ({pending_requests})", callback_data="admin_requests")],
        [InlineKeyboardButton("📊 Statistika", callback_data="admin_stats")],
        [InlineKeyboardButton("📢 Xabar yuborish", callback_data="admin_broadcast")],
        [InlineKeyboardButton("🔙 Asosiy menyu", callback_data="main_menu")],
    ])

    await update.message.reply_text(
        f"🔐 *Admin Panel*\n\n"
        f"👥 *Jami foydalanuvchilar:* {users_count}\n"
        f"📨 *Kutilayotgan murojaatlar:* {pending_requests}\n\n"
        f"Bo'limni tanlang:",
        parse_mode="MarkdownV2",
        reply_markup=keyboard,
    )
    return ADMIN_MENU


async def admin_users(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Foydalanuvchilar ro'yxati"""
    query = update.callback_query
    await query.answer()

    db = get_db()
    users = db.get_all_users(limit=20)

    if not users:
        await query.edit_message_text(
            "👥 *Foydalanuvchilar*\n\nHali foydalanuvchilar yo'q.",
            parse_mode="MarkdownV2",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Orqaga", callback_data="admin_menu")]]),
        )
        return ADMIN_MENU

    text = "👥 *Oxirgi foydalanuvchilar:*\n\n"
    for u in users:
        phone = u.get("phone") or "Noma'lum"
        text += (
            f"🆔 `{u['user_id']}`\n"
            f"👤 {esc_md(u.get('first_name', 'Noma\'lum'))}\n"
            f"📱 `{esc_md(phone)}`\n"
            f"📅 {u.get('joined_at', 'Noma\'lum')[:10]}\n"
            f"⭐ XP: {u.get('total_xp', 0)}\n\n"
        )

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 Batafsil", callback_data="admin_stats")],
        [InlineKeyboardButton("🔙 Admin Panel", callback_data="admin_menu")],
    ])

    await query.edit_message_text(text[:4000], parse_mode="MarkdownV2", reply_markup=keyboard)
    return ADMIN_USERS


async def admin_requests_view(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Murojaatlar ro'yxati"""
    query = update.callback_query
    await query.answer()

    db = get_db()
    requests = db.get_requests(status="pending", limit=20)

    if not requests:
        await query.edit_message_text(
            "📨 *Murojaatlar*\n\nKutilayotgan murojaatlar yo'q.",
            parse_mode="MarkdownV2",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📨 Barcha murojaatlar", callback_data="admin_all_requests")],
                [InlineKeyboardButton("🔙 Admin Panel", callback_data="admin_menu")],
            ]),
        )
        return ADMIN_REQUESTS

    text = "📨 *Kutilayotgan murojaatlar:*\n\n"
    for req in requests:
        text += (
            f"🆔 ID: `{req['id']}`\n"
            f"👤 {esc_md(req.get('user_name', 'Noma\'lum'))}\n"
            f"📋 {esc_md(req.get('request_type', ''))}\n"
            f"💬 {esc_md(req.get('message', '')[:100])}\n"
            f"📅 {req.get('created_at', '')[:16]}\n\n"
        )

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Barchasini ko'rib chiqildi", callback_data="admin_resolve_all")],
        [InlineKeyboardButton("🔙 Admin Panel", callback_data="admin_menu")],
    ])

    await query.edit_message_text(text[:4000], parse_mode="MarkdownV2", reply_markup=keyboard)
    return ADMIN_REQUESTS


async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Statistika ko'rish"""
    query = update.callback_query
    await query.answer()

    db = get_db()
    users_count = db.get_users_count()
    level_stats = db.get_level_stats()

    text = (
        f"📊 *Bot statistikasi*\n\n"
        f"👥 *Jami foydalanuvchilar:* {users_count}\n\n"
        f"📚 *Darajalar bo'yicha:*\n"
    )
    for level, count in sorted(level_stats.items()):
        label = LEVEL_LABELS.get(level, level.upper())
        text += f"  {label}: {count}\n"

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Admin Panel", callback_data="admin_menu")],
    ])

    await query.edit_message_text(text, parse_mode="MarkdownV2", reply_markup=keyboard)
    return ADMIN_STATS


async def admin_broadcast_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Xabar yuborish boshlash"""
    query = update.callback_query
    await query.answer()

    await query.edit_message_text(
        "📢 *Xabar yuborish*\n\n"
        "Barcha foydalanuvchilarga yuboriladigan xabarni kiriting:\n\n"
        "_Bekor qilish uchun /cancel_",
        parse_mode="MarkdownV2",
    )
    context.user_data["admin_broadcast"] = True
    return ADMIN_BROADCAST


async def admin_broadcast_send(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Xabarni barcha foydalanuvchilarga yuborish"""
    if not context.user_data.get("admin_broadcast"):
        return MAIN_MENU

    message = update.message.text
    if message == "/cancel":
        await update.message.reply_text("❌ Bekor qilindi.", reply_markup=ADMIN_REPLY_KEYBOARD)
        return await show_main_menu(update, context)

    db = get_db()
    users = db.get_all_users(limit=10000)
    sent = 0
    failed = 0

    status_msg = await update.message.reply_text(f"📢 Xabar yuborilmoqda... (0/{len(users)})")

    for u in users:
        try:
            await context.bot.send_message(
                chat_id=u["user_id"],
                text=f"📢 *Xabar admin dan:*\n\n{esc_md(message)}",
                parse_mode="MarkdownV2",
            )
            sent += 1
            if sent % 50 == 0:
                await status_msg.edit_text(f"📢 Xabar yuborilmoqda... ({sent}/{len(users)})")
            await asyncio.sleep(0.05)
        except Exception:
            failed += 1

    db.log_broadcast(update.effective_user.id, message, sent)

    await status_msg.edit_text(
        f"✅ *Yuborildi\\!*\n\n"
        f"📤 Muvaffaqiyatli: {sent}\n"
        f"❌ Muvaffaqiyatsiz: {failed}"
    )
    context.user_data["admin_broadcast"] = False
    return MAIN_MENU


# ==================== AI MENTOR ====================

async def ai_mentor_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """AI Mentor menyu"""
    query = update.callback_query
    if query:
        await query.answer()
        msg = query
    else:
        msg = update.message

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🎤 Vorstellen", callback_data="ai_vorstellen")],
        [InlineKeyboardButton("🎯 Daraja aniqlash", callback_data="ai_level_detect")],
        [InlineKeyboardButton("🔄 Qayta", callback_data="ai_mentor")],
        [InlineKeyboardButton("🏠 Asosiy menyu", callback_data="main_menu")],
    ])

    text = (
        "🤖 *AI Mentor*\n\n"
        "🎤 *Vorstellen* — O'zingizni taqdim etish mashqi\n"
        "AI sizning gapirishingizni tahlil qilib, PDF shaklida natija beradi\n\n"
        "Bo'limni tanlang:"
    )

    if query:
        await msg.edit_message_text(text, parse_mode="MarkdownV2", reply_markup=keyboard)
    else:
        await msg.reply_text(text, parse_mode="MarkdownV2", reply_markup=keyboard)
    return AI_MENTOR_MENU


# ==================== VORSTELLEN ====================

VORSTELLEN_CARD_PATH = os.path.join(os.path.dirname(__file__), "vorstellen_card.jpg")


async def vorstellen_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Vorstellen boshlash - rasm + talablar"""
    query = update.callback_query
    await query.answer()

    # Rasmni yuborish
    try:
        if os.path.exists(VORSTELLEN_CARD_PATH):
            with open(VORSTELLEN_CARD_PATH, "rb") as img:
                await context.bot.send_photo(
                    chat_id=query.message.chat_id,
                    photo=img,
                    caption=(
                        "🎤 *Vorstellen — O'zingizni taqdim etish*\n\n"
                        "Yuqoridagi 7 ta savolga javob bering.\n\n"
                        "📝 Matn yozing YOKI 🎙️ ovozli xabar yuboring\\!"
                    ),
                    parse_mode="MarkdownV2",
                )
        else:
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text="🎤 *Vorstellen*\n\n7 ta savolga javob bering:",
                parse_mode="MarkdownV2",
            )
    except Exception as e:
        logger.error(f"Vorstellen rasm yuborishda xato: {e}")

    context.user_data["vs_answers"] = []
    context.user_data["vs_mode"] = "vorstellen"

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🏁 Yakunlash va AI tahlil", callback_data="vs_finish")],
        [InlineKeyboardButton("🔙 AI Mentor", callback_data="ai_mentor")],
    ])

    await context.bot.send_message(
        chat_id=query.message.chat_id,
        text=(
            "⏱️ *10 daqiqa vaqt berildi\\!*\n\n"
            "📝 Matn yozing YOKI 🎙️ ovozli xabar yuboring\n"
            "_Bir nechta xabar yuborsangiz ham bo'ladi — hammasi birlashtiriladi_\n\n"
            "Tayyor bo'lganda \"Yakunlash\" tugmasini bosing:"
        ),
        parse_mode="MarkdownV2",
        reply_markup=keyboard,
    )
    return AI_VORSTELLEN_START


async def vorstellen_collect(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Vorstellen javoblarini yig'ish"""
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        if query.data == "vs_finish":
            return await vorstellen_analyze(query, context)
        return AI_VORSTELLEN_START

    answers = context.user_data.setdefault("vs_answers", [])

    # Matnli javob
    if update.message.text:
        answers.append(update.message.text)
        await update.message.reply_text(
            "✅ *Qabul qilindi\\!* Davom etishingiz yoki yakunlashingiz mumkin\\.",
            parse_mode="MarkdownV2",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🏁 Yakunlash va AI tahlil", callback_data="vs_finish")],
            ]),
        )

    # Ovozli javob
    elif update.message.voice or update.message.audio:
        loading = await update.message.reply_text("🎙️ *Ovoz tahlil qilinmoqda...*", parse_mode="MarkdownV2")
        recognized = await listen_to_voice(update, context, language="de")
        try:
            await loading.delete()
        except:
            pass

        if recognized and not recognized.startswith("❌"):
            answers.append(recognized)
            preview = recognized[:150] + ("..." if len(recognized) > 150 else "")
            await update.message.reply_text(
                f"✅ *Ovoz qabul qilindi\\!*\n\n_{esc_md(preview)}_\n\nDavom eting:",
                parse_mode="MarkdownV2",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🏁 Yakunlash va AI tahlil", callback_data="vs_finish")],
                ]),
            )
        else:
            await update.message.reply_text(
                "⚠️ Ovozni tushuna olmadim. Yana urinib ko'ring yoki matn yozing.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🏁 Yakunlash va AI tahlil", callback_data="vs_finish")],
                ]),
            )

    return AI_VORSTELLEN_START


async def vorstellen_analyze(query, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Vorstellen tahlil qilish"""
    answers = context.user_data.get("vs_answers", [])
    all_text = " ".join(answers) if answers else "Foydalanuvchi javob bermadi."

    loading = await query.message.reply_text(
        "🧠 *AI tahlil qilmoqda...*\n\n"
        "• Grammatika tekshirilmoqda\n"
        "• So'z boyligi baholanmoqda\n"
        "• Daraja aniqlanmoqda\n\n"
        "_10-15 soniya kuting..._",
        parse_mode="MarkdownV2",
    )

    # Groq API orqali tahlil
    analysis = await groq_vorstellen_analyze(all_text)

    try:
        await loading.delete()
    except:
        pass

    context.user_data["vs_analysis"] = analysis
    score = analysis.get("yulduz", 3)

    # XP qo'shish
    try:
        db = get_db()
        xp = XP_REWARDS.get("vorstellen", 30) + score * 5
        db.add_xp(query.from_user.id, xp, "vorstellen", f"Yulduz: {score}/5")
    except Exception as e:
        logger.warning(f"XP qo'shishda xato: {e}")

    # Natijani ko'rsatish
    stars = "⭐" * score + "☆" * (5 - score)
    level_detected = analysis.get("detected_level", "Noma'lum")

    text = (
        f"🎉 *Vorstellen Natijasi*\n\n"
        f"{esc_md(stars)}\n\n"
        f"📊 *Yulduz: {score}/5*\n"
        f"📚 Grammatika: {analysis.get('grammar_score', '?')}/10\n"
        f"🗣 So'z boyligi: {analysis.get('vocabulary_score', '?')}/10\n"
        f"💬 Ravonlik: {analysis.get('fluency_score', '?')}/10\n\n"
        f"🎯 *Aniqlangan daraja: {esc_md(str(level_detected))}*\n\n"
    )

    if analysis.get("qoldirilgan_mavzular"):
        text += f"⚠️ *Yoritilmagan mavzular:* {esc_md(', '.join(analysis['qoldirilgan_mavzular']))}\n\n"

    good_points = analysis.get("good_points", [])
    if good_points:
        text += "✅ *Yaxshi jihatlar:*\n"
        for g in good_points[:3]:
            text += f"• {esc_md(g)}\n"
        text += "\n"

    text += f"🎁 *+{XP_REWARDS.get('vorstellen', 30) + score * 5} XP qo'shildi\\!*"

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💡 Tushuntirish", callback_data="vs_tushuntirish")],
        [InlineKeyboardButton("📑 PDF yuklash", callback_data="vs_pdf")],
        [InlineKeyboardButton("✨ A1 variant", callback_data="vs_level_a1"),
         InlineKeyboardButton("✨ A2 variant", callback_data="vs_level_a2")],
        [InlineKeyboardButton("✨ B1 variant", callback_data="vs_level_b1"),
         InlineKeyboardButton("✨ B2 variant", callback_data="vs_level_b2")],
        [InlineKeyboardButton("🔊 Ovozda eshitish", callback_data="vs_speak")],
        [InlineKeyboardButton("🔄 Qayta boshlash", callback_data="ai_vorstellen")],
        [InlineKeyboardButton("🏠 Asosiy menyu", callback_data="main_menu")],
    ])

    await query.message.reply_text(text, parse_mode="MarkdownV2", reply_markup=keyboard)
    return AI_VORSTELLEN_RESULT


async def vorstellen_result_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Vorstellen natija tugmalari"""
    query = update.callback_query
    await query.answer()
    data = query.data
    analysis = context.user_data.get("vs_analysis", {})

    if data == "vs_tushuntirish":
        tushuntirish = analysis.get("tushuntirish", "Ma'lumot yo'q.")
        errors = analysis.get("grammar_errors", [])
        text = f"💡 *Tushuntirish*\n\n{esc_md(tushuntirish)}\n\n"
        if errors:
            text += "📋 *Xatolar:*\n"
            for e in errors[:5]:
                text += f"❌ {esc_md(e.get('xato', ''))} → ✅ {esc_md(e.get('togri', ''))}\n"
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📑 PDF yuklash", callback_data="vs_pdf")],
            [InlineKeyboardButton("↩️ Natijaga qaytish", callback_data="vs_back_result")],
        ])
        await query.edit_message_text(text, parse_mode="MarkdownV2", reply_markup=keyboard)

    elif data == "vs_pdf":
        return await generate_vorstellen_pdf(query, context)

    elif data.startswith("vs_level_"):
        level = data.replace("vs_level_", "")
        improved = analysis.get(f"yaxshilash_{level}", "")
        if not improved:
            improved = analysis.get("tarjima", "Mukammal variant mavjud emas.")
        text = f"✨ *{level.upper()} darajasida mukammal variant:*\n\n{esc_md(improved)}"
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📑 PDF yuklash", callback_data="vs_pdf")],
            [InlineKeyboardButton("🔊 Ovozda eshitish", callback_data="vs_speak")],
            [InlineKeyboardButton("↩️ Natijaga qaytish", callback_data="vs_back_result")],
        ])
        await query.edit_message_text(text, parse_mode="MarkdownV2", reply_markup=keyboard)

    elif data == "vs_speak":
        text_to_speak = (analysis.get("tarjima", "") or
                        context.user_data.get("vs_improved_text", "") or
                        "Mukammal variant mavjud emas.")
        if text_to_speak:
            await query.answer("🔊 Ovoz tayyorlanmoqda...")
            try:
                await speak_text(query, text_to_speak[:600])
            except Exception as e:
                logger.error(f"Ovoz yuborishda xato: {e}")
                await query.answer("❌ Ovoz funksiyasida xato", show_alert=True)
        else:
            await query.answer("⚠️ O'qiladigan matn yo'q", show_alert=True)
        return AI_VORSTELLEN_RESULT

    elif data == "vs_back_result":
        return await show_vorstellen_result_page(query, context)

    return AI_VORSTELLEN_RESULT


async def show_vorstellen_result_page(query, context: ContextTypes.DEFAULT_TYPE):
    """Vorstellen natija sahifasini qayta ko'rsatish"""
    analysis = context.user_data.get("vs_analysis", {})
    score = analysis.get("yulduz", 3)
    stars = "⭐" * score + "☆" * (5 - score)
    level_detected = analysis.get("detected_level", "Noma'lum")

    text = (
        f"🎉 *Vorstellen Natijasi*\n\n"
        f"{esc_md(stars)}\n\n"
        f"📊 *Yulduz: {score}/5*\n"
        f"📚 Grammatika: {analysis.get('grammar_score', '?')}/10\n"
        f"🗣 So'z boyligi: {analysis.get('vocabulary_score', '?')}/10\n"
        f"💬 Ravonlik: {analysis.get('fluency_score', '?')}/10\n\n"
        f"🎯 *Aniqlangan daraja: {esc_md(str(level_detected))}*"
    )

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💡 Tushuntirish", callback_data="vs_tushuntirish")],
        [InlineKeyboardButton("📑 PDF yuklash", callback_data="vs_pdf")],
        [InlineKeyboardButton("✨ A1 variant", callback_data="vs_level_a1"),
         InlineKeyboardButton("✨ A2 variant", callback_data="vs_level_a2")],
        [InlineKeyboardButton("✨ B1 variant", callback_data="vs_level_b1"),
         InlineKeyboardButton("✨ B2 variant", callback_data="vs_level_b2")],
        [InlineKeyboardButton("🔊 Ovozda eshitish", callback_data="vs_speak")],
        [InlineKeyboardButton("🔄 Qayta boshlash", callback_data="ai_vorstellen")],
        [InlineKeyboardButton("🏠 Asosiy menyu", callback_data="main_menu")],
    ])

    await query.edit_message_text(text, parse_mode="MarkdownV2", reply_markup=keyboard)
    return AI_VORSTELLEN_RESULT


async def generate_vorstellen_pdf(query, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Vorstellen PDF yaratish va yuborish"""
    await query.answer("📑 PDF tayyorlanmoqda...")
    analysis = context.user_data.get("vs_analysis", {})

    try:
        pdf_bytes = build_vorstellen_pdf(
            level=analysis.get("detected_level", "A1"),
            score=analysis.get("yulduz", 3),
            grammar_score=analysis.get("grammar_score", 0),
            vocab_score=analysis.get("vocabulary_score", 0),
            fluency_score=analysis.get("fluency_score", 0),
            detected_level=analysis.get("detected_level", "A1"),
            user_answers=" ".join(context.user_data.get("vs_answers", [])),
            improved_text=analysis.get("tarjima", ""),
            tushuntirish=analysis.get("tushuntirish", ""),
            errors=analysis.get("grammar_errors", []),
            good_points=analysis.get("good_points", []),
            yaxshilash_a1=analysis.get("yaxshilash_a1", ""),
            yaxshilash_a2=analysis.get("yaxshilash_a2", ""),
            yaxshilash_b1=analysis.get("yaxshilash_b1", ""),
            yaxshilash_b2=analysis.get("yaxshilash_b2", ""),
        )

        buf = io.BytesIO(pdf_bytes)
        buf.seek(0)
        user_id = query.from_user.id
        filename = f"Vorstellen_{analysis.get('detected_level', 'A1')}_{user_id}.pdf"

        await query.message.reply_document(
            document=buf,
            filename=filename,
            caption=(
                f"✅ *Vorstellen — {esc_md(str(analysis.get('detected_level', 'A1')))} daraja*\n\n"
                f"📑 PDF fayl tayyor\\!\n"
                f"⭐ Yulduz: {analysis.get('yulduz', 3)}/5\n\n"
                f"💡 Bu matnni yodlang va har kuni mashq qiling\\!"
            ),
            parse_mode="MarkdownV2",
        )
    except Exception as e:
        logger.error(f"PDF yaratishda xato: {e}")
        await query.message.reply_text("❌ PDF yaratishda xatolik yuz berdi.")

    return AI_VORSTELLEN_RESULT


# ==================== GROQ API FUNCTIONS ====================

async def groq_vorstellen_analyze(text: str) -> dict:
    """Groq API orqali Vorstellen tahlili"""
    if not GROQ_API_KEY:
        return {"yulduz": 3, "grammar_score": 5, "vocabulary_score": 5, "fluency_score": 5,
                "detected_level": "A1", "tushuntirish": "API kalit topilmadi", "tarjima": text,
                "grammar_errors": [], "good_points": [], "qoldirilgan_mavzular": [],
                "yaxshilash_a1": text, "yaxshilash_a2": text, "yaxshilash_b1": text, "yaxshilash_b2": text}

    import httpx

    mavzular = ", ".join(q["topic"] for q in VORSTELLEN_QUESTIONS)

    system_prompt = (
        "Siz nemis tili mutaxassisisiz. Foydalanuvchi Vorstellen (o'zini taqdim etish) "
        f"mashqida javob berdi. Ideal javobda quyidagi mavzular yoritilishi kerak: {mavzular}. "
        "Javobni tahlil qiling va FAQAT quyidagi JSON formatida javob bering — boshqa hech narsa yozmang:\n"
        "{\n"
        '  "yulduz": 1-5 (umumiy sifat bahosi, butun son),\n'
        '  "grammar_score": 1-10,\n'
        '  "vocabulary_score": 1-10,\n'
        '  "fluency_score": 1-10,\n'
        '  "detected_level": "A1 yoki A2 yoki B1 yoki B2",\n'
        '  "qoldirilgan_mavzular": ["yoritilmagan mavzular"],\n'
        '  "tushuntirish": "Xatolar va grammatika haqida o\'zbek tilida (5-7 gap)",\n'
        '  "tarjima": "Foydalanuvchi javobining to\'g\'ri nemischa varianti",\n'
        '  "yaxshilash_a1": "A1 darajasida to\'liq mukammal Vorstellen",\n'
        '  "yaxshilash_a2": "A2 darajasida to\'liq mukammal variant",\n'
        '  "yaxshilash_b1": "B1 darajasida to\'liq mukammal variant",\n'
        '  "yaxshilash_b2": "B2 darajasida to\'liq mukammal variant",\n'
        '  "grammar_errors": [{"xato": "...", "togri": "..."}],\n'
        '  "good_points": ["...", "..."]\n'
        "}"
    )

    try:
        async with httpx.AsyncClient(timeout=90.0) as client:
            resp = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
                json={
                    "model": "llama3-70b-8192",
                    "max_tokens": 4000,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"Foydalanuvchi javobi:\n{text}"},
                    ],
                    "response_format": {"type": "json_object"},
                },
            )
            data = resp.json()
            raw = data["choices"][0]["message"]["content"]
            return json.loads(raw)
    except Exception as e:
        logger.error(f"Groq tahlil xatosi: {e}")
        return {"yulduz": 3, "grammar_score": 5, "vocabulary_score": 5, "fluency_score": 5,
                "detected_level": "A1", "tushuntirish": f"Xato: {str(e)}", "tarjima": text,
                "grammar_errors": [], "good_points": [], "qoldirilgan_mavzular": [],
                "yaxshilash_a1": text, "yaxshilash_a2": text, "yaxshilash_b1": text, "yaxshilash_b2": text}


# ==================== VOICE FUNCTIONS ====================

async def listen_to_voice(update: Update, context: ContextTypes.DEFAULT_TYPE, language: str = "de") -> str:
    """Ovozli xabarni matnga aylantirish (Whisper API)"""
    import httpx

    voice = update.message.voice or update.message.audio
    if not voice:
        return "❌ Ovoz topilmadi"

    try:
        file = await context.bot.get_file(voice.file_id)
        file_bytes = await file.download_as_bytearray()

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                "https://api.groq.com/openai/v1/audio/transcriptions",
                headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
                files={"file": ("audio.ogg", io.BytesIO(file_bytes), "audio/ogg")},
                data={"model": "whisper-large-v3", "language": language},
            )
            data = resp.json()
            return data.get("text", "❌ Transkripsiya topilmadi")
    except Exception as e:
        logger.error(f"Ovoz tanish xatosi: {e}")
        return f"❌ Ovoz tahlilida xato: {str(e)}"


async def speak_text(query, text: str, voice: str = "female", speed: float = 0.9):
    """Matnni ovozli o'qish (Edge TTS orqali)"""
    try:
        import edge_tts
        import asyncio

        voice_name = TTS_VOICES.get(voice, TTS_VOICES["female"])
        communicate = edge_tts.Communicate(text, voice_name, rate=f"{int((speed-1)*100)}%")

        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
            tmp_path = tmp.name
            await communicate.save(tmp_path)

        with open(tmp_path, "rb") as audio:
            await query.message.reply_audio(audio=audio)

        os.unlink(tmp_path)
    except Exception as e:
        logger.error(f"TTS xatosi: {e}")
        await query.message.reply_text(f"🔊 Ovoz: {esc_md(text[:200])}")


# ==================== PDF GENERATOR ====================

def build_vorstellen_pdf(level, score, grammar_score, vocab_score, fluency_score,
                         detected_level, user_answers, improved_text,
                         tushuntirish="", errors=None, good_points=None,
                         yaxshilash_a1="", yaxshilash_a2="", yaxshilash_b1="", yaxshilash_b2="") -> bytes:
    """Vorstellen uchun PDF yaratish"""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm
    from reportlab.lib import colors
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    from reportlab.platypus import (
        Paragraph, Spacer, Table, TableStyle, HRFlowable,
        SimpleDocTemplate, KeepTogether,
    )
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from io import BytesIO

    errors = errors or []
    good_points = good_points or []

    # Ranglar
    C_PURPLE = colors.HexColor("#3C3489")
    C_PURPLE_L = colors.HexColor("#EEEDFE")
    C_TEAL = colors.HexColor("#085041")
    C_TEAL_L = colors.HexColor("#E1F5EE")
    C_CORAL = colors.HexColor("#712B13")
    C_CORAL_L = colors.HexColor("#FAECE7")
    C_GRAY = colors.HexColor("#444441")
    C_BLACK = colors.HexColor("#1A1A1A")

    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                           leftMargin=2*cm, rightMargin=2*cm,
                           topMargin=2*cm, bottomMargin=2*cm)

    styles = {
        "title": ParagraphStyle("title", fontSize=20, leading=26, textColor=C_PURPLE,
                                alignment=TA_CENTER, fontName="Helvetica-Bold"),
        "subtitle": ParagraphStyle("subtitle", fontSize=11, leading=16, textColor=C_GRAY,
                                   alignment=TA_CENTER, fontName="Helvetica"),
        "section": ParagraphStyle("section", fontSize=9, leading=12, textColor=colors.white,
                                  fontName="Helvetica-Bold"),
        "question_de": ParagraphStyle("qd", fontSize=14, leading=20, textColor=C_PURPLE,
                                      fontName="Helvetica-Bold"),
        "body": ParagraphStyle("body", fontSize=10, leading=15, textColor=C_BLACK, fontName="Helvetica"),
        "body_b": ParagraphStyle("body_b", fontSize=11, leading=16, textColor=C_BLACK, fontName="Helvetica-Bold"),
        "body_i": ParagraphStyle("body_i", fontSize=10, leading=14, textColor=C_GRAY, fontName="Helvetica-Oblique"),
        "error_w": ParagraphStyle("ew", fontSize=10, leading=14, textColor=colors.HexColor("#A32D2D"), fontName="Helvetica"),
        "error_r": ParagraphStyle("er", fontSize=10, leading=14, textColor=C_TEAL, fontName="Helvetica-Bold"),
        "word": ParagraphStyle("word", fontSize=10, leading=14, textColor=colors.HexColor("#633806"), fontName="Helvetica-Bold"),
    }

    story = []

    # Sarlavha
    story.append(Spacer(1, 1*cm))
    story.append(Paragraph("Vorstellen — Tahlil Natijasi", styles["title"]))
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph(f"Daraja: {level} | Yulduz: {score}/5", styles["subtitle"]))
    story.append(HRFlowable(width="100%", thickness=0.5, color=C_PURPLE, spaceAfter=0.8*cm))

    # Ballar
    score_data = [
        [Paragraph("Grammatika", styles["section"]),
         Paragraph("So'z boyligi", styles["section"]),
         Paragraph("Ravonlik", styles["section"])],
        [Paragraph(f"{grammar_score}/10", styles["body_b"]),
         Paragraph(f"{vocab_score}/10", styles["body_b"]),
         Paragraph(f"{fluency_score}/10", styles["body_b"])],
    ]
    score_t = Table(score_data, colWidths=[5.5*cm, 5.5*cm, 5.5*cm])
    score_t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), C_PURPLE),
        ("BACKGROUND", (0, 1), (-1, -1), C_PURPLE_L),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("ROUNDEDCORNERS", [4, 4, 4, 4]),
    ]))
    story.append(score_t)
    story.append(Spacer(1, 0.5*cm))

    # Tushuntirish
    if tushuntirish:
        story.append(Paragraph("💡 Tushuntirish", styles["question_de"]))
        story.append(Spacer(1, 0.2*cm))
        story.append(Paragraph(tushuntirish, styles["body"]))
        story.append(Spacer(1, 0.5*cm))

    # Xatolar
    if errors:
        story.append(Paragraph("📋 Xatolar", styles["question_de"]))
        story.append(Spacer(1, 0.2*cm))
        err_rows = [[Paragraph("❌ Xato", styles["error_w"]),
                     Paragraph("✓ To'g'ri", styles["error_r"])]]
        for e in errors[:5]:
            err_rows.append([Paragraph(e.get("xato", ""), styles["error_w"]),
                            Paragraph(e.get("togri", ""), styles["error_r"])])
        err_t = Table(err_rows, colWidths=[8*cm, 8*cm])
        err_t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F1EFE8")),
            ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#D3D1C7")),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        story.append(err_t)
        story.append(Spacer(1, 0.5*cm))

    # Yaxshilash variantlari
    for lvl_key, lvl_label in [("a1", "A1"), ("a2", "A2"), ("b1", "B1"), ("b2", "B2")]:
        lvl_text = locals().get(f"yaxshilash_{lvl_key}", "")
        if lvl_text:
            story.append(Paragraph(f"✨ {lvl_label} darajasida mukammal variant", styles["question_de"]))
            story.append(Spacer(1, 0.2*cm))
            story.append(Paragraph(lvl_text, styles["body"]))
            story.append(Spacer(1, 0.3*cm))

    doc.build(story)
    buf.seek(0)
    return buf.getvalue()


# ==================== AKTIV SPRECHHEN ====================

async def aktiv_sprechen_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Aktiv Sprechen - daraja tanlash"""
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("A1", callback_data="aktiv_level_a1"),
         InlineKeyboardButton("A2", callback_data="aktiv_level_a2")],
        [InlineKeyboardButton("B1", callback_data="aktiv_level_b1"),
         InlineKeyboardButton("B2", callback_data="aktiv_level_b2")],
        [InlineKeyboardButton("C1", callback_data="aktiv_level_c1")],
        [InlineKeyboardButton("🏠 Asosiy menyu", callback_data="main_menu")],
    ])

    if update.callback_query:
        query = update.callback_query
        await query.answer()
        await query.edit_message_text(
            "💬 *Aktiv Sprechen*\n\n"
            "Darajangizni tanlang:\n\n"
            "Har bir darajada 20 ta mavzu, har mavzuda 25 ta so'z va 1 ta hikoya.",
            parse_mode="MarkdownV2",
            reply_markup=keyboard,
        )
    else:
        await update.message.reply_text(
            "💬 *Aktiv Sprechen*\n\nDarajangizni tanlang:",
            parse_mode="MarkdownV2",
            reply_markup=keyboard,
        )
    return AI_AKTIV_LEVEL


async def aktiv_level_select(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Aktiv Sprechen - mavzu tanlash"""
    query = update.callback_query
    await query.answer()

    level = query.data.replace("aktiv_level_", "")
    context.user_data["aktiv_level"] = level

    db = get_db()
    topics = db.get_aktiv_topics(level)

    if not topics:
        await query.edit_message_text(
            f"⚠️ *{level.upper()}* darajasida hali mavzular mavjud emas.",
            parse_mode="MarkdownV2",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("↩️ Orqaga", callback_data="aktiv_sprechen")],
            ]),
        )
        return AI_AKTIV_LEVEL

    keyboard_rows = []
    for i in range(0, len(topics), 2):
        row = []
        for t in topics[i:i+2]:
            row.append(InlineKeyboardButton(
                f"{t['topic_id']}. {t['name_uz']}",
                callback_data=f"aktiv_topic_{t['id']}"
            ))
        keyboard_rows.append(row)
    keyboard_rows.append([InlineKeyboardButton("↩️ Orqaga", callback_data="aktiv_sprechen")])

    await query.edit_message_text(
        f"💬 *Aktiv Sprechen — {level.upper()}*\n\n"
        f"Mavzuni tanlang ({len(topics)} ta mavzu):",
        parse_mode="MarkdownV2",
        reply_markup=InlineKeyboardMarkup(keyboard_rows),
    )
    return AI_AKTIV_TOPIC


async def aktiv_topic_detail(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Aktiv Sprechen - mavzu tafsilotlari"""
    query = update.callback_query
    await query.answer()

    topic_db_id = int(query.data.replace("aktiv_topic_", ""))
    context.user_data["aktiv_topic_id"] = topic_db_id

    db = get_db()
    topic = db.get_aktiv_topic_by_id(topic_db_id)
    vocab = db.get_aktiv_vocab(topic_db_id)
    story = db.get_aktiv_story(topic_db_id)
    grammar = db.get_aktiv_grammar(topic_db_id)

    if not topic:
        await query.edit_message_text("❌ Mavzu topilmadi.")
        return AI_AKTIV_TOPIC

    text = (
        f"📚 *{esc_md(topic['name_de'])}*\n"
        f"🇺🇿 {esc_md(topic['name_uz'])}\n\n"
    )

    if vocab:
        text += f"📖 *Lug'at ({len(vocab)} ta so'z):*\n\n"
        for i, v in enumerate(vocab[:10], 1):
            text += f"{i}. *{esc_md(v['german'])}* — {esc_md(v['uzbek'])}\n"
        if len(vocab) > 10:
            text += f"_...va yana {len(vocab) - 10} ta so'z_\n"

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📖 Barcha so'zlarni ko'rish", callback_data="aktiv_vocab_all")],
        [InlineKeyboardButton("📖 Hikoya", callback_data="aktiv_story")],
        [InlineKeyboardButton("📊 Grammatika", callback_data="aktiv_grammar")],
        [InlineKeyboardButton("🔊 Ovozda eshitish", callback_data="aktiv_speak")],
        [InlineKeyboardButton("↩️ Mavzular", callback_data=f"aktiv_level_{topic['level']}")],
    ])

    await query.edit_message_text(text, parse_mode="MarkdownV2", reply_markup=keyboard)
    return AI_AKTIV_DETAIL


async def aktiv_detail_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Aktiv Sprechen detail tugmalari"""
    query = update.callback_query
    await query.answer()
    data = query.data

    db = get_db()
    topic_id = context.user_data.get("aktiv_topic_id", 0)
    topic = db.get_aktiv_topic_by_id(topic_id)
    level = topic.get("level", "a1") if topic else "a1"

    if data == "aktiv_vocab_all":
        vocab = db.get_aktiv_vocab(topic_id)
        text = f"📖 *{esc_md(topic['name_de'])} — Lug'at*\n\n"
        for i, v in enumerate(vocab, 1):
            article = f"{v['article']} " if v.get('article') else ""
            plural = f" ({v['plural']})" if v.get('plural') else ""
            text += f"{i}. *{esc_md(article + v['german'] + plural)}* — {esc_md(v['uzbek'])}\n"
            if v.get("example_de"):
                text += f"   _{esc_md(v['example_de'])}_\n"
            text += "\n"

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("↩️ Orqaga", callback_data=f"aktiv_topic_{topic_id}")],
        ])
        await query.edit_message_text(text[:4000], parse_mode="MarkdownV2", reply_markup=keyboard)

    elif data == "aktiv_story":
        story = db.get_aktiv_story(topic_id)
        if story:
            text = (
                f"📖 *{esc_md(story.get('title_de', ''))}*\n"
                f"🇺🇿 {esc_md(story.get('title_uz', ''))}\n\n"
                f"{esc_md(story.get('story_de', ''))}\n\n"
                f"🇺🇿 *Tarjima:*\n{esc_md(story.get('story_uz', ''))}"
            )
        else:
            text = "📖 Hikoya hali qo'shilmagan."

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔊 Ovozda eshitish", callback_data="aktiv_speak_story")],
            [InlineKeyboardButton("↩️ Orqaga", callback_data=f"aktiv_topic_{topic_id}")],
        ])
        await query.edit_message_text(text, parse_mode="MarkdownV2", reply_markup=keyboard)

    elif data == "aktiv_grammar":
        grammar = db.get_aktiv_grammar(topic_id)
        if grammar:
            text = f"📊 *Grammatika — {esc_md(topic['name_de'])}*\n\n"
            for g in grammar:
                text += f"📌 *{esc_md(g['rule_name'])}*\n{esc_md(g['rule_explanation'])}\n\n"
                if g.get("examples"):
                    text += f"_Misollar:_\n{esc_md(g['examples'])}\n\n"
        else:
            text = "📊 Grammatika qoidalari hali qo'shilmagan."

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("↩️ Orqaga", callback_data=f"aktiv_topic_{topic_id}")],
        ])
        await query.edit_message_text(text, parse_mode="MarkdownV2", reply_markup=keyboard)

    elif data in ("aktiv_speak", "aktiv_speak_story"):
        if data == "aktiv_speak_story":
            story = db.get_aktiv_story(topic_id)
            text_to_speak = story.get("story_de", "") if story else ""
        else:
            vocab = db.get_aktiv_vocab(topic_id)
            words = [v['german'] for v in vocab[:10]]
            text_to_speak = ", ".join(words) if words else "So'zlar mavjud emas."

        if text_to_speak:
            await query.answer("🔊 Ovoz tayyorlanmoqda...")
            try:
                await speak_text(query, text_to_speak[:500])
            except Exception as e:
                logger.error(f"Ovoz yuborishda xato: {e}")
        else:
            await query.answer("⚠️ Ovoz uchun matn yo'q", show_alert=True)

    return AI_AKTIV_DETAIL


# ==================== LUG'AT ====================

async def lugat_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Lug'at menyu"""
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("A1", callback_data="lugat_a1"), InlineKeyboardButton("A2", callback_data="lugat_a2")],
        [InlineKeyboardButton("B1", callback_data="lugat_b1"), InlineKeyboardButton("B2", callback_data="lugat_b2")],
        [InlineKeyboardButton("C1", callback_data="lugat_c1")],
        [InlineKeyboardButton("🏠 Asosiy menyu", callback_data="main_menu")],
    ])

    if update.callback_query:
        query = update.callback_query
        await query.answer()
        await query.edit_message_text(
            "📖 *Lug'at*\n\nDarajangizni tanlang:",
            parse_mode="MarkdownV2",
            reply_markup=keyboard,
        )
    else:
        await update.message.reply_text(
            "📖 *Lug'at*\n\nDarajangizni tanlang:",
            parse_mode="MarkdownV2",
            reply_markup=keyboard,
        )
    return LUGAT_MENU


async def lugat_level(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Lug'at - kitob tanlash"""
    query = update.callback_query
    await query.answer()

    level = query.data.replace("lugat_", "")
    context.user_data["lugat_level"] = level

    db = get_db()
    books = db.get_lugat_books(level)

    if not books:
        await query.edit_message_text(
            f"⚠️ *{level.upper()}* darajasida hali lug'atlar mavjud emas.",
            parse_mode="MarkdownV2",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("↩️ Orqaga", callback_data="lugat_menu")],
            ]),
        )
        return LUGAT_LEVEL

    keyboard_rows = [[InlineKeyboardButton(f"📗 {b['name']}", callback_data=f"lugat_book_{b['id']}")] for b in books]
    keyboard_rows.append([InlineKeyboardButton("↩️ Orqaga", callback_data="lugat_menu")])

    await query.edit_message_text(
        f"📖 *Lug'at — {level.upper()}*\n\nKitobni tanlang:",
        parse_mode="MarkdownV2",
        reply_markup=InlineKeyboardMarkup(keyboard_rows),
    )
    return LUGAT_BOOK


async def lugat_book_select(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Lug'at - bo'lim tanlash"""
    query = update.callback_query
    await query.answer()

    book_id = int(query.data.replace("lugat_book_", ""))
    context.user_data["lugat_book_id"] = book_id

    db = get_db()
    chapters = db.get_lugat_chapters(book_id)

    if not chapters:
        await query.edit_message_text(
            "⚠️ Bu kitobda hali bo'limlar mavjud emas.",
            parse_mode="MarkdownV2",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("↩️ Orqaga", callback_data=f"lugat_{context.user_data.get('lugat_level', 'a1')}")],
            ]),
        )
        return LUGAT_BOOK

    keyboard_rows = [[InlineKeyboardButton(f"📄 {c['name']}", callback_data=f"lugat_ch_{c['id']}")] for c in chapters]
    keyboard_rows.append([InlineKeyboardButton("↩️ Orqaga", callback_data=f"lugat_{context.user_data.get('lugat_level', 'a1')}")])

    await query.edit_message_text(
        "📖 *Bo'limni tanlang:*",
        parse_mode="MarkdownV2",
        reply_markup=InlineKeyboardMarkup(keyboard_rows),
    )
    return LUGAT_CHAPTER


async def lugat_chapter_words(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Lug'at - so'zlarni ko'rsatish"""
    query = update.callback_query
    await query.answer()

    chapter_id = int(query.data.replace("lugat_ch_", ""))
    db = get_db()
    words = db.get_lugat_words(chapter_id)
    chapter = db.get_lugat_chapter_by_id(chapter_id)

    if not words:
        await query.edit_message_text(
            "⚠️ Bu bo'limda hali so'zlar mavjud emas.",
            parse_mode="MarkdownV2",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("↩️ Orqaga", callback_data=f"lugat_book_{context.user_data.get('lugat_book_id', 1)}")],
            ]),
        )
        return LUGAT_CHAPTER

    text = f"📖 *{esc_md(chapter.get('name', 'Lug\'at'))}*\n\n"
    for i, w in enumerate(words[:25], 1):
        text += f"{i}. *{esc_md(w['german'])}* — {esc_md(w['uzbek'])}\n"
        if w.get("izoh"):
            text += f"   📝 _{esc_md(w['izoh'])}_\n"

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔊 Ovozda eshitish", callback_data="lugat_speak")],
        [InlineKeyboardButton("↩️ Orqaga", callback_data=f"lugat_book_{context.user_data.get('lugat_book_id', 1)}")],
    ])

    await query.edit_message_text(text[:4000], parse_mode="MarkdownV2", reply_markup=keyboard)
    return LUGAT_WORDS


# ==================== TARJIMON ====================

async def tarjimon_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Tarjimon menyu"""
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🇺🇿 UZB → 🇩🇪 DEU", callback_data="tarj_uzb_deu")],
        [InlineKeyboardButton("🇩🇪 DEU → 🇺🇿 UZB", callback_data="tarj_deu_uzb")],
        [InlineKeyboardButton("🏠 Asosiy menyu", callback_data="main_menu")],
    ])

    if update.callback_query:
        query = update.callback_query
        await query.answer()
        await query.edit_message_text(
            "🌐 *Tarjimon*\n\nYo'nalishni tanlang:",
            parse_mode="MarkdownV2",
            reply_markup=keyboard,
        )
    else:
        await update.message.reply_text(
            "🌐 *Tarjimon*\n\nYo'nalishni tanlang:",
            parse_mode="MarkdownV2",
            reply_markup=keyboard,
        )
    return TARJIMON_MENU


async def tarjimon_direction(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Tarjimon yo'nalish tanlash"""
    query = update.callback_query
    await query.answer()

    direction = query.data.replace("tarj_", "")
    context.user_data["tarj_direction"] = direction

    if direction == "uzb_deu":
        text = "🇺🇿 *UZB → 🇩🇪 DEU*\n\nO'zbekcha matnni yuboring:"
        next_state = TARJIMON_UZB_DEU
    else:
        text = "🇩🇪 *DEU → 🇺🇿 UZB*\n\nNemischa matnni yuboring:"
        next_state = TARJIMON_DEU_UZB

    await query.edit_message_text(
        text,
        parse_mode="MarkdownV2",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("↩️ Orqaga", callback_data="tarjimon")],
        ]),
    )
    return next_state


async def tarjimon_process(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Tarjima qilish"""
    direction = context.user_data.get("tarj_direction", "uzb_deu")
    user_text = update.message.text.strip()

    if not user_text:
        await update.message.reply_text("❌ Matn bo'sh. Qayta yuboring.")
        return TARJIMON_UZB_DEU if direction == "uzb_deu" else TARJIMON_DEU_UZB

    loading = await update.message.reply_text("🔄 *Tarjima qilinmoqda...*", parse_mode="MarkdownV2")

    # Groq API orqali tarjima
    result = await groq_translate(user_text, direction)

    try:
        await loading.delete()
    except:
        pass

    tarjima = result.get("tarjima", "Tarjima qilinmadi")
    tushuntirish = result.get("tushuntirish", "")
    maslahat = result.get("maslahat", "")

    text = (
        f"🌐 *Tarjima natijasi*\n\n"
        f"🇺🇿 *Asl matn:*\n`{esc_md(user_text[:200])}`\n\n"
        f"🇩🇪 *Tarjima:*\n`{esc_md(tarjima[:500])}`\n\n"
    )
    if tushuntirish:
        text += f"📝 *Tushuntirish:*\n{esc_md(tushuntirish[:300])}\n\n"
    if maslahat:
        text += f"💡 *Maslahat:*\n{esc_md(maslahat[:200])}"

    await update.message.reply_text(
        text,
        parse_mode="MarkdownV2",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 Boshqa tarjima", callback_data=f"tarj_{direction}")],
            [InlineKeyboardButton("🏠 Asosiy menyu", callback_data="main_menu")],
        ]),
    )
    return TARJIMON_UZB_DEU if direction == "uzb_deu" else TARJIMON_DEU_UZB


async def groq_translate(text: str, direction: str) -> dict:
    """Groq API orqali tarjima"""
    if not GROQ_API_KEY:
        return {"tarjima": "API kalit topilmadi", "tushuntirish": "", "maslahat": ""}

    import httpx

    if direction == "uzb_deu":
        system_msg = (
            "Siz professional nemis tili tarjimonsiz. O'zbek tilidan nemis tiliga tarjima qiling. "
            "JSON formatida: {\"tarjima\": \"nemischa\", \"tushuntirish\": \"grammatik tushuntirish o'zbek tilida\", \"maslahat\": \"qo'llash maslahati\"}"
        )
    else:
        system_msg = (
            "Siz professional nemis tili tarjimonsiz. Nemis tilidan o'zbek tiliga tarjima qiling. "
            "JSON formatida: {\"tarjima\": \"o'zbekcha\", \"tushuntirish\": \"grammatik tushuntirish o'zbek tilida\", \"maslahat\": \"qo'llash maslahati\"}"
        )

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
                json={
                    "model": "llama3-70b-8192",
                    "messages": [
                        {"role": "system", "content": system_msg},
                        {"role": "user", "content": text},
                    ],
                    "max_tokens": 1024,
                    "response_format": {"type": "json_object"},
                },
            )
            data = resp.json()
            raw = data["choices"][0]["message"]["content"]
            return json.loads(raw)
    except Exception as e:
        logger.error(f"Tarjima xatosi: {e}")
        return {"tarjima": f"Xato: {str(e)}", "tushuntirish": "", "maslahat": ""}


# ==================== SAYFA ====================

async def sayfa_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Sayfa menyu"""
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📗 B1 TELC", callback_data="sayfa_b1telc")],
        [InlineKeyboardButton("📦 Qolgan Materiallar", callback_data="sayfa_qolgan")],
        [InlineKeyboardButton("🏠 Asosiy menyu", callback_data="main_menu")],
    ])

    if update.callback_query:
        query = update.callback_query
        await query.answer()
        await query.edit_message_text(
            "📚 *Sayfa*\n\nKitob va audio materiallar:",
            parse_mode="MarkdownV2",
            reply_markup=keyboard,
        )
    else:
        await update.message.reply_text(
            "📚 *Sayfa*\n\nKitob va audio materiallar:",
            parse_mode="MarkdownV2",
            reply_markup=keyboard,
        )
    return SAYFA_MENU


async def sayfa_book(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Sayfa - kitob tanlash"""
    query = update.callback_query
    await query.answer()

    book_key = query.data.replace("sayfa_", "")
    context.user_data["sayfa_book"] = book_key

    db = get_db()
    materials = db.get_sayfa_materials(book_key)

    if not materials:
        await query.edit_message_text(
            "⚠️ Hali materiallar mavjud emas.",
            parse_mode="MarkdownV2",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("↩️ Orqaga", callback_data="sayfa_menu")],
            ]),
        )
        return SAYFA_BOOK

    keyboard_rows = []
    for m in materials:
        emoji = "🎵" if m.get('audio_path') else "📄" if m.get('pdf_path') else "📎"
        keyboard_rows.append([InlineKeyboardButton(f"{emoji} {m['name']}", callback_data=f"sayfa_mat_{m['id']}")])
    keyboard_rows.append([InlineKeyboardButton("↩️ Orqaga", callback_data="sayfa_menu")])

    await query.edit_message_text(
        "📚 *Materiallar:*",
        parse_mode="MarkdownV2",
        reply_markup=InlineKeyboardMarkup(keyboard_rows),
    )
    return SAYFA_BOOK


# ==================== KITOB MATERIALLAR ====================

async def kitob_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Kitob materiallar menyu"""
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("A1", callback_data="kitob_a1"), InlineKeyboardButton("A2", callback_data="kitob_a2")],
        [InlineKeyboardButton("B1", callback_data="kitob_b1"), InlineKeyboardButton("B2", callback_data="kitob_b2")],
        [InlineKeyboardButton("C1", callback_data="kitob_c1"), InlineKeyboardButton("C2", callback_data="kitob_c2")],
        [InlineKeyboardButton("🏠 Asosiy menyu", callback_data="main_menu")],
    ])

    if update.callback_query:
        query = update.callback_query
        await query.answer()
        await query.edit_message_text(
            "📚 *Kitob Materiallar*\n\nDarajangizni tanlang:",
            parse_mode="MarkdownV2",
            reply_markup=keyboard,
        )
    else:
        await update.message.reply_text(
            "📚 *Kitob Materiallar*\n\nDarajangizni tanlang:",
            parse_mode="MarkdownV2",
            reply_markup=keyboard,
        )
    return KITOB_MENU


async def kitob_level(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Kitob - daraja tanlash"""
    query = update.callback_query
    await query.answer()

    level = query.data.replace("kitob_", "")
    context.user_data["kitob_level"] = level

    db = get_db()
    books = db.get_kitob_books(level)

    if not books:
        await query.edit_message_text(
            f"⚠️ *{level.upper()}* darajasida hali kitoblar mavjud emas.",
            parse_mode="MarkdownV2",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("↩️ Orqaga", callback_data="kitob_menu")],
            ]),
        )
        return KITOB_LEVEL

    keyboard_rows = [[InlineKeyboardButton(f"📚 {b['name']}", callback_data=f"kitob_book_{b['id']}")] for b in books]
    keyboard_rows.append([InlineKeyboardButton("↩️ Orqaga", callback_data="kitob_menu")])

    await query.edit_message_text(
        f"📚 *Kitoblar — {level.upper()}*\n\nKitobni tanlang:",
        parse_mode="MarkdownV2",
        reply_markup=InlineKeyboardMarkup(keyboard_rows),
    )
    return KITOB_BOOK


# ==================== KUNLIK SO'Z ====================

async def daily_word(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Kunlik so'z"""
    user_id = update.effective_user.id if update.message else update.callback_query.from_user.id
    db = get_db()
    word = db.get_daily_word(user_id)

    if not word:
        # AI dan yangi so'z olish
        word = await generate_daily_word()
        db.save_daily_word(user_id, word)

    sinonimlar = word.get("sinonimlar", "")
    if isinstance(sinonimlar, str):
        try:
            sinonimlar = json.loads(sinonimlar)
        except:
            sinonimlar = []
    sinonim_str = ", ".join(sinonimlar) if sinonimlar else ""

    text = (
        f"📖 *Kunlik so'z*\n\n"
        f"🇩🇪 *{esc_md(word.get('german', ''))}*\n"
        f"🇺🇿 {esc_md(word.get('uzbek', ''))}\n\n"
    )
    if word.get('izoh'):
        text += f"📝 *Izoh:*\n{esc_md(word['izoh'])}\n\n"
    if word.get('misol'):
        text += f"📌 *Misol:*\n_{esc_md(word['misol'])}_\n\n"
    if sinonim_str:
        text += f"🔁 *Sinonimlar:* {esc_md(sinonim_str)}"

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔊 Ovozda eshitish", callback_data="daily_speak")],
        [InlineKeyboardButton("📝 Yodlash", callback_data="daily_learn")],
        [InlineKeyboardButton("🏠 Asosiy menyu", callback_data="main_menu")],
    ])

    if update.callback_query:
        await update.callback_query.edit_message_text(text, parse_mode="MarkdownV2", reply_markup=keyboard)
    else:
        await update.message.reply_text(text, parse_mode="MarkdownV2", reply_markup=keyboard)

    # XP qo'shish
    db.add_xp(user_id, XP_REWARDS.get("daily_word", 15), "daily_word")

    return DAILY_WORD


async def generate_daily_word() -> dict:
    """AI dan kunlik so'z olish"""
    if not GROQ_API_KEY:
        return {
            "german": "das Wort",
            "uzbek": "so'z",
            "izoh": "Nemis tilidagi asosiy so'z",
            "misol": "Das Wort ist wichtig.",
            "sinonimlar": ["der Begriff", "die Vokabel"],
        }

    import httpx

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
                json={
                    "model": "llama3-70b-8192",
                    "messages": [
                        {"role": "system", "content": (
                            "Nemis tili o'qituvchisi. Har kuni yangi, qiziqarli so'z bering. "
                            "JSON: {\"german\": \"so'z\", \"uzbek\": \"tarjima\", \"izoh\": \"izoh o'zbek tilida\", "
                            "\"misol\": \"nemischa misol gap\", \"sinonimlar\": [\"sinonim1\", \"sinonim2\"]}"
                        )},
                        {"role": "user", "content": "Bugungi kunlik so'zni ber. A2-B1 darajasi."},
                    ],
                    "max_tokens": 512,
                    "response_format": {"type": "json_object"},
                },
            )
            data = resp.json()
            raw = data["choices"][0]["message"]["content"]
            return json.loads(raw)
    except Exception as e:
        logger.error(f"Kunlik so'z xatosi: {e}")
        return {
            "german": "das Wort",
            "uzbek": "so'z",
            "izoh": "Nemis tilidagi asosiy so'z",
            "misol": "Das Wort ist wichtig.",
            "sinonimlar": ["der Begriff"],
        }


# ==================== PROGRESS ====================

async def progress_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Progress ko'rish"""
    user_id = update.effective_user.id if update.message else update.callback_query.from_user.id
    db = get_db()
    user = db.get_user(user_id)
    xp = user.get("total_xp", 0) if user else 0
    history = db.get_progress_history(user_id, limit=10)

    text = (
        f"📊 *Progressim*\n\n"
        f"⭐ *Jami XP:* {xp}\n"
        f"📚 *Daraja:* {esc_md(LEVEL_LABELS.get(user.get('current_level', 'a1'), 'A1'))}\n\n"
        f"📋 *So'ngi faoliyatlar:*\n"
    )
    for h in history[:5]:
        text += f"• {esc_md(h.get('activity_type', ''))}: +{h.get('xp_amount', 0)} XP\n"

    # Progress rasm yaratish
    try:
        img_buf = generate_progress_chart(user_id, xp, history)
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📊 Batafsil grafik", callback_data="progress_chart")],
            [InlineKeyboardButton("🏠 Asosiy menyu", callback_data="main_menu")],
        ])

        if update.callback_query:
            await update.callback_query.delete_message()
            await context.bot.send_photo(
                chat_id=update.callback_query.message.chat_id,
                photo=img_buf,
                caption=text,
                parse_mode="MarkdownV2",
                reply_markup=keyboard,
            )
        else:
            await update.message.reply_photo(
                photo=img_buf,
                caption=text,
                parse_mode="MarkdownV2",
                reply_markup=keyboard,
            )
    except Exception as e:
        logger.error(f"Progress rasm xatosi: {e}")
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🏠 Asosiy menyu", callback_data="main_menu")],
        ])
        if update.callback_query:
            await update.callback_query.edit_message_text(text, parse_mode="MarkdownV2", reply_markup=keyboard)
        else:
            await update.message.reply_text(text, parse_mode="MarkdownV2", reply_markup=keyboard)

    return PROGRESS_MENU


def generate_progress_chart(user_id: int, total_xp: int, history: list) -> io.BytesIO:
    """Progress grafigini rasm sifatida yaratish"""
    from PIL import Image, ImageDraw, ImageFont

    W, H = 800, 600
    img = Image.new("RGB", (W, H), "#1a1a2e")
    draw = ImageDraw.Draw(img)

    try:
        font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 28)
        font_text = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
    except:
        font_title = ImageFont.load_default()
        font_text = ImageFont.load_default()
        font_small = ImageFont.load_default()

    # Sarlavha
    draw.text((W//2, 30), "Deutsch Meister PRO", fill="#e94560", font=font_title, anchor="mm")
    draw.text((W//2, 70), f"Progress - User {user_id}", fill="#ffffff", font=font_text, anchor="mm")

    # XP ko'rsatkichi
    draw.rounded_rectangle([50, 120, W-50, 180], radius=10, fill="#16213e", outline="#e94560", width=2)
    xp_width = min((total_xp / 5000) * (W - 100), W - 100)
    draw.rounded_rectangle([50, 120, 50 + int(xp_width), 180], radius=10, fill="#e94560")
    draw.text((W//2, 150), f"XP: {total_xp} / 5000", fill="#ffffff", font=font_text, anchor="mm")

    # So'ngi faoliyatlar
    draw.text((50, 220), "So'ngi faoliyatlar:", fill="#e94560", font=font_text)
    y = 260
    for i, h in enumerate(history[:8]):
        color = "#00d9ff" if i % 2 == 0 else "#ffffff"
        draw.text((60, y), f"• {h.get('activity_type', '')}: +{h.get('xp_amount', 0)} XP", fill=color, font=font_small)
        y += 30

    # Footer
    draw.text((W//2, H-30), f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}", fill="#888888", font=font_small, anchor="mm")

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf


# ==================== SOZLAMALAR ====================

async def settings_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Sozlamalar menyu"""
    user_id = update.effective_user.id if update.message else update.callback_query.from_user.id
    db = get_db()
    user = db.get_user(user_id)

    voice = user.get("voice_preference", "female") if user else "female"
    speed = user.get("tts_speed", 1.0) if user else 1.0
    level = user.get("current_level", "a1") if user else "a1"

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"🗣 Ovoz: {voice}", callback_data="set_voice")],
        [InlineKeyboardButton(f"⚡ Tezlik: {speed}x", callback_data="set_speed")],
        [InlineKeyboardButton(f"📚 Daraja: {level.upper()}", callback_data="set_level")],
        [InlineKeyboardButton("🏠 Asosiy menyu", callback_data="main_menu")],
    ])

    text = (
        "⚙️ *Sozlamalar*\n\n"
        f"🗣 *Ovoz:* {voice}\n"
        f"⚡ *Tezlik:* {speed}x\n"
        f"📚 *Joriy daraja:* {level.upper()}\n\n"
        "O'zgartirish uchun tugmani bosing:"
    )

    if update.callback_query:
        await update.callback_query.edit_message_text(text, parse_mode="MarkdownV2", reply_markup=keyboard)
    else:
        await update.message.reply_text(text, parse_mode="MarkdownV2", reply_markup=keyboard)

    return SETTINGS_MENU


async def settings_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Sozlamalar tugmalari"""
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id
    db = get_db()

    if data == "set_voice":
        current = db.get_user(user_id).get("voice_preference", "female")
        new_voice = "male" if current == "female" else "female"
        db.update_user(user_id, voice_preference=new_voice)
        return await settings_menu(update, context)

    elif data == "set_speed":
        current = db.get_user(user_id).get("tts_speed", 1.0)
        speeds = [0.7, 0.8, 0.9, 1.0, 1.1, 1.2]
        idx = speeds.index(current) if current in speeds else 3
        new_speed = speeds[(idx + 1) % len(speeds)]
        db.update_user(user_id, tts_speed=new_speed)
        return await settings_menu(update, context)

    elif data == "set_level":
        levels = ["a1", "a2", "b1", "b2", "c1"]
        current = db.get_user(user_id).get("current_level", "a1")
        idx = levels.index(current) if current in levels else 0
        new_level = levels[(idx + 1) % len(levels)]
        db.update_user(user_id, current_level=new_level)
        return await settings_menu(update, context)

    return SETTINGS_MENU


# ==================== TEST ====================

async def test_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Test menyu"""
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("A1", callback_data="test_a1"), InlineKeyboardButton("A2", callback_data="test_a2")],
        [InlineKeyboardButton("B1", callback_data="test_b1"), InlineKeyboardButton("B2", callback_data="test_b2")],
        [InlineKeyboardButton("C1", callback_data="test_c1")],
        [InlineKeyboardButton("🏠 Asosiy menyu", callback_data="main_menu")],
    ])

    if update.callback_query:
        query = update.callback_query
        await query.answer()
        await query.edit_message_text(
            "📝 *Test*\n\nDarajangizni tanlang:",
            parse_mode="MarkdownV2",
            reply_markup=keyboard,
        )
    else:
        await update.message.reply_text(
            "📝 *Test*\n\nDarajangizni tanlang:",
            parse_mode="MarkdownV2",
            reply_markup=keyboard,
        )
    return TEST_MENU


async def test_level(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Test - savolni ko'rsatish"""
    query = update.callback_query
    await query.answer()

    level = query.data.replace("test_", "")
    context.user_data["test_level"] = level
    context.user_data["test_score"] = 0
    context.user_data["test_qnum"] = 0
    context.user_data["test_questions"] = generate_test_questions(level)

    return await show_test_question(query, context)


def generate_test_questions(level: str) -> list:
    """Test savollarini yaratish"""
    questions = {
        "a1": [
            {"q": "Ich ___ ein Student.", "options": ["bin", "bist", "ist", "sind"], "correct": 0},
            {"q": "Wie ___ du?", "options": ["heißt", "heiße", "heißen", "heißt ihr"], "correct": 0},
            {"q": "Das ist ___ Buch.", "options": ["ein", "eine", "einen", "einer"], "correct": 0},
        ],
        "a2": [
            {"q": "Ich ___ gestern ins Kino gegangen.", "options": ["bin", "war", "habe", "ist"], "correct": 0},
            {"q": "Wenn ich Zeit ___, würde ich kommen.", "options": ["habe", "hätte", "hatte", "haben"], "correct": 1},
            {"q": "Das Haus ___ vor 100 Jahren gebaut.", "options": ["wurde", "wurden", "war", "ist"], "correct": 0},
        ],
        "b1": [
            {"q": "Er behauptet, ___ krank gewesen zu sein.", "options": ["er", "sei", "es", "ihm"], "correct": 1},
            {"q": "___ du mir helfen, wäre ich sehr dankbar.", "options": ["Würdest", "Würde", "Wirst", "Warest"], "correct": 0},
            {"q": "Ich habe den Brief ___ geschrieben.", "options": ["gestern", "morgen", "jetzt", "bald"], "correct": 0},
        ],
        "b2": [
            {"q": "Wäre ich ___ gekommen, hätte ich das nicht verpasst.", "options": ["früher", "früh", "frühest", "am frühesten"], "correct": 0},
            {"q": "Es ist höchste Zeit, dass wir ___ Maßnahmen ergreifen.", "options": ["geeignete", "geeignet", "geeigneten", "geeigneter"], "correct": 0},
            {"q": "___ der Tatsache, dass er müde war, arbeitete er weiter.", "options": ["Trotz", "Wegen", "Während", "Dank"], "correct": 0},
        ],
        "c1": [
            {"q": "Seine Argumentation ___ zu wünschen übrig.", "options": ["lässt", "lässt nichts", "lässt viel", "lässt wenig"], "correct": 0},
            {"q": "Es steht außer ___, dass er kommen wird.", "options": ["Frage", "Zweifel", "Fragen", "Diskussion"], "correct": 0},
            {"q": "Er kam ___ zu spät zur Besprechung.", "options": ["wieder einmal", "noch einmal", "einmal mehr", "mehrmals"], "correct": 0},
        ],
    }
    return questions.get(level, questions["a1"])


async def show_test_question(query, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Test savolini ko'rsatish"""
    questions = context.user_data.get("test_questions", [])
    qnum = context.user_data.get("test_qnum", 0)

    if qnum >= len(questions):
        return await test_finish(query, context)

    q = questions[qnum]
    keyboard_rows = []
    for i, opt in enumerate(q["options"]):
        keyboard_rows.append([InlineKeyboardButton(opt, callback_data=f"test_ans_{i}")])

    await query.edit_message_text(
        f"📝 *Savol {qnum + 1}/{len(questions)}*\n\n{esc_md(q['q'])}",
        parse_mode="MarkdownV2",
        reply_markup=InlineKeyboardMarkup(keyboard_rows),
    )
    return TEST_QUIZ


async def test_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Test javobini qayta ishlash"""
    query = update.callback_query
    await query.answer()

    ans_idx = int(query.data.replace("test_ans_", ""))
    questions = context.user_data.get("test_questions", [])
    qnum = context.user_data.get("test_qnum", 0)

    if qnum < len(questions) and ans_idx == questions[qnum]["correct"]:
        context.user_data["test_score"] = context.user_data.get("test_score", 0) + 1

    context.user_data["test_qnum"] = qnum + 1
    return await show_test_question(query, context)


async def test_finish(query, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Test natijalari"""
    score = context.user_data.get("test_score", 0)
    questions = context.user_data.get("test_questions", [])
    total = len(questions)
    level = context.user_data.get("test_level", "a1")

    percentage = (score / total * 100) if total > 0 else 0

    if percentage >= 90:
        result = "🌟 A'lo!"
    elif percentage >= 70:
        result = "👍 Yaxshi!"
    elif percentage >= 50:
        result = "📚 O'rtacha"
    else:
        result = "💪 Yana mashq qiling"

    # XP qo'shish
    db = get_db()
    xp = XP_REWARDS.get("test_complete", 40) + score * 5
    db.add_xp(query.from_user.id, xp, "test", f"{level.upper()}: {score}/{total}")

    await query.edit_message_text(
        f"📝 *Test natijasi*\n\n"
        f"📚 Daraja: {level.upper()}\n"
        f"✅ To'g'ri javoblar: {score}/{total}\n"
        f"📊 Foiz: {percentage:.0f}%\n\n"
        f"{result}\n\n"
        f"🎁 *+{xp} XP qo'shildi!*",
        parse_mode="MarkdownV2",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 Qayta", callback_data=f"test_{level}")],
            [InlineKeyboardButton("🏠 Asosiy menyu", callback_data="main_menu")],
        ]),
    )
    return TEST_RESULT


# ==================== PASTKI TUGMA HANDLERLARI ====================

async def reply_keyboard_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Pastki doimiy tugmalarni qayta ishlash"""
    text = update.message.text

    if text == "🤖 AI Mentor":
        return await ai_mentor_menu(update, context)
    elif text == "💬 Aktiv Sprechen":
        return await aktiv_sprechen_menu(update, context)
    elif text == "📖 Lug'at":
        return await lugat_menu(update, context)
    elif text == "🌐 Tarjimon":
        return await tarjimon_menu(update, context)
    elif text == "📚 Sayfa":
        return await sayfa_menu(update, context)
    elif text == "📚 Kitob Materiallar":
        return await kitob_menu(update, context)
    elif text == "📖 Kunlik so'z":
        return await daily_word(update, context)
    elif text == "📊 Progressim":
        return await progress_menu(update, context)
    elif text == "📝 Test":
        return await test_menu(update, context)
    elif text == "⚙️ Sozlamalar":
        return await settings_menu(update, context)
    elif text == "🔐 Admin Panel":
        return await admin_panel(update, context)

    return MAIN_MENU


# ==================== CALLBACK HANDLERLAR ====================

async def callback_router(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Barcha callback_query larni yo'naltirish"""
    query = update.callback_query
    await query.answer()
    data = query.data

    # Asosiy menyu
    if data == "main_menu":
        return await show_main_menu(update, context)

    # Admin
    elif data == "admin_menu":
        return await admin_panel(update, context)
    elif data == "admin_users":
        return await admin_users(update, context)
    elif data == "admin_requests":
        return await admin_requests_view(update, context)
    elif data == "admin_stats":
        return await admin_stats(update, context)
    elif data == "admin_broadcast":
        return await admin_broadcast_start(update, context)
    elif data == "admin_resolve_all":
        db = get_db()
        for req in db.get_requests(status="pending"):
            db.update_request_status(req["id"], "resolved")
        return await admin_requests_view(update, context)

    # AI Mentor
    elif data == "ai_mentor":
        return await ai_mentor_menu(update, context)
    elif data == "ai_mentor_menu":
        return await ai_mentor_menu(update, context)
    elif data == "ai_vorstellen":
        return await vorstellen_start(update, context)
    elif data == "ai_level_detect":
        await query.edit_message_text(
            "🎯 *Daraja aniqlash* tez orada qo'shiladi.",
            parse_mode="MarkdownV2",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 AI Mentor", callback_data="ai_mentor")],
            ]),
        )
        return AI_MENTOR_MENU

    # Vorstellen natija tugmalari
    elif data.startswith("vs_"):
        return await vorstellen_result_handler(update, context)

    # Aktiv Sprechen
    elif data == "aktiv_sprechen":
        return await aktiv_sprechen_menu(update, context)
    elif data.startswith("aktiv_level_"):
        return await aktiv_level_select(update, context)
    elif data.startswith("aktiv_topic_"):
        return await aktiv_topic_detail(update, context)
    elif data in ("aktiv_vocab_all", "aktiv_story", "aktiv_grammar", "aktiv_speak", "aktiv_speak_story"):
        return await aktiv_detail_handler(update, context)

    # Lug'at
    elif data == "lugat_menu":
        return await lugat_menu(update, context)
    elif data.startswith("lugat_a") or data.startswith("lugat_b") or data.startswith("lugat_c"):
        return await lugat_level(update, context)
    elif data.startswith("lugat_book_"):
        return await lugat_book_select(update, context)
    elif data.startswith("lugat_ch_"):
        return await lugat_chapter_words(update, context)

    # Tarjimon
    elif data == "tarjimon":
        return await tarjimon_menu(update, context)
    elif data.startswith("tarj_"):
        return await tarjimon_direction(update, context)

    # Sayfa
    elif data == "sayfa_menu":
        return await sayfa_menu(update, context)
    elif data.startswith("sayfa_"):
        return await sayfa_book(update, context)

    # Kitob
    elif data == "kitob_menu":
        return await kitob_menu(update, context)
    elif data.startswith("kitob_"):
        return await kitob_level(update, context)

    # Progress
    elif data == "progress_chart":
        return await progress_menu(update, context)

    # Sozlamalar
    elif data in ("set_voice", "set_speed", "set_level"):
        return await settings_handler(update, context)

    # Test
    elif data == "test_menu":
        return await test_menu(update, context)
    elif data.startswith("test_"):
        return await test_level(update, context)

    # Kunlik so'z
    elif data == "menu_kunlik":
        return await daily_word(update, context)
    elif data in ("daily_speak", "daily_learn"):
        if data == "daily_speak":
            await query.answer("🔊 Ovoz funksiyasi ishlamoqda...")
        else:
            await query.answer("✅ So'z yodlandi!")
        return DAILY_WORD

    return MAIN_MENU


# ==================== MAIN ====================

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Xatolarni qayta ishlash"""
    logger.error(f"Xatolik: {context.error}")


def main() -> None:
    """Asosiy ishga tushirish funksiyasi"""
    if not TOKEN:
        logger.error("BOT_TOKEN topilmadi! Railway env da o'rnating.")
        return

    application = Application.builder().token(TOKEN).build()

    # Asosiy ConversationHandler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            REG_PHONE: [
                MessageHandler(filters.CONTACT, receive_phone),
            ],
            MAIN_MENU: [
                CallbackQueryHandler(callback_router),
            ],
            # Admin
            ADMIN_MENU: [
                CallbackQueryHandler(callback_router),
            ],
            ADMIN_USERS: [
                CallbackQueryHandler(callback_router),
            ],
            ADMIN_REQUESTS: [
                CallbackQueryHandler(callback_router),
            ],
            ADMIN_STATS: [
                CallbackQueryHandler(callback_router),
            ],
            ADMIN_BROADCAST: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, admin_broadcast_send),
            ],
            # AI Mentor
            AI_MENTOR_MENU: [
                CallbackQueryHandler(callback_router),
            ],
            AI_VORSTELLEN_START: [
                CallbackQueryHandler(vorstellen_collect),
                MessageHandler(filters.TEXT & ~filters.COMMAND, vorstellen_collect),
                MessageHandler(filters.VOICE | filters.AUDIO, vorstellen_collect),
            ],
            AI_VORSTELLEN_RESULT: [
                CallbackQueryHandler(callback_router),
            ],
            # Aktiv Sprechen
            AI_AKTIV_LEVEL: [
                CallbackQueryHandler(callback_router),
            ],
            AI_AKTIV_TOPIC: [
                CallbackQueryHandler(callback_router),
            ],
            AI_AKTIV_DETAIL: [
                CallbackQueryHandler(callback_router),
            ],
            # Lug'at
            LUGAT_MENU: [
                CallbackQueryHandler(callback_router),
            ],
            LUGAT_LEVEL: [
                CallbackQueryHandler(callback_router),
            ],
            LUGAT_BOOK: [
                CallbackQueryHandler(callback_router),
            ],
            LUGAT_CHAPTER: [
                CallbackQueryHandler(callback_router),
            ],
            LUGAT_WORDS: [
                CallbackQueryHandler(callback_router),
            ],
            # Tarjimon
            TARJIMON_MENU: [
                CallbackQueryHandler(callback_router),
            ],
            TARJIMON_UZB_DEU: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, tarjimon_process),
            ],
            TARJIMON_DEU_UZB: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, tarjimon_process),
            ],
            # Sayfa
            SAYFA_MENU: [
                CallbackQueryHandler(callback_router),
            ],
            SAYFA_BOOK: [
                CallbackQueryHandler(callback_router),
            ],
            # Kitob
            KITOB_MENU: [
                CallbackQueryHandler(callback_router),
            ],
            KITOB_LEVEL: [
                CallbackQueryHandler(callback_router),
            ],
            KITOB_BOOK: [
                CallbackQueryHandler(callback_router),
            ],
            # Kunlik so'z
            DAILY_WORD: [
                CallbackQueryHandler(callback_router),
            ],
            # Progress
            PROGRESS_MENU: [
                CallbackQueryHandler(callback_router),
            ],
            # Sozlamalar
            SETTINGS_MENU: [
                CallbackQueryHandler(callback_router),
            ],
            # Test
            TEST_MENU: [
                CallbackQueryHandler(callback_router),
            ],
            TEST_QUIZ: [
                CallbackQueryHandler(test_answer),
            ],
            TEST_RESULT: [
                CallbackQueryHandler(callback_router),
            ],
        },
        fallbacks=[
            CommandHandler("start", start),
            MessageHandler(filters.TEXT & ~filters.COMMAND, reply_keyboard_handler),
        ],
    )

    application.add_handler(conv_handler)
    application.add_error_handler(error_handler)

    # Pastki tugmalar handleri (conversation tashqarisida)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reply_keyboard_handler))

    logger.info("Bot ishga tushdi!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
