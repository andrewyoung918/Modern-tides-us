#!/bin/bash

# Script para verificar la configuración del repositorio para HACS
echo "🔍 Verificando configuración del repositorio para HACS..."
echo

# Verificar si el repositorio tiene description y topics usando GitHub API
REPO="ALArvi019/moderntides"

echo "📋 Obteniendo información del repositorio..."
REPO_INFO=$(curl -s "https://api.github.com/repos/$REPO")

# Extraer description
DESCRIPTION=$(echo "$REPO_INFO" | grep -o '"description":"[^"]*"' | cut -d'"' -f4)
echo "📝 Description: $DESCRIPTION"

# Extraer topics
TOPICS=$(echo "$REPO_INFO" | grep -o '"topics":\[[^\]]*\]' | sed 's/"topics":\[//g' | sed 's/\]//g' | sed 's/"//g')
echo "🏷️  Topics: $TOPICS"

echo
echo "✅ Checklist de HACS:"
echo

# Check description
if [ -n "$DESCRIPTION" ] && [ "$DESCRIPTION" != "null" ]; then
    echo "✅ Description configurada"
else
    echo "❌ Description no configurada"
fi

# Check topics
if echo "$TOPICS" | grep -q "home-assistant"; then
    echo "✅ Topics configurados (contiene 'home-assistant')"
else
    echo "❌ Topics no configurados"
fi

# Check hacs.json
if [ -f "hacs.json" ]; then
    echo "✅ hacs.json existe"
    if grep -q '"domains"' hacs.json; then
        echo "❌ hacs.json contiene claves no permitidas (domains)"
    elif grep -q '"iot_class"' hacs.json; then
        echo "❌ hacs.json contiene claves no permitidas (iot_class)"
    else
        echo "✅ hacs.json válido"
    fi
else
    echo "❌ hacs.json no existe"
fi

echo
echo "🔗 Para configurar description y topics:"
echo "   Ve a: https://github.com/$REPO"
echo "   Haz clic en ⚙️ junto a 'About'"
echo "   Añade description y topics según GITHUB_CONFIG_GUIDE.md"
