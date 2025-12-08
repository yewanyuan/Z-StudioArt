"""Scheduled tasks for PopGraph.

This module implements background scheduled tasks for:
- Subscription expiry checking (Requirements 4.7)
- History record cleanup (Requirements 6.5, 6.6)

Usage:
    # Start scheduler on application startup
    from app.tasks import start_scheduler, stop_scheduler
    
    @app.on_event("startup")
    async def startup():
        await start_scheduler()
    
    @app.on_event("shutdown")
    async def shutdown():
        await stop_scheduler()

Manual execution:
    # Run tasks manually via CLI
    python -m app.tasks.scheduler --task expiry
    python -m app.tasks.scheduler --task cleanup
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import User, get_async_session_maker
from app.models.schemas import MembershipTier
from app.services.membership_service import get_membership_service
from app.services.history_service import HistoryService

logger = logging.getLogger(__name__)

# Scheduler state
_scheduler_task: Optional[asyncio.Task] = None
_running = False

# Task intervals (in seconds)
EXPIRY_CHECK_INTERVAL = 3600  # 1 hour
CLEANUP_INTERVAL = 86400  # 24 hours


async def run_subscription_expiry_check() -> int:
    """Check and downgrade expired subscriptions.
    
    This task queries all users with non-FREE membership and checks
    if their subscription has expired. Expired users are downgraded
    to FREE tier.
    
    Returns:
        Number of users downgraded
        
    Requirements:
        - 4.7: WHEN a subscription expires THEN THE Subscription_Service 
               SHALL downgrade the user to FREE tier
    """
    logger.info("Starting subscription expiry check...")
    
    membership_service = get_membership_service()
    downgraded_count = 0
    
    try:
        async_session = get_async_session_maker()
        async with async_session() as session:
            # Query users with paid membership
            stmt = select(User).where(
                User.membership_tier.in_([
                    MembershipTier.BASIC,
                    MembershipTier.PROFESSIONAL
                ])
            )
            result = await session.execute(stmt)
            users = result.scalars().all()
            
            logger.info(f"Checking {len(users)} paid users for expiry...")
            
            for user in users:
                if membership_service.is_subscription_expired(user):
                    old_tier = user.membership_tier
                    user.membership_tier = MembershipTier.FREE
                    user.updated_at = datetime.now(timezone.utc)
                    downgraded_count += 1
                    
                    logger.info(
                        f"Downgraded user {user.id}: {old_tier.value} -> FREE"
                    )
            
            if downgraded_count > 0:
                await session.commit()
                
    except Exception as e:
        logger.error(f"Error during subscription expiry check: {e}")
        raise
    
    logger.info(f"Subscription expiry check completed: {downgraded_count} users downgraded")
    return downgraded_count


async def run_history_cleanup() -> int:
    """Clean up expired history records.
    
    This task removes history records that have exceeded their retention
    period based on user membership tier:
    - FREE users: 7 days retention
    - BASIC/PROFESSIONAL users: 90 days retention
    
    Returns:
        Number of records cleaned up
        
    Requirements:
        - 6.5: WHILE a user is on FREE tier THEN THE User_System SHALL 
               retain history records for 7 days
        - 6.6: WHILE a user is on BASIC or PROFESSIONAL tier THEN THE 
               User_System SHALL retain history records for 90 days
    """
    logger.info("Starting history cleanup...")
    
    cleaned_count = 0
    
    try:
        async_session = get_async_session_maker()
        async with async_session() as session:
            history_service = HistoryService(session)
            cleaned_count = await history_service.cleanup_expired_records()
    except Exception as e:
        logger.error(f"Error during history cleanup: {e}")
        raise
    
    logger.info(f"History cleanup completed: {cleaned_count} records removed")
    return cleaned_count


async def _scheduler_loop():
    """Main scheduler loop that runs tasks at specified intervals."""
    global _running
    
    last_expiry_check = 0
    last_cleanup = 0
    
    while _running:
        now = asyncio.get_event_loop().time()
        
        # Run subscription expiry check
        if now - last_expiry_check >= EXPIRY_CHECK_INTERVAL:
            try:
                await run_subscription_expiry_check()
            except Exception as e:
                logger.error(f"Subscription expiry check failed: {e}")
            last_expiry_check = now
        
        # Run history cleanup (less frequently)
        if now - last_cleanup >= CLEANUP_INTERVAL:
            try:
                await run_history_cleanup()
            except Exception as e:
                logger.error(f"History cleanup failed: {e}")
            last_cleanup = now
        
        # Sleep for a short interval before next check
        await asyncio.sleep(60)  # Check every minute


async def start_scheduler():
    """Start the background task scheduler.
    
    This should be called on application startup.
    """
    global _scheduler_task, _running
    
    if _running:
        logger.warning("Scheduler is already running")
        return
    
    _running = True
    _scheduler_task = asyncio.create_task(_scheduler_loop())
    logger.info("Background task scheduler started")


async def stop_scheduler():
    """Stop the background task scheduler.
    
    This should be called on application shutdown.
    """
    global _scheduler_task, _running
    
    _running = False
    
    if _scheduler_task:
        _scheduler_task.cancel()
        try:
            await _scheduler_task
        except asyncio.CancelledError:
            pass
        _scheduler_task = None
    
    logger.info("Background task scheduler stopped")


# CLI entry point for manual task execution
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run scheduled tasks manually")
    parser.add_argument(
        "--task",
        choices=["expiry", "cleanup", "all"],
        required=True,
        help="Task to run: expiry (subscription check), cleanup (history), or all"
    )
    
    args = parser.parse_args()
    
    async def main():
        if args.task in ("expiry", "all"):
            await run_subscription_expiry_check()
        if args.task in ("cleanup", "all"):
            await run_history_cleanup()
    
    asyncio.run(main())
