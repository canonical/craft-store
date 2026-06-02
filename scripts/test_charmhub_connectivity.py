# -*- Mode:Python; indent-tabs-mode:nil; tab-width:4 -*-
#
# Copyright 2026 Canonical Ltd.
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License version 3 as published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""Test connectivity to Charmhub and Ubuntu One services."""

import os
import sys

import httpx


def test_endpoint(name: str, url: str, timeout: int = 10) -> bool:
    """Test connectivity to an endpoint."""
    print(f"\n{'=' * 70}")
    print(f"Testing: {name}")
    print(f"URL: {url}")
    print(f"{'=' * 70}")

    try:
        print(f"Attempting connection with {timeout}s timeout...", end=" ")
        response = httpx.get(
            url,
            follow_redirects=True,
            timeout=timeout,
        )
        print("✓ Connected")
        print(f"  Status: {response.status_code}")
        print("  Response time: OK")
        return True
    except httpx.TimeoutException as e:
        print("✗ Timeout")
        print(f"  Error: {e}")
        print(f"  The connection took longer than {timeout} seconds")
        return False
    except httpx.SSLError as e:
        print("✗ SSL Error")
        print(f"  Error: {e}")
        print("  There's an issue with the SSL certificate or encryption")
        return False
    except httpx.ConnectError as e:
        print("✗ Connection Failed")
        print(f"  Error: {e}")
        print("  Could not establish connection to the server")
        return False
    except Exception as e:
        print("✗ Error")
        print(f"  Error: {e}")
        return False


def main() -> int:
    """Test connectivity to Charmhub and related services."""
    api_base = os.getenv("CRAFT_STORE_CHARMHUB", "https://api.charmhub.io")
    login_url = os.getenv("CRAFT_LOGIN_URL", "https://login.ubuntu.com")

    print("\n" + "=" * 70)
    print("Charmhub Connectivity Test")
    print("=" * 70)
    print("\nConfiguration:")
    print(f"  API Base: {api_base}")
    print(f"  Login URL: {login_url}")

    results = {}

    # Test API endpoints
    results["API Root"] = test_endpoint(
        "Charmhub API Root",
        f"{api_base}/",
    )

    results["Macaroon Endpoint"] = test_endpoint(
        "Macaroon Request Endpoint",
        f"{api_base}/v1/tokens/usso",
        timeout=5,
    )

    results["Whoami Endpoint"] = test_endpoint(
        "Whoami Endpoint",
        f"{api_base}/v1/tokens/whoami",
        timeout=5,
    )

    # Test login endpoint
    results["Login Root"] = test_endpoint(
        "Ubuntu One Login Root",
        login_url,
    )

    results["Discharge Endpoint"] = test_endpoint(
        "Token Discharge Endpoint",
        f"{login_url}/api/v2/tokens/discharge",
        timeout=5,
    )

    # Summary
    print("\n" + "=" * 70)
    print("Summary")
    print("=" * 70)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for name, result in results.items():
        status = "✓ OK" if result else "✗ Failed"
        print(f"  {name:.<40} {status}")

    print(f"\nResult: {passed}/{total} endpoints reachable")

    if passed == total:
        print("\n✓ All endpoints are reachable!")
        print("  You should be able to use the login script.")
        return 0
    print("\n✗ Some endpoints are not reachable.")
    print("  Check your network connection or try from a different network.")
    if not results["API Root"] or not results["Login Root"]:
        print("\nThe main services are unreachable. This could be due to:")
        print("  • Network connectivity issues")
        print("  • Firewall or proxy blocking the connection")
        print("  • DNS resolution problems")
        print("\nTry:")
        print("  • ping api.charmhub.io")
        print("  • ping login.ubuntu.com")
        print("  • Check your firewall settings")
    return 1


if __name__ == "__main__":
    sys.exit(main())
