import json
import requests

with open("config.json") as f:
    config = json.load(f)

def get_eth_balance(address, api_key):
    url = f"https://api.etherscan.io/api?module=account&action=balance&address={address}&tag=latest&apikey={api_key}"
    r = requests.get(url)
    result = r.json()
    if result["status"] == "1":
        eth = int(result["result"]) / 10**18
        print(f"[ETH] {address[:8]}...: {eth:.5f} ETH")
    else:
        print(f"[❌] Failed to fetch ETH balance for {address}")

def get_sol_balance(address):
    url = f"https://api.mainnet-beta.solana.com"
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
        sol = result["result"]["value"] / 10**9
        print(f"[SOL] {address[:8]}...: {sol:.5f} SOL")
    except:
        print(f"[❌] Failed to fetch SOL balance for {address}")

for eth_wallet in config["eth_wallets"]:
    get_eth_balance(eth_wallet, config["etherscan_api"])

for sol_wallet in config["sol_wallets"]:
    get_sol_balance(sol_wallet)
+ 0,
+ X.
