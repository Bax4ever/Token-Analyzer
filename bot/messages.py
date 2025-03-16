from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from .utils import format_number_with_spaces, escape_markdown
import datetime
from .config import logging


def generate_summary_response(data) -> str:
    if data.totalVolumen1=="N/A":
        totVol=0
    else:
        totVol=int(data.totalVolumen1)
    token_symbol=data.token_symbol
    token_address=data.token_address
    links_text = (
        " | ".join(
            f"[TG]({value})" if "tg" in key.lower() or "telegram" in key.lower()
            else f"[X]({value})" if "x" in key.lower()
            else f"[Web]({value})" if "web" in key.lower()
            else f"[{key.capitalize()}]({value})"
            for key, value in data.links.items()
        ) if data.links else "None"
    )
    if data.pairA:
        links_text += " | " + " | ".join([
            f"[DEXT](https://www.dextools.io/app/en/ether/pair-explorer/{data.pairA})",
            f"[DEXS](https://dexscreener.com/ethereum/{data.pairA})"
        ])
    maestro_bot_username ="MaestroSniperBot"  # Replace with actual bot username

    return (
        f"🪙 Token Details:\n"
        f"|[{token_symbol}](https://etherscan.io/token/{token_address})|{links_text}|`{token_address}`\n"
        f"Name: {data.token_name} | Symbol: {data.token_symbol}\n"
        f"💵 Market Cap: ${format_number_with_spaces(data.market_cap_usd)}{data.market_cap_arrow}\n"
        f"Total Supply: {format_number_with_spaces(data.total_supply)}\n"
        f"Liq:${format_number_with_spaces(data.reserveUSD)}|TotalTx: {data.tx_count}|(24h)Vol:${format_number_with_spaces(data.totalVolumen)}|TotVol:${format_number_with_spaces(totVol)}\n" 
        f"\n|[Trade with Maestro Bot](https://t.me/{maestro_bot_username}?start={token_address})|\n " 
        f"\n📊 Summary:\n"
        f"📈 Clog: {format_number_with_spaces(data.clog)} | {data.clog_percent:.1f}%\n"
        f"👛 Bundle Wallets: {data.b_count} | 🤖 Sniper Wallets: {data.s_count}\n"
        f"🔹 Initial Bundle Tokens:  {format_number_with_spaces(data.total_recivedB)} ({data.total_recivedB / data.total_supply * 100:.1f}%)\n"
        f"🔹 Initial Sniper Tokens: {format_number_with_spaces(data.total_recivedS)} ({data.total_recivedS / data.total_supply * 100:.1f}%)\n"
        f"🔹 Total Bundle Tokens: {format_number_with_spaces(data.total_bundle_balance)} ({data.total_bundle_balance / data.total_supply * 100:.1f}%){data.bundle_arrow}\n"
        f"🔹 Total Sniper Tokens: {format_number_with_spaces(data.total_sniper_balance)} ({data.total_sniper_balance / data.total_supply * 100:.1f}%){data.sniper_arrow}\n"
        f"💲 Unsold Worth: {data.unsold:.2f} ETH\n"
        f"💰 Total Bundle ETH: {data.total_ethb:.2f} ETH\n"
        f"💰 Total Sniper ETH: {data.total_eths:.2f} ETH\n" 
        f"[TokenSniffer](https://tokensniffer.com/token/1/{token_address})|[goPlus](https://gopluslabs.io/token-security/1/{token_address})\n"       
    )

def generate_tax_details(data) -> str:
    """Generates tax details by manually assigning each key a more user-friendly name."""
    
    if not data.tax:
        return "No tax information available."
    
    # Define a mapping of keys to more user-friendly labels
    tax_label_mapping = {
        "_initialBuyTax":"Initial Buy Tax",
        "_initialSellTax":"Initial Sell Tax",
        "_finalBuyTax":"Final Buy Tax",
        "_finalSellTax":"Final Sell Tax",
        "_reduceBuyTaxAt":"Reduce Buy Tax At Buy Count",
        "_reduceSellTaxAt":"Reduce Sell Tax At Buy Count",
        "_preventSwapBefore":"Prevent Swap Before Buy Count",
        "_transferTax":"Transfer Tax",
        "_buyCount":"Buy Count"
    }

    # Format each tax item into a more readable format
    formatted_lines = []
    for key, label in tax_label_mapping.items():
        # Use `get` to handle cases where the key might not exist
        value = data.tax.get(key, "N/A")  # If key doesn't exist, use "N/A"
        formatted_lines.append(f"{label}: {value}")

    # Join the formatted lines into a single string
    formatted_tax_details = "\n".join(formatted_lines)
    
    return f"📄 **Tax Details**\n\n{formatted_tax_details}"

def generate_tx_wallet_details(data, page_size=11) -> dict:
    """
    Generates detailed response of transaction and wallet details, split into pages.
    
    Args:
        data (TokenSummary): The token summary containing transaction data.
        page_size (int): Number of transactions per page.
    
    Returns:
        dict: Contains text for each page and pagination metadata.
    """
    transactions = data.combined_data if isinstance(data.combined_data, list) else []
    MAX_TELEGRAM_MESSAGE_LENGTH = 2220

    # Split transactions into pages
    pages = []
    current_page = []
    total_length = 0
    transaction_count =0
    for tx in transactions:
        transaction_count += 1
        if isinstance(tx, dict):
            # Extract transaction details
            tx_hash = tx.get("transactionHash", "")
            value_in_ether = tx.get("valueInEther", 0.0)
            token_value = tx.get("tokenValue", 0.0)
            received_percentage = tx.get("receivedPercentage", 0.0)
            token_balance = tx.get("tokenBalance", 0.0)
            balance_percentage = tx.get("balancePercentage", 0.0)
            eth_balance = tx.get("ethBalance", 0.0)
            from_address_short =tx.get("from"[:6])  # First 6 chars of the address
            # Filter relevant tags (e.g., 'sniper' or 'bundle')
            tags = tx.get("tags", [])
            filtered_tags = [tag for tag in tags if 'sniper' in tag.lower() or 'bundle' in tag.lower()]
            tags_text = ', '.join(filtered_tags) if filtered_tags else "No relevant tags"

            # Format the transaction hash link
            tx_link = f"[{from_address_short}](https://etherscan.io/tx/{tx_hash})"
            transaction_text = (
                f"\n{transaction_count}.{tx_link}"
                f"\n💰 {value_in_ether:.2f} ETH ➡️ {token_value:.1f} tokens ({received_percentage:.1f}%) |"
                f"\n📊 Balance: {token_balance:.1f} TOK ({balance_percentage:.0f}%) | Eth: {eth_balance:.2f} ETH | "
                f"{(tags_text)}\n"
            )

            # Check if adding this transaction will exceed the message limit
            if total_length + len(transaction_text) > MAX_TELEGRAM_MESSAGE_LENGTH:
                # Append current page to pages and reset for a new page
                pages.append(current_page)
                current_page = []
                total_length = 0

            # Append transaction to the current page
            current_page.append(transaction_text)
            total_length += len(transaction_text)

    # Add the last page if it has any transactions
    if current_page:
        pages.append(current_page)

    # Generate formatted text for each page
    formatted_pages = []
    for page_number, page_content in enumerate(pages, start=1):
        page_text = "🔗 **Recent Transactions**\n"
        page_text += "".join(page_content)
        page_text += f"\nPage {page_number} of {len(pages)}\n"
        formatted_pages.append(page_text)

    return {
        "pages": formatted_pages,
        "total_pages": len(pages)
    }

async def show_summary(message_id, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Displays the token summary view with a button to switch to tax details and transaction details."""
    
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

    data = context.user_data.get("users", {}).get(user_id, {}).get(message_id, {}).get("token_data", None)
    logging.info(f"User Show Summary {username} with ID {user_id} at { context.user_data["users"][user_id]["request_time"]}")
    if not data:
        await update.message.reply_text("No token data found. Please enter a valid address.")
        return

    summary_text = generate_summary_response(data)

    # Updated keyboard with the new button for Tx & Wallet Details
    keyboard = [
        [
            InlineKeyboardButton("🔍 Tax Details", callback_data=f"show_tax|{message_id}"),
            InlineKeyboardButton("📄 Tx & Wallet Details", callback_data=f"show_tx_details|{message_id}"),
            InlineKeyboardButton("🔄 Refresh", callback_data=f"refresh|{message_id}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Edit or send the message with summary details
    if hasattr(update, "callback_query") and update.callback_query:
        await update.callback_query.edit_message_text(
            text=summary_text,
            reply_markup=reply_markup,
            parse_mode="Markdown",
            disable_web_page_preview=True
        )
    elif hasattr(update, "message") and update.message:
        await update.message.reply_text(
            text=summary_text,
            reply_markup=reply_markup,
            parse_mode="Markdown",
            disable_web_page_preview=True
        )
