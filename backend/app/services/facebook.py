import asyncio
import sys
from playwright.async_api import async_playwright, Browser, Page as PlaywrightPage

from app.core.security import decrypt
from app.core.database import async_session
from app.models.settings import Settings
from app.websocket.manager import ws_manager
from sqlalchemy import select


_LOG_FILE = "debug_log.txt"

def _log(msg: str):
    """Print debug messages safely on Windows (handles Unicode) and write to file."""
    try:
        print(msg)
    except UnicodeEncodeError:
        print(msg.encode("ascii", errors="replace").decode())
    try:
        with open(_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(msg + "\n")
    except Exception:
        pass

_browser: Browser | None = None
_page: PlaywrightPage | None = None
_pw = None


async def _get_credentials() -> tuple[str, str]:
    async with async_session() as session:
        result = await session.execute(select(Settings).where(Settings.id == 1))
        settings = result.scalar_one_or_none()
        if not settings or not settings.fb_email or not settings.fb_password:
            raise ValueError("Facebook credentials not configured")
        return settings.fb_email, decrypt(settings.fb_password)


async def get_browser() -> Browser:
    global _browser, _pw
    if _browser is None or not _browser.is_connected():
        _pw = await async_playwright().start()
        _browser = await _pw.chromium.launch(headless=False)
    return _browser


async def login_to_facebook() -> PlaywrightPage:
    global _page
    browser = await get_browser()
    context = await browser.new_context(
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    )
    _page = await context.new_page()
    email, password = await _get_credentials()

    await _page.goto("https://www.facebook.com/login", wait_until="networkidle")
    await _page.fill('input[name="email"]', email)
    await _page.fill('input[name="pass"]', password)

    # Try to click the login button, but skip if already navigated away
    if "login" in _page.url.lower():
        try:
            login_btn = _page.locator('#loginbutton, button[name="login"], button[type="submit"], input[type="submit"][value="Log In"], [data-testid="royal_login_button"]').first
            await login_btn.click(timeout=5000)
        except Exception:
            pass  # May have auto-submitted

    await _page.wait_for_load_state("networkidle")
    await asyncio.sleep(3)

    # Wait for 2FA/checkpoint — give user up to 60s to complete it manually
    for _ in range(20):
        current_url = _page.url.lower()
        if "checkpoint" not in current_url and "login" not in current_url and "two_step" not in current_url:
            break
        await asyncio.sleep(3)
    else:
        raise ValueError("Facebook login failed. Could not pass login/2FA within 60 seconds.")

    return _page


async def fetch_managed_pages(page: PlaywrightPage) -> list[dict]:
    """Navigate to pages management and extract page info.
    Stores the page slug as fb_page_id since that's the most reliable identifier.
    """
    await page.goto("https://www.facebook.com/pages/?category=your_pages", wait_until="networkidle")
    await asyncio.sleep(5)

    pages = await page.evaluate("""
        () => {
            const results = [];
            const seen = new Set();
            const allLinks = document.querySelectorAll('a[href]');
            allLinks.forEach(link => {
                const href = link.href || '';
                const name = link.textContent?.trim();
                if (!name || name.length < 2 || name.length > 100) return;
                if (seen.has(name)) return;

                const idMatch = href.match(/facebook\\.com\\/(profile\\.php\\?id=)?(\\d{5,})/);
                const slugMatch = href.match(/facebook\\.com\\/([a-zA-Z0-9.]+)\\/?$/);

                if (idMatch) {
                    seen.add(name);
                    results.push({ fb_page_id: idMatch[2], name: name, url: href });
                } else if (slugMatch && !['pages','settings','login','help','watch','groups','gaming','marketplace','events','bookmarks','memories','friends','notifications','messages','videos','reels','saved'].includes(slugMatch[1])) {
                    seen.add(name);
                    results.push({ fb_page_id: slugMatch[1], name: name, url: href });
                }
            });
            return results;
        }
    """)

    if not pages:
        _log(f"[DEBUG] No pages found. Current URL: {page.url}")
        _log(f"[DEBUG] Page title: {await page.title()}")

    return pages


async def fetch_page_conversations(page: PlaywrightPage, fb_page_id: str, max_contacts: int = 100) -> list[dict]:
    """Navigate to page and find its inbox to scrape contacts."""
    # Step 1: Go to the page profile
    _log(f"[DEBUG] Navigating to page: {fb_page_id}")
    _log(f"[DEBUG] Max contacts to fetch: {max_contacts}")
    await page.goto(f"https://www.facebook.com/{fb_page_id}", wait_until="networkidle")
    await asyncio.sleep(3)

    # Step 2: Try to find and click an Inbox/Messages link on the page
    inbox_clicked = False
    inbox_selectors = [
        'a:has-text("Inbox")',
        'a:has-text("Messages")',
        'a:has-text("Messaging")',
        'a[href*="inbox"]',
        'a[href*="messages"]',
        'a[href*="messaging"]',
    ]
    for sel in inbox_selectors:
        try:
            link = page.locator(sel).first
            if await link.is_visible(timeout=2000):
                await link.click()
                await page.wait_for_load_state("networkidle")
                await asyncio.sleep(3)
                inbox_clicked = True
                _log(f"[DEBUG] Clicked inbox link with selector: {sel}")
                break
        except Exception:
            continue

    if not inbox_clicked:
        # Step 3: Try Meta Business Suite as fallback
        _log("[DEBUG] No inbox link found on page, trying Meta Business Suite...")
        await page.goto("https://business.facebook.com/latest/inbox/all", wait_until="networkidle")
        await asyncio.sleep(5)

    _log(f"[DEBUG] Now on: {page.url}")
    _log(f"[DEBUG] Title: {await page.title()}")

    # Step 4: Stay on "All messages" tab — do NOT filter by Messenger
    await asyncio.sleep(2)

    # Step 5: Scroll the conversation list with native mouse wheel.
    # IMPORTANT: div[role="presentation"] matches many tiny toolbar icons (16x16).
    # Real conversation rows are large (height > 50px).  We filter by size to find
    # actual rows, then position the mouse over one before using mouse.wheel().

    await page.evaluate("() => { window.__collectedContacts = {}; }")

    # Find a REAL conversation row — filter by bounding box size
    mouse_ready = False
    conv_row_info = await page.evaluate("""
        () => {
            const rows = document.querySelectorAll('div[role="presentation"]');
            for (const row of rows) {
                const r = row.getBoundingClientRect();
                if (r.height > 50 && r.width > 200) {
                    return { x: r.x, y: r.y, w: r.width, h: r.height };
                }
            }
            return null;
        }
    """)

    if conv_row_info:
        # Position mouse in the middle of the conversation row (left panel)
        mouse_x = conv_row_info["x"] + conv_row_info["w"] / 2
        mouse_y = conv_row_info["y"] + conv_row_info["h"] / 2
        await page.mouse.move(mouse_x, mouse_y)
        mouse_ready = True
        _log(f"[DEBUG] Mouse over conversation row at ({mouse_x:.0f}, {mouse_y:.0f}), row size {conv_row_info['w']:.0f}x{conv_row_info['h']:.0f}")
    else:
        _log("[DEBUG] Could not find a large conversation row for mouse positioning")

    stale_rounds = 0
    prev_collected = 0
    for scroll_round in range(200):
        # Harvest visible rows — only rows large enough to be conversations
        collected = await page.evaluate("""
            () => {
                const store = window.__collectedContacts;
                const rows = document.querySelectorAll('div[role="presentation"]');
                rows.forEach(row => {
                    const r = row.getBoundingClientRect();
                    if (r.height < 50 || r.width < 200) return;
                    const text = row.innerText?.trim();
                    if (!text) return;
                    const name = text.split('\\n')[0]?.trim();
                    if (!name || name.length < 2 || name.length > 80) return;
                    if (!store[name]) {
                        store[name] = {
                            fb_user_id: name.replace(/\\s+/g, '_'),
                            name: name,
                            profile_url: ''
                        };
                    }
                });
                return Object.keys(store).length;
            }
        """)

        # Send progress via WebSocket every round
        if scroll_round % 3 == 0 or collected != prev_collected:
            await ws_manager.broadcast("contacts:fetch_progress", {
                "collected": collected,
                "target": max_contacts,
            })

        if collected >= max_contacts:
            _log(f"[DEBUG] Reached max_contacts limit ({max_contacts}) at round {scroll_round}")
            break

        if collected == prev_collected:
            stale_rounds += 1
            if stale_rounds >= 8:
                _log(f"[DEBUG] No new contacts after 8 scroll attempts at {collected}, stopping")
                break
        else:
            stale_rounds = 0
            _log(f"[DEBUG] Round {scroll_round}: {collected} contacts")
        prev_collected = collected

        # Scroll with native mouse wheel
        if mouse_ready:
            await page.mouse.wheel(0, 300)
        else:
            await page.evaluate("""
                () => {
                    const rows = document.querySelectorAll('div[role="presentation"]');
                    const big = Array.from(rows).filter(r => {
                        const b = r.getBoundingClientRect();
                        return b.height > 50 && b.width > 200;
                    });
                    if (big.length) big[big.length - 1].scrollIntoView({ block: 'end' });
                }
            """)

        await asyncio.sleep(0.6)

    # Final progress update
    await ws_manager.broadcast("contacts:fetch_progress", {
        "collected": collected if 'collected' in dir() else 0,
        "target": max_contacts,
        "done": True,
    })

    # Collect final results
    contacts = await page.evaluate("""
        () => {
            const store = window.__collectedContacts || {};
            return Object.values(store);
        }
    """)

    # Respect max_contacts limit
    if contacts and len(contacts) > max_contacts:
        contacts = contacts[:max_contacts]

    if contacts:
        _log(f"[DEBUG] Found {len(contacts)} contacts (max: {max_contacts})")
    else:
        # Take a screenshot for debugging
        _log(f"[DEBUG] No contacts found. URL: {page.url}")
        try:
            await page.screenshot(path="debug_inbox.png")
            _log("[DEBUG] Screenshot saved to debug_inbox.png")
        except Exception:
            pass

    return contacts


async def navigate_to_inbox(page: PlaywrightPage) -> None:
    """Navigate to Meta Business Suite inbox (All messages)."""
    await page.goto("https://business.facebook.com/latest/inbox/all", wait_until="domcontentloaded", timeout=60000)
    await asyncio.sleep(5)


async def get_visible_conversations(page: PlaywrightPage) -> list[str]:
    """Return names of currently visible conversations in the inbox panel."""
    names = await page.evaluate("""
        () => {
            const junk = ['an admin is typing', 'you:', 'sent', 'seen', 'active now',
                          'messenger', 'instagram', 'no messages'];
            const results = [];
            const rows = document.querySelectorAll('div[role="presentation"]');
            rows.forEach(row => {
                const r = row.getBoundingClientRect();
                if (r.height < 50 || r.width < 200) return;
                const text = row.innerText?.trim();
                if (!text) return;
                const name = text.split('\\n')[0]?.trim();
                if (!name || name.length < 2 || name.length > 80) return;
                if (junk.some(j => name.toLowerCase() === j)) return;
                results.push(name);
            });
            return results;
        }
    """)
    return names


async def click_conversation_by_name(page: PlaywrightPage, name: str) -> bool:
    """Click a visible conversation row by its contact name."""
    clicked = await page.evaluate("""
        (targetName) => {
            const rows = document.querySelectorAll('div[role="presentation"]');
            for (const row of rows) {
                const r = row.getBoundingClientRect();
                if (r.height < 50 || r.width < 200) continue;
                const text = row.innerText?.trim();
                if (text && text.split('\\n')[0]?.trim() === targetName) {
                    row.click();
                    return true;
                }
            }
            return false;
        }
    """, name)
    return clicked


async def send_message_in_conversation(page: PlaywrightPage, message: str) -> bool:
    """Type and send a message in the currently open conversation."""
    try:
        # Wait for the textbox to appear (conversation may still be loading)
        msg_box = page.locator('[role="textbox"]').last
        await msg_box.wait_for(state="visible", timeout=10000)
        await msg_box.click(timeout=5000)
        await asyncio.sleep(0.5)
        await msg_box.fill(message)
        await asyncio.sleep(0.5)
        await msg_box.press("Enter")
        await asyncio.sleep(2)
        return True
    except Exception as e:
        _log(f"[DEBUG] Failed to type/send message: {e}")
        return False


async def _position_mouse_on_conv_list(page: PlaywrightPage) -> bool:
    """Move mouse over a conversation row. Returns True if positioned."""
    conv_row = await page.evaluate("""
        () => {
            const rows = document.querySelectorAll('div[role="presentation"]');
            for (const row of rows) {
                const r = row.getBoundingClientRect();
                if (r.height > 50 && r.width > 200) {
                    return { x: r.x + r.width / 2, y: r.y + r.height / 2 };
                }
            }
            return null;
        }
    """)
    if conv_row:
        await page.mouse.move(conv_row["x"], conv_row["y"])
        return True
    return False


async def scroll_conversation_list(page: PlaywrightPage):
    """Scroll the conversation list down one step."""
    if await _position_mouse_on_conv_list(page):
        await page.mouse.wheel(0, 600)
        await asyncio.sleep(1)


async def burst_scroll_to_unsent(page: PlaywrightPage, skip_names: set, max_scrolls: int = 1000) -> bool:
    """Rapidly scroll past already-sent conversations until an unsent one is found.
    Returns True if an unsent conversation is now visible, False if end of list reached."""
    if not await _position_mouse_on_conv_list(page):
        return False

    stale = 0
    total_scrolled = 0
    all_seen_names = set()

    for i in range(max_scrolls):
        # Scroll and give lazy loading time to fetch new conversations
        await page.mouse.wheel(0, 800)
        await asyncio.sleep(1.0)
        total_scrolled += 1

        visible = await get_visible_conversations(page)
        visible_set = set(visible)

        # Check if any unsent conversation is now visible
        for name in visible:
            if name not in skip_names:
                _log(f"[DEBUG] Found unsent contact after {total_scrolled} scrolls")
                return True

        # Track all names we've ever seen while scrolling
        new_names = visible_set - all_seen_names
        all_seen_names.update(visible_set)

        if new_names:
            stale = 0  # new conversations loaded, keep going
        else:
            stale += 1
            # When stale, try a bigger scroll to break through
            if stale % 5 == 0:
                await page.mouse.wheel(0, 2000)
                await asyncio.sleep(1.5)
                total_scrolled += 1
            if stale >= 30:
                _log(f"[DEBUG] Reached end of conversation list after {total_scrolled} scrolls ({len(all_seen_names)} total contacts seen)")
                return False

        # Log progress every 10 scrolls
        if total_scrolled % 10 == 0:
            _log(f"[DEBUG] Burst scrolling... {total_scrolled} scrolls, {len(all_seen_names)} contacts seen, skipping sent")

    _log(f"[DEBUG] Max burst scrolls reached ({max_scrolls})")
    return False


async def close_browser():
    global _browser, _page, _pw
    if _browser and _browser.is_connected():
        await _browser.close()
    if _pw:
        await _pw.stop()
    _browser = None
    _page = None
    _pw = None
