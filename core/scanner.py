import requests, os

class RugScanner:
    def __init__(self):
        self.api_url = "https://api.rugcheck.xyz/v1/tokens/{}/report"

    def check_token(self, token_address):
        try:
            # RugCheck is strict; some endpoints require a User-Agent
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(self.api_url.format(token_address), headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                score = data.get("score", 0)
                risks = data.get("risks", [])
                
                # Risk threshold: 500 is the standard "Danger" zone
                if score > 500:
                    risk_list = "\n".join([f"- {r['description']}" for r in risks[:3]])
                    return False, f"❌ **DANGER: RUG DETECTED**\nScore: {score}\n\nTop Risks:\n{risk_list}"
                
                return True, f"✅ **SCAN PASSED**\nScore: {score}\nStatus: **LOW RISK**"
            return False, "⚠️ RugCheck scan failed. Token might be too new."
        except Exception as e:
            return False, f"❌ Scan Error: {str(e)}"

scanner = RugScanner()
