import asyncio
import sys

# Must be set before uvicorn creates its event loop
# reload=False is required on Windows because reload spawns a child process
# that doesn't inherit the ProactorEventLoopPolicy
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

import uvicorn

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=False)
