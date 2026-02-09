import asyncio
import logging
import sys
import os
from aiohttp import web

# Add project directory to path to fix ModuleNotFoundError
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from aiogram import Bot, Dispatcher
import config
import handlers
from middlewares import SubscriptionMiddleware
import database
import scheduler

async def health_check(request):
    return web.Response(text="Bot is running OK")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', health_check)
    app.router.add_get('/health', health_check)
    
    runner = web.AppRunner(app)
    await runner.setup()
    
    port = int(os.getenv("PORT", 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    print(f"Web server started on port {port}")

async def main():
    if not config.BOT_TOKEN:
        print("ERROR: BOT_TOKEN is not set in .env file via config.py")
        return

    # Initialize DB
    database.init_db()

    bot = Bot(token=config.BOT_TOKEN)
    dp = Dispatcher()
    
    dp.include_router(handlers.router)
    
    print("Bot ishga tushdi (DB + Scheduler + WebServer)...")
    
    # Start Scheduler and Web Server
    scheduler_task = asyncio.create_task(scheduler.start_scheduler(bot))
    web_task = asyncio.create_task(start_web_server())
    
    try:
        await dp.start_polling(bot)
    finally:
        # Graceful shutdown
        await bot.session.close()
        scheduler_task.cancel()
        web_task.cancel()
        try:
            await asyncio.gather(scheduler_task, web_task, return_exceptions=True)
        except asyncio.CancelledError:
            pass

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    
    # Use uvloop for better performance on Linux if available
    try:
        import uvloop
        asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
        print("Using uvloop for better performance.")
    except ImportError:
        pass

    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Bot stopped.")
