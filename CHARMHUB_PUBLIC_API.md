# UbuntuOneLogin - Public API Reference

## Overview

`UbuntuOneLogin` is a public Python class for authenticating with Ubuntu One and obtaining macaroon tokens for authenticated access to package stores (Charmhub, Snapcraft, etc.).

## Quick Start

```python
from craft_store import auth, publisher, login
import json

# Login with one method call
root, discharged = login.UbuntuOneLogin.login_with(
    email="user@example.com",
    password="password123",
    api_base_url="https://api.charmhub.io",
    permissions=["package-view"],
)

# Use the saved credentials with PublisherGateway
store_auth = auth.Auth(
    application_name="craft-store-ubuntu-one",
    host="api.charmhub.io",
)

# We use UbuntuOneAuth which handles the exchange internally.
gateway = publisher.PublisherGateway(
    base_url="https://api.charmhub.io",
    namespace="charm",
    auth=store_auth,
    httpx_auth=publisher.UbuntuOneAuth(auth=store_auth, api_base_url="https://api.charmhub.io"),
)
```

## Public Methods

### `login_with(email, password, *, api_base_url, login_url=None, application_name="craft-store-ubuntu-one", store_auth=None, otp=None, permissions=None, channels=None, packages=None, ttl=None)`

**The primary method for authentication.** Logs in with Ubuntu One credentials and returns a pair of macaroons. It also automatically saves these credentials to the keyring. This is a **classmethod**.

**Parameters:**
- `email` (str): Ubuntu One email address
- `password` (str): Ubuntu One password
- `api_base_url` (str): Store API URL (e.g., `https://api.charmhub.io`). **Required**.
- `login_url` (str, optional): Login server URL. Defaults to `https://login.ubuntu.com`.
- `application_name` (str, optional): App name for keyring storage (default: `craft-store-ubuntu-one`).
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
from craft_store import auth, publisher, login
import json

# 1. Login
# This saves the root and discharged macaroons to the keyring.
UbuntuOneLogin.login_with(
    email="user@example.com",
    password="password123",
    api_base_url="https://api.charmhub.io",
    permissions=["package-view"],
)

# 2. Access saved credentials
store_auth = auth.Auth(
    application_name="craft-store-ubuntu-one",
    host="api.charmhub.io",
)

# 3. Create authenticated gateway
# We use UbuntuOneAuth which handles the exchange internally.
gateway = publisher.PublisherGateway(
    base_url="https://api.charmhub.io",
    namespace="charm",
    auth=store_auth,
    httpx_auth=publisher.UbuntuOneAuth(auth=store_auth, api_base_url="https://api.charmhub.io"),
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
