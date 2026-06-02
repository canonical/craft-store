# UbuntuOneLogin - Public API Reference

## Overview

`UbuntuOneLogin` is a public Python class for authenticating with Ubuntu One and obtaining macaroon tokens for authenticated access to package stores (Charmhub, Snapcraft, etc.).

## Quick Start

```python
from craft_store.login import UbuntuOneLogin

# Create a login client
login = UbuntuOneLogin()

# Login with one method call
root, discharged = login.login_with(
    email="user@example.com",
    password="password123",
    permissions=["package-view"],
)

# Use the macaroon with PublisherGateway
from craft_store import auth, creds, publisher
import json

store_auth = auth.Auth(
    application_name="myapp",
    host="https://api.charmhub.io",
)

# Note: The root and discharged macaroons are prepared for use together
# as a store token.
root_serial = root.serialize()
discharge_serial = root.prepare_for_request(discharged).serialize()
store_token = f"Macaroon root={root_serial}, discharge={discharge_serial}"

developer_token = creds.DeveloperToken(macaroon=store_token)
store_auth.set_credentials(json.dumps(developer_token.marshal()), force=True)

gateway = publisher.PublisherGateway(
    base_url="https://api.charmhub.io",
    namespace="charm",
    auth=store_auth,
)
```

## Public Methods

### `login_with(email, password, *, otp=None, permissions=None, channels=None, packages=None, ttl=None)`

**The primary method for authentication.** Logs in with Ubuntu One credentials and returns a pair of macaroons ready for use.

**Parameters:**
- `email` (str): Ubuntu One email address
- `password` (str): Ubuntu One password
- `otp` (str, optional): One-time password for two-factor authentication
- `permissions` (list of str, optional): Permission scopes (default: `["account-view-packages"]`)
  - Valid values: `"account-manage-keys"`, `"account-manage-metadata"`, `"account-register-package"`, `"account-view-packages"`, `"package-manage"`, `"package-manage-acl"`, `"package-manage-metadata"`, `"package-manage-releases"`, `"package-manage-revisions"`, `"package-view"`, `"package-view-acl"`, `"package-view-metadata"`, `"package-view-metrics"`, `"package-view-releases"`, `"package-view-revisions"`, `"store-manage"`, `"store-view"`
- `channels` (list of str, optional): Restrict to specific channels (e.g., `["stable", "edge"]`)
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
login = UbuntuOneLogin()
root, discharged = login.login_with(
    email="user@example.com",
    password="password123",
    otp="123456",  # optional
    permissions=["package-view"],
    channels=["stable"],
)
```

---

### `get_macaroon(*, permissions, channels=None, packages=None, ttl=None)`

**For advanced use.** Requests an unsigned macaroon from the store API. Most users should use `login_with()` instead.

**Parameters:**
- `permissions` (list of str): Permission scopes (required)
- `channels` (list of str, optional): Restrict to specific channels
- `packages` (list of dict, optional): Restrict to specific packages
- `ttl` (int, optional): Time-to-live in seconds (default: 86400)

**Returns:**
- `pymacaroons.Macaroon`: An unsigned macaroon

**Raises:**
- `httpx.HTTPStatusError`: If the request fails

**Example:**
```python
login = UbuntuOneLogin()
unsigned = login._get_macaroon(
    permissions=["package-manage"],
    channels=["edge"],
)
# Must be discharged with _discharge_macaroon() before use
```

---

### `discharge_macaroon(macaroon, *, email, password, otp=None)`

**For advanced use.** Discharges an unsigned macaroon using Ubuntu One credentials. Most users should use `login_with()` instead.

**Parameters:**
- `macaroon` (pymacaroons.Macaroon): The unsigned macaroon to discharge
- `email` (str): Ubuntu One email address
- `password` (str): Ubuntu One password
- `otp` (str, optional): One-time password for two-factor authentication

**Returns:**
- `pymacaroons.Macaroon`: A discharged macaroon ready to use

**Raises:**
- `httpx.HTTPStatusError`: If the discharge request fails
- `ValueError`: If the macaroon has invalid caveats

**Example:**
```python
login = UbuntuOneLogin()
unsigned = login._get_macaroon(permissions=["package-view"])
discharged = login._discharge_macaroon(
    unsigned,
    email="user@example.com",
    password="password123",
)
```

## Constructor Parameters

```python
UbuntuOneLogin(api_base_url=None, *, login_url=None, application_name="craft-store-ubuntu-one", store_auth=None)
```

- `api_base_url` (str, optional): Store API URL (Charmhub, Snapcraft, etc.)
  - Default: `https://api.charmhub.io`
  - Environment variable: `CRAFT_STORE_CHARMHUB`

- `login_url` (str, optional): Ubuntu One login server URL
  - Default: `https://login.ubuntu.com`
  - Environment variable: `CRAFT_LOGIN_URL`

- `application_name` (str, optional): The name of the application using this client.

- `store_auth` (auth.Auth, optional): An optional Auth instance to use.

## Environment Variables

- `CRAFT_LOGIN_URL`: Override Ubuntu One login server URL
- `CRAFT_STORE_CHARMHUB`: Use Charmhub API instead of default

## Complete Integration Example

```python
from craft_store.login import UbuntuOneLogin
from craft_store import auth, creds, publisher
import json

# 1. Login
login = UbuntuOneLogin()
root, discharged = login.login_with(
    email="user@example.com",
    password="password123",
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
store_token = f"Macaroon root={root_serial}, discharge={discharge_serial}"

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
)

# 4. Make authenticated API calls
package_info = gateway.get_package_metadata("my-charm")

# 5. Cleanup
store_auth.del_credentials()
```

## Error Handling

All methods raise `httpx.HTTPStatusError` on network/API errors:

```python
import httpx

try:
    macaroon = login.login_with(
        email="user@example.com",
        password="password123",
    )
except httpx.TimeoutException:
    print("Connection timeout")
except httpx.HTTPStatusError as e:
    print(f"HTTP Error {e.response.status_code}: {e.response.text}")
except ValueError as e:
    print(f"Invalid macaroon: {e}")
```

## Supported Stores

- **Charmhub**: `https://api.charmhub.io` (default)
- **Snapcraft**: `https://api.snapcraft.io` (via `CRAFT_STORE_SNAPCRAFT`)
- **Custom**: Any URL via `api_base_url` parameter or environment variable

## Testing

```bash
# Run the demo script
uv run python scripts/usso_login_demo.py

# Run integration tests
uv run pytest tests/integration/login/ -v

# Test with custom endpoint
export CRAFT_STORE_CHARMHUB=https://api.staging.charmhub.io
uv run python scripts/usso_login_demo.py
```

## API Compatibility

- **Macaroon endpoint**: `POST {api_base_url}/v1/tokens/usso`
- **Discharge endpoint**: `POST {login_url}/api/v2/tokens/discharge`
- **Verification endpoint**: `GET {api_base_url}/v1/tokens`

See https://api.charmhub.io/docs/ for complete API documentation.
