# sweeper.py
import json
import requests
import subprocess
import time

with open("config.json") as f:
    config = json.load(f)

eth_wallets = config["eth_wallets"]
sol_wallets = config["sol_wallets"]
eth_receiver = config["eth_receiver"]
sol_receiver = config["sol_receiver"]
etherscan_api = config["etherscan_api"]
sweep_trigger = config["sweep_trigger_usd"]
chat_id = config["telegram_chat_id"]
bot_token = config["telegram_bot_token"]

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {"chat_id": chat_id, "text": msg}
    try:
        requests.post(url, data=payload)
    except:
        pass

def get_eth_balance(wallet):
    try:
        url = f"https://api.etherscan.io/api?module=account&action=balance&address={wallet}&tag=latest&apikey={etherscan_api}"
        res = requests.get(url).json()
        wei = int(res["result"])
        return wei / 1e18
    except:
        return 0.0

def get_sol_balance(wallet):
    try:
        cmd = f"solana balance {wallet}"
        output = subprocess.check_output(cmd, shell=True).decode()
        return float(output.split()[0])
    except:
        return 0.0

def get_eth_price():
    res = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=ethereum&vs_currencies=usd")
    return res.json()["ethereum"]["usd"]

def get_sol_price():
    res = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=solana&vs_currencies=usd")
    return res.json()["solana"]["usd"]

def sweep_if_needed():
    eth_price = get_eth_price()
    sol_price = get_sol_price()

    for wallet in eth_wallets:
        bal = get_eth_balance(wallet)
        usd_val = bal * eth_price
        if usd_val >= sweep_trigger:
            send_telegram(f"[ETH] {wallet} hit ${usd_val:.2f}. Triggering sweep to {eth_receiver}")
            # Here you'd trigger a send via web3 or CLI (add that in next)
    
    for wallet in sol_wallets:
        bal = get_sol_balance(wallet)
        usd_val = bal * sol_price
        if usd_val >= sweep_trigger:
            send_telegram(f"[SOL] {wallet} hit ${usd_val:.2f}. Triggering sweep to {sol_receiver}")
            # Here you'd trigger a solana transfer

if __name__ == "__main__":
    send_telegram("[🚨] Sweeper check started...")
    sweep_if_needed()
