import requests, os

class RugScanner:
    def __init__(self):
        self.api_url = "https://api.rugcheck.xyz/v1/tokens/{}/report"

    def check_token(self, token_address):
        try:
            response = requests.get(self.api_url.format(token_address), timeout=10)
            if response.status_code == 200:
                data = response.json()
                score = data.get("score", 0)
                # We block anything with a risk score over 500
                if score > 500:
                    return False, f"❌ DANGER: Risk Score {score} is too high!"
                return True, f"✅ SAFE: Risk Score {score} is acceptable."
            return False, "⚠️ Warning: RugCheck API unavailable. Stay cautious."
        except Exception as e:
            return False, f"❌ Scan Error: {str(e)}"

scanner = RugScanner()
