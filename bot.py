import os
import sqlite3
from datetime import datetime

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)

# =========================
# CONFIGURAÇÕES
# =========================
TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise RuntimeError("BOT_TOKEN não configurado nas variáveis de ambiente")

# =========================
# BANCO DE DADOS
# =========================
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

# =========================
# COMANDOS
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Olá 👋 Eu sou seu assistente pessoal.\n\n"
        "Comandos disponíveis:\n"
        "/lembrete <DD/MM/AAAA HH:MM> <texto>\n"
        "/lembretes\n"
        "/nota <texto>\n"
        "/tarefas"
    )

async def add_note(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = " ".join(context.args)
    if not text:
        await update.message.reply_text("Use: /nota <texto>")
        return

    cursor.execute(
        "INSERT INTO notes (chat_id, text) VALUES (?, ?)",
        (update.effective_chat.id, text),
    )
    conn.commit()
    await update.message.reply_text("📝 Nota salva!")

async def add_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = " ".join(context.args)
    if not text:
        await update.message.reply_text("Use: /tarefa <texto>")
        return

    cursor.execute(
        "INSERT INTO tasks (chat_id, text) VALUES (?, ?)",
        (update.effective_chat.id, text),
    )
    conn.commit()
    await update.message.reply_text("✅ Tarefa adicionada!")

async def list_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cursor.execute(
        "SELECT text FROM tasks WHERE chat_id = ?",
        (update.effective_chat.id,),
    )
    rows = cursor.fetchall()

    if not rows:
        await update.message.reply_text("Nenhuma tarefa cadastrada.")
        return

    msg = "📋 Suas tarefas:\n"
    for i, row in enumerate(rows, start=1):
        msg += f"{i}. {row[0]}\n"

    await update.message.reply_text(msg)

async def add_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 3:
        await update.message.reply_text(
            "Use: /lembrete DD/MM/AAAA HH:MM <texto>"
        )
        return

    date_str = context.args[0]
    time_str = context.args[1]
    text = " ".join(context.args[2:])

    try:
        remind_time = datetime.strptime(
            f"{date_str} {time_str}", "%d/%m/%Y %H:%M"
        )
    except ValueError:
        await update.message.reply_text("Formato de data inválido.")
        return

    cursor.execute(
        "INSERT INTO reminders (chat_id, text, remind_time) VALUES (?, ?, ?)",
        (
            update.effective_chat.id,
            text,
            remind_time.isoformat(),
        ),
    )
    conn.commit()

    await update.message.reply_text("⏰ Lembrete criado com sucesso!")

async def list_reminders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cursor.execute(
        "SELECT text, remind_time FROM reminders WHERE chat_id = ?",
        (update.effective_chat.id,),
    )
    rows = cursor.fetchall()

    if not rows:
        await update.message.reply_text("Nenhum lembrete cadastrado.")
        return

    msg = "⏰ Seus lembretes:\n"
    for text, time in rows:
        dt = datetime.fromisoformat(time)
        msg += f"- {dt.strftime('%d/%m/%Y %H:%M')} → {text}\n"

    await update.message.reply_text(msg)

# =========================
# MAIN
# =========================
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("nota", add_note))
    app.add_handler(CommandHandler("tarefa", add_task))
    app.add_handler(CommandHandler("tarefas", list_tasks))
    app.add_handler(CommandHandler("lembrete", add_reminder))
    app.add_handler(CommandHandler("lembretes", list_reminders))

    app.run_polling()

if __name__ == "__main__":
    main()
