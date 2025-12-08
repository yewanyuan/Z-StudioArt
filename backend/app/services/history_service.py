"""History Service for managing user generation history.

Requirements: 6.1, 6.3, 6.4, 6.5, 6.6 - 生成历史记录管理
"""

import logging
from datetime import datetime, timedelta
from typing import Optional
from uuid import uuid4

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.database import GeneratedImageRecord, GenerationRecord, User
from app.models.schemas import GenerationType, MembershipTier

logger = logging.getLogger(__name__)


# History retention periods (in days)
FREE_RETENTION_DAYS = 7
PAID_RETENTION_DAYS = 90


class HistoryService:
    """Service for managing user generation history.
    
    Requirements:
    - 6.1: Paginated history list sorted by creation time descending
    - 6.3: Record detail retrieval
    - 6.4: Record deletion
    - 6.5: FREE users 7-day retention
    - 6.6: Paid users 90-day retention
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_history(
        self,
        user_id: str,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[GenerationRecord], int]:
        """Get paginated history records for a user.
        
        Requirements: 6.1 - Paginated list sorted by created_at descending
        
        Args:
            user_id: The user's ID
            page: Page number (1-indexed)
            page_size: Number of records per page
            
        Returns:
            Tuple of (records list, total count)
        """
        if page < 1:
            page = 1
        if page_size < 1:
            page_size = 20
        if page_size > 100:
            page_size = 100

        offset = (page - 1) * page_size

        # Get total count
        count_query = select(func.count(GenerationRecord.id)).where(
            GenerationRecord.user_id == user_id
        )
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # Get paginated records sorted by created_at descending
        records_query = (
            select(GenerationRecord)
            .where(GenerationRecord.user_id == user_id)
            .order_by(GenerationRecord.created_at.desc())
            .offset(offset)
            .limit(page_size)
            .options(selectinload(GenerationRecord.images))
        )
        result = await self.db.execute(records_query)
        records = list(result.scalars().all())

        return records, total

    async def get_record_detail(
        self,
        record_id: str,
        user_id: str,
    ) -> Optional[GenerationRecord]:
        """Get a specific history record with full details.
        
        Requirements: 6.3 - Record detail retrieval
        
        Args:
            record_id: The record's ID
            user_id: The user's ID (for authorization)
            
        Returns:
            The record if found and owned by user, None otherwise
        """
        query = (
            select(GenerationRecord)
            .where(
                GenerationRecord.id == record_id,
                GenerationRecord.user_id == user_id,
            )
            .options(selectinload(GenerationRecord.images))
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def delete_record(
        self,
        record_id: str,
        user_id: str,
    ) -> bool:
        """Delete a history record and its associated images.
        
        Requirements: 6.4 - Record deletion
        
        Args:
            record_id: The record's ID
            user_id: The user's ID (for authorization)
            
        Returns:
            True if deleted, False if not found or not owned by user
        """
        # First verify the record exists and belongs to the user
        record = await self.get_record_detail(record_id, user_id)
        if record is None:
            return False

        # Delete associated images first (cascade should handle this, but be explicit)
        await self.db.execute(
            delete(GeneratedImageRecord).where(
                GeneratedImageRecord.generation_id == record_id
            )
        )

        # Delete the record
        await self.db.execute(
            delete(GenerationRecord).where(
                GenerationRecord.id == record_id,
                GenerationRecord.user_id == user_id,
            )
        )

        await self.db.commit()
        logger.info(f"Deleted history record {record_id} for user {user_id}")
        return True

    async def create_record(
        self,
        user_id: str,
        generation_type: GenerationType,
        input_params: dict,
        output_urls: list[str],
        processing_time_ms: int,
        has_watermark: bool,
    ) -> GenerationRecord:
        """Create a new generation history record.
        
        Args:
            user_id: The user's ID
            generation_type: Type of generation (poster/scene_fusion)
            input_params: Input parameters used for generation
            output_urls: URLs of generated images
            processing_time_ms: Processing time in milliseconds
            has_watermark: Whether images have watermark
            
        Returns:
            The created record
        """
        record = GenerationRecord(
            id=str(uuid4()),
            user_id=user_id,
            type=generation_type,
            input_params=input_params,
            output_urls=output_urls,
            processing_time_ms=processing_time_ms,
            has_watermark=has_watermark,
        )
        self.db.add(record)
        await self.db.commit()
        await self.db.refresh(record)
        
        logger.info(f"Created history record {record.id} for user {user_id}")
        return record

    async def cleanup_expired_records(self) -> int:
        """Clean up expired history records based on user membership tier.
        
        Requirements:
        - 6.5: FREE users 7-day retention
        - 6.6: Paid users 90-day retention
        
        Returns:
            Number of records deleted
        """
        now = datetime.utcnow()
        free_cutoff = now - timedelta(days=FREE_RETENTION_DAYS)
        paid_cutoff = now - timedelta(days=PAID_RETENTION_DAYS)

        deleted_count = 0

        # Get all users with their membership tiers
        users_query = select(User.id, User.membership_tier)
        users_result = await self.db.execute(users_query)
        users = users_result.all()

        for user_id, membership_tier in users:
            # Determine cutoff date based on membership tier
            if membership_tier == MembershipTier.FREE:
                cutoff_date = free_cutoff
            else:
                # BASIC and PROFESSIONAL get 90 days
                cutoff_date = paid_cutoff

            # Find expired records for this user
            expired_query = select(GenerationRecord.id).where(
                GenerationRecord.user_id == user_id,
                GenerationRecord.created_at < cutoff_date,
            )
            expired_result = await self.db.execute(expired_query)
            expired_ids = [row[0] for row in expired_result.all()]

            if expired_ids:
                # Delete associated images
                await self.db.execute(
                    delete(GeneratedImageRecord).where(
                        GeneratedImageRecord.generation_id.in_(expired_ids)
                    )
                )

                # Delete the records
                result = await self.db.execute(
                    delete(GenerationRecord).where(
                        GenerationRecord.id.in_(expired_ids)
                    )
                )
                deleted_count += len(expired_ids)

        await self.db.commit()
        logger.info(f"Cleaned up {deleted_count} expired history records")
        return deleted_count

    def get_retention_days(self, membership_tier: MembershipTier) -> int:
        """Get the retention period in days for a membership tier.
        
        Args:
            membership_tier: The user's membership tier
            
        Returns:
            Number of days records are retained
        """
        if membership_tier == MembershipTier.FREE:
            return FREE_RETENTION_DAYS
        return PAID_RETENTION_DAYS

    def is_record_expired(
        self,
        record_created_at: datetime,
        membership_tier: MembershipTier,
    ) -> bool:
        """Check if a record is expired based on membership tier.
        
        Args:
            record_created_at: When the record was created
            membership_tier: The user's membership tier
            
        Returns:
            True if the record is expired, False otherwise
        """
        retention_days = self.get_retention_days(membership_tier)
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
        return record_created_at < cutoff_date
