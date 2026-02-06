import os
import sqlite3
import time
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")

conn = sqlite3.connect("data.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS reminders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id INTEGER,
    text TEXT,
    remind_time TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id INTEGER,
    text TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id INTEGER,
    text TEXT
)
""")

conn.commit()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Olá! Sou seu assistente.\n\n"
        "Comandos:\n"
        "Lembrete: me lembra 09/01/2026 12:00 marcar médico\n"
        "Nota: anotar senha do portão 4589\n"
        "Tarefa: tarefa comprar remédio\n"
        "Listar: minhas tarefas, minhas notas"
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()
    chat_id = update.message.chat_id

    if "me lembra" in text:
        try:
            parts = text.split("me lembra")[1].strip()
            date_part, time_part, *msg = parts.split()
            remind_text = " ".join(msg)
            remind_time = f"{date_part} {time_part}"

            cursor.execute(
                "INSERT INTO reminders (chat_id, text, remind_time) VALUES (?, ?, ?)",
                (chat_id, remind_text, remind_time),
            )
            conn.commit()

            await update.message.reply_text("⏰ Lembrete salvo.")
        except:
            await update.message.reply_text("Formato inválido.")

    elif text.startswith("anotar"):
        note = text.replace("anotar", "").strip()
        cursor.execute(
            "INSERT INTO notes (chat_id, text) VALUES (?, ?)",
            (chat_id, note),
        )
        conn.commit()
        await update.message.reply_text("📝 Nota salva.")

    elif text.startswith("tarefa"):
        task = text.replace("tarefa", "").strip()
        cursor.execute(
            "INSERT INTO tasks (chat_id, text) VALUES (?, ?)",
            (chat_id, task),
        )
        conn.commit()
        await update.message.reply_text("✅ Tarefa adicionada.")

    elif "minhas tarefas" in text:
        cursor.execute("SELECT text FROM tasks WHERE chat_id=?", (chat_id,))
        tasks = cursor.fetchall()
        if tasks:
            msg = "\n".join([f"- {t[0]}" for t in tasks])
        else:
            msg = "Nenhuma tarefa."
        await update.message.reply_text(msg)

    elif "minhas notas" in text:
        cursor.execute("SELECT text FROM notes WHERE chat_id=?", (chat_id,))
        notes = cursor.fetchall()
        if notes:
            msg = "\n".join([f"- {n[0]}" for n in notes])
        else:
            msg = "Nenhuma nota."
        await update.message.reply_text(msg)


async def reminder_loop(app):
    while True:
        now = datetime.now().strftime("%d/%m/%Y %H:%M")
        cursor.execute(
            "SELECT id, chat_id, text FROM reminders WHERE remind_time=?",
            (now,),
        )
        rows = cursor.fetchall()

        for row in rows:
            reminder_id, chat_id, text = row
            await app.bot.send_message(chat_id, f"⏰ Lembrete: {text}")
            cursor.execute("DELETE FROM reminders WHERE id=?", (reminder_id,))
            conn.commit()

        time.sleep(30)


async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT, handle_message))

    app.job_queue.run_repeating(lambda ctx: reminder_loop(app), interval=30)

    await app.run_polling()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
