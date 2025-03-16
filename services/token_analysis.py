from services.moralis_api import get_token_pairs_info, get_erc20_token_total_transactions
from services.etherscan_api import get_latest_eth_price
from bot.data_processing import combine_transaction_data
from services.infura_api import batch_get_token_balances, batch_get_eth_balances
from services.etherscan_api import get_wallet_balance, get_token_total_supply, get_all_token_transactions, get_contract_source_code
from services.graphql_api import get_liquidity_pair_address, get_liquidity_pair_details
from services.infura_api import batch_get_method_ids, get_transaction_details_and_receipt
import asyncio
from bot.models import TokenSummary
from contracts.contract_analitic import get_contract_source_code, extract_social_links, extract_max_wallet_limit, extract_tax_and_swap_parameters
from bot.config import logging

async def main_async(token_address):
    
    trade_addresses = set()  # Each user gets their own trade_addresses set
    tx_hashes, token_values = get_all_token_transactions(token_address)
    derived_eth, pair_id = get_liquidity_pair_address(token_address)
    method_id = await batch_get_method_ids(tx_hashes)
    pair_address,price_usd,liquidity_usd,volume_24h_usd,token0_symbol,token1_symbol =get_token_pairs_info(token_address)
    pair_address = pair_address or "N/A"
    token_symbol=""
    token_name=""
    token_decimal=0
    eth_price_usd = get_latest_eth_price()
    if token_values:
        token_symbol = token_values[0]['tokenSymbol']
        token_name = token_values[0]['tokenName']
        token_decimal = token_values[0]['tokenDecimal']
        logging.info(f"Token Symbol: {token_symbol}, Token Name: {token_name}, Token Decimals: {token_decimal}")

    clog = get_wallet_balance(token_address, token_address) / 10 ** token_decimal
    total_supply = get_token_total_supply(token_address) / 10 ** token_decimal
    clog_percent = (clog / total_supply) * 100
    logging.info(f"Total Supply {total_supply:.0f}, Clog: {clog:.1f}|{clog_percent:.0f}%")
  
    market_cap_usd=0
    if eth_price_usd:
        if derived_eth:
            market_cap_usd = derived_eth * total_supply * eth_price_usd
        else:
            market_cap_usd = float(price_usd) * total_supply
        logging.info(f"MARKET CAP ({token_symbol}) : ${market_cap_usd:.2f}")
    reserveUSD=0
    tx_count=0
    totalVolumen=0
    # Fetch liquidity pair details if pair_id exists
    if pair_id:
        pair_details = get_liquidity_pair_details(pair_id)
        if pair_details:
            # Extract values with defaults in case keys are missing
            reserveUSD = float(pair_details.get("reserveUSD", 0.0))
            tx_count = int(pair_details.get("txCount", 0))
            volumeToken1 = float(pair_details.get("volumeToken1", 0.0))
            totalVolumen1 = volumeToken1 * eth_price_usd if eth_price_usd else 0.0
            totalVolumen=get_erc20_token_total_transactions(token_address)
            logging.info(f"Liquidity: ${reserveUSD:.2f} | Transactions: {tx_count} | Total Volume: ${totalVolumen:.2f}")
        else:
            logging.debug("Pair details not found")
    else:
        totalVolumen1="N/A"
        pair_details=pair_address
        totalVolumen=volume_24h_usd
        reserveUSD=liquidity_usd
        tx_count=get_erc20_token_total_transactions(token_address)
        logging.info(f"Liquidity: ${reserveUSD:.2f} | Transactions: {tx_count} | Total Volume: ${totalVolumen}")
    transaction_details = await get_transaction_details_and_receipt(tx_hashes, token_address, method_id)
    total_bundle_balance = 0.0
    total_sniper_balance = 0.0
    total_recivedB=0.0
    total_recivedS=0.0
    combined_transactions = []
    trade_addresses_list = list(trade_addresses)
    total_ethb=0.0
    total_eths=0.0
    b_count=0
    s_count=0
    balances = await batch_get_token_balances(token_address, trade_addresses_list, token_decimal)
    eth_balances=await batch_get_eth_balances( trade_addresses_list, 18)
    for i, transaction in enumerate(transaction_details):
        token_value = token_values[i]['tokenValue'] if i < len(token_values) else None
        combined_data = combine_transaction_data(transaction, transaction, token_value, balances, total_supply,eth_balances)

        if combined_data:
            combined_transactions.append(combined_data)
            if "zero_block" in combined_data["tags"] and "📚bundle" in combined_data["tags"]:
                total_bundle_balance += combined_data["tokenBalance"]
                total_recivedB += token_value
                total_ethb+= combined_data["ethBalance"]
                b_count+=1
            elif "first_block" in combined_data["tags"] or ("zero_block" in combined_data["tags"] or "second_block" in combined_data["tags"]  and "🤖sniper" in combined_data["tags"]):
                total_sniper_balance += combined_data["tokenBalance"]
                total_recivedS += token_value
                total_eths+= combined_data["ethBalance"]
                s_count+=1

    total_bundle_balance_percent = (total_bundle_balance / total_supply) * 100
    total_sniper_balance_percent = (total_sniper_balance / total_supply) * 100
    total_sniper_worth=total_sniper_balance*derived_eth
    total_bundle_worth=total_bundle_balance*derived_eth
    totalB_recivied=(total_recivedB/total_supply)*100
    totalS_recivied=(total_recivedS/total_supply)*100
    logging.info(f"Total 📚Bundles Recivied {total_recivedB:.2f}| {totalB_recivied:.2f}%| Total 🤖Sniper Recivied: {total_recivedS:.2f}| {totalS_recivied:.2f}%")
    logging.info(f"Total 📚Bundles Holding: {total_bundle_balance:.1f}|{total_bundle_balance_percent:.1f}% |Worth:{total_bundle_worth:.2f} ETH| Total 🤖Snipers Holding: {total_sniper_balance:.1f}|{total_sniper_balance_percent:.1f}% |Worth: {total_sniper_worth:.2f} ETH")
    contract_code=get_contract_source_code(token_address)
    links=extract_social_links(contract_code)
    maxW=extract_max_wallet_limit(contract_code, total_supply)
    tax=extract_tax_and_swap_parameters(contract_code)
    unsold=(total_sniper_balance+total_bundle_balance)*derived_eth
    summary_data = TokenSummary(
    token_address=token_address,
    token_name=token_name,
    token_symbol=token_symbol,
    token_decimal=token_decimal,
    total_supply=total_supply,
    market_cap_usd=market_cap_usd,
    clog=clog,
    clog_percent=clog_percent,
    b_count=b_count,
    s_count=s_count,
    total_recivedB=total_recivedB,
    total_recivedS=total_recivedS,
    total_bundle_balance=total_bundle_balance,
    total_sniper_balance=total_sniper_balance,
    unsold=unsold,
    total_ethb=total_ethb,
    total_eths=total_eths,
    links=links,
    tax=tax,
    pairA=pair_address,
    reserveUSD=reserveUSD,
    tx_count=tx_count,
    totalVolumen=totalVolumen,
    combined_data=combined_transactions,
    totalVolumen1=totalVolumen1,
    bundle_arrow = "",
    sniper_arrow = "",
    market_cap_arrow=""
)
    return summary_data
