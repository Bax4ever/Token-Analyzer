import re
from telegram import Update

def format_number_with_spaces(number):
    """Format a number with spaces as thousand separators."""
    return "{:,.0f}".format(number).replace(",", " ")

def escape_markdown(text: str) -> str:
    """Escapes special characters for Markdown to prevent formatting issues."""
    return re.sub(r'([_*\[\]()~`>#+\-=|{}.!])', r'\\\1', text)

def get_user_data(update: Update):
    """Extract user ID and username from an update."""
    user_id = update.effective_user.id
    username = update.effective_user.username
    return user_id, username

def get_change_arrow(old_value, new_value):
    """Returns an emoji indicating whether the value increased, decreased, or stayed the same."""
    if new_value > old_value:
        return "⬆️"
    elif new_value < old_value:
        return "⬇️"
    else:
        return ""
