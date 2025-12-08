"""Create all database tables

Revision ID: 001_add_auth_models
Revises: 
Create Date: 2025-12-05

Requirements: 1.1, 1.5, 2.1 - 用户认证基础设施
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001_add_auth_models'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade database schema."""
    
    # Create enum types with IF NOT EXISTS
    conn = op.get_bind()
    conn.execute(sa.text("DO $$ BEGIN CREATE TYPE membershiptier AS ENUM ('FREE', 'BASIC', 'PRO'); EXCEPTION WHEN duplicate_object THEN null; END $$;"))
    conn.execute(sa.text("DO $$ BEGIN CREATE TYPE generationtype AS ENUM ('poster', 'scene_fusion'); EXCEPTION WHEN duplicate_object THEN null; END $$;"))
    conn.execute(sa.text("DO $$ BEGIN CREATE TYPE templatecategory AS ENUM ('promotion', 'premium', 'holiday'); EXCEPTION WHEN duplicate_object THEN null; END $$;"))
    conn.execute(sa.text("DO $$ BEGIN CREATE TYPE subscriptionplan AS ENUM ('basic_monthly', 'basic_yearly', 'pro_monthly', 'pro_yearly'); EXCEPTION WHEN duplicate_object THEN null; END $$;"))
    conn.execute(sa.text("DO $$ BEGIN CREATE TYPE paymentmethod AS ENUM ('alipay', 'wechat', 'unionpay'); EXCEPTION WHEN duplicate_object THEN null; END $$;"))
    conn.execute(sa.text("DO $$ BEGIN CREATE TYPE paymentstatus AS ENUM ('pending', 'paid', 'failed', 'expired', 'refunded'); EXCEPTION WHEN duplicate_object THEN null; END $$;"))
    
    # Create users table (if not exists)
    op.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id VARCHAR(36) PRIMARY KEY,
            phone VARCHAR(20),
            email VARCHAR(255),
            password_hash VARCHAR(255),
            membership_tier membershiptier NOT NULL DEFAULT 'FREE',
            membership_expiry TIMESTAMP,
            daily_usage_count INTEGER NOT NULL DEFAULT 0,
            last_usage_date DATE NOT NULL DEFAULT CURRENT_DATE,
            created_at TIMESTAMP NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP NOT NULL DEFAULT NOW()
        )
    """)
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_phone ON users (phone)")
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_email ON users (email)")
    
    # Create generation_records table
    op.execute("""
        CREATE TABLE IF NOT EXISTS generation_records (
            id VARCHAR(36) PRIMARY KEY,
            user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            type generationtype NOT NULL,
            input_params JSON NOT NULL,
            output_urls JSON NOT NULL,
            processing_time_ms INTEGER NOT NULL,
            has_watermark BOOLEAN NOT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT NOW()
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_generation_records_user_id ON generation_records (user_id)")
    
    # Create generated_images table
    op.execute("""
        CREATE TABLE IF NOT EXISTS generated_images (
            id VARCHAR(36) PRIMARY KEY,
            generation_id VARCHAR(36) NOT NULL REFERENCES generation_records(id) ON DELETE CASCADE,
            image_data BYTEA NOT NULL,
            width INTEGER NOT NULL,
            height INTEGER NOT NULL,
            has_watermark BOOLEAN NOT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT NOW()
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_generated_images_generation_id ON generated_images (generation_id)")
    
    # Create templates table
    op.execute("""
        CREATE TABLE IF NOT EXISTS templates (
            id VARCHAR(36) PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            category templatecategory NOT NULL,
            holiday_type VARCHAR(50),
            prompt_modifiers JSON NOT NULL,
            preview_url VARCHAR(500) NOT NULL,
            is_active BOOLEAN NOT NULL DEFAULT true,
            created_at TIMESTAMP NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP NOT NULL DEFAULT NOW()
        )
    """)
    
    # Create refresh_tokens table
    op.execute("""
        CREATE TABLE IF NOT EXISTS refresh_tokens (
            id VARCHAR(36) PRIMARY KEY,
            user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            token_hash VARCHAR(255) NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT NOW(),
            is_revoked BOOLEAN NOT NULL DEFAULT false
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_refresh_tokens_user_id ON refresh_tokens (user_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_refresh_tokens_token_hash ON refresh_tokens (token_hash)")
    
    # Create verification_codes table
    op.execute("""
        CREATE TABLE IF NOT EXISTS verification_codes (
            id VARCHAR(36) PRIMARY KEY,
            phone VARCHAR(20) NOT NULL,
            code VARCHAR(6) NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT NOW(),
            is_used BOOLEAN NOT NULL DEFAULT false
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_verification_codes_phone ON verification_codes (phone)")
    
    # Create payment_orders table
    op.execute("""
        CREATE TABLE IF NOT EXISTS payment_orders (
            id VARCHAR(36) PRIMARY KEY,
            user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            plan subscriptionplan NOT NULL,
            method paymentmethod NOT NULL,
            amount INTEGER NOT NULL,
            status paymentstatus NOT NULL DEFAULT 'pending',
            external_order_id VARCHAR(100),
            paid_at TIMESTAMP,
            created_at TIMESTAMP NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP NOT NULL DEFAULT NOW()
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_payment_orders_user_id ON payment_orders (user_id)")
    
    return  # Skip the old create_table calls below
    
    # OLD CODE - kept for reference but skipped
    op.create_table(
        'users',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('phone', sa.String(20), nullable=True),
        sa.Column('email', sa.String(255), nullable=True),
        sa.Column('password_hash', sa.String(255), nullable=True),
        sa.Column('membership_tier', sa.Enum('FREE', 'BASIC', 'PRO', name='membershiptier'), nullable=False, server_default='FREE'),
        sa.Column('membership_expiry', sa.DateTime, nullable=True),
        sa.Column('daily_usage_count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('last_usage_date', sa.Date, nullable=False, server_default=sa.func.current_date()),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_users_phone', 'users', ['phone'], unique=True)
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    
    # Create generation_records table
    op.create_table(
        'generation_records',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('type', sa.Enum('poster', 'scene_fusion', name='generationtype'), nullable=False),
        sa.Column('input_params', sa.JSON, nullable=False),
        sa.Column('output_urls', sa.JSON, nullable=False),
        sa.Column('processing_time_ms', sa.Integer, nullable=False),
        sa.Column('has_watermark', sa.Boolean, nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_generation_records_user_id', 'generation_records', ['user_id'])
    
    # Create generated_images table
    op.create_table(
        'generated_images',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('generation_id', sa.String(36), sa.ForeignKey('generation_records.id', ondelete='CASCADE'), nullable=False),
        sa.Column('image_data', sa.LargeBinary, nullable=False),
        sa.Column('width', sa.Integer, nullable=False),
        sa.Column('height', sa.Integer, nullable=False),
        sa.Column('has_watermark', sa.Boolean, nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_generated_images_generation_id', 'generated_images', ['generation_id'])
    
    # Create templates table
    op.create_table(
        'templates',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('category', sa.Enum('promotion', 'premium', 'holiday', name='templatecategory'), nullable=False),
        sa.Column('holiday_type', sa.String(50), nullable=True),
        sa.Column('prompt_modifiers', sa.JSON, nullable=False),
        sa.Column('preview_url', sa.String(500), nullable=False),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    
    # Create refresh_tokens table
    op.create_table(
        'refresh_tokens',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('token_hash', sa.String(255), nullable=False),
        sa.Column('expires_at', sa.DateTime, nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('is_revoked', sa.Boolean, nullable=False, server_default='false'),
    )
    op.create_index('ix_refresh_tokens_user_id', 'refresh_tokens', ['user_id'])
    op.create_index('ix_refresh_tokens_token_hash', 'refresh_tokens', ['token_hash'])
    
    # Create verification_codes table
    op.create_table(
        'verification_codes',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('phone', sa.String(20), nullable=False),
        sa.Column('code', sa.String(6), nullable=False),
        sa.Column('expires_at', sa.DateTime, nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('is_used', sa.Boolean, nullable=False, server_default='false'),
    )
    op.create_index('ix_verification_codes_phone', 'verification_codes', ['phone'])
    
    # Create payment_orders table
    op.create_table(
        'payment_orders',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('plan', sa.Enum('basic_monthly', 'basic_yearly', 'pro_monthly', 'pro_yearly', name='subscriptionplan'), nullable=False),
        sa.Column('method', sa.Enum('alipay', 'wechat', 'unionpay', name='paymentmethod'), nullable=False),
        sa.Column('amount', sa.Integer, nullable=False),
        sa.Column('status', sa.Enum('pending', 'paid', 'failed', 'expired', 'refunded', name='paymentstatus'), nullable=False, server_default='pending'),
        sa.Column('external_order_id', sa.String(100), nullable=True),
        sa.Column('paid_at', sa.DateTime, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_payment_orders_user_id', 'payment_orders', ['user_id'])


def downgrade() -> None:
    """Downgrade database schema."""
    op.drop_index('ix_payment_orders_user_id', table_name='payment_orders')
    op.drop_table('payment_orders')
    
    op.drop_index('ix_verification_codes_phone', table_name='verification_codes')
    op.drop_table('verification_codes')
    
    op.drop_index('ix_refresh_tokens_token_hash', table_name='refresh_tokens')
    op.drop_index('ix_refresh_tokens_user_id', table_name='refresh_tokens')
    op.drop_table('refresh_tokens')
    
    op.drop_table('templates')
    
    op.drop_index('ix_generated_images_generation_id', table_name='generated_images')
    op.drop_table('generated_images')
    
    op.drop_index('ix_generation_records_user_id', table_name='generation_records')
    op.drop_table('generation_records')
    
    op.drop_index('ix_users_email', table_name='users')
    op.drop_index('ix_users_phone', table_name='users')
    op.drop_table('users')
    
    # Drop enums
    op.execute('DROP TYPE IF EXISTS membershiptier')
    op.execute('DROP TYPE IF EXISTS generationtype')
    op.execute('DROP TYPE IF EXISTS templatecategory')
    op.execute('DROP TYPE IF EXISTS subscriptionplan')
    op.execute('DROP TYPE IF EXISTS paymentmethod')
    op.execute('DROP TYPE IF EXISTS paymentstatus')
