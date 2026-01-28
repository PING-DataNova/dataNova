
locals {
  # Noms des ressources avec suffixe unique
  resource_prefix = "${var.project_name}-${var.environment}"
  

  common_tags = merge(
    var.tags,
    {
      Environment = var.environment
      Location    = var.location
      ManagedBy   = "Terraform"
      Project     = var.project_name
    }
  )

  # URL du backend (sera calculé après déploiement)
  backend_url = "https://${azurerm_container_app.backend.ingress[0].fqdn}"
}

# -----------------------------------------------------------------------------
# 1. RESOURCE GROUP
# -----------------------------------------------------------------------------
# Conteneur logique qui regroupe toutes les ressources du projet

resource "azurerm_resource_group" "main" {
  name     = "${local.resource_prefix}-rg"
  location = var.location
  tags     = local.common_tags
}

# -----------------------------------------------------------------------------
# 2. GÉNÉRATION DE MOT DE PASSE POSTGRESQL
# -----------------------------------------------------------------------------
# Génère un mot de passe aléatoire sécurisé pour PostgreSQL

resource "random_password" "postgres_admin_password" {
  length  = 32
  special = true
  # Caractères spéciaux compatibles avec PostgreSQL
  override_special = "!#$%&*()-_=+[]{}<>:?"
  min_lower        = 1
  min_upper        = 1
  min_numeric      = 1
  min_special      = 1
}

# -----------------------------------------------------------------------------
# 3. POSTGRESQL FLEXIBLE SERVER
# -----------------------------------------------------------------------------
# Base de données principale de l'application

resource "azurerm_postgresql_flexible_server" "main" {
  name                = "${local.resource_prefix}-postgres"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  
  # Authentification
  administrator_login    = var.postgres_admin_username
  administrator_password = random_password.postgres_admin_password.result
  
  # Version et SKU
  version = var.postgres_version
  sku_name = var.postgres_sku_name  # B_Standard_B1ms = 1 vCore, 2 GB RAM
  
  # Stockage
  storage_mb = var.postgres_storage_mb  # 32 GB
  
  # Backup et maintenance
  backup_retention_days = var.backup_retention_days
  geo_redundant_backup_enabled = false  # false pour économiser
  
  # Configuration SSL
  # SSL est obligatoire par défaut sur Azure PostgreSQL Flexible
  # Note : public_network_access est géré automatiquement via les firewall rules
  
  tags = local.common_tags

  lifecycle {
    # Empêche la recréation du serveur si le mot de passe change
    ignore_changes = [
      administrator_password,
      zone  # Evite les recréations inutiles
    ]
  }
}

# Configuration du firewall PostgreSQL - Autoriser les services Azure
resource "azurerm_postgresql_flexible_server_firewall_rule" "allow_azure_services" {
  name             = "AllowAzureServices"
  server_id        = azurerm_postgresql_flexible_server.main.id
  start_ip_address = "0.0.0.0"
  end_ip_address   = "0.0.0.0"
}

# Firewall rule pour ton IP locale (développement)
# Tu devras ajouter ton IP manuellement après le déploiement ou via variable
# resource "azurerm_postgresql_flexible_server_firewall_rule" "allow_my_ip" {
#   name             = "AllowMyIP"
#   server_id        = azurerm_postgresql_flexible_server.main.id
#   start_ip_address = "TonIP"
#   end_ip_address   = "TonIP"
# }

# -----------------------------------------------------------------------------
# 4. BASE DE DONNÉES POSTGRESQL
# -----------------------------------------------------------------------------
# Crée la base de données "datanova" dans le serveur PostgreSQL

resource "azurerm_postgresql_flexible_server_database" "main" {
  name      = var.project_name
  server_id = azurerm_postgresql_flexible_server.main.id
  collation = "en_US.utf8"
  charset   = "utf8"
}

# -----------------------------------------------------------------------------
# 5. AZURE CONTAINER REGISTRY (ACR)
# -----------------------------------------------------------------------------
# Registry privé pour stocker les images Docker

resource "azurerm_container_registry" "main" {
  name                = "${replace(local.resource_prefix, "-", "")}acr"  # Pas de tirets dans le nom ACR
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  sku                 = "Basic"  # Basic = 5 GB, ~5€/mois
  admin_enabled       = true     # Active les credentials admin pour Container Apps
  
  tags = local.common_tags
}

# -----------------------------------------------------------------------------
# 6. KEY VAULT - STOCKAGE DES SECRETS
# -----------------------------------------------------------------------------
# Coffre-fort pour stocker les API keys et mots de passe de manière sécurisée

data "azurerm_client_config" "current" {}

resource "azurerm_key_vault" "main" {
  name                = "${replace(local.resource_prefix, "-", "")}kv"  # Max 24 caractères
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  tenant_id           = data.azurerm_client_config.current.tenant_id
  
  sku_name = "standard"
  
  # Configuration de la purge (suppression définitive)
  soft_delete_retention_days = 7
  purge_protection_enabled   = false  # false pour permettre destruction complète en dev
  
  # Accès réseau
  public_network_access_enabled = true
  
  # Politique d'accès pour le compte qui exécute Terraform
  access_policy {
    tenant_id = data.azurerm_client_config.current.tenant_id
    object_id = data.azurerm_client_config.current.object_id
    
    secret_permissions = [
      "Get",
      "List",
      "Set",
      "Delete",
      "Recover",
      "Backup",
      "Restore",
      "Purge"
    ]
  }
  
  tags = local.common_tags
}

# -----------------------------------------------------------------------------
# 7. SECRETS DANS KEY VAULT
# -----------------------------------------------------------------------------

# Secret 1 : Mot de passe PostgreSQL
resource "azurerm_key_vault_secret" "postgres_password" {
  name         = "postgres-admin-password"
  value        = random_password.postgres_admin_password.result
  key_vault_id = azurerm_key_vault.main.id
  
  depends_on = [azurerm_key_vault.main]
}

# Secret 2 : Clé API Anthropic
resource "azurerm_key_vault_secret" "anthropic_api_key" {
  name         = "anthropic-api-key"
  value        = var.anthropic_api_key
  key_vault_id = azurerm_key_vault.main.id
  
  depends_on = [azurerm_key_vault.main]
}

# Secret 3 : Clé API Google
resource "azurerm_key_vault_secret" "google_api_key" {
  name         = "google-api-key"
  value        = var.google_api_key
  key_vault_id = azurerm_key_vault.main.id
  
  depends_on = [azurerm_key_vault.main]
}

# Secret 4 : URL de connexion PostgreSQL complète
resource "azurerm_key_vault_secret" "database_url" {
  name  = "database-url"
  value = "postgresql://${var.postgres_admin_username}:${random_password.postgres_admin_password.result}@${azurerm_postgresql_flexible_server.main.fqdn}:5432/${azurerm_postgresql_flexible_server_database.main.name}?sslmode=require"
  key_vault_id = azurerm_key_vault.main.id
  
  depends_on = [azurerm_key_vault.main]
}

# -----------------------------------------------------------------------------
# 8. CONTAINER APPS ENVIRONMENT
# -----------------------------------------------------------------------------
# Environnement qui héberge les Container Apps (comme un cluster Kubernetes simplifié)

resource "azurerm_log_analytics_workspace" "main" {
  name                = "${local.resource_prefix}-logs"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  sku                 = "PerGB2018"
  retention_in_days   = 30
  
  tags = local.common_tags
}

resource "azurerm_container_app_environment" "main" {
  name                = "${local.resource_prefix}-env"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  
  log_analytics_workspace_id = azurerm_log_analytics_workspace.main.id
  
  tags = local.common_tags
}

# -----------------------------------------------------------------------------
# 9. CONTAINER APP - BACKEND
# -----------------------------------------------------------------------------
# Application backend (FastAPI Python)

resource "azurerm_container_app" "backend" {
  name                         = "${local.resource_prefix}-backend"
  resource_group_name          = azurerm_resource_group.main.name
  container_app_environment_id = azurerm_container_app_environment.main.id
  revision_mode                = "Single"  # Une seule version active à la fois
  
  # Configuration des secrets (référencés depuis Key Vault)
  secret {
    name  = "database-url"
    value = azurerm_key_vault_secret.database_url.value
  }
  
  secret {
    name  = "anthropic-api-key"
    value = azurerm_key_vault_secret.anthropic_api_key.value
  }
  
  secret {
    name  = "google-api-key"
    value = azurerm_key_vault_secret.google_api_key.value
  }
  
  secret {
    name  = "registry-password"
    value = azurerm_container_registry.main.admin_password
  }
  
  # Configuration du registry
  registry {
    server               = azurerm_container_registry.main.login_server
    username             = azurerm_container_registry.main.admin_username
    password_secret_name = "registry-password"
  }
  
  # Template du container
  template {
    # Configuration de l'image Docker
    container {
      name   = "backend"
      image  = "${azurerm_container_registry.main.login_server}/datanova-backend:latest"
      cpu    = var.backend_cpu     # 0.5 vCore
      memory = var.backend_memory  # 1 GB
      
      # Variables d'environnement
      env {
        name        = "DATABASE_URL"
        secret_name = "database-url"
      }
      
      env {
        name        = "ANTHROPIC_API_KEY"
        secret_name = "anthropic-api-key"
      }
      
      env {
        name        = "GOOGLE_API_KEY"
        secret_name = "google-api-key"
      }
      
      env {
        name  = "ENVIRONMENT"
        value = var.environment
      }
    }
    
    # Autoscaling
    min_replicas = var.backend_min_replicas  # 1
    max_replicas = var.backend_max_replicas  # 3
  }
  
  # Configuration du réseau (ingress)
  ingress {
    external_enabled = true  # Accessible depuis Internet
    target_port      = 8000  # Port du backend FastAPI
    
    traffic_weight {
      latest_revision = true
      percentage      = 100
    }
  }
  
  tags = local.common_tags
  
  lifecycle {
    # Empêche la recréation si seule l'image change
    ignore_changes = [
      template[0].container[0].image
    ]
  }
}

# -----------------------------------------------------------------------------
# 10. STATIC WEB APP - FRONTEND
# -----------------------------------------------------------------------------
# Application frontend (React/Vite)

resource "azurerm_static_site" "frontend" {
  name                = "${local.resource_prefix}-frontend"
  resource_group_name = azurerm_resource_group.main.name
  location            = var.frontend_location  # Disponibilité limitée pour Static Web Apps
  sku_tier            = "Free"  # Free tier suffisant pour démarrer
  sku_size            = "Free"
  
  tags = local.common_tags
}

# -----------------------------------------------------------------------------
# 11. ROLE ASSIGNMENTS - ACCÈS ÉQUIPE (6 MEMBRES)
# -----------------------------------------------------------------------------
# Donne les accès "Contributor" aux membres de l'équipe

# Récupère les données Azure AD des membres de l'équipe
data "azuread_user" "team_members" {
  count               = length(var.team_members_emails)
  user_principal_name = var.team_members_emails[count.index]
}

# Assigne le rôle Contributor à chaque membre sur le Resource Group
resource "azurerm_role_assignment" "team_members" {
  count                = length(var.team_members_emails)
  scope                = azurerm_resource_group.main.id
  role_definition_name = var.team_role  # "Contributor"
  principal_id         = data.azuread_user.team_members[count.index].object_id
}

# Accès Key Vault pour les membres de l'équipe (lecture seule)
resource "azurerm_key_vault_access_policy" "team_members" {
  count        = length(var.team_members_emails)
  key_vault_id = azurerm_key_vault.main.id
  tenant_id    = data.azurerm_client_config.current.tenant_id
  object_id    = data.azuread_user.team_members[count.index].object_id
  
  secret_permissions = [
    "Get",
    "List"
  ]
}
