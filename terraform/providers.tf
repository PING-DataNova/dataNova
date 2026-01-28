# =============================================================================
# TERRAFORM PROVIDERS CONFIGURATION
# =============================================================================
# Ce fichier configure les providers nécessaires pour déployer sur Azure.
# Un "provider" est un plugin qui permet à Terraform de communiquer avec 
# l'API d'un cloud provider (ici Azure).
# =============================================================================

terraform {
  required_version = ">= 1.5.0"

  # Providers requis avec leurs versions
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.85.0"  # Version 3.85.x (compatible avec les dernières features)
    }

    # Provider Random - pour générer des valeurs aléatoires (mots de passe, suffixes)
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6.0"
    }
  }
}

# Configuration du provider Azure
provider "azurerm" {
  # Désactive l'enregistrement automatique des Resource Providers
  # Nécessaire pour les comptes avec permissions limitées (étudiants, etc.)
  skip_provider_registration = true
  
  features {
    # Configuration pour la suppression des Key Vaults
    key_vault {
      # Permet de purger définitivement les Key Vaults supprimés
      purge_soft_delete_on_destroy    = true
      # Récupère les Key Vaults supprimés au lieu d'échouer
      recover_soft_deleted_key_vaults = true
    }

    # Configuration pour les Resource Groups
    resource_group {
      # Empêche la suppression d'un RG qui contient encore des ressources
      prevent_deletion_if_contains_resources = false
    }
  }
}

provider "random" {}
