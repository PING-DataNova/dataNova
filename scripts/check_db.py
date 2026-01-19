import sqlite3
import json

conn = sqlite3.connect('data/datanova.db')
cursor = conn.cursor()

cursor.execute('SELECT * FROM company_profiles')
row = cursor.fetchone()

if row:
    print('✅ Données trouvées dans company_profiles!')
    print('=' * 60)
    columns = [desc[0] for desc in cursor.description]
    
    for i, col in enumerate(columns):
        value = row[i]
        if isinstance(value, str) and (value.startswith('[') or value.startswith('{')):
            try:
                parsed = json.loads(value)
                if isinstance(parsed, list):
                    print(f'\n{col}: {len(parsed)} éléments')
                    if len(parsed) <= 10:
                        for item in parsed:
                            print(f'  - {item}')
                    else:
                        for item in parsed[:5]:
                            print(f'  - {item}')
                        print(f'  ... et {len(parsed)-5} autres')
                else:
                    print(f'\n{col}: (objet JSON)')
            except:
                print(f'\n{col}: {str(value)[:100]}')
        else:
            print(f'\n{col}: {value}')
else:
    print('❌ Aucune donnée trouvée')

conn.close()
