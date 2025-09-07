"""initial migration

Revision ID: initial_migration
Revises: 
Create Date: 2023-09-05 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic
revision = 'initial_migration'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Create platforms table
    op.create_table('platforms',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )

    # Create securities table
    op.create_table('securities',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('symbol', sa.String(length=20), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('security_type', sa.String(length=20), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('symbol')
    )

    # Create transactions table
    op.create_table('transactions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('security_id', sa.Integer(), nullable=False),
        sa.Column('platform_id', sa.Integer(), nullable=False),
        sa.Column('transaction_type', sa.String(length=20), nullable=False),
        sa.Column('quantity', sa.Float(), nullable=False),
        sa.Column('price', sa.Float(), nullable=False),
        sa.Column('date', sa.DateTime(), nullable=False),
        sa.Column('fees', sa.Float(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['platform_id'], ['platforms.id'], ),
        sa.ForeignKeyConstraint(['security_id'], ['securities.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade():
    op.drop_table('transactions')
    op.drop_table('securities')
    op.drop_table('platforms')
```

4. Run the migration:

```bash
flask db migrate -m "initial migration"
flask db upgrade
```

5. Verify the migration status:

```bash
flask db current
```

The migrations folder structure should look like this:

```
backend/
└── migrations/
    ├── README
    ├── alembic.ini
    ├── env.py
    ├── script.py.mako
    └── versions/
        └── initial_migration.py
```

If you encounter any errors, check that:
1. Your database URL in `.env` is correct
2. PostgreSQL is running
3. The database exists and is accessible
4. You have the required permissions

To troubleshoot database connection:

```bash
psql -U username -d investment_tracker
```// filepath: /home/pi/investment-tracker/backend/migrations/versions/initial_migration.py
"""initial migration

Revision ID: initial_migration
Revises: 
Create Date: 2023-09-05 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic
revision = 'initial_migration'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Create platforms table
    op.create_table('platforms',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )

    # Create securities table
    op.create_table('securities',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('symbol', sa.String(length=20), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('security_type', sa.String(length=20), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('symbol')
    )

    # Create transactions table
    op.create_table('transactions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('security_id', sa.Integer(), nullable=False),
        sa.Column('platform_id', sa.Integer(), nullable=False),
        sa.Column('transaction_type', sa.String(length=20), nullable=False),
        sa.Column('quantity', sa.Float(), nullable=False),
        sa.Column('price', sa.Float(), nullable=False),
        sa.Column('date', sa.DateTime(), nullable=False),
        sa.Column('fees', sa.Float(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['platform_id'], ['platforms.id'], ),
        sa.ForeignKeyConstraint(['security_id'], ['securities.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade():
    op.drop_table('transactions')
    op.drop_table('securities')
    op.drop_table('platforms')
```

4. Run the migration:

```bash
flask db migrate -m "initial migration"
flask db upgrade
```

5. Verify the migration status:

```bash
flask db current
```

The migrations folder structure should look like this:

```
backend/
└── migrations/
    ├── README
    ├── alembic.ini
    ├── env.py
    ├── script.py.mako
    └── versions/
        └── initial_migration.py
```

If you encounter any errors, check that:
1. Your database URL in `.env` is correct
2. PostgreSQL is running
3. The database exists and is accessible
4. You have the required permissions

To troubleshoot database connection:

```bash
psql -U