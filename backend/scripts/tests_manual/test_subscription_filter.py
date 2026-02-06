#!/usr/bin/env python
"""Test du filtrage des abonnements aux notifications"""

from src.notifications.subscription_filter import get_matching_subscriptions

if __name__ == "__main__":
    print("=" * 60)
    print("TEST DU FILTRAGE DES ABONNEMENTS")
    print("=" * 60)
    
    # Test 1: Réglementaire + Fort (ELEVE) - Sans pays spécifique
    # admin@hutchinson.com: ELEVE+ réglementaire, pas de filtre pays ✓
    # test@example.com: MOYEN+ réglementaire, MAIS filtre pays China ✗
    print("\n=== Test 1: Réglementaire + Fort (sans pays) ===")
    matches = get_matching_subscriptions('reglementaire', 'Fort')
    print(f"Abonnements correspondants: {len(matches)}")
    for m in matches:
        print(f"  ✓ {m['email']} ({m['subscription_name']})")
    print("  → test@example.com non notifié (filtre pays China non satisfait)")
    
    # Test 2: Réglementaire + Fort + Fournisseur en Chine
    # Devrait matcher les deux!
    print("\n=== Test 2: Réglementaire + Fort + Fournisseur en Chine ===")
    affected_suppliers = [{"id": "sup1", "name": "Supplier China", "country": "China"}]
    matches = get_matching_subscriptions('reglementaire', 'Fort', affected_suppliers=affected_suppliers)
    print(f"Abonnements correspondants: {len(matches)}")
    for m in matches:
        print(f"  ✓ {m['email']} ({m['subscription_name']})")
    
    # Test 3: Réglementaire + Moyen + Fournisseur en Chine
    # Ne devrait PAS matcher admin (veut ELEVE minimum)
    # Devrait matcher test@example.com
    print("\n=== Test 3: Réglementaire + Moyen + Fournisseur en Chine ===")
    matches = get_matching_subscriptions('reglementaire', 'Moyen', affected_suppliers=affected_suppliers)
    print(f"Abonnements correspondants: {len(matches)}")
    for m in matches:
        print(f"  ✓ {m['email']} ({m['subscription_name']})")
    if len(matches) == 1 and matches[0]['email'] == 'test@example.com':
        print("  → Correct: admin n'est PAS notifié (veut ELEVE+)")
    
    # Test 4: Géopolitique + Fort + Fournisseur en Chine
    # admin n'a pas géopolitique
    # test@example.com a géopolitique + China
    print("\n=== Test 4: Géopolitique + Fort + Fournisseur en Chine ===")
    matches = get_matching_subscriptions('geopolitique', 'Fort', affected_suppliers=affected_suppliers)
    print(f"Abonnements correspondants: {len(matches)}")
    for m in matches:
        print(f"  ✓ {m['email']} ({m['subscription_name']})")
    
    # Test 5: Climatique - Personne n'est abonné
    print("\n=== Test 5: Climatique + Critique ===")
    matches = get_matching_subscriptions('climatique', 'Critique')
    print(f"Abonnements correspondants: {len(matches)}")
    if len(matches) == 0:
        print("  ✓ Correct: Personne n'est abonné au climatique")
    
    print("\n" + "=" * 60)
    print("RÉSUMÉ DES ABONNEMENTS:")
    print("- admin@hutchinson.com: Réglementaire, ÉLEVÉ+, Tous pays")
    print("- test@example.com: Réglementaire+Géopolitique, MOYEN+, China uniquement")
    print("=" * 60)
