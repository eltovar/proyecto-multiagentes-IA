import sqlite3
import os
import sys
import shutil
import argparse
from datetime import datetime
from pathlib import Path


class DatabaseMigrator:
    """Gestor de migraciones de base de datos."""

    def __init__(self, db_path: str = "multiagent_leads.db"):
        """
        Inicializa el migrador.

        Args:
            db_path: Ruta a la base de datos SQLite
        """
        self.db_path = db_path
        self.backup_dir = "backups"
        self.migrations_dir = "scripts/migrations"

        # Asegurar que directorios existen
        os.makedirs(self.backup_dir, exist_ok=True)

    def create_backup(self) -> str:
        """
        Crea backup de la base de datos.

        Returns:
            Path al archivo de backup
        """
        if not os.path.exists(self.db_path):
            print(f"[WARNING] Base de datos no existe: {self.db_path}")
            print(f"[INFO] Se creará durante la migración")
            return None

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(self.backup_dir, f"multiagent_leads_backup_{timestamp}.db")

        try:
            shutil.copy2(self.db_path, backup_path)
            backup_size = os.path.getsize(backup_path)
            print(f"[OK] Backup creado: {backup_path} ({backup_size:,} bytes)")
            return backup_path
        except Exception as e:
            print(f"[ERROR] No se pudo crear backup: {e}")
            raise

    def execute_migration(self, migration_file: str, dry_run: bool = False) -> bool:
        """ Ejecuta una migración SQL. """
        migration_path = os.path.join(self.migrations_dir, migration_file)

        if not os.path.exists(migration_path):
            print(f"[ERROR] Archivo de migración no encontrado: {migration_path}")
            return False

        # Leer SQL
        with open(migration_path, 'r', encoding='utf-8') as f:
            sql_content = f.read()

        if dry_run:
            print("\n" + "=" * 70)
            print("DRY RUN - SQL A EJECUTAR:")
            print("=" * 70)
            print(sql_content)
            print("=" * 70)
            return True

        # Ejecutar migración
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            print(f"\n[INFO] Ejecutando migración: {migration_file}")
            cursor.executescript(sql_content)

            conn.commit()
            conn.close()

            print(f"[OK] Migración ejecutada exitosamente")
            return True

        except sqlite3.Error as e:
            print(f"[ERROR] Error ejecutando migración: {e}")
            conn.rollback()
            conn.close()
            return False
        except Exception as e:
            print(f"[ERROR] Error inesperado: {e}")
            return False

    def verify_migration(self, expected_columns: list) -> bool:
        """ Verifica que la migración se aplicó correctamente. """
        if not os.path.exists(self.db_path):
            print(f"[ERROR] Base de datos no existe: {self.db_path}")
            return False

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Obtener schema de la tabla
            cursor.execute("PRAGMA table_info(conversations)")
            columns = [row[1] for row in cursor.fetchall()]

            # Verificar que todas las columnas esperadas existen
            missing_columns = [col for col in expected_columns if col not in columns]

            if missing_columns:
                print(f"[ERROR] Columnas faltantes: {missing_columns}")
                conn.close()
                return False

            print(f"[OK] Verificación exitosa. Columnas encontradas:")
            for col in expected_columns:
                print(f"     ✓ {col}")

            # Mostrar estadísticas
            cursor.execute("SELECT COUNT(*) FROM conversations")
            total = cursor.fetchone()[0]
            print(f"\n[INFO] Total de conversaciones: {total}")

            conn.close()
            return True

        except sqlite3.Error as e:
            print(f"[ERROR] Error verificando migración: {e}")
            return False

    def restore_backup(self, backup_path: str) -> bool:
        """ Restaura la base de datos desde un backup."""
        if not os.path.exists(backup_path):
            print(f"[ERROR] Backup no encontrado: {backup_path}")
            return False

        try:
            shutil.copy2(backup_path, self.db_path)
            print(f"[OK] Base de datos restaurada desde: {backup_path}")
            return True
        except Exception as e:
            print(f"[ERROR] No se pudo restaurar backup: {e}")
            return False


def main():
    """Función principal."""
    parser = argparse.ArgumentParser(
        description="Ejecuta migraciones de base de datos"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simula la migración sin ejecutarla"
    )
    parser.add_argument(
        "--rollback",
        action="store_true",
        help="Revierte la última migración"
    )
    parser.add_argument(
        "--migration",
        default="001",
        help="Número de migración a ejecutar (default: 001)"
    )

    args = parser.parse_args()

    # Banner
    print("\n" + "=" * 70)
    print("DATABASE MIGRATION TOOL - PR #1 Fundamentos")
    print("=" * 70)

    # Inicializar migrador
    migrator = DatabaseMigrator()

    # Rollback
    if args.rollback:
        print("\n[INFO] Ejecutando ROLLBACK...")

        # Crear backup antes del rollback
        backup_path = migrator.create_backup()

        # Ejecutar rollback
        rollback_file = f"{args.migration}_rollback.sql"
        success = migrator.execute_migration(rollback_file, dry_run=args.dry_run)

        if success and not args.dry_run:
            print("\n[OK] Rollback completado exitosamente")
        elif not success:
            print("\n[ERROR] Rollback falló")
            if backup_path:
                print(f"[INFO] Puedes restaurar desde: {backup_path}")
            sys.exit(1)

        sys.exit(0)

    # Migración normal
    print(f"\n[INFO] Preparando migración {args.migration}...")

    # Crear backup
    if not args.dry_run:
        backup_path = migrator.create_backup()

    # Ejecutar migración
    migration_file = f"{args.migration}_add_intent_fields.sql"
    success = migrator.execute_migration(migration_file, dry_run=args.dry_run)

    if not success:
        print("\n[ERROR] Migración falló")
        if backup_path and not args.dry_run:
            print(f"[INFO] Restaurando desde backup...")
            migrator.restore_backup(backup_path)
        sys.exit(1)

    # Verificar migración (solo si no es dry-run)
    if not args.dry_run:
        expected_columns = [
            "intent",
            "extracted_data",
            "business_hours_valid",
            "last_message_at",
            "interaction_count",
            "form_data"
        ]

        if not migrator.verify_migration(expected_columns):
            print("\n[ERROR] Verificación de migración falló")
            print(f"[INFO] Restaurando desde backup...")
            migrator.restore_backup(backup_path)
            sys.exit(1)

    # Éxito
    print("\n" + "=" * 70)
    if args.dry_run:
        print("[DRY-RUN] Migración simulada exitosamente")
    else:
        print("[SUCCESS] Migración completada exitosamente")
        print(f"[INFO] Backup disponible en: {backup_path}")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
