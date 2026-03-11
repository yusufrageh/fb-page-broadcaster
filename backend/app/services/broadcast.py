import asyncio
import random
from datetime import datetime

from sqlalchemy import select

from app.core.database import async_session
from app.models.settings import Settings
from app.models.broadcast import Broadcast
from app.models.contact import Contact
from app.models.message_log import MessageLog
from app.services.facebook import (
    login_to_facebook, navigate_to_inbox,
    get_visible_conversations, click_conversation_by_name,
    send_message_in_conversation, scroll_conversation_list,
    burst_scroll_to_unsent, _log,
)
from app.services.message import rephrase_message
from app.websocket.manager import ws_manager

_current_task: asyncio.Task | None = None
_stop_event = asyncio.Event()


def is_running() -> bool:
    return _current_task is not None and not _current_task.done()


async def start_broadcast(broadcast_id: int):
    global _current_task
    _stop_event.clear()
    _current_task = asyncio.create_task(_run_broadcast(broadcast_id))
    return _current_task


async def stop_broadcast():
    _stop_event.set()


async def _run_broadcast(broadcast_id: int):
    async with async_session() as session:
        broadcast = await session.get(Broadcast, broadcast_id)
        if not broadcast:
            return

        broadcast.status = "running"
        await session.commit()

        # Load settings
        result = await session.execute(select(Settings).where(Settings.id == 1))
        settings = result.scalar_one_or_none()
        min_delay = settings.min_delay if settings else 5.0
        max_delay = settings.max_delay if settings else 15.0

        batch_size = broadcast.batch_size
        broadcast.total_contacts = batch_size
        await session.commit()

        try:
            page = await login_to_facebook()
            await navigate_to_inbox(page)

            # Track names we've sent to in this broadcast
            sent_names = set()
            # Also load names already sent to recently (from DB)
            result = await session.execute(
                select(Contact.name)
                .where(Contact.page_id == broadcast.page_id)
                .where(Contact.last_broadcast_at.isnot(None))
            )
            already_sent = {row[0] for row in result.all()}
            skip_names = set(already_sent)

            sent_count = 0
            failed_count = 0
            stale_scroll_rounds = 0

            await ws_manager.broadcast("broadcast:progress", {
                "sent": 0, "failed": 0,
                "remaining": batch_size,
                "total": batch_size,
                "current_contact": None,
            })

            while sent_count < batch_size:
                if _stop_event.is_set():
                    broadcast.status = "stopped"
                    broadcast.completed_at = datetime.utcnow()
                    await session.commit()
                    await ws_manager.broadcast("broadcast:completed", {
                        "total_sent": broadcast.sent_count,
                        "total_failed": broadcast.failed_count,
                        "duration": str(broadcast.completed_at - broadcast.created_at),
                    })
                    return

                # Get visible conversation names
                visible = await get_visible_conversations(page)
                # Find first unsent conversation
                target = None
                for name in visible:
                    if name not in skip_names:
                        target = name
                        break

                if not target:
                    # All visible are already sent — burst scroll past them
                    _log(f"[DEBUG] All visible sent, burst scrolling to find unsent...")
                    await ws_manager.broadcast("broadcast:progress", {
                        "sent": sent_count, "failed": failed_count,
                        "remaining": batch_size - sent_count,
                        "total": batch_size,
                        "current_contact": "Scrolling to find new contacts...",
                    })
                    found = await burst_scroll_to_unsent(page, skip_names)
                    if not found:
                        _log(f"[DEBUG] No more unsent conversations in inbox")
                        break
                    continue

                stale_scroll_rounds = 0
                skip_names.add(target)

                await ws_manager.broadcast("broadcast:progress", {
                    "sent": sent_count, "failed": failed_count,
                    "remaining": batch_size - sent_count,
                    "total": batch_size,
                    "current_contact": target,
                })

                # Click on the conversation
                clicked = await click_conversation_by_name(page, target)
                if not clicked:
                    _log(f"[DEBUG] Could not click conversation: {target}")
                    failed_count += 1
                    broadcast.failed_count += 1
                    await session.commit()
                    continue

                await asyncio.sleep(3)

                # Rephrase message
                try:
                    variants = await rephrase_message(broadcast.base_message, variant_count=1)
                    rephrased = variants[0]
                except Exception:
                    rephrased = broadcast.base_message

                # Send message
                success = await send_message_in_conversation(page, rephrased)

                # Save / update contact in DB
                fb_user_id = target.replace(' ', '_')
                result = await session.execute(
                    select(Contact).where(
                        Contact.fb_user_id == fb_user_id,
                        Contact.page_id == broadcast.page_id,
                    )
                )
                contact = result.scalar_one_or_none()
                if not contact:
                    contact = Contact(
                        fb_user_id=fb_user_id,
                        name=target,
                        page_id=broadcast.page_id,
                    )
                    session.add(contact)
                    await session.flush()

                log = MessageLog(
                    broadcast_id=broadcast.id,
                    contact_id=contact.id,
                    message_text=rephrased,
                    status="sent" if success else "failed",
                    error_message=None if success else "Failed to send",
                )
                session.add(log)

                if success:
                    sent_count += 1
                    broadcast.sent_count += 1
                    contact.last_broadcast_at = datetime.utcnow()
                    _log(f"[DEBUG] Sent to: {target} ({sent_count}/{batch_size})")
                else:
                    failed_count += 1
                    broadcast.failed_count += 1
                    _log(f"[DEBUG] Failed to send to: {target}")

                await session.commit()

                await ws_manager.broadcast("broadcast:message_sent", {
                    "contact_name": target,
                    "message_preview": rephrased[:80],
                    "status": "sent" if success else "failed",
                })

                # Wait briefly, then scroll down one step so the next unsent
                # conversation becomes visible (no full page reload — keeps scroll position)
                await asyncio.sleep(1)
                await scroll_conversation_list(page)

                # Random delay between messages
                if sent_count < batch_size:
                    delay = random.uniform(min_delay, max_delay)
                    await asyncio.sleep(delay)

            broadcast.status = "completed" if sent_count >= batch_size else "partial"
            _log(f"[DEBUG] Broadcast finished: {sent_count}/{batch_size} sent")
            broadcast.completed_at = datetime.utcnow()
            await session.commit()

            await ws_manager.broadcast("broadcast:completed", {
                "total_sent": broadcast.sent_count,
                "total_failed": broadcast.failed_count,
                "duration": str(broadcast.completed_at - broadcast.created_at),
            })

        except Exception as e:
            import traceback
            _log(f"[ERROR] Broadcast failed: {e}")
            _log(traceback.format_exc())
            broadcast.status = "failed"
            broadcast.completed_at = datetime.utcnow()
            await session.commit()
            await ws_manager.broadcast("broadcast:error", {
                "error_message": str(e),
            })
