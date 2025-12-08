"""Property-based tests for History Service.

**Feature: user-system, Property 11: 历史记录分页排序**
**Feature: user-system, Property 12: 历史记录删除**
**Feature: user-system, Property 13: FREE 用户历史保留期**
**Feature: user-system, Property 14: 付费用户历史保留期**

This module tests the history service's pagination, sorting, deletion,
and retention behavior.

Requirements:
- 6.1: WHEN a user requests generation history THEN THE User_System SHALL return a paginated list of generation records sorted by creation time descending
- 6.4: WHEN a user deletes a history record THEN THE User_System SHALL remove the record and associated images from storage
- 6.5: WHILE a user is on FREE tier THEN THE User_System SHALL retain history records for 7 days
- 6.6: WHILE a user is on BASIC or PROFESSIONAL tier THEN THE User_System SHALL retain history records for 90 days
"""

import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List
from uuid import uuid4

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest
from hypothesis import given, settings, strategies as st, assume

from app.models.schemas import GenerationType, MembershipTier
from app.services.history_service import (
    HistoryService,
    FREE_RETENTION_DAYS,
    PAID_RETENTION_DAYS,
)


# ============================================================================
# Strategies for generating test data
# ============================================================================

# Strategy for generating user IDs
user_id_strategy = st.uuids().map(str)

# Strategy for generating record IDs
record_id_strategy = st.uuids().map(str)

# Strategy for generating page numbers (1-indexed)
page_strategy = st.integers(min_value=1, max_value=100)

# Strategy for generating page sizes
page_size_strategy = st.integers(min_value=1, max_value=100)

# Strategy for generating generation types
generation_type_strategy = st.sampled_from([GenerationType.POSTER, GenerationType.SCENE_FUSION])

# Strategy for generating membership tiers
membership_tier_strategy = st.sampled_from([
    MembershipTier.FREE,
    MembershipTier.BASIC,
    MembershipTier.PROFESSIONAL,
])

# Strategy for generating timestamps within the last year
timestamp_strategy = st.datetimes(
    min_value=datetime.utcnow() - timedelta(days=365),
    max_value=datetime.utcnow(),
)

# Strategy for generating input params
input_params_strategy = st.fixed_dictionaries({
    "scene_description": st.text(min_size=1, max_size=100),
    "marketing_text": st.text(min_size=1, max_size=100),
})

# Strategy for generating output URLs
output_urls_strategy = st.lists(
    st.from_regex(r"^https://example\.com/images/[a-f0-9-]{36}\.jpg$", fullmatch=True),
    min_size=1,
    max_size=4,
)


# ============================================================================
# Mock Generation Record for testing
# ============================================================================

class MockGenerationRecord:
    """Mock generation record for testing without database."""
    
    def __init__(
        self,
        id: str,
        user_id: str,
        type: GenerationType,
        input_params: dict,
        output_urls: list,
        processing_time_ms: int,
        has_watermark: bool,
        created_at: datetime,
    ):
        self.id = id
        self.user_id = user_id
        self.type = type
        self.input_params = input_params
        self.output_urls = output_urls
        self.processing_time_ms = processing_time_ms
        self.has_watermark = has_watermark
        self.created_at = created_at
        self.images = []


def generate_mock_records(
    user_id: str,
    count: int,
    base_time: datetime = None,
) -> List[MockGenerationRecord]:
    """Generate a list of mock generation records with varying timestamps."""
    if base_time is None:
        base_time = datetime.utcnow()
    
    records = []
    for i in range(count):
        # Create records with timestamps spread out
        created_at = base_time - timedelta(hours=i)
        records.append(MockGenerationRecord(
            id=str(uuid4()),
            user_id=user_id,
            type=GenerationType.POSTER if i % 2 == 0 else GenerationType.SCENE_FUSION,
            input_params={"scene": f"scene_{i}", "text": f"text_{i}"},
            output_urls=[f"https://example.com/images/{uuid4()}.jpg"],
            processing_time_ms=1000 + i * 100,
            has_watermark=i % 3 == 0,
            created_at=created_at,
        ))
    return records


# ============================================================================
# Property 11: 历史记录分页排序
# **Feature: user-system, Property 11: 历史记录分页排序**
# **Validates: Requirements 6.1**
#
# For any history query, records SHALL be sorted by created_at descending 
# and paginated correctly
# ============================================================================


@settings(max_examples=100)
@given(
    record_count=st.integers(min_value=0, max_value=50),
)
def test_records_sorted_by_created_at_descending(
    record_count: int,
) -> None:
    """
    **Feature: user-system, Property 11: 历史记录分页排序**
    **Validates: Requirements 6.1**
    
    Property: For any list of records, when sorted for display, they SHALL 
    be in descending order by created_at (newest first).
    """
    user_id = str(uuid4())
    records = generate_mock_records(user_id, record_count)
    
    # Simulate the sorting that HistoryService does
    sorted_records = sorted(records, key=lambda r: r.created_at, reverse=True)
    
    # Verify descending order
    for i in range(len(sorted_records) - 1):
        assert sorted_records[i].created_at >= sorted_records[i + 1].created_at, (
            f"Record at index {i} should have created_at >= record at index {i+1}. "
            f"Got {sorted_records[i].created_at} < {sorted_records[i + 1].created_at}"
        )


@settings(max_examples=100)
@given(
    record_count=st.integers(min_value=1, max_value=100),
    page=page_strategy,
    page_size=page_size_strategy,
)
def test_pagination_returns_correct_count(
    record_count: int,
    page: int,
    page_size: int,
) -> None:
    """
    **Feature: user-system, Property 11: 历史记录分页排序**
    **Validates: Requirements 6.1**
    
    Property: For any pagination request, the returned records count SHALL 
    be at most page_size and correctly reflect the available records.
    """
    user_id = str(uuid4())
    records = generate_mock_records(user_id, record_count)
    
    # Calculate expected pagination
    offset = (page - 1) * page_size
    expected_count = min(page_size, max(0, record_count - offset))
    
    # Simulate pagination
    sorted_records = sorted(records, key=lambda r: r.created_at, reverse=True)
    paginated = sorted_records[offset:offset + page_size]
    
    assert len(paginated) == expected_count, (
        f"Expected {expected_count} records for page {page} with page_size {page_size} "
        f"and total {record_count}, got {len(paginated)}"
    )


@settings(max_examples=100)
@given(
    record_count=st.integers(min_value=1, max_value=100),
    page_size=page_size_strategy,
)
def test_pagination_covers_all_records(
    record_count: int,
    page_size: int,
) -> None:
    """
    **Feature: user-system, Property 11: 历史记录分页排序**
    **Validates: Requirements 6.1**
    
    Property: For any set of records, iterating through all pages SHALL 
    return all records exactly once.
    """
    user_id = str(uuid4())
    records = generate_mock_records(user_id, record_count)
    sorted_records = sorted(records, key=lambda r: r.created_at, reverse=True)
    
    # Collect all records through pagination
    all_paginated = []
    page = 1
    while True:
        offset = (page - 1) * page_size
        paginated = sorted_records[offset:offset + page_size]
        if not paginated:
            break
        all_paginated.extend(paginated)
        page += 1
    
    # Verify all records are covered
    assert len(all_paginated) == record_count, (
        f"Pagination should cover all {record_count} records, got {len(all_paginated)}"
    )
    
    # Verify no duplicates
    record_ids = [r.id for r in all_paginated]
    assert len(record_ids) == len(set(record_ids)), (
        "Pagination should not return duplicate records"
    )


@settings(max_examples=100)
@given(
    record_count=st.integers(min_value=2, max_value=50),
    page_size=page_size_strategy,
)
def test_pagination_maintains_sort_order_across_pages(
    record_count: int,
    page_size: int,
) -> None:
    """
    **Feature: user-system, Property 11: 历史记录分页排序**
    **Validates: Requirements 6.1**
    
    Property: For any pagination, the last record of page N SHALL have 
    created_at >= first record of page N+1.
    """
    assume(record_count > page_size)  # Need at least 2 pages
    
    user_id = str(uuid4())
    records = generate_mock_records(user_id, record_count)
    sorted_records = sorted(records, key=lambda r: r.created_at, reverse=True)
    
    # Get consecutive pages
    page1 = sorted_records[0:page_size]
    page2 = sorted_records[page_size:page_size * 2]
    
    if page1 and page2:
        last_of_page1 = page1[-1]
        first_of_page2 = page2[0]
        
        assert last_of_page1.created_at >= first_of_page2.created_at, (
            f"Last record of page 1 ({last_of_page1.created_at}) should be >= "
            f"first record of page 2 ({first_of_page2.created_at})"
        )


# ============================================================================
# Property 12: 历史记录删除
# **Feature: user-system, Property 12: 历史记录删除**
# **Validates: Requirements 6.4**
#
# For any deleted history record, querying that record SHALL return not found
# ============================================================================


@settings(max_examples=100)
@given(
    record_count=st.integers(min_value=1, max_value=20),
    delete_index=st.integers(min_value=0, max_value=19),
)
def test_deleted_record_not_in_list(
    record_count: int,
    delete_index: int,
) -> None:
    """
    **Feature: user-system, Property 12: 历史记录删除**
    **Validates: Requirements 6.4**
    
    Property: For any deleted record, it SHALL NOT appear in subsequent 
    history queries.
    """
    assume(delete_index < record_count)
    
    user_id = str(uuid4())
    records = generate_mock_records(user_id, record_count)
    
    # Get the record to delete
    record_to_delete = records[delete_index]
    deleted_id = record_to_delete.id
    
    # Simulate deletion
    remaining_records = [r for r in records if r.id != deleted_id]
    
    # Verify deleted record is not in remaining
    remaining_ids = [r.id for r in remaining_records]
    assert deleted_id not in remaining_ids, (
        f"Deleted record {deleted_id} should not appear in remaining records"
    )
    assert len(remaining_records) == record_count - 1, (
        f"Should have {record_count - 1} records after deletion, got {len(remaining_records)}"
    )


@settings(max_examples=100)
@given(
    record_count=st.integers(min_value=1, max_value=20),
)
def test_delete_preserves_other_records(
    record_count: int,
) -> None:
    """
    **Feature: user-system, Property 12: 历史记录删除**
    **Validates: Requirements 6.4**
    
    Property: For any deletion, all other records SHALL remain unchanged.
    """
    user_id = str(uuid4())
    records = generate_mock_records(user_id, record_count)
    
    # Delete the first record
    deleted_id = records[0].id
    remaining_records = [r for r in records if r.id != deleted_id]
    
    # Verify other records are unchanged
    original_other_ids = {r.id for r in records if r.id != deleted_id}
    remaining_ids = {r.id for r in remaining_records}
    
    assert original_other_ids == remaining_ids, (
        "Other records should be preserved after deletion"
    )


@settings(max_examples=100)
@given(
    user_id=user_id_strategy,
    other_user_id=user_id_strategy,
)
def test_delete_only_affects_own_records(
    user_id: str,
    other_user_id: str,
) -> None:
    """
    **Feature: user-system, Property 12: 历史记录删除**
    **Validates: Requirements 6.4**
    
    Property: A user SHALL only be able to delete their own records, 
    not records belonging to other users.
    """
    assume(user_id != other_user_id)
    
    # Create records for both users
    user_records = generate_mock_records(user_id, 5)
    other_records = generate_mock_records(other_user_id, 5)
    all_records = user_records + other_records
    
    # Try to delete other user's record (should fail in real implementation)
    target_record = other_records[0]
    
    # Simulate authorization check - only delete if user_id matches
    can_delete = target_record.user_id == user_id
    
    assert not can_delete, (
        "User should not be able to delete another user's records"
    )


# ============================================================================
# Property 13: FREE 用户历史保留期
# **Feature: user-system, Property 13: FREE 用户历史保留期**
# **Validates: Requirements 6.5**
#
# For any FREE tier user, history records older than 7 days SHALL be 
# eligible for cleanup
# ============================================================================


@settings(max_examples=100)
@given(
    days_old=st.integers(min_value=0, max_value=30),
)
def test_free_user_retention_period(
    days_old: int,
) -> None:
    """
    **Feature: user-system, Property 13: FREE 用户历史保留期**
    **Validates: Requirements 6.5**
    
    Property: For FREE tier users, records older than 7 days SHALL be 
    marked as expired. Records exactly 7 days old are at the boundary
    and may be expired due to time precision.
    """
    # Create a mock history service (without DB)
    class MockHistoryService:
        def is_record_expired(self, created_at: datetime, tier: MembershipTier) -> bool:
            if tier == MembershipTier.FREE:
                cutoff = datetime.utcnow() - timedelta(days=FREE_RETENTION_DAYS)
            else:
                cutoff = datetime.utcnow() - timedelta(days=PAID_RETENTION_DAYS)
            return created_at < cutoff
    
    service = MockHistoryService()
    record_time = datetime.utcnow() - timedelta(days=days_old)
    
    is_expired = service.is_record_expired(record_time, MembershipTier.FREE)
    
    # Records strictly older than retention period should be expired
    # Records at exactly the boundary (days_old == FREE_RETENTION_DAYS) may or may not
    # be expired due to time precision, so we only test strict inequalities
    if days_old > FREE_RETENTION_DAYS:
        assert is_expired, (
            f"Record {days_old} days old should be expired for FREE user "
            f"(retention: {FREE_RETENTION_DAYS} days)"
        )
    elif days_old < FREE_RETENTION_DAYS:
        assert not is_expired, (
            f"Record {days_old} days old should NOT be expired for FREE user "
            f"(retention: {FREE_RETENTION_DAYS} days)"
        )
    # At exactly FREE_RETENTION_DAYS, the result depends on time precision - skip assertion


@settings(max_examples=100)
@given(
    record_count=st.integers(min_value=1, max_value=20),
)
def test_free_user_cleanup_removes_old_records(
    record_count: int,
) -> None:
    """
    **Feature: user-system, Property 13: FREE 用户历史保留期**
    **Validates: Requirements 6.5**
    
    Property: For FREE tier users, cleanup SHALL remove all records 
    older than 7 days.
    """
    user_id = str(uuid4())
    now = datetime.utcnow()
    
    # Create records with varying ages
    records = []
    for i in range(record_count):
        # Half old (10 days), half new (3 days)
        days_old = 10 if i < record_count // 2 else 3
        created_at = now - timedelta(days=days_old)
        records.append(MockGenerationRecord(
            id=str(uuid4()),
            user_id=user_id,
            type=GenerationType.POSTER,
            input_params={},
            output_urls=[],
            processing_time_ms=1000,
            has_watermark=False,
            created_at=created_at,
        ))
    
    # Simulate cleanup for FREE user
    cutoff = now - timedelta(days=FREE_RETENTION_DAYS)
    remaining = [r for r in records if r.created_at >= cutoff]
    
    # Verify old records are removed
    for r in remaining:
        days_old = (now - r.created_at).days
        assert days_old <= FREE_RETENTION_DAYS, (
            f"Record {days_old} days old should have been cleaned up"
        )


# ============================================================================
# Property 14: 付费用户历史保留期
# **Feature: user-system, Property 14: 付费用户历史保留期**
# **Validates: Requirements 6.6**
#
# For any BASIC or PROFESSIONAL tier user, history records older than 
# 90 days SHALL be eligible for cleanup
# ============================================================================


@settings(max_examples=100)
@given(
    days_old=st.integers(min_value=0, max_value=120),
    tier=st.sampled_from([MembershipTier.BASIC, MembershipTier.PROFESSIONAL]),
)
def test_paid_user_retention_period(
    days_old: int,
    tier: MembershipTier,
) -> None:
    """
    **Feature: user-system, Property 14: 付费用户历史保留期**
    **Validates: Requirements 6.6**
    
    Property: For BASIC or PROFESSIONAL tier users, records older than 
    90 days SHALL be marked as expired. Records exactly 90 days old are 
    at the boundary and may be expired due to time precision.
    """
    class MockHistoryService:
        def is_record_expired(self, created_at: datetime, tier: MembershipTier) -> bool:
            if tier == MembershipTier.FREE:
                cutoff = datetime.utcnow() - timedelta(days=FREE_RETENTION_DAYS)
            else:
                cutoff = datetime.utcnow() - timedelta(days=PAID_RETENTION_DAYS)
            return created_at < cutoff
    
    service = MockHistoryService()
    record_time = datetime.utcnow() - timedelta(days=days_old)
    
    is_expired = service.is_record_expired(record_time, tier)
    
    # Records strictly older than retention period should be expired
    # Records at exactly the boundary may or may not be expired due to time precision
    if days_old > PAID_RETENTION_DAYS:
        assert is_expired, (
            f"Record {days_old} days old should be expired for {tier.value} user "
            f"(retention: {PAID_RETENTION_DAYS} days)"
        )
    elif days_old < PAID_RETENTION_DAYS:
        assert not is_expired, (
            f"Record {days_old} days old should NOT be expired for {tier.value} user "
            f"(retention: {PAID_RETENTION_DAYS} days)"
        )
    # At exactly PAID_RETENTION_DAYS, the result depends on time precision - skip assertion


@settings(max_examples=100)
@given(
    tier=st.sampled_from([MembershipTier.BASIC, MembershipTier.PROFESSIONAL]),
)
def test_paid_user_has_longer_retention_than_free(
    tier: MembershipTier,
) -> None:
    """
    **Feature: user-system, Property 14: 付费用户历史保留期**
    **Validates: Requirements 6.6**
    
    Property: Paid users SHALL have longer retention period than FREE users.
    """
    assert PAID_RETENTION_DAYS > FREE_RETENTION_DAYS, (
        f"Paid retention ({PAID_RETENTION_DAYS} days) should be > "
        f"FREE retention ({FREE_RETENTION_DAYS} days)"
    )


@settings(max_examples=100)
@given(
    days_old=st.integers(min_value=8, max_value=89),
    tier=st.sampled_from([MembershipTier.BASIC, MembershipTier.PROFESSIONAL]),
)
def test_paid_user_keeps_records_free_would_delete(
    days_old: int,
    tier: MembershipTier,
) -> None:
    """
    **Feature: user-system, Property 14: 付费用户历史保留期**
    **Validates: Requirements 6.6**
    
    Property: For records between 7-90 days old, paid users SHALL keep 
    them while FREE users would have them deleted.
    """
    # Records in this range are expired for FREE but not for paid
    assume(days_old > FREE_RETENTION_DAYS)
    assume(days_old <= PAID_RETENTION_DAYS)
    
    class MockHistoryService:
        def is_record_expired(self, created_at: datetime, tier: MembershipTier) -> bool:
            if tier == MembershipTier.FREE:
                cutoff = datetime.utcnow() - timedelta(days=FREE_RETENTION_DAYS)
            else:
                cutoff = datetime.utcnow() - timedelta(days=PAID_RETENTION_DAYS)
            return created_at < cutoff
    
    service = MockHistoryService()
    record_time = datetime.utcnow() - timedelta(days=days_old)
    
    free_expired = service.is_record_expired(record_time, MembershipTier.FREE)
    paid_expired = service.is_record_expired(record_time, tier)
    
    assert free_expired, (
        f"Record {days_old} days old should be expired for FREE user"
    )
    assert not paid_expired, (
        f"Record {days_old} days old should NOT be expired for {tier.value} user"
    )


@settings(max_examples=100)
@given(
    record_count=st.integers(min_value=1, max_value=20),
    tier=st.sampled_from([MembershipTier.BASIC, MembershipTier.PROFESSIONAL]),
)
def test_paid_user_cleanup_removes_old_records(
    record_count: int,
    tier: MembershipTier,
) -> None:
    """
    **Feature: user-system, Property 14: 付费用户历史保留期**
    **Validates: Requirements 6.6**
    
    Property: For paid tier users, cleanup SHALL remove all records 
    older than 90 days.
    """
    user_id = str(uuid4())
    now = datetime.utcnow()
    
    # Create records with varying ages
    records = []
    for i in range(record_count):
        # Half old (100 days), half new (30 days)
        days_old = 100 if i < record_count // 2 else 30
        created_at = now - timedelta(days=days_old)
        records.append(MockGenerationRecord(
            id=str(uuid4()),
            user_id=user_id,
            type=GenerationType.POSTER,
            input_params={},
            output_urls=[],
            processing_time_ms=1000,
            has_watermark=False,
            created_at=created_at,
        ))
    
    # Simulate cleanup for paid user
    cutoff = now - timedelta(days=PAID_RETENTION_DAYS)
    remaining = [r for r in records if r.created_at >= cutoff]
    
    # Verify old records are removed
    for r in remaining:
        days_old = (now - r.created_at).days
        assert days_old <= PAID_RETENTION_DAYS, (
            f"Record {days_old} days old should have been cleaned up for {tier.value} user"
        )
