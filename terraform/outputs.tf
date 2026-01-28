# =============================================================================
# TERRAFORM OUTPUTS
# =============================================================================
# Ce fichier définit les informations affichées après le déploiement
# Ces valeurs sont utiles pour configurer l'application et donner accès à l'équipe
# =============================================================================

# -----------------------------------------------------------------------------
# INFORMATIONS GÉNÉRALES
# -----------------------------------------------------------------------------

output "resource_group_name" {
  description = "Nom du Resource Group créé"
  value       = azurerm_resource_group.main.name
}

output "location" {
  description = "Région Azure du déploiement"
  value       = azurerm_resource_group.main.location
}

# -----------------------------------------------------------------------------
# BASE DE DONNÉES POSTGRESQL
# -----------------------------------------------------------------------------

output "postgres_server_fqdn" {
  description = "FQDN du serveur PostgreSQL (pour connexion)"
  value       = azurerm_postgresql_flexible_server.main.fqdn
}

output "postgres_database_name" {
  description = "Nom de la base de données"
  value       = azurerm_postgresql_flexible_server_database.main.name
}

output "postgres_admin_username" {
  description = "Nom d'utilisateur admin PostgreSQL"
  value       = var.postgres_admin_username
  sensitive   = false
}

output "postgres_admin_password" {
  description = "Mot de passe admin PostgreSQL (SENSIBLE - ne pas partager)"
  value       = random_password.postgres_admin_password.result
  sensitive   = true  # Masqué par défaut, visible avec : terraform output -raw postgres_admin_password
}

output "postgres_connection_string" {
  description = "Chaîne de connexion complète PostgreSQL (SENSIBLE)"
  value       = azurerm_key_vault_secret.database_url.value
  sensitive   = true
}

# -----------------------------------------------------------------------------
# CONTAINER REGISTRY (ACR)
# -----------------------------------------------------------------------------

output "acr_login_server" {
  description = "URL du Container Registry pour docker login"
  value       = azurerm_container_registry.main.login_server
}

output "acr_admin_username" {
  description = "Username admin ACR"
  value       = azurerm_container_registry.main.admin_username
  sensitive   = false
}

output "acr_admin_password" {
  description = "Password admin ACR (SENSIBLE)"
  value       = azurerm_container_registry.main.admin_password
  sensitive   = true
}

# -----------------------------------------------------------------------------
# BACKEND (CONTAINER APP)
# -----------------------------------------------------------------------------

output "backend_url" {
  description = "URL publique du backend FastAPI"
  value       = "https://${azurerm_container_app.backend.ingress[0].fqdn}"
}

output "backend_fqdn" {
  description = "FQDN du backend (sans https://)"
  value       = azurerm_container_app.backend.ingress[0].fqdn
}

output "backend_swagger_url" {
  description = "URL de la documentation Swagger du backend"
  value       = "https://${azurerm_container_app.backend.ingress[0].fqdn}/docs"
}

# -----------------------------------------------------------------------------
# FRONTEND (STATIC WEB APP)
# -----------------------------------------------------------------------------

output "frontend_default_hostname" {
  description = "URL par défaut du frontend (Azure)"
  value       = azurerm_static_site.frontend.default_host_name
}

output "frontend_url" {
  description = "URL complète du frontend"
  value       = "https://${azurerm_static_site.frontend.default_host_name}"
}

output "frontend_deployment_token" {
  description = "Token pour déployer sur Static Web App (SENSIBLE)"
  value       = azurerm_static_site.frontend.api_key
  sensitive   = true
}

# -----------------------------------------------------------------------------
# KEY VAULT
# -----------------------------------------------------------------------------

output "key_vault_name" {
  description = "Nom du Key Vault (coffre-fort des secrets)"
  value       = azurerm_key_vault.main.name
}

output "key_vault_uri" {
  description = "URI du Key Vault"
  value       = azurerm_key_vault.main.vault_uri
}

# -----------------------------------------------------------------------------
# INSTRUCTIONS DE DÉPLOIEMENT
# -----------------------------------------------------------------------------

output "deployment_instructions" {
  description = "Instructions pour déployer les applications"
  value = <<-EOT
  
  ╔════════════════════════════════════════════════════════════════════════════╗
  ║                     DÉPLOIEMENT DATANOVA - ÉTAPES                          ║
  ╚════════════════════════════════════════════════════════════════════════════╝
  
  ✅ Infrastructure Azure créée avec succès !
  
  📦 ÉTAPE 1 : CONSTRUIRE ET POUSSER L'IMAGE DOCKER DU BACKEND
  ────────────────────────────────────────────────────────────────────────────
  cd backend
  
  # Se connecter au Container Registry
  docker login ${azurerm_container_registry.main.login_server}
  Username: ${azurerm_container_registry.main.admin_username}
  Password: [utilise : terraform output -raw acr_admin_password]
  
  # Build et push de l'image
  docker build -t ${azurerm_container_registry.main.login_server}/datanova-backend:latest .
  docker push ${azurerm_container_registry.main.login_server}/datanova-backend:latest
  
  # Redémarrer le Container App pour charger la nouvelle image
  az containerapp update \\
    --name ${azurerm_container_app.backend.name} \\
    --resource-group ${azurerm_resource_group.main.name}
  
  
  🌐 ÉTAPE 2 : DÉPLOYER LE FRONTEND
  ────────────────────────────────────────────────────────────────────────────
  cd frontend
  
  # Installer les dépendances et build
  npm install
  npm run build
  
  # Déployer sur Static Web App
  npx @azure/static-web-apps-cli deploy \\
    --app-location ./dist \\
    --deployment-token [utilise : terraform output -raw frontend_deployment_token]
  
  Ou utilise GitHub Actions (recommandé) :
  - Configure le secret AZURE_STATIC_WEB_APPS_API_TOKEN dans GitHub
  - Push ton code, le déploiement sera automatique
  
  
  🔗 ÉTAPE 3 : URLS DE L'APPLICATION
  ────────────────────────────────────────────────────────────────────────────
  Backend API  : ${azurerm_container_app.backend.ingress[0].fqdn}
  Swagger Docs : ${azurerm_container_app.backend.ingress[0].fqdn}/docs
  Frontend     : ${azurerm_static_site.frontend.default_host_name}
  
  
  🗄️  ÉTAPE 4 : INITIALISER LA BASE DE DONNÉES
  ────────────────────────────────────────────────────────────────────────────
  # Récupérer les credentials PostgreSQL
  terraform output postgres_admin_username
  terraform output -raw postgres_admin_password
  
  # Se connecter via psql ou pgAdmin
  psql "postgresql://${var.postgres_admin_username}@${azurerm_postgresql_flexible_server.main.fqdn}:5432/${azurerm_postgresql_flexible_server_database.main.name}?sslmode=require"
  
  # Ou lancer le script d'initialisation depuis le backend
  docker exec -it <backend_container> python scripts/init_db.py
  
  
  🔒 SECRETS STOCKÉS DANS KEY VAULT
  ────────────────────────────────────────────────────────────────────────────
  Key Vault : ${azurerm_key_vault.main.name}
  
  Pour voir les secrets :
  az keyvault secret show --vault-name ${azurerm_key_vault.main.name} --name postgres-admin-password
  az keyvault secret show --vault-name ${azurerm_key_vault.main.name} --name anthropic-api-key
  az keyvault secret show --vault-name ${azurerm_key_vault.main.name} --name google-api-key
  
  
  👥 ACCÈS ÉQUIPE
  ────────────────────────────────────────────────────────────────────────────
  Les membres de l'équipe ont le rôle "Contributor" sur le Resource Group.
  Ils peuvent gérer toutes les ressources depuis le portail Azure.
  
  EOT
}

# -----------------------------------------------------------------------------
# COMMANDES UTILES
# -----------------------------------------------------------------------------

output "useful_commands" {
  description = "Commandes Azure CLI utiles"
  value = <<-EOT
  
  📋 COMMANDES UTILES
  ══════════════════════════════════════════════════════════════════════════
  
  # Voir les logs du backend
  az containerapp logs show \\
    --name ${azurerm_container_app.backend.name} \\
    --resource-group ${azurerm_resource_group.main.name} \\
    --follow
  
  # Redémarrer le backend
  az containerapp revision restart \\
    --name ${azurerm_container_app.backend.name} \\
    --resource-group ${azurerm_resource_group.main.name}
  
  # Voir les métriques PostgreSQL
  az postgres flexible-server show \\
    --name ${azurerm_postgresql_flexible_server.main.name} \\
    --resource-group ${azurerm_resource_group.main.name}
  
  # Ouvrir le portail Azure
  az resource show \\
    --resource-group ${azurerm_resource_group.main.name} \\
    --name ${azurerm_container_app.backend.name} \\
    --resource-type "Microsoft.App/containerApps" \\
    --query id -o tsv | xargs -I {} open "https://portal.azure.com/#@/resource{}"
  
  EOT
}

# -----------------------------------------------------------------------------
# RÉSUMÉ DES COÛTS ESTIMÉS
# -----------------------------------------------------------------------------

output "estimated_monthly_cost" {
  description = "Estimation des coûts mensuels Azure"
  value = <<-EOT
  
  💰 ESTIMATION DES COÛTS MENSUELS (RÉGION WEST EUROPE)
  ══════════════════════════════════════════════════════════════════════════
  
  PostgreSQL Flexible Server (B_Standard_B1ms)  : ~25€/mois
  Container Registry (Basic, 5GB)               : ~5€/mois
  Container App Backend (0.5 vCore, 1GB)        : ~10-30€/mois
  Container App Environment + Logs              : ~10€/mois
  Static Web App (Free tier)                    : 0€/mois
  Key Vault                                     : ~1€/mois
  ────────────────────────────────────────────────────────────────────────
  TOTAL ESTIMÉ                                  : ~51-71€/mois
  
  ⚠️  Remarques :
  - Les Container Apps facturent à l'usage (CPU/RAM/requêtes)
  - Avec 200€ de crédit, tu as ~3 mois d'utilisation
  - Pour réduire les coûts : arrête les ressources quand tu ne les utilises pas
  
  EOT
}
