import os
import json
import asyncio
from http.server import BaseHTTPRequestHandler
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import sqlalchemy

# --- Environment Variables ---
BOT_TOKEN = os.getenv('8202067450:AAGZ-0OHMOmVlk-fjyiETLPHkTzbponbfic')
DATABASE_URL = os.getenv('postgresql://neondb_owner:npg_mMBQ3c7qjOFg@ep-noisy-frog-adt8ya3o-pooler.c-2.us-east-1.aws.neon.tech/neondb?sslmode=require')

# SQLAlchemy ইঞ্জিন তৈরি করুন (কানেকশন পুলিং-এর জন্য)
engine = sqlalchemy.create_engine(DATABASE_URL)

# --- Command Handlers ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_message = (
        "Welcome to the Digital Store! 🤖\n\n"
        "Available commands:\n"
        "/products - See the list of available items"
    )
    await update.message.reply_text(welcome_message)

async def products(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = "Sorry, couldn't fetch products right now."
    try:
        # ইঞ্জিন থেকে একটি কানেকশন নিন
        with engine.connect() as conn:
            result = conn.execute(sqlalchemy.text("SELECT name, price FROM products WHERE is_available = TRUE ORDER BY price;"))
            all_products = result.fetchall()
            
            if all_products:
                message = "✨ Available Products ✨\n\n"
                for product in all_products:
                    message += f"🔹 {product[0]} - ${product[1]:.2f}\n"
            else:
                message = "No products available at the moment. 🙁"
    except Exception as e:
        print(f"Database Error: {e}")
    
    await update.message.reply_text(message)

# --- Vercel Entry Point ---
class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            content_length = int(self.headers['Content-Length'])
            body = self.rfile.read(content_length)
            update_data = json.loads(body.decode('utf-8'))

            application = Application.builder().token(BOT_TOKEN).build()
            application.add_handler(CommandHandler("start", start))
            application.add_handler(CommandHandler("products", products))

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            update = Update.de_json(data=update_data, bot=application.bot)
            loop.run_until_complete(application.process_update(update))

            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'Success')
        except Exception as e:
            print(f"Error in handler: {e}")
            self.send_response(500)
            self.end_headers()
            self.wfile.write(b'Error')
        return