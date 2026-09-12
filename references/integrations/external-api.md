# External API Integration Patterns

```
╔══════════════════════════════════════════════════════════════════════════════╗
║  EXTERNAL API INTEGRATION PATTERNS                                           ║
║  Connecting to third-party services, REST/SOAP APIs, and webhooks            ║
║  Use for payment gateways, shipping providers, CRM sync, etc.                ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

## Configuration Model

### API Credentials Storage
```python
from odoo import api, fields, models
from odoo.exceptions import ValidationError
import requests


class ExternalAPIConfig(models.Model):
    _name = 'external.api.config'
    _description = 'External API Configuration'

    name = fields.Char(string='Name', required=True)
    api_url = fields.Char(string='API URL', required=True)
    api_key = fields.Char(string='API Key', groups='base.group_system')
    api_secret = fields.Char(string='API Secret', groups='base.group_system')
    environment = fields.Selection(
        selection=[
            ('sandbox', 'Sandbox'),
            ('production', 'Production'),
        ],
        string='Environment',
        default='sandbox',
        required=True,
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        default=lambda self: self.env.company,
    )
    active = fields.Boolean(default=True)
    last_sync = fields.Datetime(string='Last Sync', readonly=True)

    @api.constrains('api_url')
    def _check_api_url(self):
        for config in self:
            if not config.api_url.startswith(('http://', 'https://')):
                raise ValidationError("API URL must start with http:// or https://")

    def action_test_connection(self):
        """Test API connection."""
        self.ensure_one()
        try:
            response = self._make_request('GET', '/health')
            if response.status_code == 200:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Success',
                        'message': 'Connection successful!',
                        'type': 'success',
                    }
                }
        except Exception as e:
            raise ValidationError(f"Connection failed: {str(e)}")
```

### System Parameters (Alternative)
```python
# Store in ir.config_parameter
def _get_api_key(self):
    """Get API key from system parameters."""
    return self.env['ir.config_parameter'].sudo().get_param(
        'my_module.api_key', default=''
    )

def _set_api_key(self, value):
    """Set API key in system parameters."""
    self.env['ir.config_parameter'].sudo().set_param(
        'my_module.api_key', value
    )
```

---

## HTTP Client Mixin

### Reusable API Client
```python
import json
import logging
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

_logger = logging.getLogger(__name__)


class APIClientMixin(models.AbstractModel):
    _name = 'api.client.mixin'
    _description = 'API Client Mixin'

    def _get_session(self):
        """Get requests session with retry logic."""
        session = requests.Session()

        retries = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=[500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retries)
        session.mount('http://', adapter)
        session.mount('https://', adapter)

        return session

    def _get_headers(self):
        """Get default headers."""
        config = self._get_api_config()
        return {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {config.api_key}',
            'X-API-Version': '2024-01',
        }

    def _get_api_config(self):
        """Get API configuration for current company."""
        config = self.env['external.api.config'].search([
            ('company_id', '=', self.env.company.id),
            ('active', '=', True),
        ], limit=1)

        if not config:
            raise ValidationError("No API configuration found for this company.")

        return config

    def _make_request(self, method, endpoint, data=None, params=None):
        """Make HTTP request to external API."""
        config = self._get_api_config()
        url = f"{config.api_url.rstrip('/')}/{endpoint.lstrip('/')}"

        session = self._get_session()
        headers = self._get_headers()

        _logger.info("API Request: %s %s", method, url)

        try:
            response = session.request(
                method=method,
                url=url,
                headers=headers,
                json=data,
                params=params,
                timeout=30,
            )

            _logger.info("API Response: %s", response.status_code)

            if response.status_code >= 400:
                self._handle_error(response)

            return response

        except requests.Timeout:
            _logger.error("API Timeout: %s", url)
            raise ValidationError("API request timed out. Please try again.")

        except requests.RequestException as e:
            _logger.error("API Error: %s", str(e))
            raise ValidationError(f"API request failed: {str(e)}")

    def _handle_error(self, response):
        """Handle API error response."""
        try:
            error_data = response.json()
            message = error_data.get('message', response.text)
        except json.JSONDecodeError:
            message = response.text

        _logger.error("API Error %s: %s", response.status_code, message)

        if response.status_code == 401:
            raise ValidationError("Authentication failed. Check your API credentials.")
        elif response.status_code == 403:
            raise ValidationError("Access forbidden. Check your API permissions.")
        elif response.status_code == 404:
            raise ValidationError("Resource not found.")
        elif response.status_code == 429:
            raise ValidationError("Rate limit exceeded. Please try again later.")
        else:
            raise ValidationError(f"API Error ({response.status_code}): {message}")
```

---

## Sync Patterns

### Pull Sync (Import from External)
```python
class ExternalProduct(models.Model):
    _name = 'external.product'
    _description = 'External Product Sync'
    _inherit = ['api.client.mixin']

    external_id = fields.Char(string='External ID', index=True)
    product_id = fields.Many2one('product.product', string='Odoo Product')
    sync_date = fields.Datetime(string='Last Sync')
    sync_status = fields.Selection([
        ('pending', 'Pending'),
        ('synced', 'Synced'),
        ('error', 'Error'),
    ], default='pending')
    sync_error = fields.Text(string='Sync Error')

    @api.model
    def _cron_sync_products(self):
        """Cron job to sync products from external API."""
        _logger.info("Starting product sync from external API")

        try:
            response = self._make_request('GET', '/products', params={
                'updated_since': self._get_last_sync_date(),
                'limit': 100,
            })
            products = response.json().get('data', [])

            for product_data in products:
                self._sync_single_product(product_data)

            _logger.info("Synced %d products", len(products))

        except Exception as e:
            _logger.error("Product sync failed: %s", str(e))

    def _sync_single_product(self, data):
        """Sync single product from external data."""
        external_id = str(data['id'])

        # Find or create mapping
        mapping = self.search([('external_id', '=', external_id)], limit=1)
        if not mapping:
            mapping = self.create({'external_id': external_id})

        try:
            # Find or create Odoo product
            product = mapping.product_id
            if not product:
                product = self.env['product.product'].create({
                    'name': data['name'],
                    'default_code': data.get('sku'),
                    'list_price': data.get('price', 0),
                })
                mapping.product_id = product
            else:
                product.write({
                    'name': data['name'],
                    'list_price': data.get('price', 0),
                })

            mapping.write({
                'sync_date': fields.Datetime.now(),
                'sync_status': 'synced',
                'sync_error': False,
            })

        except Exception as e:
            mapping.write({
                'sync_status': 'error',
                'sync_error': str(e),
            })
            _logger.error("Failed to sync product %s: %s", external_id, str(e))
```

### Push Sync (Export to External)
```python
class ResPartner(models.Model):
    _inherit = 'res.partner'

    external_customer_id = fields.Char(string='External Customer ID')
    sync_to_external = fields.Boolean(string='Sync to External', default=True)

    def write(self, vals):
        """Override write to trigger external sync."""
        result = super().write(vals)

        # Sync if relevant fields changed
        sync_fields = {'name', 'email', 'phone', 'street', 'city'}
        if self.sync_to_external and sync_fields & set(vals.keys()):
            self._sync_to_external_api()

        return result

    def _sync_to_external_api(self):
        """Push customer data to external API."""
        for partner in self:
            if not partner.sync_to_external:
                continue

            data = {
                'name': partner.name,
                'email': partner.email,
                'phone': partner.phone,
                'address': {
                    'street': partner.street,
                    'city': partner.city,
                    'zip': partner.zip,
                    'country': partner.country_id.code,
                },
            }

            try:
                api_client = self.env['api.client.mixin']

                if partner.external_customer_id:
                    # Update existing
                    response = api_client._make_request(
                        'PUT',
                        f'/customers/{partner.external_customer_id}',
                        data=data
                    )
                else:
                    # Create new
                    response = api_client._make_request(
                        'POST', '/customers', data=data
                    )
                    result = response.json()
                    partner.external_customer_id = result['id']

            except Exception as e:
                _logger.error("Failed to sync partner %s: %s", partner.id, str(e))
```

### Bidirectional Sync
```python
class SyncManager(models.Model):
    _name = 'sync.manager'
    _description = 'Bidirectional Sync Manager'
    _inherit = ['api.client.mixin']

    @api.model
    def _cron_full_sync(self):
        """Full bidirectional sync."""
        self._pull_changes()
        self._push_changes()

    def _pull_changes(self):
        """Pull changes from external system."""
        last_sync = self._get_last_sync_timestamp('pull')

        response = self._make_request('GET', '/changes', params={
            'since': last_sync,
            'types': 'customer,product,order',
        })

        for change in response.json().get('changes', []):
            self._process_incoming_change(change)

        self._set_last_sync_timestamp('pull')

    def _push_changes(self):
        """Push local changes to external system."""
        # Get records modified since last push
        last_sync = self._get_last_sync_timestamp('push')

        modified_partners = self.env['res.partner'].search([
            ('write_date', '>', last_sync),
            ('sync_to_external', '=', True),
        ])

        for partner in modified_partners:
            partner._sync_to_external_api()

        self._set_last_sync_timestamp('push')
```

---

## Webhook Handling

### Incoming Webhooks
```python
from odoo import http
from odoo.http import request
import hmac
import hashlib


class WebhookController(http.Controller):

    @http.route('/webhook/external', type='json', auth='none',
                methods=['POST'], csrf=False)
    def handle_webhook(self):
        """Handle incoming webhook from external service."""
        # Verify signature
        signature = request.httprequest.headers.get('X-Signature')
        if not self._verify_signature(signature):
            return {'error': 'Invalid signature'}, 401

        data = request.jsonrequest
        event_type = data.get('event')

        _logger.info("Received webhook: %s", event_type)

        try:
            if event_type == 'customer.created':
                self._handle_customer_created(data['payload'])
            elif event_type == 'customer.updated':
                self._handle_customer_updated(data['payload'])
            elif event_type == 'order.completed':
                self._handle_order_completed(data['payload'])
            else:
                _logger.warning("Unknown webhook event: %s", event_type)

            return {'status': 'success'}

        except Exception as e:
            _logger.error("Webhook processing failed: %s", str(e))
            return {'status': 'error', 'message': str(e)}

    def _verify_signature(self, signature):
        """Verify webhook signature."""
        if not signature:
            return False

        secret = request.env['ir.config_parameter'].sudo().get_param(
            'my_module.webhook_secret'
        )
        if not secret:
            return False

        raw_body = request.httprequest.get_data()
        expected = hmac.new(
            secret.encode(),
            raw_body,
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(signature, expected)

    def _handle_customer_created(self, payload):
        """Process customer creation webhook."""
        partner = request.env['res.partner'].sudo().create({
            'name': payload['name'],
            'email': payload['email'],
            'external_customer_id': payload['id'],
        })
        _logger.info("Created partner %s from webhook", partner.id)
```

### Outgoing Webhooks
```python
class WebhookSender(models.Model):
    _name = 'webhook.sender'
    _description = 'Outgoing Webhook Sender'

    @api.model
    def send_webhook(self, event_type, payload, url=None):
        """Send webhook to external endpoint."""
        if not url:
            url = self.env['ir.config_parameter'].sudo().get_param(
                'my_module.webhook_url'
            )

        if not url:
            _logger.warning("No webhook URL configured")
            return False

        data = {
            'event': event_type,
            'timestamp': fields.Datetime.now().isoformat(),
            'payload': payload,
        }

        # Sign the payload
        secret = self.env['ir.config_parameter'].sudo().get_param(
            'my_module.webhook_secret'
        )
        signature = hmac.new(
            secret.encode(),
            json.dumps(data).encode(),
            hashlib.sha256
        ).hexdigest()

        headers = {
            'Content-Type': 'application/json',
            'X-Signature': signature,
        }

        try:
            response = requests.post(
                url, json=data, headers=headers, timeout=10
            )
            response.raise_for_status()
            _logger.info("Webhook sent successfully: %s", event_type)
            return True

        except Exception as e:
            _logger.error("Webhook failed: %s", str(e))
            # Queue for retry
            self._queue_webhook_retry(event_type, payload, url)
            return False
```

---

## OAuth2 Integration

### OAuth2 Token Management
```python
from datetime import timedelta


class OAuth2Config(models.Model):
    _name = 'oauth2.config'
    _description = 'OAuth2 Configuration'

    name = fields.Char(string='Name', required=True)
    client_id = fields.Char(string='Client ID', required=True)
    client_secret = fields.Char(
        string='Client Secret',
        required=True,
        groups='base.group_system',
    )
    auth_url = fields.Char(string='Authorization URL')
    token_url = fields.Char(string='Token URL', required=True)
    scope = fields.Char(string='Scope')

    access_token = fields.Char(string='Access Token', groups='base.group_system')
    refresh_token = fields.Char(string='Refresh Token', groups='base.group_system')
    token_expiry = fields.Datetime(string='Token Expiry')

    def get_access_token(self):
        """Get valid access token, refreshing if needed."""
        self.ensure_one()

        if self.access_token and self.token_expiry:
            if fields.Datetime.now() < self.token_expiry - timedelta(minutes=5):
                return self.access_token

        # Token expired or missing, refresh
        if self.refresh_token:
            self._refresh_token()
        else:
            self._get_new_token()

        return self.access_token

    def _refresh_token(self):
        """Refresh the access token."""
        response = requests.post(self.token_url, data={
            'grant_type': 'refresh_token',
            'refresh_token': self.refresh_token,
            'client_id': self.client_id,
            'client_secret': self.client_secret,
        })

        if response.status_code != 200:
            raise ValidationError("Token refresh failed")

        self._process_token_response(response.json())

    def _get_new_token(self):
        """Get new token using client credentials."""
        response = requests.post(self.token_url, data={
            'grant_type': 'client_credentials',
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'scope': self.scope,
        })

        if response.status_code != 200:
            raise ValidationError("Token acquisition failed")

        self._process_token_response(response.json())

    def _process_token_response(self, data):
        """Process token response and store tokens."""
        expires_in = data.get('expires_in', 3600)
        self.write({
            'access_token': data['access_token'],
            'refresh_token': data.get('refresh_token', self.refresh_token),
            'token_expiry': fields.Datetime.now() + timedelta(seconds=expires_in),
        })
```

---

## Rate Limiting

### Rate Limiter
```python
import time
from collections import deque


class RateLimiter:
    """Simple rate limiter for API calls."""

    def __init__(self, max_calls, period):
        self.max_calls = max_calls
        self.period = period  # seconds
        self.calls = deque()

    def wait_if_needed(self):
        """Wait if rate limit would be exceeded."""
        now = time.time()

        # Remove old calls outside the window
        while self.calls and self.calls[0] < now - self.period:
            self.calls.popleft()

        if len(self.calls) >= self.max_calls:
            sleep_time = self.period - (now - self.calls[0])
            if sleep_time > 0:
                _logger.info("Rate limit reached, sleeping %.2fs", sleep_time)
                time.sleep(sleep_time)

        self.calls.append(time.time())


# Usage in API client
class APIClient(models.AbstractModel):
    _name = 'api.client'
    _rate_limiter = RateLimiter(max_calls=100, period=60)

    def _make_request(self, method, endpoint, **kwargs):
        self._rate_limiter.wait_if_needed()
        # ... rest of request logic
```

---

## Error Handling & Retry

### Retry with Exponential Backoff
```python
import time
from functools import wraps


def retry_on_failure(max_retries=3, backoff_factor=2):
    """Decorator for retry with exponential backoff."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except (requests.Timeout, requests.ConnectionError) as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        sleep_time = backoff_factor ** attempt
                        _logger.warning(
                            "Attempt %d failed, retrying in %ds: %s",
                            attempt + 1, sleep_time, str(e)
                        )
                        time.sleep(sleep_time)
            raise last_exception
        return wrapper
    return decorator


class APIClientWithRetry(models.AbstractModel):
    _name = 'api.client.retry'

    @retry_on_failure(max_retries=3, backoff_factor=2)
    def _make_request(self, method, endpoint, **kwargs):
        # Request implementation
        pass
```

---

## Inbound Web Services API (XML-RPC & JSON-RPC)

External applications (mobile apps, ecommerce storefronts, microservices, third-party ERPs) can interact directly with Odoo without installing custom modules by using Odoo's built-in Web Services: **JSON-RPC** and **XML-RPC**.

### Protocol Comparison

| Feature | JSON-RPC (`/jsonrpc`) | XML-RPC (`/xmlrpc/2/*`) |
| :--- | :--- | :--- |
| **Transport** | Standard HTTP POST with JSON body | HTTP POST with XML payloads |
| **Best For** | Modern web, Node.js, frontend, Python `requests`, cURL | Legacy integrations, systems with built-in XML-RPC |
| **Payload Size** | Lightweight (compact JSON) | Verbose (XML tags) |
| **Authentication** | Pass API Key or Password | Pass API Key or Password |

---

### Authentication & Developer API Keys (`res.users.apikeys`)

> [!IMPORTANT]
> In **Odoo 17, 18, and 19**, external integrations should **never use the user's master password**. Always generate a **Developer API Key** via:
> `User Profile -> Account Security -> Developer API Keys -> New API Key`.
>
> API Keys:
> 1. Bypass 2FA/TOTP blocks on automated service accounts.
> 2. Can be revoked individually without changing user account passwords.
> 3. Restrict access strictly according to the owning user's Access Rights and Record Rules.

---

### 1. JSON-RPC Client Pattern (`/jsonrpc`)

The `/jsonrpc` endpoint is the most universal integration interface. It requires zero third-party SDKs—any standard HTTP client works.

#### Python Example (using `requests`)

```python
import requests

url = "https://odoo.example.com/jsonrpc"
db = "my_database"
login = "api_user@example.com"
api_key = "a1b2c3d4e5f6..."  # Generated Developer API Key


def jsonrpc_call(service, method, args):
    """Execute generic JSON-RPC call against Odoo."""
    payload = {
        "jsonrpc": "2.0",
        "method": "call",
        "params": {
            "service": service,
            "method": method,
            "args": args,
        },
        "id": 1,
    }
    response = requests.post(url, json=payload, timeout=15)
    response.raise_for_status()
    res = response.json()
    if "error" in res:
        raise RuntimeError(res["error"]["data"].get("message", res["error"]["message"]))
    return res["result"]


# 1. Authenticate to get UID
uid = jsonrpc_call("common", "authenticate", [db, login, api_key, {}])
assert uid, "Authentication failed"

# 2. Search & Read records
customers = jsonrpc_call("object", "execute_kw", [
    db, uid, api_key,
    "res.partner", "search_read",
    [[("customer_rank", ">", 0)]],
    {"fields": ["name", "email", "phone"], "limit": 10, "order": "name asc"}
])
print(f"Found {len(customers)} customers.")

# 3. Create a new record
new_partner_id = jsonrpc_call("object", "execute_kw", [
    db, uid, api_key,
    "res.partner", "create",
    [{"name": "Global Imports Ltd", "email": "info@globalimports.com"}]
])
print("Created Partner ID:", new_partner_id)

# 4. Trigger custom business method
jsonrpc_call("object", "execute_kw", [
    db, uid, api_key,
    "sale.order", "action_confirm",
    [[42]]
])
```

#### JavaScript / Node.js Example (using `fetch`)

```javascript
const url = "https://odoo.example.com/jsonrpc";
const db = "my_database";
const login = "api_user@example.com";
const apiKey = "a1b2c3d4e5f6...";

async function odooJsonRpc(service, method, args) {
    const response = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            jsonrpc: "2.0",
            method: "call",
            params: { service, method, args },
            id: Date.now(),
        }),
    });
    const data = await response.json();
    if (data.error) {
        throw new Error(data.error.data?.message || data.error.message);
    }
    return data.result;
}

// Usage:
// const uid = await odooJsonRpc("common", "authenticate", [db, login, apiKey, {}]);
// const partners = await odooJsonRpc("object", "execute_kw", [db, uid, apiKey, "res.partner", "search_read", [], { limit: 5 }]);
```

---

### 2. XML-RPC Client Pattern (`/xmlrpc/2/*`)

Standard XML-RPC interface using Python's built-in `xmlrpc.client`:

```python
import xmlrpc.client

url = "https://odoo.example.com"
db = "my_database"
login = "api_user@example.com"
api_key = "a1b2c3d4e5f6..."

# 1. Connection endpoints
common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common", allow_none=True)
models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object", allow_none=True)

# 2. Check Server Version & Authenticate
server_info = common.version()
print("Odoo Server Version:", server_info.get("server_version"))

uid = common.authenticate(db, login, api_key, {})
assert uid, "Failed to authenticate"

# 3. Check model access rights
can_create = models.execute_kw(
    db, uid, api_key,
    'sale.order', 'check_access_rights',
    ['create'], {'raise_exception': False}
)
print("Can create sale orders:", can_create)

# 4. Search and read with field projection and paging
orders = models.execute_kw(
    db, uid, api_key,
    'sale.order', 'search_read',
    [[('state', '=', 'sale')]],
    {
        'fields': ['name', 'partner_id', 'amount_total', 'date_order'],
        'limit': 20,
        'offset': 0,
        'order': 'date_order desc',
    }
)

# 5. Update record
models.execute_kw(
    db, uid, api_key,
    'res.partner', 'write',
    [[new_partner_id], {'phone': '+1 555 0199'}]
)

# 6. Delete record
models.execute_kw(
    db, uid, api_key,
    'res.partner', 'unlink',
    [[new_partner_id]]
)
```

---

### 3. Odoo 19 External JSON-2 API (`/json/2/<model>/<method>`)

> [!NOTE]
> **New in Odoo 19.0**: Odoo introduced the **JSON-2** external API (`/json/2/`). Unlike legacy JSON-RPC (`/jsonrpc`) or XML-RPC, JSON-2 is a modern REST-like JSON endpoint that:
> - Uses HTTP bearer token authentication (`Authorization: Bearer <API_KEY>`) directly—no preliminary `authenticate()` roundtrip required.
> - Accepts direct named JSON parameters mapped directly to Python method signatures without RPC envelopes.
> - Returns pure JSON payloads with real HTTP status codes (200, 401, 404, 422).
> - Operates statelessly (`save_session=False`) with zero cookie overhead and automatically leverages readonly database cursors on `@api.readonly` methods.
> - Self-documents models and methods at `https://your-odoo-instance.example.com/doc`.

#### Protocol & Headers

| Header | Requirement | Description |
| :--- | :--- | :--- |
| `Authorization` | Required | `Bearer <API_KEY>` (from `res.users.apikeys`) |
| `Content-Type` | Required | `application/json; charset=utf-8` |
| `X-Odoo-Database` | Optional | Target database name (required in multi-db environments without dbfilter host match) |
| `User-Agent` | Recommended | Identifier of the calling application |

#### Python Client Example (Odoo 19 JSON-2)

```python
import requests

BASE_URL = "https://odoo.example.com/json/2"
API_KEY = "6578616d706c65206a736f6e20617069206b6579"
DB_NAME = "production_db"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "X-Odoo-Database": DB_NAME,
    "Content-Type": "application/json",
}

# 1. Search & Read records (direct named parameters)
res = requests.post(
    f"{BASE_URL}/res.partner/search_read",
    headers=headers,
    json={
        "domain": [("customer_rank", ">", 0)],
        "fields": ["name", "email", "phone"],
        "limit": 10,
        "context": {"lang": "en_US"},
    },
    timeout=15,
)
res.raise_for_status()
partners = res.json()  # Returns list of dicts directly
print(f"Retrieved {len(partners)} partners.")

# 2. Create a record (vals parameter)
res = requests.post(
    f"{BASE_URL}/res.partner/create",
    headers=headers,
    json={
        "vals_list": [{"name": "Acme Corp", "email": "contact@acme.com"}],
    },
    timeout=15,
)
res.raise_for_status()
created_ids = res.json()  # Returns [id] directly
partner_id = created_ids[0]

# 3. Call recordset method (pass ids array in body)
res = requests.post(
    f"{BASE_URL}/sale.order/action_confirm",
    headers=headers,
    json={
        "ids": [42],
        "context": {"lang": "en_US"},
    },
    timeout=15,
)
res.raise_for_status()
```

#### JavaScript / Fetch Example (Odoo 19 JSON-2)

```javascript
const BASE_URL = "https://odoo.example.com/json/2";
const API_KEY = "6578616d706c65206a736f6e20617069206b6579";

async function odooJson2(model, method, params = {}) {
    const response = await fetch(`${BASE_URL}/${model}/${method}`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${API_KEY}`,
            "X-Odoo-Database": "production_db",
        },
        body: JSON.stringify(params),
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(`[${response.status}] ${error.name}: ${error.message}`);
    }
    return response.json();
}

// Usage:
// const partners = await odooJson2("res.partner", "search_read", {
//     domain: [["is_company", "=", true]],
//     fields: ["name", "vat"],
//     limit: 5,
// });
```

#### cURL Example (Odoo 19 JSON-2)

```bash
curl -X POST https://odoo.example.com/json/2/res.partner/search_read \
    -H "Authorization: Bearer $API_KEY" \
    -H "X-Odoo-Database: my_database" \
    -H "Content-Type: application/json" \
    -d '{
        "domain": [["is_company", "=", true]],
        "fields": ["name", "email"],
        "limit": 5
    }'
```

#### Programmatic API Key Management (Odoo 19)

In Odoo 19, API keys can be generated and revoked programmatically over `/json/2` when enabled via system parameter `base.enable_programmatic_api_keys = True`:

```python
# Generate a scoped API key
gen_res = requests.post(
    f"{BASE_URL}/res.users.apikeys/generate",
    headers=headers,
    json={
        "key": API_KEY,
        "name": "Integration Worker Key",
        "scope": "rpc",
        "expiration_date": "2027-01-01",
    },
)
gen_res.raise_for_status()
new_key = gen_res.json()  # Returns new secret string

# Revoke an old API key
rev_res = requests.post(
    f"{BASE_URL}/res.users.apikeys/revoke",
    headers=headers,
    json={"key": old_key},
)
rev_res.raise_for_status()
```

---

## Best Practices

1. **Always use Developer API Keys** - Never use user master passwords in automated integrations.
2. **Select the right protocol for the Odoo version**:
   - In **Odoo 19+**: Prefer **External JSON-2 API** (`/json/2/`) for clean REST semantics, stateless execution, and native bearer auth.
   - In **Odoo 17 & 18**: Use **JSON-RPC** (`/jsonrpc`) for lightweight, universal integration.
3. **Never hardcode credentials** - Use environment variables or dedicated encrypted config records.
4. **Use HTTPS** - Always use TLS encrypted connections.
5. **Implement retry logic with backoff** - Handle transient network blips and rate limits.
6. **Limit field projections** - In `search_read`, always specify explicit `'fields'` to prevent querying heavy binary or computed fields.
7. **Batch operations** - Pass multiple IDs to `write()`, `unlink()`, or custom methods instead of calling the API in a loop.
8. **Secure webhooks** - Always verify HMAC cryptographic signatures before processing inbound payloads.

## Related References

- [Web Controllers & Endpoints](controllers.md)
- [Bulk Data Import & Export](import-export.md)
- [Integrations Directory Index](README.md)
- [General Development Guide](../../skills/odoo-development/SKILL.md)
