"""
Review Report Generator for PPTPlaner

Tracks each phase's review comments, evaluation scores, and processing details.
Generates a readable markdown report alongside the raw research logs.

Usage:
    from scripts.review_report import ReviewReport
    
    report = ReviewReport(output_dir)
    report.start_phase("Analysis")
    report.add_review("Content Quality", 8, "Good coverage of key topics")
    report.complete_phase()
    report.save_report()
"""
import json
from pathlib import Path
from datetime import datetime
from typing import Optional


class PhaseReview:
    """Represents a single phase's review data."""
    
    def __init__(self, phase_name: str):
        self.phase_name = phase_name
        self.start_time = datetime.now()
        self.end_time: Optional[datetime] = None
        self.reviews = []  # List of {criteria, score, comment}
        self.processing_summary = []  # High-level actions taken
        self.detailed_steps = []  # Detailed step-by-step actions
    
    def add_review(self, criteria: str, score: int, comment: str, max_score: int = 10):
        """Add a review evaluation for this phase."""
        self.reviews.append({
            "criteria": criteria,
            "score": score,
            "max_score": max_score,
            "comment": comment,
            "percentage": round(score / max_score * 100, 1)
        })
    
    def add_processing_step(self, step: str, detail: str = ""):
        """Add a processing step description."""
        self.processing_summary.append(step)
        if detail:
            self.detailed_steps.append({
                "step": step,
                "detail": detail,
                "timestamp": datetime.now().strftime("%H:%M:%S")
            })
    
    def complete(self):
        """Mark phase as complete."""
        self.end_time = datetime.now()
    
    @property
    def duration(self) -> str:
        """Get human-readable duration."""
        if not self.end_time:
            return "Running..."
        delta = self.end_time - self.start_time
        total_seconds = int(delta.total_seconds())
        minutes, seconds = divmod(total_seconds, 60)
        return f"{minutes}m {seconds}s"
    
    @property
    def average_score(self) -> float:
        """Calculate average review score."""
        if not self.reviews:
            return 0
        return round(sum(r["score"] / r["max_score"] * 100 for r in self.reviews) / len(self.reviews), 1)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "phase_name": self.phase_name,
            "start_time": self.start_time.strftime("%Y-%m-%d %H:%M:%S"),
            "end_time": self.end_time.strftime("%Y-%m-%d %H:%M:%S") if self.end_time else None,
            "duration": self.duration,
            "average_score": self.average_score,
            "reviews": self.reviews,
            "processing_steps": self.processing_summary,
            "detailed_steps": self.detailed_steps
        }


class ReviewReport:
    """
    Generates a comprehensive review report for the entire generation process.
    
    Tracks:
    - Phase-by-phase evaluation
    - Quality scores for each phase
    - Detailed review comments
    - Processing timeline
    """
    
    def __init__(self, output_dir: Path, source_file: str = ""):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.source_file = source_file
        self.start_time = datetime.now()
        self.end_time: Optional[datetime] = None
        self.phases: list[PhaseReview] = []
        self.current_phase: Optional[PhaseReview] = None
        
        # Report file paths
        self.report_file = self.output_dir / "REVIEW_REPORT.md"
        self.report_json = self.output_dir / "review_report.json"
    
    def start_phase(self, phase_name: str):
        """Start tracking a new phase."""
        if self.current_phase:
            self.current_phase.complete()
        
        self.current_phase = PhaseReview(phase_name)
        self.phases.append(self.current_phase)
        
        # Print to console
        print(f"  📊 [Review] Starting phase: {phase_name}", flush=True)
    
    def add_review(self, criteria: str, score: int, comment: str, max_score: int = 10):
        """Add a quality review to the current phase."""
        if self.current_phase:
            self.current_phase.add_review(criteria, score, comment, max_score)
            print(f"  ⭐ [Review] {criteria}: {score}/{max_score} - {comment}", flush=True)
    
    def add_step(self, step: str, detail: str = ""):
        """Add a processing step to the current phase."""
        if self.current_phase:
            self.current_phase.add_processing_step(step, detail)
    
    def complete_phase(self):
        """Mark current phase as complete."""
        if self.current_phase:
            self.current_phase.complete()
            print(f"  ✅ [Review] Phase '{self.current_phase.phase_name}' completed ({self.current_phase.duration})",
                  flush=True)
    
    def save_report(self):
        """Save the review report in both Markdown and JSON formats."""
        self.end_time = datetime.now()
        
        # Generate Markdown report
        self._save_markdown()
        
        # Generate JSON report (for programmatic access)
        self._save_json()
        
        # Print summary
        self._print_summary()
    
    def _save_markdown(self):
        """Generate and save Markdown report."""
        lines = []
        lines.append("# 📊 PPTPlaner 品質檢核報告")
        lines.append("")
        lines.append(f"**來源檔案**: {self.source_file}")
        lines.append(f"**開始時間**: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"**結束時間**: {self.end_time.strftime('%Y-%m-%d %H:%M:%S') if self.end_time else '進行中'}")
        lines.append("")
        
        # Calculate total duration
        if self.end_time:
            total_delta = self.end_time - self.start_time
            total_seconds = int(total_delta.total_seconds())
            minutes, seconds = divmod(total_seconds, 60)
            lines.append(f"**總耗時**: {minutes}分 {seconds}秒")
        lines.append("")
        
        # Overall quality score
        all_scores = [r["percentage"] for phase in self.phases for r in phase.reviews]
        if all_scores:
            avg_score = round(sum(all_scores) / len(all_scores), 1)
            lines.append(f"**整體品質評分**: ⭐ {avg_score}%")
            lines.append("")
        
        # Table of Contents
        lines.append("## 📋 目錄")
        lines.append("")
        for i, phase in enumerate(self.phases, 1):
            lines.append(f"{i}. [{phase.phase_name}](#{phase.phase_name.lower().replace(' ', '-')})")
        lines.append("")
        lines.append("---")
        lines.append("")
        
        # Phase Reports
        for phase in self.phases:
            lines.append(self._generate_phase_report(phase))
        
        # Save to file
        self.report_file.write_text("\n".join(lines), encoding="utf-8")
    
    def _generate_phase_report(self, phase: PhaseReview) -> str:
        """Generate Markdown report for a single phase."""
        lines = []
        
        # Phase Header
        lines.append(f"## {phase.phase_name}")
        lines.append("")
        lines.append(f"- **時間**: {phase.start_time.strftime('%H:%M:%S')} → {phase.end_time.strftime('%H:%M:%S') if phase.end_time else '進行中'}")
        lines.append(f"- **耗時**: {phase.duration}")
        lines.append(f"- **平均評分**: ⭐ {phase.average_score}%")
        lines.append("")
        
        # Processing Steps
        if phase.processing_summary:
            lines.append("### 📝 處理步驟")
            lines.append("")
            for step in phase.processing_summary:
                lines.append(f"1. {step}")
            lines.append("")
        
        # Detailed Steps
        if phase.detailed_steps:
            lines.append("### 🔍 詳細執行步驟")
            lines.append("")
            for step in phase.detailed_steps:
                lines.append(f"- **[{step['timestamp']}]** {step['step']}")
                if step.get('detail'):
                    lines.append(f"  - {step['detail']}")
            lines.append("")
        
        # Quality Reviews
        if phase.reviews:
            lines.append("### ⭐ 品質檢核")
            lines.append("")
            lines.append("| 檢核項目 | 評分 | 評價 |")
            lines.append("|----------|------|------|")
            
            for review in phase.reviews:
                stars = "⭐" * int(review["percentage"] / 20) + "☆" * (5 - int(review["percentage"] / 20))
                lines.append(f"| {review['criteria']} | {review['score']}/{review['max_score']} {stars} | {review['comment']} |")
            lines.append("")
        
        lines.append("---")
        lines.append("")
        
        return "\n".join(lines)
    
    def _save_json(self):
        """Save report as JSON for programmatic access."""
        report_data = {
            "source_file": self.source_file,
            "start_time": self.start_time.strftime("%Y-%m-%d %H:%M:%S"),
            "end_time": self.end_time.strftime("%Y-%m-%d %H:%M:%S") if self.end_time else None,
            "phases": [phase.to_dict() for phase in self.phases]
        }
        
        self.report_json.write_text(
            json.dumps(report_data, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
    
    def _print_summary(self):
        """Print a summary to console."""
        print("\n" + "=" * 60)
        print("📊 品質檢核報告摘要")
        print("=" * 60)
        print(f"📁 報告檔案: {self.report_file.name}")
        print(f"📊 JSON 數據: {self.report_json.name}")
        
        for phase in self.phases:
            score = phase.average_score
            status = "✅" if score >= 70 else "⚠️" if score >= 50 else "❌"
            print(f"  {status} {phase.phase_name}: {score}%")
        
        print("=" * 60)


# Module-level convenience functions
_review_report: Optional[ReviewReport] = None


def init_review_report(output_dir: Path, source_file: str = ""):
    """Initialize the global review report."""
    global _review_report
    _review_report = ReviewReport(output_dir, source_file)
    return _review_report


def get_review_report() -> Optional[ReviewReport]:
    """Get the current review report instance."""
    return _review_report


def report_start_phase(phase_name: str):
    """Start a new phase in the review report."""
    if _review_report:
        _review_report.start_phase(phase_name)


def report_add_review(criteria: str, score: int, comment: str, max_score: int = 10):
    """Add a quality review to the current phase."""
    if _review_report:
        _review_report.add_review(criteria, score, comment, max_score)


def report_add_step(step: str, detail: str = ""):
    """Add a processing step to the current phase."""
    if _review_report:
        _review_report.add_step(step, detail)


def report_complete_phase():
    """Complete the current phase."""
    if _review_report:
        _review_report.complete_phase()


def report_save():
    """Save the review report."""
    if _review_report:
        _review_report.save_report()
