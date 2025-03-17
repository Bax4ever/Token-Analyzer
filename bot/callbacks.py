from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from .utils import get_user_data, get_change_arrow
from .messages import generate_tax_details, generate_tx_wallet_details, show_summary, generate_summary_response
import datetime
import re
import asyncio
from services.token_analysis import main_async
from .config import logging


async def handle_tx_wallet_details(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Displays the transaction and wallet details view with pagination support."""
    query = update.callback_query
    await query.answer()

    # Extract message ID and page number from the callback data
    try:
        data_parts = query.data.split('|')
        if len(data_parts) < 2:
            raise ValueError("Invalid format")

        _, message_id_str = data_parts[0:2]
        current_page = int(data_parts[2]) if len(data_parts) == 3 else 1
        message_id = int(message_id_str.strip())

    except (ValueError, IndexError):
        await query.edit_message_text("Invalid request format. Please try again.")
        return
    user_id = update.effective_user.id 
    # Retrieve data for this specific message ID
    data = context.user_data.get("users", {}).get(user_id, {}).get(message_id, {}).get("token_data", None)  # ✅ Fixed
    if not data:
        await query.edit_message_text("No token data found for this message.")
        return

    # Generate transaction and wallet details for all pages
    page_data = generate_tx_wallet_details(data)

    # Get the current page text and metadata
    if current_page < 1 or current_page > page_data["total_pages"]:
        await query.edit_message_text("Invalid page number. Please try again.")
        return

    page_text = page_data["pages"][current_page - 1]
     # Escape Markdown to avoid formatting errors

    # Create navigation buttons
    navigation_buttons = []
    if current_page > 1:
        navigation_buttons.append(InlineKeyboardButton("⬅️ Previous Page", callback_data=f"show_tx_details|{message_id}|{current_page - 1}"))
    if current_page < page_data["total_pages"]:
        navigation_buttons.append(InlineKeyboardButton("➡️ Next Page", callback_data=f"show_tx_details|{message_id}|{current_page + 1}"))

    # Add buttons to switch back to summary or refresh
    keyboard = [
        [
            InlineKeyboardButton("📊 Token Summary", callback_data=f"show_summary|{message_id}"),
            InlineKeyboardButton("🔍 Tax Details", callback_data=f"show_tax|{message_id}"),
        ],
        navigation_buttons  # Add navigation buttons as a separate row
    ]
    reply_markup = InlineKeyboardMarkup([row for row in keyboard if row])

    # Edit the message to show the selected page of transaction and wallet details
    await query.edit_message_text(
        text=page_text,
        reply_markup=reply_markup,
        parse_mode="Markdown",
        disable_web_page_preview=True
    )

async def handle_refresh(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    # Extract message ID from the callback data
    try:
        _, message_id_str = query.data.split('|')
        message_id = int(message_id_str)
    except ValueError:
        await query.edit_message_text("Invalid request format.")
        return

    # Initialize the message-specific storage if it doesn't exist
    if message_id not in context.user_data:
        context.user_data[message_id] = {}

    user_id = update.effective_user.id
    username = update.effective_user.username
    request_time = datetime.datetime.now()

    if "users" not in context.user_data:
        context.user_data["users"] = {}

    if user_id not in context.user_data["users"]:
        context.user_data["users"][user_id] = {}

    context.user_data["users"][user_id]["username"] = username
    context.user_data["users"][user_id]["request_time"] = request_time.strftime("%Y-%m-%d %H:%M:%S")


    # Retrieve refresh count from the message and update
    current_text = query.message.text
    match = re.search(r"🔄Refreshed Count : (\d+)", current_text)
    if match:
        refresh_count = int(match.group(1)) + 1
    else:
        refresh_count = 1
    context.user_data["users"][user_id][message_id]["refresh_count"] = refresh_count  # ✅ Fixed

    # Print logs for debugging
    logging.info(f"User Show Summary {username} with ID {user_id} at {context.user_data['users'][user_id][message_id]['refresh_count']}")
    logging.info(f"Message ID HF! {message_id}")

    # Retrieve the token data
    data = context.user_data.get("users", {}).get(user_id, {}).get(message_id, {}).get("token_data", None)  
    if not data:
        await query.edit_message_text("No token data found for this message.")
        return

    # Get old bundle and sniper percentages for comparison
    old_bundle_percentage = data.total_bundle_balance
    old_sniper_percentage = data.total_sniper_balance
    old_market_cap = data.market_cap_usd
    logging.debug(f"Old Bundle: {old_bundle_percentage}, Old Sniper: {old_sniper_percentage}|{old_market_cap}")

    # Retrieve the token address and refresh the data
    token_address = data.token_address
    updated_data = await main_async(token_address)

    # Update context with the new token data
    context.user_data["users"][user_id][message_id]["token_data"] = updated_data  # ✅ Correct storage


    # Get new values for bundle and sniper balances
    new_bundle_percentage = updated_data.total_bundle_balance
    new_sniper_percentage = updated_data.total_sniper_balance
    new_market_cap = updated_data.market_cap_usd
    # Determine arrows based on the comparison
    updated_data.bundle_arrow = get_change_arrow(old_bundle_percentage, new_bundle_percentage) if old_bundle_percentage is not None else ""
    updated_data.sniper_arrow = get_change_arrow(old_sniper_percentage, new_sniper_percentage) if old_sniper_percentage is not None else ""
    updated_data.market_cap_arrow = get_change_arrow(old_market_cap, new_market_cap) if old_market_cap is not None else ""
    logging.debug(f"New Bundle Arrow: {updated_data.bundle_arrow}, New Sniper Arrow: {updated_data.sniper_arrow}, New Market Cap Arrow: {updated_data.market_cap_arrow}")

    # Update context with the new percentages
    context.user_data[message_id]["bundle_percentage"] = new_bundle_percentage
    context.user_data[message_id]["sniper_percentage"] = new_sniper_percentage

    # Generate the updated summary
    summary_text = generate_summary_response(updated_data)

    # Create buttons for further actions
    keyboard = [
        [
            InlineKeyboardButton("🔍 Tax Details", callback_data=f"show_tax|{message_id}"),
            InlineKeyboardButton("📄 Tx & Wallet Details", callback_data=f"show_tx_details|{message_id}"),
            InlineKeyboardButton("🔄 Refresh", callback_data=f"refresh|{message_id}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        text=f"🔄Refreshed Count : {refresh_count}\n" + summary_text,
        reply_markup=reply_markup,
        parse_mode="Markdown",
        disable_web_page_preview=True
    )

    # Show a temporary message that disappears after 2 seconds
    temporary_message = await query.message.reply_text(f"Refreshed Count: {refresh_count}")
    await asyncio.sleep(2)
    await temporary_message.delete()

async def handle_tax_details(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Displays the tax details view with a button to switch to the token summary."""
    query = update.callback_query
    await query.answer()
    # Extract message ID from the callback data
    _, message_id_str = query.data.split('|')
    message_id = int(message_id_str)
    user_id = update.effective_user.id
    username = update.effective_user.username
    request_time = datetime.datetime.now()
    # Fetch token data
    if "users" not in context.user_data:
        context.user_data["users"] = {}

    if user_id not in context.user_data["users"]:
        context.user_data["users"][user_id] = {}

    context.user_data["users"][user_id]["username"] = username
    context.user_data["users"][user_id]["request_time"] = request_time.strftime("%Y-%m-%d %H:%M:%S")


    logging.info(f"User Show Summary {username} with ID {user_id} at { context.user_data["users"][user_id]["request_time"]}")
    logging.info(f"Message Id HTx:{message_id}")
    # Retrieve data for this specific message ID
    data = context.user_data.get("users", {}).get(user_id, {}).get(message_id, {}).get("token_data", None)  # ✅ Correct retrieval
    if not data:
        await query.edit_message_text("No token data found for this message.")
        return

    # Generate tax details text
    tax_text = generate_tax_details(data)

    # Escape problematic characters for MarkdownV2


    # Create buttons to switch back to summary or refresh
    keyboard = [
        [
            InlineKeyboardButton("📊 Token Summary", callback_data=f"show_summary|{message_id}"),
            InlineKeyboardButton("📄 Tx & Wallet Details", callback_data=f"show_tx_details|{message_id}"),
            InlineKeyboardButton("🔄 Refresh", callback_data=f"refresh|{message_id}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Enable MarkdownV2 for safe Markdown usage
    await query.edit_message_text(
        text=tax_text,
        reply_markup=reply_markup,
        parse_mode="MarkdownV2",
        disable_web_page_preview=True
    )

async def handle_token_summary(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Switches back to the token summary view."""
    query = update.callback_query
    await query.answer()  # Acknowledge the button press

    # Extract the message ID from the callback data
    _, message_id_str = query.data.split('|')
    message_id = int(message_id_str)
    user_id = update.effective_user.id
    username = update.effective_user.username
    request_time = datetime.datetime.now()
    # Fetch token data
    if "users" not in context.user_data:
        context.user_data["users"] = {}

    if user_id not in context.user_data["users"]:
        context.user_data["users"][user_id] = {}

    context.user_data["users"][user_id]["username"] = username
    context.user_data["users"][user_id]["request_time"] = request_time.strftime("%Y-%m-%d %H:%M:%S")


    logging.info(f"User Show Summary {username} with ID {user_id} at {context.user_data["users"][user_id]["request_time"]}")
    # Retrieve data for this specific message
    data = context.user_data.get("users", {}).get(user_id, {}).get(message_id, {}).get("token_data", None)

    if not data:
        await query.edit_message_text("No token data found for this message.")
        return

    # Generate the summary view again
    summary_text = generate_summary_response(data)

    # Create keyboard with message ID
    keyboard = [
        [
            InlineKeyboardButton("🔍 Tax Details", callback_data=f"show_tax|{message_id}"),
            InlineKeyboardButton("📄 Tx & Wallet Details", callback_data=f"show_tx_details|{message_id}"),
            InlineKeyboardButton("🔄 Refresh", callback_data=f"refresh|{message_id}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        text=summary_text,
        reply_markup=reply_markup,
        parse_mode="Markdown",
        disable_web_page_preview=True
    )

