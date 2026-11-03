import sqlite3
import random
import os
from aiohttp import web
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor

API_TOKEN = '9273864217:AAHGHGVNb0nHVQTIuDhh7tuDKeMxJhRRL4w'  # Bot Token kee
ADMIN_ID = 5558713786  # Admin ID kee (Gemechu Reta)

EXCHANGE_RATE = 220.0  # 1 USDT = 220 ETB Rate

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# --- DATABASE SETUP (SQLite) ---
def init_db():
    conn = sqlite3.connect('virtual_card_bot.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            balance_usd REAL DEFAULT 0.0
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            card_number TEXT,
            expiry TEXT,
            cvv TEXT,
            brand TEXT,
            amount_usd REAL
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def get_user_balance(user_id):
    conn = sqlite3.connect('virtual_card_bot.db')
    cursor = conn.cursor()
    cursor.execute('SELECT balance_usd FROM users WHERE user_id = ?', (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else 0.0

def update_user_balance(user_id, amount):
    conn = sqlite3.connect('virtual_card_bot.db')
    cursor = conn.cursor()
    cursor.execute('INSERT OR IGNORE INTO users (user_id, username, balance_usd) VALUES (?, ?, 0.0)', (user_id, ""))
    cursor.execute('UPDATE users SET balance_usd = balance_usd + ? WHERE user_id = ?', (amount, user_id))
    conn.commit()
    conn.close()

# --- KEYBOARDS (English) ---
start_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
start_keyboard.row(KeyboardButton("➡️ Get Started"), KeyboardButton("❓ Help"))

main_menu_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
main_menu_keyboard.row(KeyboardButton("💸 Add Funds (USDT / Telebirr)"))
main_menu_keyboard.row(KeyboardButton("🛒 Create Virtual Card 💳"))
main_menu_keyboard.row(KeyboardButton("📋 My Virtual Cards 💳"))
main_menu_keyboard.row(KeyboardButton("📞 Support / Contact"))
main_menu_keyboard.row(KeyboardButton("🚪 Exit"))

deposit_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
deposit_keyboard.row(KeyboardButton("USDT (TRC20) / Telebirr"))
deposit_keyboard.row(KeyboardButton("🔙 Back to Menu"))

card_plans_keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
card_plans_keyboard.add(
    KeyboardButton("💳 $5 Card (1,100 ETB)"),
    KeyboardButton("💳 $10 Card (2,200 ETB)"),
    KeyboardButton("💳 $20 Card (4,400 ETB)"),
    KeyboardButton("💳 $50 Card (11,000 ETB)"),
    KeyboardButton("💳 $100 Card (22,000 ETB)"),
    KeyboardButton("🔙 Back to Menu")
)

brand_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
brand_keyboard.row(KeyboardButton("Visa"), KeyboardButton("MasterCard"))
brand_keyboard.row(KeyboardButton("🔙 Back to Menu"))

# --- HANDLERS ---
@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    conn = sqlite3.connect('virtual_card_bot.db')
    cursor = conn.cursor()
    cursor.execute('INSERT OR IGNORE INTO users (user_id, username, balance_usd) VALUES (?, ?, 0.0)', 
                   (message.from_user.id, message.from_user.username))
    conn.commit()
    conn.close()

    welcome_text = (
        "🌟 **Welcome to Apex Forex Edge Virtual Card Bot!** 🌟\n\n"
        "💳 Generate real international Virtual Visa & Mastercards instantly.\n"
        "💱 **Exchange Rate:** `1 USDT = 220 ETB`\n\n"
        "👉 Type **Hi** or click **Get Started** below to begin!"
    )
    await message.answer(welcome_text, parse_mode="Markdown", reply_markup=start_keyboard)

@dp.message_handler(lambda message: message.text == "➡️ Get Started")
async def handle_get_started(message: types.Message):
    await message.answer("✨ **To continue, please type:**\n`Hi`", parse_mode="Markdown")

@dp.message_handler(lambda message: message.text.lower() == "hi")
async def handle_hi(message: types.Message):
    balance = get_user_balance(message.from_user.id)
    etb_val = balance * EXCHANGE_RATE
    await message.answer("✅ **Login successful! Accessing your dashboard...**", parse_mode="Markdown")
    menu_text = (
        f"🎉 **Welcome back! Manage your account below:** 👇\n\n"
        f"💵 **Wallet Balance:** `${balance:.2f} USD` (`{etb_val:.2f} ETB`)"
    )
    await message.answer(menu_text, parse_mode="Markdown", reply_markup=main_menu_keyboard)

# --- ADMIN COMMAND: View All Created Cards ---
@dp.message_handler(commands=['admin_cards'])
async def admin_view_all_cards(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("⚠️ **You are not authorized to use this command!**")
        return
    
    conn = sqlite3.connect('virtual_card_bot.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT cards.id, cards.user_id, users.username, cards.card_number, cards.expiry, cards.cvv, cards.brand, cards.amount_usd 
        FROM cards 
        LEFT JOIN users ON cards.user_id = users.user_id
    ''')
    all_cards = cursor.fetchall()
    conn.close()
    
    if not all_cards:
        await message.answer("📂 **No virtual cards have been generated by any users yet.**", parse_mode="Markdown")
    else:
        response = "👑 **ADMIN PANEL: All Generated Virtual Cards**\n\n"
        for card in all_cards:
            response += (
                f"🆔 Card ID:\n"
                f"👤 **User ID:** `{card[1]}` (@{card[2] or 'No Username'})\n"
                f"💳 Brand: | **Balance:** `${card[7]}`\n"
                f"💳 **Number:** `{card[3]}`\n"
                f"📅 **Exp:** `{card[4]}` | 🔒 **CVV:** `{card[5]}`\n"
                f"----------------------------------------\n"
            )
        if len(response) > 4000:
            for x in range(0, len(response), 4000):
                await message.answer(response[x:x+4000], parse_mode="Markdown")
        else:
            await message.answer(response, parse_mode="Markdown")

@dp.message_handler(lambda message: message.text == "💸 Add Funds (USDT / Telebirr)")
async def handle_add_funds(message: types.Message):
    await message.answer("💵 **Select deposit method:**", parse_mode="Markdown", reply_markup=deposit_keyboard)

@dp.message_handler(lambda message: message.text == "USDT (TRC20) / Telebirr")
async def handle_deposit_info(message: types.Message):
    deposit_text = (
        "💎 **Deposit Instructions (1 USDT = 220 ETB)**\n\n"
        "📌 **USDT TRC20 Address:**\n`TDEvyq3VokpJWjPrvKRVz4mPXvVgWBP5GW`\n\n"
        "🏦 **Telebirr Account:** Gemechu Reta (+251917091612)\n\n"
        f"👤 **Your User ID (Memo/Ref):** `{message.from_user.id}`\n\n"
        "📋 _Transfer funds and send your transaction hash or receipt screenshot here for instant admin approval._"
    )
    await message.answer(deposit_text, parse_mode="Markdown", reply_markup=deposit_keyboard)

@dp.message_handler(lambda message: "Create Virtual Card" in message.text)
async def handle_create_card(message: types.Message):
    await message.answer("💠 **Please select your virtual card plan (Rate: 1 USDT = 220 ETB):**", parse_mode="Markdown", reply_markup=card_plans_keyboard)

@dp.message_handler(lambda message: "Card (" in message.text)
async def handle_card_plan_selection(message: types.Message):
    await message.answer("💡 **Almost there!**\nPlease provide the **Card Holder Name** (e.g., John Doe):", parse_mode="Markdown")

@dp.message_handler(lambda message: len(message.text.split()) >= 1 and message.text not in ["Visa", "MasterCard", "USDT (TRC20) / Telebirr", "💸 Add Funds (USDT / Telebirr)", "🛒 Create Virtual Card 💳", "📋 My Virtual Cards 💳", "📞 Support / Contact", "🚪 Exit", "🔙 Back to Menu"])
async def handle_name_input(message: types.Message):
    await message.answer("💳 **Please select the card brand:**", parse_mode="Markdown", reply_markup=brand_keyboard)

@dp.message_handler(lambda message: message.text in ["Visa", "MasterCard"])
async def handle_card_brand_selection(message: types.Message):
    user_id = message.from_user.id
    balance = get_user_balance(user_id)
    required_usd = 5.0  # $5 card (1,100 ETB)
    
    if user_id != ADMIN_ID and balance < required_usd:
        warning_text = (
            "⚠️ **Insufficient funds in your wallet!**\n"
            "Please fund your account first or contact support: @Apexforexsupport"
        )
        await message.answer(warning_text, parse_mode="Markdown", reply_markup=main_menu_keyboard)
    else:
        if user_id != ADMIN_ID:
            update_user_balance(user_id, -required_usd)
            card_info_text = f"💵 **Card Balance:** `${required_usd:.2f} USD` (`{required_usd * EXCHANGE_RATE:.2f} ETB`)"
        else:
            card_info_text = f"👑 **Admin Free Card** | 💵 **Balance:** `${required_usd:.2f} USD` (Free)"
        
        prefix = "4" if message.text == "Visa" else "5"
        card_num = f"{prefix}{random.randint(100,999)} {random.randint(1000,9999)} {random.randint(1000,9999)} {random.randint(1000,9999)}"
        cvv_num = f"{random.randint(100,999)}"
        expiry_date = "12/28"
        
        conn = sqlite3.connect('virtual_card_bot.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO cards (user_id, card_number, expiry, cvv, brand, amount_usd) VALUES (?, ?, ?, ?, ?, ?)',
                       (user_id, card_num, expiry_date, cvv_num, message.text, required_usd))
        conn.commit()
        conn.close()
        
        card_success = (
            f"🎉 **Virtual {message.text} Card Generated Successfully!**\n\n"
            f"💳 **Card Number:** `{card_num}`\n"
            f"📅 **Expiry Date:** `{expiry_date}`\n"
            f"🔒 **CVV:** `{cvv_num}`\n"
            f"{card_info_text}\n\n"
            f"🌍 _Ready for international online payments!_"
        )
        await message.answer(card_success, parse_mode="Markdown", reply_markup=main_menu_keyboard)

@dp.message_handler(lambda message: message.text == "📋 My Virtual Cards 💳")
async def show_user_cards(message: types.Message):
    user_id = message.from_user.id
    conn = sqlite3.connect('virtual_card_bot.db')
    cursor = conn.cursor()
    cursor.execute('SELECT card_number, expiry, cvv, brand, amount_usd FROM cards WHERE user_id = ?', (user_id,))
    cards = cursor.fetchall()
    conn.close()
    
    if not cards:
        await message.answer("📂 **You don't have any active virtual cards yet.**", parse_mode="Markdown", reply_markup=main_menu_keyboard)
    else:
        response = "📋 **Your Active Virtual Cards:**\n\n"
        for idx, card in enumerate(cards, 1):
            response += f"*{idx}. {card[3]} Card*\n💳 `{card[0]}`\n📅 Exp: `{card[1]}` | 🔒 CVV: `{card[2]}` | Bal: `${card[4]}`\n\n"
        await message.answer(response, parse_mode="Markdown", reply_markup=main_menu_keyboard)

@dp.message_handler(lambda message: message.text in ["🔙 Back to Menu", "🚪 Exit"])
async def back_to_menu(message: types.Message):
    balance = get_user_balance(message.from_user.id)
    etb_val = balance * EXCHANGE_RATE
    menu_text = f"🏠 **Main Menu**\n\n💵 **Wallet Balance:** `${balance:.2f} USD` (`{etb_val:.2f} ETB`)"
    await message.answer(menu_text, parse_mode="Markdown", reply_markup=main_menu_keyboard)

@dp.message_handler(lambda message: message.text == "📞 Support / Contact")
async def support_contact(message: types.Message):
    support_text = (
        "📞 **Support & Contact Center**\n\n"
        "For any inquiries, payment issues, or assistance, please contact our support team directly:\n\n"
        "👉 **Telegram Support:** @Apexforexsupport"
    )
    await message.answer(support_text, parse_mode="Markdown", reply_markup=main_menu_keyboard)

# Admin Approval: Receipt / Transaction Proof handling
@dp.message_handler(content_types=['photo'])
async def handle_receipt_photo(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username or "No Username"
    
    admin_keyboard = InlineKeyboardMarkup(row_width=2)
    admin_keyboard.add(
        InlineKeyboardButton("✅ Add $5 (1,100 ETB)", callback_data=f"app_{user_id}_5"),
        InlineKeyboardButton("✅ Add $10 (2,200 ETB)", callback_data=f"app_{user_id}_10"),
        InlineKeyboardButton("❌ Reject", callback_data=f"rej_{user_id}")
    )
    
    caption = (
        f"📥 **New Deposit Proof Received!**\n\n"
        f"👤 **User:** @{username} (ID: `{user_id}`)\n"
        f"📋 _Please verify transaction (1 USDT = 220 ETB) and approve balance._"
    )
    
    await bot.send_photo(
        chat_id=ADMIN_ID,
        photo=message.photo[-1].file_id,
        caption=caption,
        parse_mode="Markdown",
        reply_markup=admin_keyboard
    )
    
    await message.answer("⏳ **Deposit proof submitted successfully!** Admin is verifying your payment. Balance will be updated soon.")

@dp.callback_query_handler(lambda c: c.data.startswith(('app_', 'rej_')))
async def process_admin_decision(callback_query: types.CallbackQuery):
    data_parts = callback_query.data.split('_')
    action = data_parts[0]
    user_id = int(data_parts[1])
    
    if action == 'app':
        amount_usd = float(data_parts[2])
        update_user_balance(user_id, amount_usd)
        etb_added = amount_usd * EXCHANGE_RATE
        await bot.send_message(user_id, f"🎉 **Your deposit has been approved!** `${amount_usd} USD` (`{etb_added} ETB`) has been added to your wallet.")
        await callback_query.message.edit_caption("✅ **Approved & Balance Added Successfully!**")
    else:
        await bot.send_message(user_id, f"❌ **Your deposit verification failed or was rejected.** Contact support: @Apexforexsupport")
        await callback_query.message.edit_caption("❌ **Rejected!**")

# --- WEB SERVER FOR RENDER FREE WEB SERVICE (PORT BINDING) ---
async def handle_web(request):
    return web.Response(text="Bot is running!")

async def web_server():
    app = web.Application()
    app.router.add_get("/", handle_web)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    print(f"Web server started on port {port}")

if __name__ == '__main__':
    import asyncio
    loop = asyncio.get_event_loop()
    loop.create_task(web_server())
    print("Bot and Web Server are running...")
    executor.start_polling(dp, skip_updates=True)
