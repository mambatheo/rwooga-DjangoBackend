import requests
import json
from django.conf import settings
from decouple import config
import time

class PaypackService:
    BASE_URL = "https://payments.paypack.rw/api"
    
    def __init__(self):
        # Check if we're in sandbox/test mode
        self.mode = config('PAYPACK_MODE', default='production')
        
        if self.mode == 'sandbox':
            self.client_id = config('PAYPACK_SANDBOX_CLIENT_ID', default=config('PAYPACK_CLIENT_ID'))
            self.client_secret = config('PAYPACK_SANDBOX_CLIENT_SECRET', default=config('PAYPACK_CLIENT_SECRET'))
            print(" PAYPACK SANDBOX MODE - Using test credentials")
        else:
            self.client_id = config('PAYPACK_CLIENT_ID')
            self.client_secret = config('PAYPACK_CLIENT_SECRET')
            print(" PAYPACK PRODUCTION MODE - Using live credentials")
        
        self.token = None
        self.token_expiry = 0

    def authenticate(self):
        """
        Authenticate with Paypack API and get access token
        """
        # Return existing token if valid
        if self.token and time.time() < self.token_expiry:
            return self.token

        url = f"{self.BASE_URL}/auth/agents/authorize"
        
        try:
            response = requests.post(url, json={
                "client_id": self.client_id,
                "client_secret": self.client_secret
            })
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get('access')
                # Set expiry slightly earlier than actual to be safe (e.g., 5 mins)
                self.token_expiry = time.time() + data.get('expires_in', 3600) - 60 
                return self.token
            else:
                print(f"Paypack Authentication Failed: {response.text}")
                return None
        except Exception as e:
            print(f"Paypack Auth Error: {str(e)}")
            return None

    def cashin(self, amount, phone_number, attempt_reference=None):
        """
        Initiate a Mobile Money payment (Cashin)
        """
        token = self.authenticate()
        if not token:
            return {"ok": False, "error": "Authentication failed"}

        url = f"{self.BASE_URL}/transactions/cashin"
        
        # Ensure phone number is in correct format (078...)
        if phone_number.startswith('+250'):
            phone_number = phone_number[4:]
        
        payload = {
            "amount": float(amount),
            "number": phone_number,
        }
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        try:
            print(f"DEBUG: Initiating Cashin to {phone_number} amount {amount}")
            response = requests.post(url, json=payload, headers=headers)
            print(f"DEBUG: Paypack Response Status: {response.status_code}")
            print(f"DEBUG: Paypack Response Body: {response.text}")
            
            data = response.json()
            
            if response.status_code == 200:
                return {
                    "ok": True,
                    "ref": data.get('ref'),
                    "status": data.get('status'),
                    "amount": data.get('amount')
                }
            else:
                print(f"Paypack Cashin Failed: {response.text}")
                return {
                    "ok": False, 
                    "error": "Payment request failed",
                    "details": data
                }
        except Exception as e:
            print(f"Paypack Cashin Error: {str(e)}")
            return {"ok": False, "error": str(e)}

    def check_status(self, ref):
        """
        Check transaction status
        """
        token = self.authenticate()
        if not token:
            return None

        url = f"{self.BASE_URL}/events/transactions?ref={ref}"
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                # Use the latest transaction if multiple
                if data.get('transactions'):
                    return data['transactions'][0]
                return data
            return None
        except Exception as e:
            print(f"Paypack Status Check Error: {str(e)}")
            return None

paypack_service = PaypackService()
