"""
Dashboard de métriques pour le LLM Judge

Permet de visualiser et analyser les performances du Judge
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
from pathlib import Path
import json
from collections import defaultdict

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box
from rich.text import Text


console = Console()


class JudgeMetricsDashboard:
    """
    Dashboard des performances du Judge avec visualisation Rich
    """
    
    def __init__(self, results_dir: Optional[Path] = None):
        """
        Initialise le dashboard
        
        Args:
            results_dir: Répertoire contenant les résultats d'évaluation (JSON)
        """
        self.results_dir = results_dir or Path(__file__).parent
        self.evaluations: List[Dict[str, Any]] = []
        self.load_evaluations()
    
    def load_evaluations(self):
        """Charge tous les résultats d'évaluation disponibles"""
        # Charger judge_result.json s'il existe
        result_file = self.results_dir / "judge_result.json"
        if result_file.exists():
            with open(result_file, 'r', encoding='utf-8') as f:
                result = json.load(f)
                self.evaluations.append(result)
        
        # Charger d'autres fichiers de résultats (pattern: judge_result_*.json)
        for result_file in self.results_dir.glob("judge_result_*.json"):
            with open(result_file, 'r', encoding='utf-8') as f:
                result = json.load(f)
                self.evaluations.append(result)
    
    def show_metrics(self):
        """Affiche les métriques clés (interface simple)"""
        if not self.evaluations:
            print("⚠️  Aucune évaluation trouvée")
            return
        
        total = len(self.evaluations)
        avg_score = sum(e['judge_evaluation']['overall_quality_score'] for e in self.evaluations) / total
        avg_confidence = sum(e['judge_evaluation']['overall_confidence'] for e in self.evaluations) / total
        
        print("📊 MÉTRIQUES JUDGE")
        print(f"   Évaluations: {total}")
        print(f"   Score moyen: {avg_score:.2f}/10")
        print(f"   Confiance moyenne: {avg_confidence:.1%}")
        
        # Décisions
        decisions = defaultdict(int)
        for e in self.evaluations:
            decisions[e['judge_evaluation']['action_recommended']] += 1
        
        for decision, count in decisions.items():
            print(f"   {decision}: {count} ({count/total*100:.1f}%)")
    
    def display_full_dashboard(self):
        """Affiche le dashboard complet avec Rich"""
        console.clear()
        console.print("\n")
        console.print("=" * 100, style="bold cyan")
        console.print("📊 DASHBOARD MÉTRIQUES LLM JUDGE", style="bold cyan", justify="center")
        console.print("=" * 100, style="bold cyan")
        console.print("\n")
        
        if not self.evaluations:
            console.print("⚠️  Aucune évaluation trouvée", style="yellow")
            console.print(f"   Recherche dans: {self.results_dir}")
            return
        
        # 1. Vue d'ensemble
        self._display_overview()
        
        # 2. Scores par critère
        self._display_criteria_scores()
        
        # 3. Décisions
        self._display_decisions_summary()
        
        # 4. Performance par type d'événement
        self._display_event_type_performance()
        
        # 5. Timeline des évaluations
        self._display_timeline()
        
        console.print("\n" + "=" * 100, style="bold cyan")
    
    def _display_overview(self):
        """Affiche la vue d'ensemble"""
        total = len(self.evaluations)
        
        # Calculer les statistiques globales
        avg_overall_score = sum(
            e['judge_evaluation']['overall_quality_score'] 
            for e in self.evaluations
        ) / total if total > 0 else 0
        
        avg_confidence = sum(
            e['judge_evaluation']['overall_confidence'] 
            for e in self.evaluations
        ) / total if total > 0 else 0
        
        # Créer le tableau de vue d'ensemble
        table = Table(title="📈 Vue d'Ensemble", box=box.ROUNDED, show_header=True)
        table.add_column("Métrique", style="cyan", width=30)
        table.add_column("Valeur", style="bold green", justify="right", width=20)
        
        table.add_row("Nombre d'évaluations", str(total))
        table.add_row("Score moyen global", f"{avg_overall_score:.2f}/10")
        table.add_row("Confiance moyenne", f"{avg_confidence:.2%}")
        
        # Score Pertinence Checker moyen
        avg_pertinence = sum(
            e['judge_evaluation']['pertinence_checker_evaluation']['weighted_score']
            for e in self.evaluations
        ) / total if total > 0 else 0
        
        # Score Risk Analyzer moyen
        avg_risk = sum(
            e['judge_evaluation']['risk_analyzer_evaluation']['weighted_score']
            for e in self.evaluations
        ) / total if total > 0 else 0
        
        table.add_row("Score Pertinence Checker", f"{avg_pertinence:.2f}/10")
        table.add_row("Score Risk Analyzer", f"{avg_risk:.2f}/10")
        
        console.print(table)
        console.print("\n")
    
    def _display_criteria_scores(self):
        """Affiche les scores détaillés par critère"""
        if not self.evaluations:
            return
        
        # Extraire tous les critères
        criteria_scores = defaultdict(list)
        
        for eval_result in self.evaluations:
            # Pertinence Checker
            pc_eval = eval_result['judge_evaluation']['pertinence_checker_evaluation']
            for criterion, data in pc_eval.items():
                if isinstance(data, dict) and 'score' in data:
                    criteria_scores[f"PC: {criterion}"].append(data['score'])
            
            # Risk Analyzer
            ra_eval = eval_result['judge_evaluation']['risk_analyzer_evaluation']
            for criterion, data in ra_eval.items():
                if isinstance(data, dict) and 'score' in data:
                    criteria_scores[f"RA: {criterion}"].append(data['score'])
        
        # Créer le tableau
        table = Table(title="📊 Scores par Critère", box=box.ROUNDED, show_header=True)
        table.add_column("Critère", style="cyan", width=40)
        table.add_column("Moyenne", style="yellow", justify="right", width=10)
        table.add_column("Min", style="red", justify="right", width=8)
        table.add_column("Max", style="green", justify="right", width=8)
        table.add_column("Barre", width=30)
        
        # Trier par moyenne décroissante
        sorted_criteria = sorted(
            criteria_scores.items(),
            key=lambda x: sum(x[1]) / len(x[1]),
            reverse=True
        )
        
        for criterion, scores in sorted_criteria:
            avg = sum(scores) / len(scores)
            min_score = min(scores)
            max_score = max(scores)
            
            # Barre de progression
            bar_length = int((avg / 10) * 20)
            bar = "█" * bar_length + "░" * (20 - bar_length)
            
            # Couleur selon le score
            if avg >= 8:
                bar_color = "green"
            elif avg >= 6:
                bar_color = "yellow"
            else:
                bar_color = "red"
            
            table.add_row(
                criterion.replace("_", " ").title(),
                f"{avg:.1f}",
                f"{min_score}",
                f"{max_score}",
                Text(bar, style=bar_color)
            )
        
        console.print(table)
        console.print("\n")
    
    def _display_decisions_summary(self):
        """Affiche le résumé des décisions"""
        decisions = defaultdict(int)
        
        for eval_result in self.evaluations:
            action = eval_result['judge_evaluation']['action_recommended']
            decisions[action] += 1
        
        total = len(self.evaluations)
        
        # Créer le tableau
        table = Table(title="🚦 Répartition des Décisions", box=box.ROUNDED, show_header=True)
        table.add_column("Décision", style="cyan", width=20)
        table.add_column("Nombre", style="yellow", justify="right", width=10)
        table.add_column("Pourcentage", style="green", justify="right", width=15)
        table.add_column("Barre", width=40)
        
        # Ordre de priorité
        decision_order = ["APPROVE", "REVIEW", "REVIEW_PRIORITY", "REJECT"]
        decision_colors = {
            "APPROVE": "green",
            "REVIEW": "yellow",
            "REVIEW_PRIORITY": "orange3",
            "REJECT": "red"
        }
        
        for decision in decision_order:
            count = decisions.get(decision, 0)
            percentage = (count / total * 100) if total > 0 else 0
            
            # Barre de progression
            bar_length = int((count / total) * 30) if total > 0 else 0
            bar = "█" * bar_length + "░" * (30 - bar_length)
            
            table.add_row(
                decision,
                str(count),
                f"{percentage:.1f}%",
                Text(bar, style=decision_colors.get(decision, "white"))
            )
        
        console.print(table)
        console.print("\n")
    
    def _display_event_type_performance(self):
        """Affiche les performances par type d'événement"""
        event_stats = defaultdict(lambda: {"scores": [], "decisions": defaultdict(int)})
        
        for eval_result in self.evaluations:
            event_type = eval_result.get('event_type', 'unknown')
            score = eval_result['judge_evaluation']['overall_quality_score']
            decision = eval_result['judge_evaluation']['action_recommended']
            
            event_stats[event_type]["scores"].append(score)
            event_stats[event_type]["decisions"][decision] += 1
        
        # Créer le tableau
        table = Table(title="🌍 Performance par Type d'Événement", box=box.ROUNDED, show_header=True)
        table.add_column("Type", style="cyan", width=20)
        table.add_column("Évaluations", style="yellow", justify="right", width=12)
        table.add_column("Score Moyen", style="green", justify="right", width=15)
        table.add_column("Décision Dominante", style="magenta", width=20)
        
        for event_type, stats in event_stats.items():
            count = len(stats["scores"])
            avg_score = sum(stats["scores"]) / count if count > 0 else 0
            
            # Décision la plus fréquente
            dominant_decision = max(stats["decisions"].items(), key=lambda x: x[1])[0] if stats["decisions"] else "N/A"
            
            table.add_row(
                event_type.capitalize(),
                str(count),
                f"{avg_score:.2f}/10",
                dominant_decision
            )
        
        console.print(table)
        console.print("\n")
    
    def _display_timeline(self):
        """Affiche la timeline des évaluations"""
        if not self.evaluations:
            return
        
        # Créer le tableau
        table = Table(title="⏰ Timeline des Évaluations", box=box.ROUNDED, show_header=True)
        table.add_column("Date", style="cyan", width=25)
        table.add_column("Event ID", style="yellow", width=25)
        table.add_column("Type", style="magenta", width=15)
        table.add_column("Score", style="green", justify="right", width=10)
        table.add_column("Décision", style="bold", width=15)
        
        # Trier par timestamp
        sorted_evals = sorted(
            self.evaluations,
            key=lambda x: x['judge_evaluation']['metadata'].get('evaluation_timestamp', ''),
            reverse=True
        )
        
        for eval_result in sorted_evals[:10]:  # Afficher les 10 derniers
            timestamp = eval_result['judge_evaluation']['metadata'].get('evaluation_timestamp', 'N/A')
            event_id = eval_result.get('event_id', 'unknown')[:20]
            event_type = eval_result.get('event_type', 'unknown')
            score = eval_result['judge_evaluation']['overall_quality_score']
            decision = eval_result['judge_evaluation']['action_recommended']
            
            # Couleur de la décision
            decision_colors = {
                "APPROVE": "green",
                "REVIEW": "yellow",
                "REVIEW_PRIORITY": "orange3",
                "REJECT": "red"
            }
            
            table.add_row(
                timestamp[:19] if timestamp != 'N/A' else 'N/A',
                event_id,
                event_type,
                f"{score:.2f}",
                Text(decision, style=decision_colors.get(decision, "white"))
            )
        
        console.print(table)
        console.print("\n")
    
    def export_metrics(self, output_file: Path):
        """
        Exporte les métriques au format JSON
        
        Args:
            output_file: Fichier de sortie
        """
        metrics = {
            "export_timestamp": datetime.now(timezone.utc).isoformat(),
            "total_evaluations": len(self.evaluations),
            "overview": self._compute_overview_metrics(),
            "criteria_scores": self._compute_criteria_metrics(),
            "decisions": self._compute_decision_metrics(),
            "event_types": self._compute_event_type_metrics()
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(metrics, f, indent=2, ensure_ascii=False)
        
        console.print(f"✅ Métriques exportées vers: {output_file}", style="green")
    
    def _compute_overview_metrics(self) -> Dict:
        """Calcule les métriques de vue d'ensemble"""
        if not self.evaluations:
            return {}
        
        total = len(self.evaluations)
        
        return {
            "avg_overall_score": sum(e['judge_evaluation']['overall_quality_score'] for e in self.evaluations) / total,
            "avg_confidence": sum(e['judge_evaluation']['overall_confidence'] for e in self.evaluations) / total,
            "avg_pertinence_score": sum(e['judge_evaluation']['pertinence_checker_evaluation']['weighted_score'] for e in self.evaluations) / total,
            "avg_risk_score": sum(e['judge_evaluation']['risk_analyzer_evaluation']['weighted_score'] for e in self.evaluations) / total
        }
    
    def _compute_criteria_metrics(self) -> Dict:
        """Calcule les métriques par critère"""
        criteria_scores = defaultdict(list)
        
        for eval_result in self.evaluations:
            pc_eval = eval_result['judge_evaluation']['pertinence_checker_evaluation']
            for criterion, data in pc_eval.items():
                if isinstance(data, dict) and 'score' in data:
                    criteria_scores[f"pertinence_{criterion}"].append(data['score'])
            
            ra_eval = eval_result['judge_evaluation']['risk_analyzer_evaluation']
            for criterion, data in ra_eval.items():
                if isinstance(data, dict) and 'score' in data:
                    criteria_scores[f"risk_{criterion}"].append(data['score'])
        
        return {
            criterion: {
                "average": sum(scores) / len(scores),
                "min": min(scores),
                "max": max(scores),
                "count": len(scores)
            }
            for criterion, scores in criteria_scores.items()
        }
    
    def _compute_decision_metrics(self) -> Dict:
        """Calcule les métriques de décision"""
        decisions = defaultdict(int)
        
        for eval_result in self.evaluations:
            action = eval_result['judge_evaluation']['action_recommended']
            decisions[action] += 1
        
        total = len(self.evaluations)
        
        return {
            decision: {
                "count": count,
                "percentage": (count / total * 100) if total > 0 else 0
            }
            for decision, count in decisions.items()
        }
    
    def _compute_event_type_metrics(self) -> Dict:
        """Calcule les métriques par type d'événement"""
        event_stats = defaultdict(lambda: {"scores": [], "decisions": defaultdict(int)})
        
        for eval_result in self.evaluations:
            event_type = eval_result.get('event_type', 'unknown')
            score = eval_result['judge_evaluation']['overall_quality_score']
            decision = eval_result['judge_evaluation']['action_recommended']
            
            event_stats[event_type]["scores"].append(score)
            event_stats[event_type]["decisions"][decision] += 1
        
        return {
            event_type: {
                "count": len(stats["scores"]),
                "avg_score": sum(stats["scores"]) / len(stats["scores"]) if stats["scores"] else 0,
                "decisions": dict(stats["decisions"])
            }
            for event_type, stats in event_stats.items()
        }


def main():
    """Point d'entrée principal pour afficher le dashboard"""
    dashboard = JudgeMetricsDashboard()
    dashboard.display_full_dashboard()
    
    # Exporter les métriques
    output_file = Path(__file__).parent / "judge_metrics_export.json"
    dashboard.export_metrics(output_file)


if __name__ == "__main__":
    main()