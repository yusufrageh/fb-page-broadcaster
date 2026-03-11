# Phase 3: Facebook Login & Page Selection

## Goal
Use Playwright to log into Facebook with saved credentials, fetch the user's managed pages, and let them select which page to broadcast from.

## Backend Tasks

### 3.1 Facebook service (`services/facebook.py`)
- `FacebookService` class that manages a Playwright browser instance
- `login(email, password)`:
  - Launch Chromium (headless)
  - Navigate to facebook.com/login
  - Fill email & password, click login
  - Handle 2FA prompt if needed (return status to frontend)
  - Save session cookies for reuse
- `fetch_pages()`:
  - Navigate to page management or /pages/?category=your_pages
  - Scrape page names, IDs, and URLs
  - Return list of pages
- `is_logged_in()`:
  - Check if saved cookies are still valid
- Cookie persistence: save/load cookies to a JSON file so user doesn't re-login every time

### 3.2 Pages routes (`routes/pages.py`)
- `POST /api/pages/fetch` — Trigger login + fetch pages, store in DB
- `GET /api/pages` — Return stored pages
- `PUT /api/pages/{id}/activate` — Set a page as the active page (deactivate others)

### 3.3 Handle login edge cases
- Invalid credentials → return clear error
- 2FA/checkpoint → return "2fa_required" status + prompt user
- Session expired → prompt re-login
- Rate limiting → inform user to wait

## Frontend Tasks

### 3.4 Pages page (`pages/Pages.jsx`)
- "Fetch My Pages" button → calls POST /api/pages/fetch
- Loading state while Playwright logs in and scrapes
- Display pages as cards with:
  - Page name
  - Page URL
  - "Set Active" button
  - Active badge on selected page
- Status indicator: logged in / not logged in
- Error handling: show login errors, 2FA prompts

## Verification
- Click "Fetch My Pages" with valid credentials → pages appear
- Select a page → it shows as active
- Refresh → active page persists
- Invalid credentials → clear error message
- Re-fetch → updates page list without duplicates
