# Charmhub Ubuntu One Login Demo Script

This script demonstrates the complete Ubuntu One login flow with Charmhub, including macaroon verification.

## What It Does

1. **Prompts for credentials**:
   - Email address (required)
   - Password (required, hidden input)
   - OTP (optional, for 2FA)

2. **Performs login flow**:
   - Calls `UbuntuOneLogin.login_with` (classmethod)
   - Requests a macaroon from Charmhub API
   - Discharges the macaroon with your credentials
   - Saves the root and discharged macaroons to your keyring
   - Verifies identity using the `whoami` endpoint

3. **Displays results**:
   - Your account information (display name, email)
   - Your registered charms

## Running the Script

### Run the Script
```bash
uv run python scripts/usso_login_demo.py
```

## How It Uses UbuntuOneLogin

The script demonstrates the core `login_with` method:

```python
from craft_store.login import UbuntuOneLogin

root, discharged = UbuntuOneLogin.login_with(
    email="your.email@example.com",
    password="your_password",
    otp="123456",  # optional
    api_base_url="https://api.charmhub.io",
)
```

## Integration Points

### With PublisherGateway
The saved macaroon pair can be used with `PublisherGateway` using `UbuntuOneAuth`:

```python
from craft_store import auth, publisher
import json

# 1. Access saved credentials from keyring
# UbuntuOneLogin.login_with saved them to the default application name
test_auth = auth.Auth(
    application_name="craft-store-ubuntu-one",
    host="api.charmhub.io",
)

# 2. Use with PublisherGateway
# UbuntuOneAuth handles the macaroon exchange internally.
gateway = publisher.PublisherGateway(
    base_url="https://api.charmhub.io",
    namespace="charm",
    auth=test_auth,
    httpx_auth=publisher.UbuntuOneAuth(auth=test_auth, api_base_url="https://api.charmhub.io"),
)
```

## Troubleshooting

### Connection Error
- Check your internet connection
- Verify Charmhub API is reachable

### Invalid Credentials
- Double-check your email and password
- If using 2FA, ensure OTP is correct

## Related Files
- Script: `/home/lengau/Work/Code/craft-store/scripts/usso_login_demo.py`
- Implementation: `/home/lengau/Work/Code/craft-store/craft_store/login/_ubuntuone.py`
- Integration tests: `/home/lengau/Work/Code/craft-store/tests/integration/login/test_ubuntuone.py`
