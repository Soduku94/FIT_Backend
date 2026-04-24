"""change role to enum

Revision ID: dbe1078ceedd
Revises: bf15c4aef982
Create Date: 2026-04-20 15:21:15.039401

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'dbe1078ceedd'
down_revision = 'bf15c4aef982'
branch_labels = None
depends_on = None


# Định nghĩa Enum
enum_name = 'userrole'
role_options = ('student', 'lecturer', 'admin', 'editor')

def upgrade():
    # 1. DỌN DẸP DỮ LIỆU CŨ: Đổi tất cả 'teacher' thành 'lecturer' để khớp với Enum
    op.execute("UPDATE users SET role = 'lecturer' WHERE role = 'teacher'")

    # 2. Tạo kiểu dữ liệu ENUM trong Postgres
    user_role_enum = postgresql.ENUM(*role_options, name=enum_name)
    user_role_enum.create(op.get_bind())

    # 3. Đổi kiểu cột 'role' và ÉP KIỂU (cast) dữ liệu cũ sang Enum
    op.alter_column('users', 'role',
               existing_type=sa.VARCHAR(length=20),
               type_=user_role_enum,
               existing_nullable=False,
               postgresql_using=f'role::{enum_name}')

def downgrade():
    # Khi rollback, trả cột role về lại kiểu VARCHAR(20)
    op.alter_column('users', 'role',
               existing_type=postgresql.ENUM(*role_options, name=enum_name),
               type_=sa.VARCHAR(length=20),
               existing_nullable=False)

    # Xóa kiểu ENUM khỏi Postgres
    user_role_enum = postgresql.ENUM(*role_options, name=enum_name)
    user_role_enum.drop(op.get_bind())
