# get_token.py
import requests

def get_jwt_token():
    url = "http://localhost:8000/api/v1/auth/login"
    
    data = {
        "username": "arifmazumder@daffodilvarsity.edu.bd",  # Replace with your email
        "password": "test123456"            # Replace with your password
    }
    
    response = requests.post(url, data=data)
    if response.status_code == 200:
        token = response.json()["access_token"]
        print("Your JWT token:")
        print(token)
        print("\nFull authorization header:")
        print(f"Bearer {token}")
        return token
    else:
        print("Error:", response.json())
        return None

if __name__ == "__main__":
    get_jwt_token()