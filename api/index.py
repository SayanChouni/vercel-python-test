import os
import json
import asyncio
import psycopg2
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# --- Vercel-এর Environment Variable থেকে টোকেন ও ডেটাবেস URL নিন ---
BOT_TOKEN = os.getenv('8202067450:AAGZ-0OHMOmVlk-fjyiETLPHkTzbponbfic')
DATABASE_URL = os.getenv('postgresql://neondb_owner:npg_mMBQ3c7qjOFg@ep-noisy-frog-adt8ya3o-pooler.c-2.us-east-1.aws.neon.tech/neondb?sslmode=requireL')

# --- কমান্ড হ্যান্ডলার ফাংশনগুলো ---

# /start কমান্ডের জন্য
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/start কমান্ড দিলে একটি স্বাগত বার্তা পাঠায়।"""
    welcome_message = (
        "Welcome to the Digital Store! 🤖\n\n"
        "You can buy awesome digital products here.\n\n"
        "Available commands:\n"
        "/products - See the list of available items"
    )
    await update.message.reply_text(welcome_message)

# /products কমান্ডের জন্য (ডেটাবেস সহ)
async def products(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """ডেটাবেস থেকে প্রোডাক্টের তালিকা এনে পাঠায়।"""
    conn = None
    product_list_message = "Sorry, couldn't fetch products right now. Please try again later."

    try:
        # ডেটাবেসের সাথে সংযোগ স্থাপন
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()

        # ডেটাবেস থেকে প্রোডাক্টের তথ্য আনা
        cur.execute("SELECT name, price FROM products WHERE is_available = TRUE ORDER BY price;")
        all_products = cur.fetchall()

        # ফলাফলটিকে সুন্দর করে সাজানো
        if all_products:
            product_list_message = "✨ Available Products ✨\n\n"
            for product in all_products:
                product_name = product[0]
                product_price = product[1]
                # '.2f' ব্যবহার করে মূল্যকে দুটি দশমিক স্থান পর্যন্ত দেখানো হচ্ছে
                product_list_message += f"🔹 {product_name} - ${product_price:.2f}\n"
        else:
            product_list_message = "No products available at the moment. 🙁"

        cur.close()

    except Exception as e:
        print(f"Database Error: {e}")

    finally:
        # সংযোগটি অবশ্যই বন্ধ করা
        if conn is not None:
            conn.close()

    await update.message.reply_text(product_list_message)

# --- Vercel-এর জন্য মূল হ্যান্ডলার ---
async def main(update_data):
    """Vercel থেকে আসা প্রতিটি অনুরোধ হ্যান্ডেল করে।"""
    application = Application.builder().token(BOT_TOKEN).build()

    # কমান্ড হ্যান্ডলার যোগ করুন
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("products", products))

    # টেলিগ্রাম থেকে আসা একটি মাত্র আপডেট প্রসেস করুন
    async with application:
        update = Update.de_json(data=update_data, bot=application.bot)
        await application.process_update(update)

def handler(event, context):
    """Vercel-এর জন্য মূল এন্ট্রি পয়েন্ট।"""
    try:
        update_data = json.loads(event['body'])
        asyncio.run(main(update_data))
        return {'statusCode': 200, 'body': 'Success'}
    except Exception as e:
        print(f"Error in handler: {e}")
        return {'statusCode': 500, 'body': 'Error'}