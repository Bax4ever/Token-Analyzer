import aiohttp
import asyncio
from bot.config import infura_url
import random
from bot.data_processing import process_response_data
from bot.config import logging

async def fetch_batch(session, payload,retries=50, delay=3):
    for attempt in range(retries):
        try:
            async with session.post(infura_url, json=payload, timeout=20) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logging.error(f"Error: Received status {response.status}. Retrying...")
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            logging.error(f"Request error: {e}. Retrying {attempt + 1}/{retries} after delay {delay}s.")
        await asyncio.sleep(delay * (1 ** attempt) + random.uniform(0, 1))  # Exponential backoff

    logging.debug("Max retries reached. Failed to fetch batch.")
    return None


async def batch_get_eth_balances(addresses, token_decimal=18, max_retries=5):
    batch_requests = [
        {
            "jsonrpc": "2.0",
            "method": "eth_getBalance",
            "params": [address, "latest"],
            "id": idx
        }
        for idx, address in enumerate(addresses)
    ]

    balances = {}
    async with aiohttp.ClientSession() as session:
        async with session.post(infura_url, json=batch_requests) as response:
            if response.status == 200:
                responses = await response.json()
                for result in responses:
                    address_idx = result["id"]
                    address = addresses[address_idx]
                    balance_hex = result.get("result", "0x0")
                    balance = int(balance_hex, 16) / 10**token_decimal  
                    balances[address] = balance
                return balances
            else:
                logging.error(f"Error: {response.status}")
                return {}

    return balances  # Return partial data if it fails

async def batch_get_token_balances(token_address, addresses, token_decimal):
    token_address = token_address.lower()

    batch_requests = [
        {
            "jsonrpc": "2.0",
            "method": "eth_call",
            "params": [{"to": token_address, "data": f"0x70a08231{address[2:].zfill(64)}"}, "latest"],
            "id": idx
        }
        for idx, address in enumerate(addresses)
    ]

    balances = {}
    async with aiohttp.ClientSession() as session:
        async with session.post(infura_url, json=batch_requests) as response:
            if response.status == 200:
                responses = await response.json()
                for result in responses:
                    address_idx = result["id"]
                    address = addresses[address_idx]
                    balance_hex = result.get("result", "0x0")
                    balance = int(balance_hex, 16) / 10**token_decimal  
                    balances[address] = balance
                return balances
            else:
                logging.error(f"Error: {response.status}")
                return {}

    return balances  # Return partial results if failure

async def get_transaction_details_and_receipt(tx_hashes, address, methodIds):
    async with aiohttp.ClientSession() as session:
        tasks = []
        for i in range(0, len(tx_hashes), 100):  # 🛑 Process 100 transactions at a time
            batch = tx_hashes[i:i + 100]
            payload = []
            for tx_hash in batch:
                payload.append({
                    "jsonrpc": "2.0",
                    "method": "eth_getTransactionByHash",
                    "params": [tx_hash],
                    "id": len(payload)
                })
                payload.append({
                    "jsonrpc": "2.0",
                    "method": "eth_getTransactionReceipt",
                    "params": [tx_hash],
                    "id": len(payload)
                })
            tasks.append(fetch_batch(session, payload))

        all_responses = await asyncio.gather(*tasks)
        
        transactions = []
        for response_data in all_responses:
            if response_data:
                process_response_data(response_data, transactions, address, methodIds)
        return transactions

async def batch_get_method_ids(tx_hashes, max_retries=50):
    # Prepare batch requests
    batch_requests = [
        {
            "jsonrpc": "2.0",
            "method": "eth_getTransactionByHash",
            "params": [tx_hash],
            "id": idx
        }
        for idx, tx_hash in enumerate(tx_hashes)
    ]
    
    method_ids = {}

    async with aiohttp.ClientSession() as session:
        retries = 0
        delay = 9  # Initial delay

        while retries < max_retries:
            try:
                async with session.post(infura_url, json=batch_requests) as response:
                    if response.status == 429:  # Too Many Requests
                        await asyncio.sleep(delay)
                        delay *= 6  # Exponential backoff
                        retries += 1
                        continue  # Retry the request
                    
                    # If successful, parse response
                    response_data = await response.json()
                    for result in response_data:
                        tx = result.get("result")
                        if tx and tx.get("input") and tx["input"] != "0x":
                            # Extract first 4 bytes for the method ID
                            method_id = tx["input"][:10]
                            method_ids[tx["hash"]] = method_id
                        else:
                            method_ids[tx["hash"]] = None  # No input or empty transaction
                    break  # Exit loop if successful

            except aiohttp.ClientError as e:
                logging.error(f"HTTP error: {e}")
                await asyncio.sleep(delay)
                delay *= 2  # Exponential backoff
                retries += 1
            except Exception as e:
                logging.error(f"Unexpected error: {e}")
                return {}  # Exit with empty result in case of unexpected error

        if retries == max_retries:
            logging.debug("Max retries reached. Could not complete batch method ID request.")
            method_ids=None
    return method_ids
