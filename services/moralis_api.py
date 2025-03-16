import requests
import json
from web3 import Web3
from bot.config import MORALIS_API_KEY
from bot.config import logging


from functools import lru_cache
import time

cached_moralis_data = {}
cache_expiry_time = 300  # 5 minutes

def get_erc20_token_price_stats(token_address, chain="eth"):
    global cached_moralis_data
    current_time = time.time()

    # Check if cached value exists and is valid
    if token_address in cached_moralis_data and current_time - cached_moralis_data[token_address]["timestamp"] < cache_expiry_time:
        return cached_moralis_data[token_address]["data"]

    # Otherwise, make API request
    checksum_address = Web3.to_checksum_address(token_address)
    url = f"https://deep-index.moralis.io/api/v2.2/erc20/{checksum_address}/price?chain={chain}"
    headers = {"Accept": "application/json", "X-API-Key": MORALIS_API_KEY}

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        cached_moralis_data[token_address] = {"data": data, "timestamp": current_time}
        return data

    return {"error": "Failed to fetch token price"}


import requests
from web3 import Web3

def get_token_pairs_info(token_address, chain="eth"):
    """
    Retrieves liquidity, volume, price, and pair address information for an ERC20 token using the Moralis API.

    Args:
    - token_address (str): The token address for which you want to get liquidity pair information.
    - chain (str): The blockchain chain, default is Ethereum ("eth").

    Returns:
    - A tuple containing the token pair address, price in USD, liquidity in USD, 24-hour volume, 
      token0 symbol, and token1 symbol. If no data is found, defaults to `N/A` or `0.0`.
    """

    # Convert token address to checksum format using Web3
    checksum_address = Web3.to_checksum_address(token_address)

    # Moralis API endpoint to get token pair information
    url = f"https://deep-index.moralis.io/api/v2.2/erc20/{checksum_address}/pairs?chain={chain}"

    # Set headers with API key
    headers = {
        "Accept": "application/json",
        "X-API-Key": MORALIS_API_KEY
    }

    # Make the request
    response = requests.get(url, headers=headers)

    # ✅ Handle API errors gracefully
    if response.status_code != 200:
        logging.error(f"⚠️ Moralis API Error: {response.status_code}, Message: {response.text}")
        return "N/A", 0.0, 0.0, 0.0, "N/A", "N/A"  # Return defaults to prevent crashes

    # Parse JSON response
    response_json = response.json()

    # ✅ Ensure we have 'pairs' in the response and it's a list
    if 'pairs' not in response_json or not isinstance(response_json['pairs'], list) or len(response_json['pairs']) == 0:
        logging.debug("⚠️ No valid pair data found, returning default values.")
        return "N/A", 0.0, 0.0, 0.0, "N/A", "N/A"

    # ✅ Extract relevant information from the first available pair
    pair = response_json['pairs'][0]  # Take the first pair as the most relevant

    # ✅ Extract required fields from the pair, defaulting to safe values if missing
    pair_address = pair.get("pair_address", "N/A")
    price_usd = float(pair.get("usd_price", 0.0)) if pair.get("usd_price") is not None else 0.0
    liquidity_usd = float(pair.get("liquidity_usd", 0.0)) if pair.get("liquidity_usd") is not None else 0.0
    volume_24h_usd = float(pair.get("volume_24h_usd", 0.0)) if pair.get("volume_24h_usd") is not None else 0.0

    # ✅ Handle token symbols safely
    token0_symbol = (
        pair.get("pair", [{}])[0].get("token_symbol", "N/A") if isinstance(pair.get("pair", []), list) and len(pair.get("pair", [])) > 0 else "N/A"
    )
    token1_symbol = (
        pair.get("pair", [{}])[1].get("token_symbol", "N/A") if isinstance(pair.get("pair", []), list) and len(pair.get("pair", [])) > 1 else "N/A"
    )

    # ✅ Print extracted data for debugging
    logging.debug(f"🔍 Pair Data Extracted: Address={pair_address}, Price=${price_usd}, Liquidity=${liquidity_usd}, Volume_24h=${volume_24h_usd}, Token0={token0_symbol}, Token1={token1_symbol}")

    # Return tuple with extracted data
    return pair_address, price_usd, liquidity_usd, volume_24h_usd, token0_symbol, token1_symbol



def get_erc20_token_total_transactions(token_address, chain="eth"):
    """
    Retrieves the total transaction count for an ERC20 token using the Moralis API.

    Args:
    - token_address (str): The token address for which you want to get the total transaction count.
    - chain (str): The blockchain chain, default is Ethereum ("eth").

    Returns:
    - An integer representing the total transaction count or an error message if unsuccessful.
    """

    # Convert token address to checksum format using Web3
    try:
        checksum_address = Web3.to_checksum_address(token_address)
    except ValueError as e:
        return {"error": f"Invalid token address: {e}"}

    # Moralis API endpoint to get token stats
    url = f"https://deep-index.moralis.io/api/v2.2/erc20/{checksum_address}/stats"

    # Set headers with API key
    headers = {
        "Accept": "application/json",
        "X-API-Key": MORALIS_API_KEY
    }

    # Make the request
    response = requests.get(url, headers=headers)

    # Check if request was successful
    if response.status_code != 200:
        return {"error": f"Error: {response.status_code}, Message: {response.text}"}
    # Parse JSON response
    response_json = response.json()
    # Extract the total transaction count from the response
    total_transactions = response_json.get("transfers", {}).get("total")
    # If the total number of transactions is not found, return an error
    if total_transactions is None:
        return {"error": "Total transactions count not found in the response."}

    # Convert total to an integer
    try:
        total_transactions = int(total_transactions)
    except ValueError:
        return {"error": "Failed to convert transaction count to an integer."}
    # Return only the total transaction count
    return total_transactions

def get_erc20_token_transfers(token_address, from_block="0", chain="eth", limit=100):
    """
    Fetches ERC20 token transfers for a given token contract address starting from a specific block.

    Args:
    - token_address (str): The ERC20 token contract address.
    - from_block (str): The block number to start fetching transfers from (default is None).
    - chain (str): Blockchain network (default is 'eth' for Ethereum).
    - limit (int): The number of transfer events to fetch (default is 100).

    Returns:
    - list: A list of dictionaries representing token transfers.
    """
    try:
        # Convert to checksum address for consistency
        checksum_address = Web3.to_checksum_address(token_address)

        # Define API URL for getting ERC20 token transfers
        url = f"https://deep-index.moralis.io/api/v2/erc20/{checksum_address}/transfers?chain={chain}&limit={limit}&from_block=0"

        # Add 'from_block' if provided

        # Set the request headers with the Moralis API key
        headers = {
            "Accept": "application/json",
            "X-API-Key": MORALIS_API_KEY
        }

        # Make the GET request
        response = requests.get(url, headers=headers)

        # Raise an error if the response was unsuccessful
        response.raise_for_status()

        # Get the list of transfers
        transfers = response.json().get("result", [])

        # Sort transfers by block number in descending order (most recent first)
        sorted_transfers = sorted(transfers, key=lambda x: int(x.get("block_number", 0)), reverse=True)

        return sorted_transfers

    except requests.RequestException as e:
        return {"error": str(e)}

