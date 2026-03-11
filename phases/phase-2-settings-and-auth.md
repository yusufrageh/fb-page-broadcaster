# Phase 2: Settings Page & Credential Management

## Goal
Build the Settings page where the user configures their Facebook credentials, Claude API key, delay range, and default batch size.

## Backend Tasks

### 2.1 Settings routes (`routes/settings.py`)
- `GET /api/settings` — Return current settings (passwords masked)
- `PUT /api/settings` — Update settings, encrypt sensitive fields before storing
- On first run, auto-create a default settings row

### 2.2 Encryption (`core/security.py`)
- Use Fernet symmetric encryption
- `encrypt_value(plain_text)` → encrypted string
- `decrypt_value(encrypted_text)` → plain text
- Key derived from SECRET_KEY in .env

## Frontend Tasks

### 2.3 Settings page (`pages/Settings.jsx`)
- Form fields:
  - **Facebook Email** — text input
  - **Facebook Password** — password input (show/hide toggle)
  - **Claude API Key** — password input (show/hide toggle)
  - **Min Delay** — number input (seconds, default: 30)
  - **Max Delay** — number input (seconds, default: 90)
  - **Default Batch Size** — number input (default: 50, the max messages per run)
- Save button → PUT /api/settings
- Success/error toast notifications
- Load existing settings on mount (passwords show as "••••••" if set)

### 2.4 Settings validation
- Min delay must be > 0
- Max delay must be > min delay
- Batch size must be between 1 and 500
- Email format validation
- All fields required before saving

## Verification
- Open Settings page → fill in all fields → Save
- Refresh page → settings persist (passwords masked)
- Check database → credentials are encrypted (not plain text)
- Invalid inputs show validation errors
