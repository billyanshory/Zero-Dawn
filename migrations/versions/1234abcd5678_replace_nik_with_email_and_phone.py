"""replace_nik_with_email_and_phone

Revision ID: 1234abcd5678
Revises:
Create Date: 2024-05-24 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.orm import Session
import hashlib
import os

# revision identifiers, used by Alembic.
revision = '1234abcd5678'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # 1. Add new columns as nullable
    op.add_column('akun_pengguna', sa.Column('email', sa.String(length=255), nullable=True))
    op.add_column('akun_pengguna', sa.Column('email_hash', sa.String(length=64), nullable=True))
    op.add_column('akun_pengguna', sa.Column('nomor_hp', sa.String(length=255), nullable=True))
    op.add_column('akun_pengguna', sa.Column('nomor_hp_hash', sa.String(length=64), nullable=True))

    # 2. Data migration
    # Instead of running the encryption in alembic, we will run python code that imports the app
    import sys
    import importlib.util

    # Load the app module dynamically to get the keys and engine
    spec = importlib.util.spec_from_file_location("app_module", "sekolah-luar-biasa-91 ( idcloudhost - Nineteenth Layer of Quality Control - Data Privacy & Compliance (SLB-Specific) - v.90 - Opus 4.7 Ad. Think - Second Effort ).py")
    app_module = importlib.util.module_from_spec(spec)
    sys.modules["app_module"] = app_module
    spec.loader.exec_module(app_module)

    bind = op.get_bind()
    session = Session(bind=bind)

    from sqlalchemy_utils.types.encrypted.encrypted_type import AesGcmEngine

    result = bind.execute(sa.text("SELECT id FROM akun_pengguna"))

    for row in result:
        user_id = row[0]

        email_plain = f"legacy_user_{user_id}@slb-samarinda.local"
        hp_plain = f"0800000000{user_id:04d}"

        email_hash = hashlib.sha256(email_plain.encode('utf-8')).hexdigest()
        nomor_hp_hash = hashlib.sha256(hp_plain.encode('utf-8')).hexdigest()

        engine = AesGcmEngine()
        engine._initialize_engine(app_module._PRIMARY_FIELD_KEY)
        email_enc = engine.encrypt(email_plain)
        hp_enc = engine.encrypt(hp_plain)

        bind.execute(
            sa.text("""
                UPDATE akun_pengguna
                SET email = :email_enc, email_hash = :email_hash, nomor_hp = :hp_enc, nomor_hp_hash = :hp_hash
                WHERE id = :id
            """),
            {"email_enc": email_enc, "email_hash": email_hash, "hp_enc": hp_enc, "hp_hash": nomor_hp_hash, "id": user_id}
        )

    # 3. Create indexes
    op.create_index(op.f('ix_akun_pengguna_email_hash'), 'akun_pengguna', ['email_hash'], unique=True)
    op.create_index(op.f('ix_akun_pengguna_nomor_hp_hash'), 'akun_pengguna', ['nomor_hp_hash'], unique=True)

    # 4. Alter columns to NOT NULL
    op.alter_column('akun_pengguna', 'email', existing_type=sa.String(length=255), nullable=False)
    op.alter_column('akun_pengguna', 'email_hash', existing_type=sa.String(length=64), nullable=False)
    op.alter_column('akun_pengguna', 'nomor_hp', existing_type=sa.String(length=255), nullable=False)
    op.alter_column('akun_pengguna', 'nomor_hp_hash', existing_type=sa.String(length=64), nullable=False)

    # 5. Drop old columns
    op.drop_index('ix_akun_pengguna_nik_hash', table_name='akun_pengguna')
    op.drop_column('akun_pengguna', 'nik_hash')
    op.drop_column('akun_pengguna', 'nik')


def downgrade():
    op.add_column('akun_pengguna', sa.Column('nik', sa.String(length=255), nullable=True))
    op.add_column('akun_pengguna', sa.Column('nik_hash', sa.String(length=64), nullable=True))

    op.drop_index(op.f('ix_akun_pengguna_nomor_hp_hash'), table_name='akun_pengguna')
    op.drop_index(op.f('ix_akun_pengguna_email_hash'), table_name='akun_pengguna')
    op.drop_column('akun_pengguna', 'nomor_hp_hash')
    op.drop_column('akun_pengguna', 'nomor_hp')
    op.drop_column('akun_pengguna', 'email_hash')
    op.drop_column('akun_pengguna', 'email')
