#!/usr/bin/env bash
# init.sh — Verificación e inicialización del entorno
#
# Este script lo ejecuta el agente al COMENZAR una sesión y antes de
# declarar cualquier tarea como `done`. Si falla, la sesión no debe avanzar.
#
# Salida esperada: códigos de salida claros y bloques marcados con [OK]/[FAIL].

set -u
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m'

ok()    { printf "${GREEN}[OK]${NC}    %s\n" "$1"; }
warn()  { printf "${YELLOW}[WARN]${NC}  %s\n" "$1"; }
fail()  { printf "${RED}[FAIL]${NC}  %s\n" "$1"; }

EXIT_CODE=0

echo "── 1. Verificando entorno ─────────────────────────────"

# Python disponible
if ! command -v python3 >/dev/null 2>&1; then
  fail "python3 no está instalado"
  exit 1
fi
ok "python3 -> $(python3 --version)"

# Versión mínima 3.9 (dataclasses + typing moderno)
PY_VERSION_OK=$(python3 -c 'import sys; print(int(sys.version_info >= (3, 9)))')
if [ "$PY_VERSION_OK" != "1" ]; then
  fail "Se requiere Python >= 3.9"
  exit 1
fi
ok "Versión de Python compatible"

echo ""
echo "── 2. Verificando archivos base del arnés ──────────────"

for f in AGENTS.md feature_list.json progress/current.md docs/architecture.md docs/conventions.md docs/verification.md CHECKPOINTS.md; do
  if [ ! -f "$f" ]; then
    fail "Falta archivo base: $f"
    EXIT_CODE=1
  else
    ok "Existe $f"
  fi
done

echo ""
echo "── 3. Validando feature_list.json ──────────────────────"

python3 - <<'PY'
import json, sys
try:
    data = json.load(open("feature_list.json"))
    valid_status = {"pending", "in_progress", "done", "blocked"}
    valid_types  = {"feature", "bugfix", "refactor"}
    errors = []
    in_progress = [f for f in data["features"] if f["status"] == "in_progress"]
    if len(in_progress) > 1:
        errors.append(f"Hay {len(in_progress)} features en in_progress (máximo 1)")
    for f in data["features"]:
        if f["status"] not in valid_status:
            errors.append(f"Estado inválido en feature {f['id']}: {f['status']}")
        if "type" not in f:
            errors.append(f"Feature {f['id']} ({f['name']}) sin campo 'type'")
        elif f["type"] not in valid_types:
            errors.append(f"Tipo inválido en feature {f['id']}: {f['type']}")
    if errors:
        for e in errors: print(f"[FAIL]  {e}")
        sys.exit(1)
    print(f"[OK]    feature_list.json válido ({len(data['features'])} features)")
except Exception as e:
    print(f"[FAIL]  feature_list.json inválido: {e}")
    sys.exit(1)
PY

if [ $? -ne 0 ]; then EXIT_CODE=1; fi

echo ""
echo "── 4. Validando specs SDD ──────────────────────────────"

python3 - <<'PY'
import json, sys, os
data = json.load(open("feature_list.json"))
errors = []
warnings = []
for f in data["features"]:
    if not f.get("sdd"):
        continue
    specs_dir = f"specs/{f['name']}"
    required = ["requirements.md", "design.md", "tasks.md"]
    if f["status"] == "in_progress":
        for doc in required:
            if not os.path.isfile(f"{specs_dir}/{doc}"):
                errors.append(f"  [{f['id']}] {f['name']}: falta {specs_dir}/{doc}")
    elif f["status"] == "pending":
        if not os.path.isdir(specs_dir):
            warnings.append(f"  [{f['id']}] {f['name']}: specs/ no creada aún (pendiente)")
if errors:
    for e in errors: print(f"[FAIL]  Feature in_progress con sdd=true sin specs: {e}")
    sys.exit(1)
for w in warnings: print(f"[WARN]  {w}")
if not errors and not warnings:
    print("[OK]    Specs SDD presentes o no requeridas")
elif not errors:
    print("[OK]    Specs SDD: sin bloqueos (warnings solo)")
PY

if [ $? -ne 0 ]; then EXIT_CODE=1; fi

echo ""
echo "── 5. Ejecutando tests ─────────────────────────────────"

if [ -d "tests" ]; then
  TEST_FILES=$(find tests -name "test_*.py" | wc -l | tr -d ' ')
  if [ "$TEST_FILES" -eq 0 ]; then
    warn "Carpeta tests/ existe pero no hay archivos test_*.py todavía"
  elif uv run pytest tests -v 2>&1; then
    ok "Todos los tests pasan"
  else
    fail "Hay tests rotos"
    EXIT_CODE=1
  fi
else
  warn "Carpeta tests/ no existe todavía"
fi

echo ""
echo "── 6. Resumen ──────────────────────────────────────────"

if [ $EXIT_CODE -eq 0 ]; then
  ok "Entorno listo. Puedes empezar a trabajar."
else
  fail "Entorno NO está listo. Resuelve los errores antes de avanzar."
fi

exit $EXIT_CODE
