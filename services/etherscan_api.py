import requests
from bot.config import etherscan_api_key
from bot.config import logging

def get_all_token_transactions(token_address):
    url = f"https://api.etherscan.io/api?module=account&action=tokentx&contractaddress={token_address}&page=1&offset=60&sort=asc&apikey={etherscan_api_key}"
    try:
        response = requests.get(url, timeout=20)
        response.raise_for_status()
        data = response.json()
        if data['status'] == '1':
            filtered_transactions = [
                tx['hash'] for tx in data["result"]
                if tx["to"].lower() != token_address.lower() and tx["from"].lower() != "0x0000000000000000000000000000000000000000"
            ]
            token_values = [
                {
                    "hash": tx['hash'],
                    "tokenValue": int(tx['value']) / 10**int(tx['tokenDecimal']),
                    "tokenDecimal": int(tx['tokenDecimal']),
                    "tokenSymbol": tx.get('tokenSymbol'),
                    "tokenName": tx.get('tokenName')
                }
                for tx in data["result"]
                if tx["to"].lower() != token_address.lower() and tx["from"].lower() != "0x0000000000000000000000000000000000000000"
            ]

            return filtered_transactions, token_values
        else:
            logging.debug("No transactions found or API returned an error.")
            return [], []
    except requests.exceptions.RequestException as e:
        logging.error(f"An error occurred: {e}")
        return [], []

def get_wallet_balance(wallet_address, contract_address):
    url = f"https://api.etherscan.io/api?module=account&action=tokenbalance&contractaddress={contract_address}&address={wallet_address}&tag=latest&apikey={etherscan_api_key}"
    response = requests.get(url)
    data = response.json()
    if data['status'] == '1':
        return int(data['result']) 
    else:
        logging.error(f"Error fetching balance for wallet: {wallet_address}")
        return 0  
    
def get_latest_eth_price():
    try:
        url = f"https://api.etherscan.io/api?module=stats&action=ethprice&apikey={etherscan_api_key}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data.get('status') == '1':
            return float(data['result']['ethusd'])
        else:
            logging.error(f"Error: Could not retrieve ETH price. Status: {data.get('status')}, Message: {data.get('message', 'No message available')}")
            return 0
    except requests.exceptions.RequestException as e:
        logging.error(f"An error occurred: {e}")
        return 0
    
def get_token_total_supply(token_address):
    supply_url = f"https://api.etherscan.io/api?module=stats&action=tokensupply&contractaddress={token_address}&apikey={etherscan_api_key}"
    response = requests.get(supply_url)
    supply_data = response.json()
    if 'status' in supply_data and supply_data['status'] == '1':
        return int(supply_data.get('result', 0))  # ✅ Use `.get()` to avoid crash

    else:
        logging.error(f"Error fetching total supply for {token_address}: {supply_data['message']}")
        return 0    

def get_contract_source_code(token_address):
    url = f"https://api.etherscan.io/api?module=contract&action=getsourcecode&address={token_address}&apikey={etherscan_api_key}"
    response = requests.get(url)
    data = response.json()
    if data['status'] == '1' and len(data['result']) > 0:
        return data['result'][0].get('SourceCode', '')
    else:
        logging.error(f"Error fetching source code: {data.get('message', 'Unknown error')}")
        return None

