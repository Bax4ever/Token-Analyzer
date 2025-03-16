from .config import logging

WETH_ADDRESS = "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2"

def process_response_data(response_data, transactions, address, methodIds):
   
    zero_block = None
    first_block = None
    second_block = None

    #global zero_block, first_block, second_block, bundle_groups, method, zero_block_set, trade_addresses
    
    zero_block_set = False  # Ensure this is initialized
    trade_addresses = set()  # Ensure this is initialized
    
    for i in range(0, len(response_data), 2):
        tx = response_data[i].get("result")
        receipt = response_data[i + 1].get("result")
        
        if tx and receipt:
            transaction_hash = tx.get('hash')
            method_id = methodIds.get(transaction_hash, None)
            TRANSACTION_TAGS = []

            # Construct transaction data
            transaction_data = {
                'transactionHash': tx.get('hash'),
                'blockNumber': int(tx['blockNumber'], 16) if tx.get('blockNumber') else None,
                'from': tx.get('from'),
                'to': tx.get('to'),
                'gas': int(tx['gas'], 16) if tx.get('gas') else None,
                'gasPrice': int(tx['gasPrice'], 16) if tx.get('gasPrice') else None,
                'input': tx.get('input'),
                'value': int(tx['value'], 16) if tx.get('value') else None,
                'nonce': tx.get('nonce'),
                'transactionIndex': tx.get('transactionIndex'),
                'status': int(receipt['status'], 16) if receipt.get('status') else None,
                'cumulativeGasUsed': int(receipt['cumulativeGasUsed'], 16) if receipt.get('cumulativeGasUsed') else None,
                'gasUsed': int(receipt['gasUsed'], 16) if receipt.get('gasUsed') else None,
                'contractAddress': receipt.get('contractAddress'),
                'valueInEther': int(tx['value'], 16) / 10**18 if tx.get('value') else None,
                'tags': [],
                "methodId": method_id
            }
            
            # Check if transaction involves WETH and add trade tag
            if transaction_data['to'] and transaction_data['to'].lower() != address.lower():
                for log in receipt.get('logs', []):
                    first_log = receipt.get('logs', [])[0] if receipt.get('logs') else None
                    if first_log and first_log.get('address').lower() == WETH_ADDRESS.lower():
                        TRANSACTION_TAGS.append("trade")
                        break

            # Set zero_block and add appropriate tags
            if "trade" in TRANSACTION_TAGS and not zero_block_set:
                zero_block = transaction_data['blockNumber']
                first_block = zero_block + 1
                second_block = first_block + 1
                zero_block_set = True
                method=method_id
                TRANSACTION_TAGS.append("zero_block")

            # Add block-specific tags
            if transaction_data['blockNumber'] == zero_block:
                TRANSACTION_TAGS.append("zero_block")
                if method_id == method:
                    TRANSACTION_TAGS.append("📚bundle")
                else:
                    TRANSACTION_TAGS.append("🤖sniper")

            elif transaction_data['blockNumber'] == first_block:
                TRANSACTION_TAGS.extend(["first_block", "🤖sniper"])

            elif transaction_data['blockNumber'] == second_block:
                TRANSACTION_TAGS.extend(["second_block", "🤖sniper"])

            # Detect known bots
            known_bots = {
                "0x034131bcc29b9801af37a826925e58a4a6e0e866": "📚TitanDeployer",
                "0x3328f7f4a1d1c57c35df56bbf0c9dcafca309c49": "🤖Banana",
                "0x80a64c6d7f12c47b7c66c5b4e20e72bc1fcd5d9e": "🤖Maestro",
                "0x3a10dc1a145da500d5fba38b9ec49c8ff11a981f": "🤖Sigma"
            }
            to_address = transaction_data.get('to', '').lower()
            bot_name = known_bots.get(to_address)
            if bot_name:
                transaction_data['botUsed'] = bot_name
                TRANSACTION_TAGS.append(bot_name)
            from_address = transaction_data.get("from")

            # Update transaction_data tags
            transaction_data['tags'] = TRANSACTION_TAGS

            transactions.append(transaction_data)
            if "trade" in transaction_data["tags"] and from_address and from_address not in trade_addresses:
                trade_addresses.add(from_address)

def combine_transaction_data(details, receipt, token_value,balances,total_supply,eth_balances):

    if not isinstance(details, dict) or not isinstance(receipt, dict):
        logging.error("Error: Expected dictionaries for details and receipt.")
        return None
    # Skip non-trade transactions
    if 'trade' not in details.get('tags', []):
        #print(f"Skipping transaction {details.get('transactionHash')} as it does not have a 'trade' tag.")
        return None
    from_address = details.get("from")
    token_balance = balances.get(from_address, 0.0)
    eth_balance=eth_balances.get(from_address,0.0)
    # Calculate percentages
    balance_percentage = (token_balance / total_supply) * 100 if total_supply else 0
    received_percentage = (token_value / total_supply) * 100 if total_supply else 0
    combined_data = {
        "transactionHash": details.get("transactionHash"),
        "blockNumber": details.get("blockNumber"),
        "from": details.get("from"),
        "to": details.get("to"),
        "input": details.get("input"),
        "value": details.get("value"),
        "valueInEther": details.get("valueInEther"),
        "status": receipt.get("status"),
        "cumulativeGasUsed": receipt.get("cumulativeGasUsed"),
        "gasUsed": receipt.get("gasUsed"),
        "contractAddress": receipt.get("contractAddress"),
        "tags": details.get("tags", []),
        "tokenValue": token_value, # Add token value directly
        "tokenBalance": balances.get(from_address, 0.0),
        "balancePercentage": balance_percentage,     # Token balance as a percentage of total supply
        "receivedPercentage": received_percentage,    # Tokens received as a percentage of total supply
        "ethBalance": eth_balance
         }
    

        
    return combined_data
