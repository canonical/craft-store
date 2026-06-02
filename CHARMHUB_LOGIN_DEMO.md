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
   - Exchanges for a store token
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
The discharged macaroon pair can be used with `PublisherGateway` using `DeveloperTokenAuth`:

```python
from craft_store import DeveloperTokenAuth, auth, creds, publisher
import json

# 1. Prepare the combined store token string
root_serial = root.serialize()
discharge_serial = root.prepare_for_request(discharged).serialize()
# Format: "root=..., discharge=..."
store_token = f"root={root_serial}, discharge={discharge_serial}"

# 2. Store in Auth keyring
test_auth = auth.Auth(
    application_name="myapp",
    host="https://api.charmhub.io",
)
developer_token = creds.DeveloperToken(macaroon=store_token)
test_auth.set_credentials(json.dumps(developer_token.marshal()), force=True)

# 3. Use with PublisherGateway
gateway = publisher.PublisherGateway(
    base_url="https://api.charmhub.io",
    namespace="charm",
    auth=test_auth,
    httpx_auth=DeveloperTokenAuth(auth=test_auth, auth_type="macaroon"),
)
```

## Troubleshooting

### Connection Error
- Check your internet connection
- Verify Charmhub API is reachable

### Invalid Credentials
- Double-check your email and password
- If using 2FA, ensure OTP is correct

### Validation Error: Invalid macaroon
- This usually means the authorization header is malformed.
- Ensure you are NOT prepending "Macaroon " to the string if using `DeveloperTokenAuth`.

## Related Files
- Script: `/home/lengau/Work/Code/craft-store/scripts/usso_login_demo.py`
- Implementation: `/home/lengau/Work/Code/craft-store/craft_store/login/_ubuntuone.py`
- Integration tests: `/home/lengau/Work/Code/craft-store/tests/integration/login/test_ubuntuone.py`
