# Phase 6: Broadcast Engine & Real-time Progress

## Goal
Build the core broadcast engine that sends messages one by one with randomized delays, AI rephrasing per message, and real-time progress via WebSocket.

## Backend Tasks

### 6.1 WebSocket manager (`websocket/manager.py`)
- `ConnectionManager` class
  - `connect(websocket)` — accept and store connection
  - `disconnect(websocket)` — remove connection
  - `broadcast(event, data)` — send JSON to all connected clients
- Single connection (single user app)

### 6.2 Broadcast service (`services/broadcast.py`)
- `BroadcastService` class — the core engine
- `start_broadcast(base_message, batch_size, page_id)`:
  - Create a Broadcast record in DB (status: running)
  - Fetch contacts for the page (up to batch_size)
  - Skip contacts already messaged in a previous broadcast (optional: configurable)
  - For each contact (up to batch_size limit):
    1. Check if broadcast was stopped (poll a stop flag)
    2. Generate a unique message variant via Claude API
    3. Send the message via Playwright (navigate to conversation, type, send)
    4. Log result in MessageLog (sent/failed)
    5. Send WebSocket progress update
    6. Wait random delay (between min_delay and max_delay from settings)
  - On completion: update Broadcast record (status: completed, counts, timestamp)
  - Send WebSocket completion event

- `stop_broadcast()`:
  - Set a stop flag (threading Event or similar)
  - Current message finishes, then loop exits
  - Update Broadcast status to "stopped"

- **Batch size enforcement**: Never exceed the user's configured batch_size per run
- **Error handling**: If a message fails, log error, continue to next contact
- **Background execution**: Run in a background thread/asyncio task so API remains responsive

### 6.3 Facebook service — send message (`services/facebook.py`)
- `send_message(contact_id_or_url, message_text)`:
  - Navigate to conversation with the contact
  - Find message input box
  - **Human-like typing simulation** (NOT paste):
    - Use Playwright's `type()` with randomized per-keystroke delay (30-80ms)
    - Add micro-pauses every 5-15 characters (200-500ms) to simulate thinking
    - Occasional typo + backspace correction (small random chance ~5%)
    - Variable speed: faster on common words, slower on longer words
    ```python
    async def human_type(page, selector, text):
        for i, char in enumerate(text):
            # Base keystroke delay: 30-80ms
            delay = random.randint(30, 80)

            # Micro-pause every 5-15 chars (simulate thinking)
            if i > 0 and i % random.randint(5, 15) == 0:
                await asyncio.sleep(random.uniform(0.2, 0.5))

            # Occasional typo + correction (~5% chance)
            if random.random() < 0.05 and char.isalpha():
                wrong_char = random.choice('abcdefghijklmnopqrstuvwxyz')
                await page.type(selector, wrong_char, delay=delay)
                await asyncio.sleep(random.uniform(0.1, 0.3))
                await page.keyboard.press('Backspace')
                await asyncio.sleep(random.uniform(0.1, 0.2))

            await page.type(selector, char, delay=delay)
    ```
  - Press Enter (or click send) after a short post-typing pause (0.5-1.5s)
  - Verify message was sent (check for sent indicator)
  - Return success/failure

- **Why type, not paste**: Facebook monitors input events. Pasting fires a single `paste` event with no keyboard activity — a strong bot signal. Typing fires realistic `keydown/keyup/input` event sequences that match human behavior.

### 6.4 Broadcast routes (`routes/broadcast.py`)
- `POST /api/broadcast/start` — Body: `{base_message, batch_size}` → starts broadcast in background
  - Validates: active page exists, contacts fetched, message not empty, no broadcast already running
- `POST /api/broadcast/stop` — Stop running broadcast
- `GET /api/broadcast/status` — Return current broadcast state (running/idle, progress counts)
- WebSocket endpoint: `ws://localhost:8000/ws` — for real-time updates

### 6.5 Delay logic
```python
import random, asyncio
delay = random.uniform(settings.min_delay, settings.max_delay)
await asyncio.sleep(delay)
```

## Frontend Tasks

### 6.6 Broadcast page (`pages/Broadcast.jsx`)
- **Pre-broadcast checklist** (all must be green before starting):
  - Settings configured
  - Facebook logged in
  - Active page selected
  - Contacts fetched (show count)
- **Message input**: Textarea for primary message (or load from Compose page)
- **Batch size input**: Number input (override default from settings)
- **"Start Broadcast" button** — big, prominent, with confirmation dialog
- **"Stop Broadcast" button** — red, appears while broadcast is running

### 6.7 Live progress panel
- **Progress bar**: sent / total (batch_size)
- **Stats cards**: Sent (green), Failed (red), Remaining (gray)
- **Current status**: "Sending to [contact name]..." / "Waiting X seconds..."
- **Live message log**: Scrollable list of sent messages with:
  - Contact name
  - Message preview (truncated)
  - Status icon (checkmark / X)
  - Timestamp
- **Estimated time remaining**: Based on average delay and remaining count

### 6.8 WebSocket hook (`hooks/useWebSocket.js`)
- Connect to `ws://localhost:8000/ws`
- Listen for broadcast events
- Update React state on each event
- Auto-reconnect on disconnect

## Verification
- Set batch_size to 3 for testing
- Start broadcast → see real-time progress for 3 contacts
- Each message is different (check MessageLog)
- Stop mid-broadcast → stops after current message
- Delays are randomized within configured range
- Failed messages logged but don't stop the broadcast
- Re-start after stop → continues with remaining contacts
