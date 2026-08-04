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


def self_ping_loop():
    time.sleep(5)
    url = os.environ.get(
        "RENDER_EXTERNAL_URL",
        f"http://127.0.0.1:{os.environ.get('PORT', 8080)}/",
    )

    while True:
        try:
            requests.get(url, timeout=5)
        except Exception:
            pass
        time.sleep(15)


def start_keep_alive():
    t_flask = Thread(target=run_flask)
    t_flask.daemon = True
    t_flask.start()

    t_ping = Thread(target=self_ping_loop)
    t_ping.daemon = True
    t_ping.start()


# ==================== CONFIGURATION ====================
BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = 7485181331
UPI_ID = "9467702174@pthdfc"
COUPON_EXPIRY = "31 August 2026"
FOOTER_TEXT = "\n\n💬 **Need help? Contact Admin:** @Kartikji3009"

# ==================== PRICES & STOCK ====================
PRICES = {
    "iphone_1500": 400,
    "iphone17pro_3pct": 1200,
    "android_5pct": 500,
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
    "android_5pct": [
        "CTSANDUBFKF",
        "CTSAND8MFNR",
        "CTSANDXMQ12",
        "CTSANDDTNPS",
        "CTSANDM4QE9",
        "CTSANDOT2SQ",
        "CTSANDNYJ14",
        "CTSANDAIAMB",
        "CTSAND4IYTU",
        "CTSAND7UTTD",
        "CTSAND4BVM2",
        "CTSANDLWMOA",
        "CTSANDESKG3",
        "CTSANDY6WWQ",
        "CTSANDA5MF3",
        "CTSAND5KRB6",
        "CTSAND5RAXK",
        "CTSANDDZQA2",
        "CTSANDKTQNH",
        "CTSANDWUPGC",
        "CTSANDNYGE6",
        "CTSANDG7R8X",
        "CTSANDSML24",
        "CTSANDCN1AC",
        "CTSAND60RCH",
        "CTSANDP60MN",
        "CTSAND0DG00",
        "CTSANDTAEUE",
        "CTSANDOKV7O",
        "CTSANDFDRPA",
        "CTSANDPQNWU",
        "CTSANDJAAVZ",
        "CTSAND6QWRY",
        "CTSANDVPKBU",
        "CTSANDXA17D",
        "CTSAND43MUI",
        "CTSAND7I5GQ",
        "CTSAND3KY8T",
        "CTSANDGUTHG",
        "CTSAND7FWF1",
        "CTSAND2FEAK",
        "CTSANDI1K27",
        "CTSAND5G9MT",
        "CTSANDLVF9Q",
        "CTSAND0PJMK",
        "CTSAND3X3FO",
        "CTSANDGLMGA",
        "CTSANDE451I",
        "CTSAND38D27",
        "CTSAND187VW",
        "CTSAND73063",
        "CTSAND88225",
        "CTSANDPBPQB",
    ],
}

USER_ORDERS = {}

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)


def get_coupon_name(c_type):
    if c_type == "iphone_1500":
        return "Flat ₹1500 OFF on iPhone"
    elif c_type == "iphone17pro_3pct":
        return "3% OFF on iPhone 17 Pro models"
    elif c_type == "android_5pct":
        return "5% OFF on android smartphone"
    return "Coupon"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton(
                f"📱 Flat ₹1500 OFF on iPhone15,16,16Plus - ₹{PRICES['iphone_1500']}",
                callback_data="select_iphone_1500",
            )
        ],
        [
            InlineKeyboardButton(
                f"📲 3% OFF on iPhone 17 Pro models - ₹{PRICES['iphone17pro_3pct']}",
                callback_data="select_iphone17pro_3pct",
            )
        ],
        [
            InlineKeyboardButton(
                f"🤖 5% OFF on android smartphone - ₹{PRICES['android_5pct']}",
                callback_data="select_android_5pct",
            )
        ],
    ]

    text = f"Hello Sir! 👋\n\n⏰ **All Coupons Valid Till: {COUPON_EXPIRY}**\n\nAapko Croma ka kaun sa coupon chahiye? Niche button daba kar select karein:{FOOTER_TEXT}"

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


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    if query.data in [
        "select_iphone_1500",
        "select_iphone17pro_3pct",
        "select_android_5pct",
    ]:
        if query.data == "select_iphone_1500":
            coupon_type = "iphone_1500"
        elif query.data == "select_iphone17pro_3pct":
            coupon_type = "iphone17pro_3pct"
        else:
            coupon_type = "android_5pct"

        if len(STOCK[coupon_type]) == 0:
            await query.message.reply_text(
                f"❌ Sorry Sir! Ye coupon abhi Out of Stock hai.{FOOTER_TEXT}",
                parse_mode="Markdown",
            )

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
            f"{FOOTER_TEXT}"
        )

        await query.message.reply_text(message_text, parse_mode="Markdown")


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    user_id = user.id
    text = update.message.text.strip() if update.message.text else ""

    if user_id not in USER_ORDERS:
        return

    order = USER_ORDERS[user_id]

    if order.get("step") == "WAITING_FOR_QUANTITY":
        if text.isdigit() and int(text) > 0:
            qty = int(text)
            c_type = order["type"]
            available = len(STOCK[c_type])

            if qty > available:
                await update.message.reply_text(
                    f"⚠️ Stock me sirf {available} coupons bache hain!{FOOTER_TEXT}",
                    parse_mode="Markdown",
                )
                return

            total = qty * PRICES[c_type]
            order["qty"] = qty
            order["amount"] = total
            order["step"] = "WAITING_FOR_PAYMENT"

            c_name = get_coupon_name(c_type)

            # Dynamic QR Code URL generation with exact amount (Without showing UPI text)
            qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=350x350&data=upi://pay?pa={UPI_ID}%26pn=CromaStore%26am={total}"

            pay_msg = (
                f"📋 **Order Details:**\n"
                f"🎟 Coupon: {c_name}\n"
                f"🔢 Quantity: {qty}\n"
                f"⏳ Expiry: {COUPON_EXPIRY}\n"
                f"💵 Total Amount: **₹{total}**\n\n"
                f"📲 **Scan QR Code to Pay ₹{total}**\n\n"
                f"Payment karne ke baad yahan **12-Digit UTR Number** ya **Payment Screenshot** bhej dein."
                f"{FOOTER_TEXT}"
            )

            await update.message.reply_photo(
                photo=qr_url, caption=pay_msg, parse_mode="Markdown"
            )

    elif order.get("step") == "WAITING_FOR_PAYMENT":
        order["step"] = "VERIFYING"

        await update.message.reply_text(
            f"⏳ Payment details mil gayi hain. Admin verify karke aapko coupon bhej denge...{FOOTER_TEXT}",
            parse_mode="Markdown",
        )

        full_name = user.full_name or "Unknown User"
        username_str = (
            f"@{user.username}" if user.username else "No Username Set"
        )

        direct_chat_url = (
            f"https://t.me/{user.username}"
            if user.username
            else f"tg://user?id={user_id}"
        )

        admin_btn = [
            [
                InlineKeyboardButton(
                    "✅ Approve & Send", callback_data=f"app_{user_id}"
                ),
                InlineKeyboardButton(
                    "❌ Reject", callback_data=f"rej_{user_id}"
                ),
            ],
            [InlineKeyboardButton("💬 Direct Chat User", url=direct_chat_url)],
        ]

        c_name = get_coupon_name(order["type"])
        admin_msg = (
            f"🚨 **NEW PAYMENT RECEIVED**\n\n"
            f"👤 **Name:** {full_name}\n"
            f"🆔 **User ID:** `{user_id}`\n"
            f"🌐 **Username:** {username_str}\n"
            f"🎟 **Coupon:** {c_name}\n"
            f"🔢 **Quantity:** {order['qty']}\n"
            f"💵 **Amount:** ₹{order['amount']}\n"
            f"💬 **UTR/Msg:** {text if text else 'Photo Attached'}"
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

            await context.bot.send_message(
                chat_id=target_user_id,
                text=f"🎉 **Payment Verified!**\n\nAapke Coupons (Valid till {COUPON_EXPIRY}):\n{coupons_txt}\n\nDhanyawad! /start se naya order kar sakte hain.{FOOTER_TEXT}",
                parse_mode="Markdown",
            )

            updated_text = (
                query.message.caption or query.message.text
            ) + f"\n\n✅ **APPROVED ({qty} coupons sent)**"
            if query.message.photo:
                await query.edit_message_caption(caption=updated_text)
            else:
                await query.edit_message_text(text=updated_text)

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
            text=f"❌ Payment verification failed. Kripya correct screenshot ya UTR bhejien.{FOOTER_TEXT}",
            parse_mode="Markdown",
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
    start_keep_alive()

    if not BOT_TOKEN:
        print("ERROR: BOT_TOKEN is missing from Environment Variables!")
        return

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(admin_callback, pattern="^(app|rej)_"))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(
        MessageHandler(filters.ALL & ~filters.COMMAND, message_handler)
    )

    print("Bot is Starting Polling...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
