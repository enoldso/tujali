"""Initial migration with SQLite support

Revision ID: initial_sqlite
Revises: 
Create Date: 2025-06-08 13:08:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey

# revision identifiers, used by Alembic.
revision = 'initial_sqlite'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Create health_info_articles table
    op.create_table('health_info_articles',
        Column('id', Integer, primary_key=True),
        Column('title', String(200), nullable=False),
        Column('content', Text, nullable=False),
        Column('category', String(50), nullable=True),
        Column('language', String(20), nullable=True),
        Column('is_published', Boolean, nullable=True, default=False),
        Column('created_at', DateTime, nullable=True),
        Column('updated_at', DateTime, nullable=True)
    )
    
    # Create patients table
    op.create_table('patients',
        Column('id', Integer, primary_key=True),
        Column('phone_number', String(20), unique=True, nullable=False),
        Column('name', String(100), nullable=False),
        Column('age', Integer, nullable=True),
        Column('gender', String(20), nullable=True),
        Column('location', String(200), nullable=True),
        Column('coordinates', Text, nullable=True),  # Store as JSON string
        Column('language', String(10), nullable=True),
        Column('created_at', DateTime, nullable=True)
    )
    
    # Create users table
    op.create_table('users',
        Column('id', Integer, primary_key=True),
        Column('username', String(80), unique=True, nullable=False),
        Column('email', String(120), unique=True, nullable=True),
        Column('password_hash', String(128), nullable=True),
        Column('is_admin', Boolean, default=False, nullable=False),
        Column('created_at', DateTime, nullable=True)
    )
    
    # Create other tables with similar structure
    op.create_table('pharmacies',
        Column('id', Integer, primary_key=True),
        Column('name', String(100), nullable=False),
        Column('address', String(200), nullable=True),
        Column('city', String(100), nullable=True),
        Column('state', String(100), nullable=True),
        Column('phone', String(20), nullable=True),
        Column('location', String(200), nullable=True),
        Column('created_at', DateTime, nullable=True)
    )
    
    # Add more tables as needed...
    
    # Create indexes for better performance
    op.create_index(op.f('ix_patients_phone_number'), 'patients', ['phone_number'], unique=True)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

def downgrade():
    # Drop tables in reverse order of creation
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_index(op.f('ix_patients_phone_number'), table_name='patients')
    
    op.drop_table('pharmacies')
    op.drop_table('users')
    op.drop_table('patients')
    op.drop_table('health_info_articles')
