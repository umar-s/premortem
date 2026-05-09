#!/usr/bin/env bash
# premortem skill installer
# Copies premortem/ to ~/.claude/skills/premortem/

set -euo pipefail

REPO_NAME="premortem"
SKILL_NAME="premortem"
TARGET_DIR="${HOME}/.claude/skills/${SKILL_NAME}"

color() { printf '\033[%sm%s\033[0m' "$1" "$2"; }
green() { color '0;32' "$1"; }
yellow() { color '0;33' "$1"; }
red() { color '0;31' "$1"; }

log_step() { echo "$(green '==>') $1"; }
log_warn() { echo "$(yellow 'warn:') $1"; }
log_err()  { echo "$(red 'error:') $1" >&2; }

# Detect whether we're running from a git checkout or piped via curl
if [[ -d "$(dirname "${BASH_SOURCE[0]:-$0}")/${SKILL_NAME}" ]]; then
    SOURCE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)/${SKILL_NAME}"
    INSTALL_MODE="local"
else
    INSTALL_MODE="remote"
fi

log_step "Installing ${SKILL_NAME} skill to ${TARGET_DIR}"

if [[ -d "${TARGET_DIR}" ]]; then
    log_warn "Existing installation found at ${TARGET_DIR} — overwriting"
    rm -rf "${TARGET_DIR}"
fi

mkdir -p "${TARGET_DIR}"

if [[ "${INSTALL_MODE}" == "local" ]]; then
    cp "${SOURCE_DIR}/SKILL.md" "${TARGET_DIR}/SKILL.md"
    for sub in scripts references assets evals; do
        if [[ -d "${SOURCE_DIR}/${sub}" ]]; then
            cp -R "${SOURCE_DIR}/${sub}" "${TARGET_DIR}/${sub}"
        fi
    done
    if [[ -f "${SOURCE_DIR}/Makefile" ]]; then
        cp "${SOURCE_DIR}/Makefile" "${TARGET_DIR}/Makefile"
    fi
else
    log_err "Remote install не поддерживается — скилл требует scripts/ рядом с SKILL.md."
    log_err "Сделай git clone и запусти ./install.sh из локальной копии:"
    log_err "  git clone https://github.com/AndyShaman/premortem.git"
    log_err "  cd premortem && ./install.sh"
    rmdir "${TARGET_DIR}" 2>/dev/null || true
    exit 1
fi

log_step "Installed"
echo ""
echo "  Location: ${TARGET_DIR}"
echo ""
echo "  In Claude Code, the skill will load automatically when you ask for"
echo "  a premortem on a concrete plan, launch, or decision. Try:"
echo ""
echo "    \"premortem this: <your plan>\""
echo "    \"stress-test this <decision>\""
echo "    \"what could kill <plan>?\""
echo ""
