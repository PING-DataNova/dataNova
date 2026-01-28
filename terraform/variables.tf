
variable "project_name" {
  description = "Nom du projet (utilisé pour nommer toutes les ressources)"
  type        = string
  default     = "datanova"
  
  validation {
    condition     = can(regex("^[a-z0-9-]+$", var.project_name))
    error_message = "Le nom doit contenir uniquement des minuscules, chiffres et tirets"
  }
}

variable "environment" {
  description = "Environnement de déploiement"
  type        = string
  default     = "dev"
  
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "L'environnement doit être : dev, staging ou prod"
  }
}

variable "location" {
  description = "Région Azure pour le déploiement"
  type        = string
  default     = "westeurope"
}

variable "tags" {
  description = "Tags à appliquer à toutes les ressources"
  type        = map(string)
  default = {
    Project     = "DataNova"
    ManagedBy   = "Terraform"
    Environment = "dev"
  }
}

# -----------------------------------------------------------------------------
# ACCÈS ÉQUIPE - 6 MEMBRES
# -----------------------------------------------------------------------------

variable "team_members_emails" {
  description = "Liste des emails Azure AD des membres de l'équipe (6 personnes)"
  type        = list(string)
  default = [
    # À remplir avec les vrais emails de l'équipe
    # Exemple : "marc.junior@hutchinson.com",
    # Exemple : "membre2@hutchinson.com",
  ]
  
  validation {
    condition     = length(var.team_members_emails) <= 10
    error_message = "Maximum 10 membres dans l'équipe"
  }
}

variable "team_role" {
  description = "Rôle Azure RBAC pour les membres de l'équipe"
  type        = string
  default     = "Contributor"  # Permet de gérer toutes les ressources sauf les accès
  # Autres options : Owner (tout), Reader (lecture seule)
}

# -----------------------------------------------------------------------------
# BASE DE DONNÉES POSTGRESQL
# -----------------------------------------------------------------------------

variable "postgres_version" {
  description = "Version de PostgreSQL"
  type        = string
  default     = "16"
}

variable "postgres_sku_name" {
  description = "SKU PostgreSQL (taille de l'instance)"
  type        = string
  default     = "B_Standard_B1ms"  # Burstable, 1 vCore, 2 GB RAM (~25€/mois)
  # Options : 
  # - B_Standard_B1ms : Burstable, 1 vCore, 2 GB (~25€/mois) - Pour dev/test
  # - GP_Standard_D2s_v3 : General Purpose, 2 vCores, 8 GB (~200€/mois) - Pour prod
}

variable "postgres_storage_mb" {
  description = "Taille du stockage PostgreSQL en MB"
  type        = number
  default     = 32768  # 32 GB
}

variable "postgres_admin_username" {
  description = "Nom d'utilisateur admin PostgreSQL"
  type        = string
  default     = "pgadmin"
}

# -----------------------------------------------------------------------------
# CONTAINER APPS (BACKEND)
# -----------------------------------------------------------------------------

variable "backend_cpu" {
  description = "CPU alloués au container backend (en cores)"
  type        = number
  default     = 0.5  # 0.5 vCore
}

variable "backend_memory" {
  description = "Mémoire allouée au container backend (en GB)"
  type        = string
  default     = "1Gi"  # 1 GB
}

variable "backend_min_replicas" {
  description = "Nombre minimum de réplicas du backend"
  type        = number
  default     = 1
}

variable "backend_max_replicas" {
  description = "Nombre maximum de réplicas du backend"
  type        = number
  default     = 3
}

# -----------------------------------------------------------------------------
# SECRETS & API KEYS
# -----------------------------------------------------------------------------

variable "anthropic_api_key" {
  description = "Clé API Anthropic Claude (Agent 1B)"
  type        = string
  sensitive   = true  # Masqué dans les logs Terraform
  
  validation {
    condition     = can(regex("^sk-ant-", var.anthropic_api_key)) || var.anthropic_api_key == ""
    error_message = "La clé API Anthropic doit commencer par 'sk-ant-'"
  }
}

variable "google_api_key" {
  description = "Clé API Google Gemini (Agent 2)"
  type        = string
  sensitive   = true
}

# -----------------------------------------------------------------------------
# CONFIGURATION FRONTEND
# -----------------------------------------------------------------------------

variable "frontend_location" {
  description = "Région pour Static Web App (doit être différente selon disponibilité)"
  type        = string
  default     = "westeurope"
}

# -----------------------------------------------------------------------------
# OPTIONS AVANCÉES
# -----------------------------------------------------------------------------

variable "enable_public_network_access" {
  description = "Autoriser l'accès public à PostgreSQL (false = plus sécurisé mais plus complexe)"
  type        = bool
  default     = true  # true pour simplicité, false pour prod avec VNet
}

variable "backup_retention_days" {
  description = "Nombre de jours de rétention des backups PostgreSQL"
  type        = number
  default     = 7
}

variable "enable_container_app_logs" {
  description = "Activer les logs détaillés pour Container Apps"
  type        = bool
  default     = true
}
