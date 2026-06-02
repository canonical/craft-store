# Charmhub Ubuntu One Login Demo Script

This script demonstrates the complete Ubuntu One login flow with Charmhub, including macaroon verification.

## What It Does

1. **Prompts for credentials**:
   - Email address (required)
   - Password (required, hidden input)
   - OTP (optional, for 2FA)

2. **Performs login flow**:
   - Creates `UbuntuOneLogin` client
   - Requests a macaroon from Charmhub dashboard API
   - Discharges the macaroon with your credentials
   - Verifies identity using the `macaroon_info` endpoint

3. **Displays results**:
   - Your account information (username, email, display name, ID)
   - Macaroon details and caveats
   - The complete serialized macaroon (base64)

## Running the Script

### Prerequisites
```bash
cd /home/lengau/Work/Code/craft-store
make setup  # if not already done
```

### Run the Script
```bash
uv run python scripts/usso_login_demo.py
```

### Interactive Flow
```
======================================================================
Charmhub Ubuntu One Login Demo
======================================================================

Email address: your.email@example.com
Password: [hidden input]
OTP (optional, press Enter to skip): 123456

Authenticating with Charmhub...

✓ Created UbuntuOneLogin client
  Requesting macaroon from Charmhub...
✓ Received root macaroon
  Discharging macaroon with credentials...
✓ Successfully discharged macaroon
  Verifying identity with macaroon_info endpoint...
✓ Identity verified

======================================================================
Login Successful!
======================================================================

Account Information:
  Username: your-username
  Display Name: Your Name
  Email: your.email@example.com
  ID: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

Macaroon Details:
  Serialized: [long base64 string]

Macaroon Caveats:
  1. [caveat details]
  2. [caveat details]

======================================================================
Complete Macaroon (base64):
======================================================================
[full serialized macaroon]
```

## How It Uses UbuntuOneLogin

The script demonstrates the two key private methods of `UbuntuOneLogin`:

### 1. Request Root Macaroon
```python
login_client = UbuntuOneLogin(
    api_base_url="https://api.charmhub.io",
)

macaroon = login_client._get_macaroon(
    permissions=["package-access"],
    channels=["stable", "edge", "beta", "candidate"],
)
```

### 2. Discharge Macaroon
```python
discharged = login_client._discharge_macaroon(
    macaroon,
    email="your.email@example.com",
    password="your_password",
    otp="123456",  # optional
)
```

## Integration Points

### With PublisherGateway
The discharged macaroon pair can be used with `PublisherGateway`:

```python
from craft_store import auth, creds, publisher
import json

# 1. Login
login = UbuntuOneLogin()
root, discharged = login.login_with(
    email="user@example.com",
    password="password123",
)

# 2. Prepare the combined store token
root_serial = root.serialize()
discharge_serial = root.prepare_for_request(discharged).serialize()
store_token = f"Macaroon root={root_serial}, discharge={discharge_serial}"

# 3. Store the macaroon
test_auth = auth.Auth(
    application_name="myapp",
    host="https://api.charmhub.io",
)

developer_token = creds.DeveloperToken(macaroon=store_token)
credentials_json = json.dumps(developer_token.marshal())
test_auth.set_credentials(credentials_json, force=True)

# 4. Use with PublisherGateway
gateway = publisher.PublisherGateway(
    base_url="https://api.charmhub.io",
    namespace="charm",
    auth=test_auth,
)
```

## Troubleshooting

### Connection Error
```
✗ Connection Error: [Errno -2] Name or service not known
```
- Check your internet connection
- Verify Charmhub API is reachable
- Try pinging `api.charmhub.io`

### Invalid Credentials
```
✗ HTTP Error: 401 Unauthorized
```
- Double-check your email and password
- If using 2FA, ensure OTP is correct
- Account may not be registered

### Validation Error
```
✗ Validation Error: Invalid macaroon: no valid login caveats found
```
- The macaroon received is malformed
- Charmhub API may have changed
- Try again or contact support

## Related Files
- Script: `/home/lengau/Work/Code/craft-store/scripts/usso_login_demo.py`
- Implementation: `/home/lengau/Work/Code/craft-store/craft_store/login/_ubuntuone.py`
- Integration tests: `/home/lengau/Work/Code/craft-store/tests/integration/login/test_ubuntuone.py`
