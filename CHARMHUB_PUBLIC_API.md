# UbuntuOneLogin - Public API Reference

## Overview

`UbuntuOneLogin` is a public Python class for authenticating with Ubuntu One and obtaining macaroon tokens for authenticated access to package stores (Charmhub, Snapcraft, etc.).

## Quick Start

```python
from craft_store import DeveloperTokenAuth, auth, creds, publisher, login
import json

# Login with one method call
root, discharged = login.UbuntuOneLogin.login_with(
    email="user@example.com",
    password="password123",
    api_base_url="https://api.charmhub.io",
    permissions=["package-view"],
)

# Use the macaroon with PublisherGateway
store_auth = auth.Auth(
    application_name="myapp",
    host="https://api.charmhub.io",
)

# Note: The root and discharged macaroons are prepared for use together
# as a store token.
root_serial = root.serialize()
discharge_serial = root.prepare_for_request(discharged).serialize()
store_token = f"root={root_serial}, discharge={discharge_serial}"

developer_token = creds.DeveloperToken(macaroon=store_token)
store_auth.set_credentials(json.dumps(developer_token.marshal()), force=True)

gateway = publisher.PublisherGateway(
    base_url="https://api.charmhub.io",
    namespace="charm",
    auth=store_auth,
    httpx_auth=DeveloperTokenAuth(auth=store_auth, auth_type="macaroon"),
)
```

## Public Methods

### `login_with(email, password, *, api_base_url, login_url=None, application_name="craft-store-ubuntu-one", store_auth=None, otp=None, permissions=None, channels=None, packages=None, ttl=None)`

**The primary method for authentication.** Logs in with Ubuntu One credentials and returns a pair of macaroons ready for use. This is a **classmethod**.

**Parameters:**
- `email` (str): Ubuntu One email address
- `password` (str): Ubuntu One password
- `api_base_url` (str): Store API URL (e.g., `https://api.charmhub.io`). **Required**.
- `login_url` (str, optional): Login server URL. Defaults to `https://login.ubuntu.com`.
- `application_name` (str, optional): App name for keyring storage.
- `store_auth` (auth.Auth, optional): Existing Auth instance.
- `otp` (str, optional): One-time password for two-factor authentication
- `permissions` (list of str, optional): Permission scopes (default: `["account-view-packages"]`)
- `channels` (list of str, optional): Restrict to specific channels
- `packages` (list of dict, optional): Restrict to specific packages
- `ttl` (int, optional): Time-to-live in seconds (default: 86400, i.e., 24 hours)

**Returns:**
- `tuple[pymacaroons.Macaroon, pymacaroons.Macaroon]`: A tuple of `(root, discharged)` macaroons.

**Raises:**
- `httpx.HTTPStatusError`: If any HTTP request fails
- `ValueError`: If the macaroon has invalid caveats
- `craft_store.errors.UbuntuOneOtpRequiredError`: If two-factor authentication is required
- `craft_store.errors.UbuntuOneCredentialsError`: If credentials are invalid

**Example:**
```python
from craft_store.login import UbuntuOneLogin

root, discharged = UbuntuOneLogin.login_with(
    email="user@example.com",
    password="password123",
    api_base_url="https://api.charmhub.io",
    otp="123456",  # optional
    permissions=["package-view"],
    channels=["stable"],
)
```

---

### `get_macaroon(*, permissions, channels=None, packages=None, ttl=None)`

**For advanced use.** Requests an unsigned macaroon from the store API.

**Example:**
```python
login_client = UbuntuOneLogin(api_base_url="https://api.charmhub.io")
unsigned = login_client._get_macaroon(
    permissions=["package-manage"],
    channels=["edge"],
)
# Must be discharged with _discharge_macaroon() before use
```

---

### `discharge_macaroon(macaroon, *, email, password, otp=None)`

**For advanced use.** Discharges an unsigned macaroon using Ubuntu One credentials.

**Example:**
```python
login_client = UbuntuOneLogin(api_base_url="https://api.charmhub.io")
unsigned = login_client._get_macaroon(permissions=["package-view"])
discharged = login_client._discharge_macaroon(
    unsigned,
    email="user@example.com",
    password="password123",
)
```

## Constructor Parameters

```python
UbuntuOneLogin(api_base_url, *, login_url=None, application_name="craft-store-ubuntu-one", store_auth=None)
```

- `api_base_url` (str): Store API URL (Charmhub, Snapcraft, etc.). **Required**.
- `login_url` (str, optional): Ubuntu One login server URL. Defaults to `https://login.ubuntu.com`.
- `application_name` (str, optional): The name of the application using this client.
- `store_auth` (auth.Auth, optional): An optional Auth instance to use.

## Complete Integration Example

```python
from craft_store import DeveloperTokenAuth, auth, creds, publisher, login
import json

# 1. Login
root, discharged = login.UbuntuOneLogin.login_with(
    email="user@example.com",
    password="password123",
    api_base_url="https://api.charmhub.io",
    permissions=["package-view"],
)

# 2. Store credentials
# UbuntuOneLogin.login_with already saves the credentials to its internal store_auth,
# but if you need to set it up manually:
store_auth = auth.Auth(
    application_name="myapp",
    host="https://api.charmhub.io",
)

root_serial = root.serialize()
discharge_serial = root.prepare_for_request(discharged).serialize()
# Prepare the combined string without the "Macaroon " prefix
store_token = f"root={root_serial}, discharge={discharge_serial}"

developer_token = creds.DeveloperToken(macaroon=store_token)
store_auth.set_credentials(
    json.dumps(developer_token.marshal()),
    force=True,
)

# 3. Create authenticated gateway
gateway = publisher.PublisherGateway(
    base_url="https://api.charmhub.io",
    namespace="charm",
    auth=store_auth,
    httpx_auth=DeveloperTokenAuth(auth=store_auth, auth_type="macaroon"),
)

# 4. Make authenticated API calls
package_info = gateway.get_package_metadata("my-charm")

# 5. Cleanup
store_auth.del_credentials()
```

## Error Handling

```python
import httpx
from craft_store.login import UbuntuOneLogin, UbuntuOneOtpRequiredError, UbuntuOneCredentialsError

try:
    root, discharged = UbuntuOneLogin.login_with(
        email="user@example.com",
        password="password123",
        api_base_url="https://api.charmhub.io",
    )
except UbuntuOneOtpRequiredError:
    print("2FA required")
except UbuntuOneCredentialsError:
    print("Invalid email or password")
except httpx.HTTPStatusError as e:
    print(f"HTTP Error {e.response.status_code}")
```

## Supported Stores

- **Charmhub**: `https://api.charmhub.io`
- **Snapcraft**: `https://api.snapcraft.io`

## Testing

```bash
# Run the demo script
uv run python scripts/usso_login_demo.py

# Run integration tests
uv run pytest tests/integration/login/ -v
```
