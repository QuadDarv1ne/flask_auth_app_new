"""
Database migrations management
"""
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os


class Migration:
    """Base class for database migrations."""
    
    version = None  # Override in subclass
    description = None  # Override in subclass
    
    def __init__(self, db: SQLAlchemy):
        self.db = db
    
    def up(self):
        """Apply migration."""
        raise NotImplementedError
    
    def down(self):
        """Rollback migration."""
        raise NotImplementedError


class Migration001_InitialSchema(Migration):
    """Initial database schema."""
    
    version = '001'
    description = 'Create initial tables'
    
    def up(self):
        """Create all initial tables."""
        # Users table
        self.db.session.execute("""
            CREATE TABLE IF NOT EXISTS user (
                id SERIAL PRIMARY KEY,
                username VARCHAR(80) UNIQUE NOT NULL,
                email VARCHAR(120) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE,
                is_admin BOOLEAN DEFAULT FALSE,
                two_factor_secret VARCHAR(32),
                two_factor_enabled BOOLEAN DEFAULT FALSE
            )
        """)
        
        # Login history table
        self.db.session.execute("""
            CREATE TABLE IF NOT EXISTS login_history (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES user(id),
                ip_address VARCHAR(45),
                user_agent TEXT,
                success BOOLEAN,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # User sessions table
        self.db.session.execute("""
            CREATE TABLE IF NOT EXISTS user_session (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES user(id),
                session_token VARCHAR(255) UNIQUE NOT NULL,
                ip_address VARCHAR(45),
                user_agent TEXT,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP,
                last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        self.db.session.commit()
    
    def down(self):
        """Drop all tables."""
        self.db.session.execute("DROP TABLE IF EXISTS user_session CASCADE")
        self.db.session.execute("DROP TABLE IF EXISTS login_history CASCADE")
        self.db.session.execute("DROP TABLE IF EXISTS user CASCADE")
        self.db.session.commit()


class Migration002_AddUserProfile(Migration):
    """Add user profile fields."""
    
    version = '002'
    description = 'Add profile fields to user table'
    
    def up(self):
        """Add profile columns."""
        self.db.session.execute("""
            ALTER TABLE user 
            ADD COLUMN IF NOT EXISTS first_name VARCHAR(50),
            ADD COLUMN IF NOT EXISTS last_name VARCHAR(50),
            ADD COLUMN IF NOT EXISTS phone VARCHAR(20),
            ADD COLUMN IF NOT EXISTS bio TEXT,
            ADD COLUMN IF NOT EXISTS avatar_url VARCHAR(255)
        """)
        self.db.session.commit()
    
    def down(self):
        """Remove profile columns."""
        self.db.session.execute("""
            ALTER TABLE user 
            DROP COLUMN IF EXISTS first_name,
            DROP COLUMN IF EXISTS last_name,
            DROP COLUMN IF EXISTS phone,
            DROP COLUMN IF EXISTS bio,
            DROP COLUMN IF EXISTS avatar_url
        """)
        self.db.session.commit()


class Migration003_AddIndexes(Migration):
    """Add database indexes for performance."""
    
    version = '003'
    description = 'Add indexes for better query performance'
    
    def up(self):
        """Create indexes."""
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_user_email ON user(email)",
            "CREATE INDEX IF NOT EXISTS idx_user_username ON user(username)",
            "CREATE INDEX IF NOT EXISTS idx_user_created_at ON user(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_login_history_user_id ON login_history(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_login_history_created_at ON login_history(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_session_user_id ON user_session(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_session_token ON user_session(session_token)",
            "CREATE INDEX IF NOT EXISTS idx_session_active ON user_session(is_active)",
        ]
        
        for index_sql in indexes:
            self.db.session.execute(index_sql)
        
        self.db.session.commit()
    
    def down(self):
        """Drop indexes."""
        indexes = [
            "DROP INDEX IF EXISTS idx_user_email",
            "DROP INDEX IF EXISTS idx_user_username",
            "DROP INDEX IF EXISTS idx_user_created_at",
            "DROP INDEX IF EXISTS idx_login_history_user_id",
            "DROP INDEX IF EXISTS idx_login_history_created_at",
            "DROP INDEX IF EXISTS idx_session_user_id",
            "DROP INDEX IF EXISTS idx_session_token",
            "DROP INDEX IF EXISTS idx_session_active",
        ]
        
        for index_sql in indexes:
            self.db.session.execute(index_sql)
        
        self.db.session.commit()


class MigrationManager:
    """Manage database migrations."""
    
    def __init__(self, db: SQLAlchemy):
        self.db = db
        self.migrations = [
            Migration001_InitialSchema,
            Migration002_AddUserProfile,
            Migration003_AddIndexes,
        ]
        self._ensure_migrations_table()
    
    def _ensure_migrations_table(self):
        """Create migrations tracking table."""
        self.db.session.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version VARCHAR(10) PRIMARY KEY,
                description TEXT,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.db.session.commit()
    
    def get_applied_migrations(self):
        """Get list of applied migrations."""
        result = self.db.session.execute(
            "SELECT version FROM schema_migrations ORDER BY version"
        )
        return [row[0] for row in result]
    
    def get_pending_migrations(self):
        """Get list of pending migrations."""
        applied = set(self.get_applied_migrations())
        return [m for m in self.migrations if m.version not in applied]
    
    def apply_migration(self, migration_class):
        """Apply a single migration."""
        migration = migration_class(self.db)
        
        print(f"Applying migration {migration.version}: {migration.description}")
        
        try:
            migration.up()
            
            # Record migration
            self.db.session.execute(
                "INSERT INTO schema_migrations (version, description) VALUES (%s, %s)",
                (migration.version, migration.description)
            )
            self.db.session.commit()
            
            print(f"✓ Migration {migration.version} applied successfully")
            return True
        
        except Exception as e:
            self.db.session.rollback()
            print(f"✗ Migration {migration.version} failed: {e}")
            return False
    
    def rollback_migration(self, migration_class):
        """Rollback a single migration."""
        migration = migration_class(self.db)
        
        print(f"Rolling back migration {migration.version}: {migration.description}")
        
        try:
            migration.down()
            
            # Remove migration record
            self.db.session.execute(
                "DELETE FROM schema_migrations WHERE version = %s",
                (migration.version,)
            )
            self.db.session.commit()
            
            print(f"✓ Migration {migration.version} rolled back successfully")
            return True
        
        except Exception as e:
            self.db.session.rollback()
            print(f"✗ Rollback of migration {migration.version} failed: {e}")
            return False
    
    def migrate(self):
        """Apply all pending migrations."""
        pending = self.get_pending_migrations()
        
        if not pending:
            print("No pending migrations")
            return True
        
        print(f"Found {len(pending)} pending migration(s)")
        
        for migration_class in pending:
            if not self.apply_migration(migration_class):
                return False
        
        print("All migrations applied successfully")
        return True
    
    def rollback(self, steps=1):
        """Rollback last N migrations."""
        applied = self.get_applied_migrations()
        
        if not applied:
            print("No migrations to rollback")
            return True
        
        to_rollback = applied[-steps:]
        
        for version in reversed(to_rollback):
            migration_class = next(
                (m for m in self.migrations if m.version == version),
                None
            )
            
            if migration_class:
                if not self.rollback_migration(migration_class):
                    return False
        
        return True
    
    def status(self):
        """Show migration status."""
        applied = set(self.get_applied_migrations())
        
        print("\nMigration Status:")
        print("-" * 60)
        
        for migration_class in self.migrations:
            migration = migration_class(self.db)
            status = "✓ Applied" if migration.version in applied else "✗ Pending"
            print(f"{status} | {migration.version} | {migration.description}")
        
        print("-" * 60)


def main():
    """CLI for migrations."""
    import sys
    from app import create_app
    
    app = create_app()
    
    with app.app_context():
        from extensions import db
        manager = MigrationManager(db)
        
        if len(sys.argv) < 2:
            print("Usage: python migrations.py [migrate|rollback|status]")
            return
        
        command = sys.argv[1]
        
        if command == 'migrate':
            manager.migrate()
        elif command == 'rollback':
            steps = int(sys.argv[2]) if len(sys.argv) > 2 else 1
            manager.rollback(steps)
        elif command == 'status':
            manager.status()
        else:
            print(f"Unknown command: {command}")


if __name__ == '__main__':
    main()
