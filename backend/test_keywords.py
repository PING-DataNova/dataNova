#!/usr/bin/env python3
"""Test script pour voir les mots-clés extraits."""

from src.agent_1a.tools.keyword_extractor import extract_keywords_from_profile, get_default_profile_path

profile_path = get_default_profile_path()
print(f"📁 Profil: {profile_path}")

kw = extract_keywords_from_profile(profile_path)
if kw:
    print(f"\n🏢 Entreprise: {kw.company_name}")
    print(f"\n📊 MOTS-CLÉS EXTRAITS:")
    print(f"   • Codes NC: {len(kw.nc_codes)} → {kw.nc_codes}")
    print(f"   • Matériaux: {len(kw.materials)} → {kw.materials}")
    print(f"   • Pays: {len(kw.countries)} → {kw.countries}")
    print(f"   • Secteurs: {len(kw.sectors)} → {kw.sectors}")
    print(f"   • Produits: {len(kw.products)} → {kw.products}")
    print(f"   • Termes commerce: {len(kw.trade_terms)} → {kw.trade_terms}")
    print(f"\n📈 TOTAL UNIQUE: {len(kw.get_all_keywords())} mots-clés")
    print(f"\n🔑 Liste complète: {kw.get_all_keywords()}")
else:
    print("❌ Erreur: profil non trouvé")
