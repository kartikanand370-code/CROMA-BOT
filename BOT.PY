import logging
import os
import time
from threading import Thread
import requests
from flask import Flask
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# ==================== DUMMY WEB SERVER & AUTO KEEP-ALIVE ====================
app = Flask("")


@app.route("/")
def home():
    return "Bot is Active and Running!"


def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)


# 15-second Self Ping Thread to keep Render awake forever
def self_ping_loop():
    time.sleep(5)  # Wait for flask to start
    port = int(os.environ.get("PORT", 8080))
    url = f"http://127.0.0.1:{port}/"

    while True:
        try:
            requests.get(url, timeout=5)
        except Exception:
            pass
        time.sleep(15)  # Ping every 15 seconds


def start_keep_alive():
    t_flask = Thread(target=run_flask)
    t_flask.daemon = True
    t_flask.start()

    t_ping = Thread(target=self_ping_loop)
    t_ping.daemon = True
    t_ping.start()


# ==================== CONFIGURATION ====================
BOT_TOKEN = "8973177478:AAG1SskJdAYIpBzc21IHmFhsx0im3zPnTEc"
ADMIN_ID = 7485181331
UPI_ID = "9467702174@pthdfc"
COUPON_EXPIRY = "31 August 2026"

# ==================== PRICES & UPDATED STOCK ====================
PRICES = {
    "iphone_1500": 650,  # 1500 OFF wale coupon ka price (₹650)
    "iphone17pro_3pct": 1300,  # 17 Pro 3% OFF wale coupon ka price (₹1300)
}

STOCK = {
    "iphone_1500": [
        "CTSIPHZUJGQ",
        "CTSIPH7Z4JD",
        "CTSIPHUTGOI",
        "CTSIPHFK1Q9",
        "CTSIPHKZY3R",
    ],
    "iphone17pro_3pct": [
        "CTSLTP09BLL",
        "CTSLTPY0M9D",
        "CTSLTP87YJT",
        "CTSLTP9LFR4",
        "CTSLTPGPCMO",
    ],
}

USER_ORDERS = {}

# Clean Logs Setup
logging.basicConfig(level=logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)


def get_coupon_name(c_type):
    return (
        "Flat ₹1500 OFF on iPhone"
        if c_type == "iphone_1500"
        else "3% OFF on iPhone 17 Pro models"
    )


# /start Command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton(
                f"📱 Flat ₹1500 OFF on iPhone - ₹{PRICES['iphone_1500']}",
                callback_data="select_iphone_1500",
            )
        ],
        [
            InlineKeyboardButton(
                f"📲 3% OFF on iPhone 17 Pro models - ₹{PRICES['iphone17pro_3pct']}",
                callback_data="select_iphone17pro_3pct",
            )
        ],
    ]

    text = f"Hello Sir! 👋\n\n⏰ **All Coupons Valid Till: {COUPON_EXPIRY}**\n\nAapko Croma ka kaun sa coupon chahiye? Niche button daba kar select karein:"

    if update.message:
        await update.message.reply_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown",
        )
    elif update.callback_query:
        await update.callback_query.message.reply_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown",
        )


# Coupon Selection Handler
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    if query.data in ["select_iphone_1500", "select_iphone17pro_3pct"]:
        coupon_type = (
            "iphone_1500"
            if query.data == "select_iphone_1500"
            else "iphone17pro_3pct"
        )

        if len(STOCK[coupon_type]) == 0:
            await query.message.reply_text(
                "❌ Sorry Sir! Ye coupon abhi Out of Stock hai."
            )

            # Alert Admin when user hits out of stock
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=f"⚠️ **STOCK ALERT:** User `{user_id}` ne **{get_coupon_name(coupon_type)}** buy karne ki koshish ki, par wo **Out of Stock** hai!",
                parse_mode="Markdown",
            )
            return

        USER_ORDERS[user_id] = {
            "type": coupon_type,
            "step": "WAITING_FOR_QUANTITY",
        }

        c_title = get_coupon_name(coupon_type)

        message_text = (
            f"🎟 **{c_title}**\n\n"
            f"✅ Available Stock: {len(STOCK[coupon_type])}\n"
            f"💰 Price: ₹{PRICES[coupon_type]}/coupon\n"
            f"⏳ Expiry: **{COUPON_EXPIRY}**\n\n"
            f"Sir, kitni quantity chahiye? Number enter karein (e.g. 1, 2, 3):"
        )

        await query.message.reply_text(message_text, parse_mode="Markdown")


# Message Handler
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text.strip() if update.message.text else ""

    if user_id not in USER_ORDERS:
        return

    order = USER_ORDERS[user_id]

    # Step 1: User enters Quantity
    if order.get("step") == "WAITING_FOR_QUANTITY":
        if text.isdigit() and int(text) > 0:
            qty = int(text)
            c_type = order["type"]
            available = len(STOCK[c_type])

            if qty > available:
                await update.message.reply_text(
                    f"⚠️ Stock me sirf {available} coupons bache hain!"
                )
                return

            total = qty * PRICES[c_type]
            order["qty"] = qty
            order["amount"] = total
            order["step"] = "WAITING_FOR_PAYMENT"

            c_name = get_coupon_name(c_type)

            pay_msg = (
                f"📋 **Order Details:**\n"
                f"🎟 Coupon: {c_name}\n"
                f"🔢 Quantity: {qty}\n"
                f"⏳ Expiry: {COUPON_EXPIRY}\n"
                f"💵 Total: **₹{total}**\n\n"
                f"💳 **Pay Using UPI:**\n"
                f"UPI ID: `{UPI_ID}`\n\n"
                f"Payment karne ke baad yahan **12-Digit UTR Number** ya **Payment Screenshot** bhej dein."
            )
            await update.message.reply_text(pay_msg, parse_mode="Markdown")

    # Step 2: User sends Payment Proof
    elif order.get("step") == "WAITING_FOR_PAYMENT":
        order["step"] = "VERIFYING"

        await update.message.reply_text(
            "⏳ Payment details mil gayi hain. Admin verify karke aapko coupon bhej denge..."
        )

        admin_btn = [
            [
                InlineKeyboardButton(
                    "✅ Approve & Send", callback_data=f"app_{user_id}"
                ),
                InlineKeyboardButton(
                    "❌ Reject", callback_data=f"rej_{user_id}"
                ),
            ]
        ]

        c_name = get_coupon_name(order["type"])
        admin_msg = (
            f"🚨 **NEW PAYMENT RECEIVED**\n\n"
            f"👤 User ID: `{user_id}`\n"
            f"🎟 Type: {c_name}\n"
            f"🔢 Quantity: {order['qty']}\n"
            f"💵 Amount: ₹{order['amount']}\n"
            f"💬 UTR/Text: {text}"
        )

        if update.message.photo:
            await context.bot.send_photo(
                chat_id=ADMIN_ID,
                photo=update.message.photo[-1].file_id,
                caption=admin_msg,
                reply_markup=InlineKeyboardMarkup(admin_btn),
                parse_mode="Markdown",
            )
        else:
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=admin_msg,
                reply_markup=InlineKeyboardMarkup(admin_btn),
                parse_mode="Markdown",
            )


# Admin Action (Approve / Reject)
async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    action, target_user_id = data.split("_")
    target_user_id = int(target_user_id)

    if target_user_id not in USER_ORDERS:
        await query.message.reply_text(
            "⚠️ Order session expired ya already process ho chuka hai!"
        )
        return

    order = USER_ORDERS[target_user_id]
    c_type = order["type"]
    qty = order["qty"]

    if action == "app":
        if len(STOCK[c_type]) >= qty:
            delivered = [STOCK[c_type].pop(0) for _ in range(qty)]
            coupons_txt = "\n".join([f"`{c}`" for c in delivered])

            # Send coupons to User
            await context.bot.send_message(
                chat_id=target_user_id,
                text=f"🎉 **Payment Verified!**\n\nAapke Coupons (Valid till {COUPON_EXPIRY}):\n{coupons_txt}\n\nDhanyawad! /start se naya order kar sakte hain.",
                parse_mode="Markdown",
            )

            # Update Admin Message
            updated_text = (
                query.message.caption or query.message.text
            ) + f"\n\n✅ **APPROVED ({qty} coupons sent)**"
            if query.message.photo:
                await query.edit_message_caption(caption=updated_text)
            else:
                await query.edit_message_text(text=updated_text)

            # Stock Alert Check
            remaining_stock = len(STOCK[c_type])
            c_name = get_coupon_name(c_type)

            if remaining_stock == 0:
                await context.bot.send_message(
                    chat_id=ADMIN_ID,
                    text=f"🚨 **OUT OF STOCK ALERT!** 🚨\n\n**{c_name}** ke saare coupons khatam ho chuke hain (`0` bache hain)!",
                    parse_mode="Markdown",
                )
            elif remaining_stock <= 1:
                await context.bot.send_message(
                    chat_id=ADMIN_ID,
                    text=f"⚠️ **LOW STOCK WARNING!**\n\n**{c_name}** ka sirf `{remaining_stock}` coupon bacha hai.",
                    parse_mode="Markdown",
                )

        else:
            await query.message.reply_text(
                "❌ Stock khatam ho gaya hai! Pehle code me stock badhayein."
            )

        del USER_ORDERS[target_user_id]

    elif action == "rej":
        await context.bot.send_message(
            chat_id=target_user_id,
            text="❌ Payment verification failed. Kripya correct screenshot ya UTR bhejien.",
        )

        updated_text = (
            query.message.caption or query.message.text
        ) + "\n\n❌ **REJECTED**"
        if query.message.photo:
            await query.edit_message_caption(caption=updated_text)
        else:
            await query.edit_message_text(text=updated_text)

        del USER_ORDERS[target_user_id]


def main():
    # Start Web Server & 15-second Keep-Alive Self Ping Thread
    start_keep_alive()

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(admin_callback, pattern="^(app|rej)_"))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(
        MessageHandler(filters.ALL & ~filters.COMMAND, message_handler)
    )

    print("Bot is Running Successfully...")
    app.run_polling()


if __name__ == "__main__":
    main()
