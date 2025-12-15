"""Add updated_at auto-update triggers

Revision ID: 003_add_updated_at_triggers
Revises: 002_fix_enum_consistency
Create Date: 2025-12-09

Requirements: 11.2 - 添加 updated_at 自动更新触发器
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '003_add_updated_at_triggers'
down_revision: Union[str, None] = '002_fix_enum_consistency'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade database schema.
    
    创建 update_updated_at_column() 函数并为以下表添加触发器：
    - users
    - templates
    - payment_orders
    """
    conn = op.get_bind()
    
    # Step 1: 创建通用的 updated_at 更新函数
    conn.execute(sa.text("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ language 'plpgsql'
    """))
    
    # Step 2: 为 users 表添加触发器
    conn.execute(sa.text("DROP TRIGGER IF EXISTS update_users_updated_at ON users"))
    conn.execute(sa.text("""
        CREATE TRIGGER update_users_updated_at
            BEFORE UPDATE ON users
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column()
    """))
    
    # Step 3: 为 templates 表添加触发器
    conn.execute(sa.text("DROP TRIGGER IF EXISTS update_templates_updated_at ON templates"))
    conn.execute(sa.text("""
        CREATE TRIGGER update_templates_updated_at
            BEFORE UPDATE ON templates
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column()
    """))
    
    # Step 4: 为 payment_orders 表添加触发器
    conn.execute(sa.text("DROP TRIGGER IF EXISTS update_payment_orders_updated_at ON payment_orders"))
    conn.execute(sa.text("""
        CREATE TRIGGER update_payment_orders_updated_at
            BEFORE UPDATE ON payment_orders
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column()
    """))


def downgrade() -> None:
    """Downgrade database schema.
    
    删除触发器和函数
    """
    conn = op.get_bind()
    
    # 删除触发器
    conn.execute(sa.text("DROP TRIGGER IF EXISTS update_users_updated_at ON users"))
    conn.execute(sa.text("DROP TRIGGER IF EXISTS update_templates_updated_at ON templates"))
    conn.execute(sa.text("DROP TRIGGER IF EXISTS update_payment_orders_updated_at ON payment_orders"))
    
    # 删除函数
    conn.execute(sa.text("DROP FUNCTION IF EXISTS update_updated_at_column()"))
