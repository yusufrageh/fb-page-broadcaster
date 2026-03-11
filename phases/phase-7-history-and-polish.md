# Phase 7: History Page & Final Polish

## Goal
Build the History page to view past broadcasts, and polish the overall UI/UX.

## Backend Tasks

### 7.1 History routes (`routes/history.py`)
- `GET /api/history` — List all broadcasts (newest first)
  - Returns: id, page_name, base_message (truncated), status, sent_count, failed_count, created_at
- `GET /api/history/{id}` — Single broadcast details + all message logs
  - Returns: full broadcast info + list of MessageLog entries with contact names

## Frontend Tasks

### 7.2 History page (`pages/History.jsx`)
- **Broadcast list**: Table or card list showing past broadcasts
  - Date, page name, message preview, batch size
  - Status badge (completed/stopped/failed)
  - Sent/Failed counts
  - Click to expand → see individual message logs
- **Broadcast detail view**: Expandable or modal
  - Full base message
  - List of all messages sent with:
    - Contact name
    - Actual message sent
    - Status (sent/failed)
    - Error message if failed
    - Timestamp
- **Filters**: By status (all/completed/stopped/failed), by page
- **Empty state**: "No broadcasts yet" with link to Compose page

### 7.3 UI Polish
- Consistent dark theme across all pages
- Loading skeletons for data fetching
- Toast notifications (react-toastify) for all actions:
  - Settings saved
  - Pages fetched
  - Broadcast started/stopped/completed
  - Errors
- Responsive sidebar (collapsible on small screens)
- Smooth page transitions
- Icons from react-icons throughout the UI
- Confirmation dialogs for destructive actions (start broadcast, stop broadcast)

### 7.4 Error handling polish
- Global error boundary in React
- API error interceptor in axios client
- Friendly error messages (not raw API errors)
- Retry buttons where appropriate

### 7.5 Final checks
- All pages connected and functional end-to-end
- Database stores everything correctly
- WebSocket reconnects gracefully
- No console errors
- Playwright handles Facebook UI changes gracefully (use stable selectors)

## Verification
- Complete a full broadcast → appears in History
- Click broadcast → see all sent messages
- Stop a broadcast → shows as "stopped" in history
- All toasts fire correctly
- Dark theme consistent across all pages
- App works after full restart (data persists)
