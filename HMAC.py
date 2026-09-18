import hmac
import hashlib
import json

payload_dict = {
  "sender_account_id": 2,
  "receiver_account_id": 1,
  "amount": 150
}

compact_bytes = json.dumps(payload_dict, separators=(',', ':')).encode('utf-8')
secret = b"super-secret-hmac-key"

sig = hmac.new(secret, compact_bytes, hashlib.sha256).hexdigest()
print("X-Signature:", sig)