#!/usr/bin/env python3
"""
Script para aplicar todos los cambios de PR002 al archivo leadsales_service.py
"""
import re

# Leer el archivo original
with open('app/services/leadsales_service.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Agregar imports después de la línea 7
imports_to_add = """from app.services.scoring.strategies import (
    DemoQualityScorer,
    InterestLevelScorer,
    TransactionTypeTagger,
    PropertyTypeTagger,
    UrgencyTagger,
    MetadataTagger,
    UrgencyPriorityClassifier
)
"""

# Insertar imports después de "from app.config import settings"
content = content.replace(
    'from app.config import settings\n',
    f'from app.config import settings\n{imports_to_add}\n'
)

# 2. Modificar __init__ para agregar _init_scoring_components()
init_pattern = r'(def __init__\(self\):\s+self\.client = LeadsalesClient\(\)\s+self\.initialized = False)'
init_replacement = r'\1\n\n        # ✅ NUEVO: Inicializar scorers\n        self._init_scoring_components()'

content = re.sub(init_pattern, init_replacement, content)

# 3. Agregar método _init_scoring_components después de initialize()
init_scoring_method = '''
    def _init_scoring_components(self):
        """Inicializa scorers, taggers y classifier del sistema refactorizado"""
        # Scorers
        self.quality_scorer = DemoQualityScorer()
        self.interest_scorer = InterestLevelScorer()

        # Taggers
        self.taggers = [
            TransactionTypeTagger(),
            PropertyTypeTagger(),
            UrgencyTagger(),
            MetadataTagger()
        ]

        # Classifier
        self.priority_classifier = UrgencyPriorityClassifier()

        print(f"[LeadsalesService] Scoring components initialized: "
              f"1 quality_scorer, {len(self.taggers)} taggers, 1 priority_classifier")
'''

# Insertar después del método initialize()
content = re.sub(
    r'(except Exception as e:\s+print\(f"\[LeadsalesService\] Error inicializando: \{e\}"\)\s+return False)',
    r'\1' + init_scoring_method,
    content
)

# 4. Agregar método _score_lead
score_lead_method = '''
    def _score_lead(self, customer_needs: str, additional_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calcula scoring usando estrategias refactorizadas"""
        lead_data = {
            "customer_needs": customer_needs,
            "additional_data": additional_data or {}
        }

        # Quality Score
        quality_result = self.quality_scorer.score(lead_data)

        # Tags (agregar todos los taggers)
        all_tags = []
        for tagger in self.taggers:
            all_tags.extend(tagger.generate_tags(lead_data))

        # Eliminar duplicados manteniendo orden y limitar a 5
        unique_tags = list(dict.fromkeys(all_tags))[:5]

        # Priority Classification
        priority = self.priority_classifier.classify(lead_data)

        result = {
            "quality_score": int(quality_result.score),
            "tags": unique_tags,
            "priority": priority,
            "scoring_metadata": {
                "quality_confidence": quality_result.confidence,
                "quality_factors": quality_result.factors,
                "quality_reasoning": quality_result.reasoning
            }
        }

        # Log del scoring realizado
        priority_short = priority.split(' - ')[0] if ' - ' in priority else priority
        print(f"[LeadsalesService] Lead scored: quality={result['quality_score']}, "
              f"tags={len(result['tags'])}, priority={priority_short}")

        return result
'''

# Insertar _score_lead después de _init_scoring_components
content = re.sub(
    r'(f"1 quality_scorer, \{len\(self\.taggers\)\} taggers, 1 priority_classifier"\))',
    r'\1' + score_lead_method,
    content
)

# 5. Modificar create_lead para agregar scoring antes del check de demo mode
create_lead_scoring = '''
        # Calcular scoring (funciona en demo Y producción)
        scoring_result = self._score_lead(customer_needs, additional_data or {})

'''

content = re.sub(
    r'(def create_lead\([^)]+\) -> Dict\[str, Any\]:\s+"""[^"]+"""\s+if not self\.initialized:)',
    lambda m: m.group(0),
    content
)

# Insertar scoring_result antes de "# DEMO MODE DETECTION"
content = content.replace(
    '        # DEMO MODE DETECTION',
    f'{create_lead_scoring}        # DEMO MODE DETECTION'
)

# 6. Modificar el lead_data en create_lead para usar scoring_result
content = re.sub(
    r'"priority": "normal"',
    r'"priority": scoring_result["priority"]',
    content
)

# Agregar nuevos campos después de priority
content = re.sub(
    r'("priority": scoring_result\["priority"\],)',
    r'\1\n            "quality_score": scoring_result["quality_score"],\n            "tags": scoring_result["tags"],',
    content
)

# 7. Modificar _create_mock_lead para usar scoring
# Agregar scoring_result al inicio del método
content = re.sub(
    r'(def _create_mock_lead[^:]+:[^{]+\{[^}]+\})\s+(enriched_metadata =)',
    r'\1\n\n        # Calcular scoring usando sistema refactorizado\n        scoring_result = self._score_lead(customer_needs, additional_data or {})\n\n        \2',
    content
)

# Reemplazar los campos en customer_data
content = re.sub(
    r'"quality_score": self\._calculate_demo_quality_score\([^)]+\)',
    r'"quality_score": scoring_result["quality_score"]',
    content
)

content = re.sub(
    r'"tags": self\._generate_demo_tags\([^)]+\)',
    r'"tags": scoring_result["tags"]',
    content
)

content = re.sub(
    r'"priority": self\._determine_demo_priority\([^)]+\)',
    r'"priority": scoring_result["priority"]',
    content
)

# Agregar scoring_metadata
content = re.sub(
    r'(\*\*enriched_metadata)',
    r'\1,\n                **scoring_result["scoring_metadata"]  # ✅ Metadata adicional',
    content
)

# 8. Eliminar los 3 métodos duplicados
# Patrón para _calculate_demo_quality_score
content = re.sub(
    r'    def _calculate_demo_quality_score\(self[^:]+:[^}]+\}[^}]+return total_score\n',
    '',
    content,
    flags=re.DOTALL
)

# Patrón para _generate_demo_tags
content = re.sub(
    r'    def _generate_demo_tags\(self[^:]+:[^}]+return tags\n',
    '',
    content,
    flags=re.DOTALL
)

# Patrón para _determine_demo_priority
content = re.sub(
    r'    def _determine_demo_priority\(self[^:]+:[^}]+return "[^"]+"\n',
    '',
    content,
    flags=re.DOTALL
)

# Guardar el archivo modificado
with open('app/services/leadsales_service.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ PR002 aplicado exitosamente a leadsales_service.py")
print("Cambios realizados:")
print("  - Imports agregados")
print("  - __init__ modificado")
print("  - _init_scoring_components() creado")
print("  - _score_lead() creado")
print("  - create_lead() modificado para scoring en producción")
print("  - _create_mock_lead() modificado para scoring en demo")
print("  - 3 métodos duplicados eliminados")
