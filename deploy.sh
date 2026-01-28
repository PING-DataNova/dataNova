#!/bin/bash
# Script de déploiement manuel pour DataNova Backend

set -e

echo "🚀 Déploiement du backend DataNova sur Azure..."
echo ""

# Configuration
RESOURCE_GROUP="datanova-dev-rg"
CONTAINER_APP="datanova-dev-backend"
ACR_NAME="datanovadevacr"
IMAGE="$ACR_NAME.azurecr.io/datanova-backend:latest"

# Vérifier la connexion Azure
echo "🔐 Vérification de la connexion Azure..."
az account show --query name -o tsv || {
  echo "❌ Erreur: Non connecté à Azure. Lance 'az login' d'abord."
  exit 1
}

echo "✅ Connecté à Azure"
echo ""

# Récupérer la dernière image
echo "📦 Image à déployer: $IMAGE"
echo ""

# Mettre à jour la Container App
echo "🔄 Mise à jour de la Container App..."
az containerapp update \
  --name "$CONTAINER_APP" \
  --resource-group "$RESOURCE_GROUP" \
  --image "$IMAGE" \
  --output table

echo ""
echo "✅ Déploiement terminé !"
echo "🌐 Backend URL: https://datanova-dev-backend.happyforest-90d4db38.francecentral.azurecontainerapps.io"
echo ""
echo "📊 Pour voir les logs :"
echo "az containerapp logs show --name $CONTAINER_APP --resource-group $RESOURCE_GROUP --follow"
