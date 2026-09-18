import pyotp

# THIS IS AN AUTHENTICATOR APP SIMULATOR!!


secret = "KSGQJN2D2PVLM7ELQYLNX54AVFEDD3OQ"

totp = pyotp.TOTP(secret)
print("Current 6-digit MFA Code:", totp.now())