#!/bin/bash
# 🧹 LIMPIEZA EXHAUSTIVA DEL PROYECTO MULTIAGENTE IA
# Ejecutar desde el directorio raíz del proyecto

echo "🧹 INICIANDO LIMPIEZA EXHAUSTIVA DEL PROYECTO..."
echo "Directorio actual: $(pwd)"
echo "Fecha: $(date)"
echo ""

# PASO 1: Backup de seguridad en Git
echo "📦 PASO 1: Creando backup de seguridad..."
if [ -d ".git" ]; then
    git add -A
    git commit -m "Pre-limpieza: Backup automático antes de eliminar archivos temporales

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>" 2>/dev/null || echo "Sin cambios para commit"
    echo "✅ Backup de seguridad completado"
else
    echo "⚠️ No es un repositorio Git - continuando sin backup"
fi

# PASO 2: Limpiar caché de Python
echo ""
echo "🗑️ PASO 2: Eliminando archivos de caché Python..."
PYCACHE_BEFORE=$(find . -name "__pycache__" -not -path "./.venv/*" -type d | wc -l)
PYC_BEFORE=$(find . -name "*.pyc" -not -path "./.venv/*" -type f | wc -l)

echo "Directorios __pycache__ encontrados: $PYCACHE_BEFORE"
echo "Archivos .pyc encontrados: $PYC_BEFORE"

# Eliminar __pycache__ y .pyc (excluyendo .venv)
find . -name "__pycache__" -not -path "./.venv/*" -type d -exec rm -rf {} + 2>/dev/null
find . -name "*.pyc" -not -path "./.venv/*" -type f -delete 2>/dev/null

PYCACHE_AFTER=$(find . -name "__pycache__" -not -path "./.venv/*" -type d | wc -l)
PYC_AFTER=$(find . -name "*.pyc" -not -path "./.venv/*" -type f | wc -l)

echo "✅ Directorios __pycache__ eliminados: $((PYCACHE_BEFORE - PYCACHE_AFTER))"
echo "✅ Archivos .pyc eliminados: $((PYC_BEFORE - PYC_AFTER))"

# PASO 3: Limpiar caché de testing
echo ""
echo "🗑️ PASO 3: Eliminando caché de testing..."
find . -name ".pytest_cache" -type d -exec rm -rf {} + 2>/dev/null
echo "✅ Cache de pytest eliminado"

# PASO 4: Eliminar archivos backup
echo ""
echo "🗑️ PASO 4: Eliminando archivos backup..."
BACKUP_COUNT=$(find . -name "*backup*" -type f | wc -l)
echo "Archivos backup encontrados: $BACKUP_COUNT"

find . -name "*backup_*" -type f -delete 2>/dev/null
find . -name "*_backup.py" -type f -delete 2>/dev/null
find . -name "*backup.py" -type f -delete 2>/dev/null

BACKUP_REMAINING=$(find . -name "*backup*" -type f | wc -l)
echo "✅ Archivos backup eliminados: $((BACKUP_COUNT - BACKUP_REMAINING))"

# PASO 5: Eliminar archivos temporales
echo ""
echo "🗑️ PASO 5: Eliminando archivos temporales..."
find . \( -name "*.tmp" -o -name "*.temp" -o -name "*~" -o -name "*.bak" -o -name "*.pid" -o -name "*.lock" -o -name ".DS_Store" \) -not -path "./.venv/*" -type f -delete 2>/dev/null
echo "✅ Archivos temporales eliminados"

# PASO 6: Eliminar logs
echo ""
echo "🗑️ PASO 6: Eliminando archivos de log..."
find . \( -name "*.log" -o -name "*.out" -o -name "nohup.out" \) -not -path "./.venv/*" -type f -delete 2>/dev/null
echo "✅ Archivos de log eliminados"

# PASO 7: Eliminar documentación con prefijos incorrectos (PRESERVAR .gitignore)
echo ""
echo "🗑️ PASO 7: Eliminando documentación con prefijos incorrectos..."
DOC_COUNT=$(find . -maxdepth 1 -name ".*.md" -type f | wc -l)
echo "Archivos .md con prefijo encontrados: $DOC_COUNT"
find . -maxdepth 1 -name ".*.md" -type f -delete 2>/dev/null
echo "✅ Documentación con prefijos incorrectos eliminada (preservando .gitignore y .env*)"

# PASO 8: Verificación final
echo ""
echo "📊 VERIFICACIÓN FINAL:"
echo "✅ Archivos Python (.py): $(find . -name '*.py' -not -path './.venv/*' | wc -l)"
echo "✅ Archivos Markdown (.md): $(find . -name '*.md' | wc -l)"
echo "✅ README.md: $([ -f 'README.md' ] && echo 'EXISTS' || echo 'MISSING')"
echo "✅ .gitignore: $([ -f '.gitignore' ] && echo 'EXISTS' || echo 'MISSING')"
echo "✅ requirements.txt: $([ -f 'requirements.txt' ] && echo 'EXISTS' || echo 'MISSING')"

echo ""
echo "🎉 LIMPIEZA EXHAUSTIVA COMPLETADA"
echo "Fecha finalización: $(date)"