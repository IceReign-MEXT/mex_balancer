import json
import requests

# Load config
with open("config.json") as f:
    config = json.load(f)

def get_eth_balance(address, api_key):
    url = f"https://api.etherscan.io/api?module=account&action=balance&address={address}&tag=latest&apikey={api_key}"
    r = requests.get(url)
    result = r.json()
    if result.get("status") == "1":
        balance = int(result["result"]) / 1e18
        print(f"[ETH] {address[:8]}...: {balance:.6f} ETH")
    else:
        print(f"[❌ ETH] Failed to fetch for {address}: {result.get('message')}")

def get_sol_balance(address):
    url = "https://api.mainnet-beta.solana.com"
    headers = {"Content-Type": "application/json"}
    payload = {

        "jsonrpc": "2.0",
        "id": 1,
        "method": "getBalance",
        "params": [address]
    }
    r = requests.post(url, headers=headers, json=payload)
    result = r.json()
    try:
        balance = result["result"]["value"] / 1e9
        print(f"[SOL] {address[:8]}...: {balance:.6f} SOL")
    except:
        print(f"[❌ SOL] Failed for {address}")

# Run checks
for eth in config["eth_wallets"]:
    get_eth_balance(eth, config["etherscan_api"])

for sol in config["sol_wallets"]:
    get_sol_balance(sol)

