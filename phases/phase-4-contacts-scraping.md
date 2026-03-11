# Phase 4: Contact Scraping

## Goal
Scrape the list of people who have messaged the active Facebook page and store them in the database.

## Backend Tasks

### 4.1 Facebook service — contact scraping (`services/facebook.py`)
- `fetch_contacts(page_id)`:
  - Navigate to the page's inbox (Messenger for Pages or /page_id/inbox)
  - Scroll through conversation list to load all contacts
  - For each conversation, extract:
    - Contact name
    - Facebook user ID or profile URL
    - Last message date (if visible)
  - Handle pagination / infinite scroll (scroll down, wait, repeat until no new contacts)
  - Return list of contacts

### 4.2 Contacts routes (`routes/pages.py` or new `routes/contacts.py`)
- `POST /api/contacts/fetch` — Trigger contact scraping for active page
- `GET /api/contacts` — Return stored contacts for active page
- `GET /api/contacts/count` — Return total contact count

### 4.3 Deduplication
- Before inserting, check if contact already exists (by fb_user_id + page_id)
- Update last_interaction date if contact already exists
- Track new vs existing contacts in response

## Frontend Tasks

### 4.4 Contacts section (on Pages page or Broadcast page)
- "Fetch Contacts" button on the active page
- Loading spinner with status: "Scraping contacts... found X so far"
- Display contact count after fetch
- Optional: scrollable contact list showing names

## Verification
- Select active page → click "Fetch Contacts"
- Contacts appear in DB with names and IDs
- Re-fetch → no duplicates, count stays consistent
- Large inbox (100+ contacts) → scrolling works, all contacts captured
