from telegram import Update
from telegram.ext import CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from .callbacks import handle_refresh, handle_tax_details, handle_tx_wallet_details, handle_token_summary
from .utils import get_user_data
import datetime
from .messages import show_summary
from services.token_analysis import main_async
from .config import logging

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    username = update.effective_user.username
    request_time = datetime.datetime.now()

    # Store user information
    if "users" not in context.user_data:
        context.user_data["users"] = {}

    if user_id not in context.user_data["users"]:
        context.user_data["users"][user_id] = {}

    context.user_data["users"][user_id]["username"] = username
    context.user_data["users"][user_id]["request_time"] = request_time.strftime("%Y-%m-%d %H:%M:%S")


    # Add the user information to a central log (example: print to console or store somewhere)
    logging.info(f"User {username} with ID {user_id} started interaction at {context.user_data['users'][user_id]['request_time']}")

    await update.message.reply_text("Please enter the token address:")

async def handle_address(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    token_address = update.message.text.strip()
    user_id = update.effective_user.id
    username = update.effective_user.username
    request_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # ✅ Ensure we store data per user using their user ID
    if "users" not in context.user_data:
        context.user_data["users"] = {}

    if user_id not in context.user_data["users"]:
        context.user_data["users"][user_id] = {}  # ✅ Ensure dictionary exists

    context.user_data["users"][user_id]["username"] = username
    context.user_data["users"][user_id]["request_time"] = request_time  # ✅ Store the string directly

    logging.info(f"User {username} (ID {user_id}) requested token {token_address} at {request_time}")

    data = await main_async(token_address)

    # Send summary and get the sent message object
    sent_message = await update.message.reply_text("Generating summary...")

    if user_id not in context.user_data["users"]:
        context.user_data["users"][user_id] = {}

    context.user_data["users"][user_id][sent_message.message_id] = {"token_data": data}

    # Show the initial summary view
    await show_summary(sent_message.message_id, update, context)

def register_handlers(application):
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_address))
    application.add_handler(CallbackQueryHandler(handle_tax_details, pattern="show_tax"))
    application.add_handler(CallbackQueryHandler(handle_token_summary, pattern="show_summary"))
    application.add_handler(CallbackQueryHandler(handle_refresh, pattern="refresh"))
    application.add_handler(CallbackQueryHandler(handle_tx_wallet_details, pattern="^show_tx_details\\|"))
    
