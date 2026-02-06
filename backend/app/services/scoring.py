"""
Scoring Service for Questionnaires.

Supports multiple scoring systems:
- Simple Sum: Add up all question scores
- Subscale: Group questions into subscales (like DASS-21, PHQ-9)
- Weighted: Apply weights to questions
- Custom: Custom scoring rules

Example scoring configurations:

1. DASS-21 Style (subscales with multipliers):
{
    "enabled": true,
    "type": "subscale",
    "subscales": [
        {
            "name": "Depression",
            "key": "depression",
            "questionIds": ["q3", "q5", "q10", "q13", "q16", "q17", "q21"],
            "multiplier": 2,
            "severityRanges": [
                {"min": 0, "max": 9, "label": "Normal", "severity": "normal"},
                {"min": 10, "max": 13, "label": "Mild", "severity": "mild"},
                {"min": 14, "max": 20, "label": "Moderate", "severity": "moderate"},
                {"min": 21, "max": 27, "label": "Severe", "severity": "severe"},
                {"min": 28, "max": null, "label": "Extremely Severe", "severity": "extreme"}
            ]
        },
        {
            "name": "Anxiety",
            "key": "anxiety",
            "questionIds": ["q2", "q4", "q7", "q9", "q15", "q19", "q20"],
            "multiplier": 2,
            "severityRanges": [...]
        }
    ]
}

2. PHQ-9 Style (simple sum with severity):
{
    "enabled": true,
    "type": "simple_sum",
    "totalScore": {
        "enabled": true,
        "maxScore": 27,
        "severityRanges": [
            {"min": 0, "max": 4, "label": "Minimal", "severity": "normal"},
            {"min": 5, "max": 9, "label": "Mild", "severity": "mild"},
            {"min": 10, "max": 14, "label": "Moderate", "severity": "moderate"},
            {"min": 15, "max": 19, "label": "Moderately Severe", "severity": "severe"},
            {"min": 20, "max": 27, "label": "Severe", "severity": "extreme"}
        ]
    }
}

3. Eligibility/Pass-Fail:
{
    "enabled": true,
    "type": "simple_sum",
    "passingScore": 70,
    "totalScore": {"enabled": true, "maxScore": 100}
}
"""
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from app.schemas.questionnaire import (
    ScoringConfig, ScoringType, ScoringResult, SubscaleScoreResult,
    MissingValueHandling, SeverityRange
)


class ScoringService:
    """Service for calculating questionnaire scores."""
    
    def __init__(self, questionnaire_id: int, scoring_config: Dict[str, Any], questions: List[Dict[str, Any]]):
        """
        Initialize the scoring service.
        
        Args:
            questionnaire_id: ID of the questionnaire
            scoring_config: The scoring configuration from the questionnaire
            questions: List of questions from the questionnaire
        """
        self.questionnaire_id = questionnaire_id
        self.config = scoring_config or {}
        self.questions = questions
        self.questions_by_id = {q.get('id'): q for q in questions}
        self.warnings: List[str] = []
        
    def calculate(self, responses: Dict[str, Any]) -> ScoringResult:
        """
        Calculate scores based on the responses.
        
        Args:
            responses: Dict mapping question ID to answer value
            
        Returns:
            ScoringResult with calculated scores
        """
        if not self.config.get('enabled', False):
            return ScoringResult(
                questionnaireId=self.questionnaire_id,
                scoringType=ScoringType.SIMPLE_SUM,
                totalScore=None,
                calculatedAt=datetime.utcnow(),
                warnings=["Scoring is not enabled for this questionnaire"]
            )
        
        scoring_type = ScoringType(self.config.get('type', 'simple_sum'))
        
        if scoring_type == ScoringType.SUBSCALE:
            return self._calculate_subscale_scoring(responses)
        elif scoring_type == ScoringType.WEIGHTED:
            return self._calculate_weighted_scoring(responses)
        else:
            # SIMPLE_SUM or default
            return self._calculate_simple_sum(responses)
    
    def _get_question_score(self, question_id: str, answer: Any) -> Tuple[Optional[float], bool]:
        """
        Get the score for a question answer.
        
        Args:
            question_id: ID of the question
            answer: The answer value
            
        Returns:
            Tuple of (score, was_answered)
        """
        question = self.questions_by_id.get(question_id)
        if not question:
            self.warnings.append(f"Question {question_id} not found")
            return None, False
            
        if answer is None or answer == '' or answer == []:
            return None, False
            
        question_type = question.get('type', '')
        options = question.get('options', [])
        
        # For scale/rating questions, the answer IS the score
        if question_type in ['scale', 'rating', 'number']:
            try:
                return float(answer), True
            except (ValueError, TypeError):
                self.warnings.append(f"Could not convert answer for {question_id} to number")
                return None, False
        
        # For single choice / dropdown / yes_no, look up the score in options
        if question_type in ['single_choice', 'dropdown', 'yes_no']:
            for opt in options:
                if opt.get('value') == answer:
                    score = opt.get('score')
                    if score is not None:
                        return float(score), True
                    # If no score defined, return 0
                    return 0.0, True
            # Answer not found in options
            self.warnings.append(f"Answer value '{answer}' not found in options for {question_id}")
            return None, False
            
        # For multiple choice, sum the scores of selected options
        if question_type == 'multiple_choice':
            if not isinstance(answer, list):
                answer = [answer]
            total_score = 0.0
            found_any = False
            for selected_value in answer:
                for opt in options:
                    if opt.get('value') == selected_value:
                        score = opt.get('score', 0)
                        if score is not None:
                            total_score += float(score)
                            found_any = True
                        break
            return (total_score, True) if found_any else (None, False)
        
        # For other question types, return None (not scored)
        return None, False
    
    def _handle_missing_value(self, answered_scores: List[float], total_questions: int) -> float:
        """Handle missing values based on configuration."""
        rules = self.config.get('scoringRules') or {}
        handling = rules.get('missingValueHandling', 'zero')
        
        if handling == 'average' and answered_scores:
            # Calculate what the unanswered questions would contribute
            average = sum(answered_scores) / len(answered_scores)
            missing_count = total_questions - len(answered_scores)
            return average * missing_count
        elif handling == 'skip':
            return 0.0
        else:  # 'zero' or default
            return 0.0
    
    def _get_severity(self, score: float, severity_ranges: Optional[List[Dict[str, Any]]]) -> Tuple[Optional[str], Optional[str]]:
        """
        Determine severity level based on score.
        
        Returns:
            Tuple of (severity_key, severity_label)
        """
        if not severity_ranges:
            return None, None
            
        for range_def in severity_ranges:
            min_val = range_def.get('min', 0)
            max_val = range_def.get('max')
            
            if score >= min_val:
                if max_val is None or score <= max_val:
                    return range_def.get('severity'), range_def.get('label')
        
        return None, None
    
    def _calculate_simple_sum(self, responses: Dict[str, Any]) -> ScoringResult:
        """Calculate simple sum scoring."""
        total_score = 0.0
        answered_scores: List[float] = []
        questions_answered = 0
        
        for question in self.questions:
            q_id = question.get('id')
            if q_id and q_id in responses:
                score, was_answered = self._get_question_score(q_id, responses[q_id])
                if was_answered and score is not None:
                    total_score += score
                    answered_scores.append(score)
                    questions_answered += 1
        
        # Handle missing values
        total_score += self._handle_missing_value(answered_scores, len(self.questions))
        
        # Get total score config
        total_config = self.config.get('totalScore', {})
        max_score = total_config.get('maxScore')
        percentage = (total_score / max_score * 100) if max_score else None
        
        # Check passing
        passing_score = self.config.get('passingScore')
        passed = None
        if passing_score is not None:
            passed = total_score >= passing_score
        
        # Get severity
        severity_ranges = total_config.get('severityRanges')
        severity, severity_label = self._get_severity(total_score, severity_ranges)
        
        return ScoringResult(
            questionnaireId=self.questionnaire_id,
            scoringType=ScoringType.SIMPLE_SUM,
            totalScore=total_score,
            maxPossibleScore=max_score,
            percentage=percentage,
            passed=passed,
            severity=severity,
            severityLabel=severity_label,
            subscales=None,
            calculatedAt=datetime.utcnow(),
            warnings=self.warnings if self.warnings else None
        )
    
    def _calculate_subscale_scoring(self, responses: Dict[str, Any]) -> ScoringResult:
        """Calculate subscale-based scoring (like DASS-21)."""
        subscales_config = self.config.get('subscales', [])
        subscale_results: List[SubscaleScoreResult] = []
        overall_total = 0.0
        overall_max = 0.0
        
        # Build a list of questions sorted by order for index-based assignment
        sorted_questions = sorted(self.questions, key=lambda q: q.get('order', 0))
        question_id_by_index = {i + 1: q.get('id') for i, q in enumerate(sorted_questions)}
        
        for subscale in subscales_config:
            subscale_name = subscale.get('name', 'Unknown')
            subscale_key = subscale.get('key', subscale_name.lower())
            multiplier = subscale.get('multiplier', 1.0)
            
            # Support both questionIds (by ID) and questionIndices (by position 1-indexed)
            question_ids = subscale.get('questionIds', [])
            question_indices = subscale.get('questionIndices', [])
            
            # If questionIndices provided, convert to actual IDs based on current questions
            if question_indices:
                question_ids = []
                for idx in question_indices:
                    actual_id = question_id_by_index.get(idx)
                    if actual_id:
                        question_ids.append(actual_id)
                    else:
                        self.warnings.append(f"Question index {idx} not found for subscale {subscale_name}")
            
            raw_score = 0.0
            answered_scores: List[float] = []
            questions_answered = 0
            
            for q_id in question_ids:
                if q_id in responses:
                    score, was_answered = self._get_question_score(q_id, responses[q_id])
                    if was_answered and score is not None:
                        raw_score += score
                        answered_scores.append(score)
                        questions_answered += 1
            
            # Handle missing values in subscale
            raw_score += self._handle_missing_value(answered_scores, len(question_ids))
            
            # Apply multiplier
            final_score = raw_score * multiplier
            
            # Calculate max possible for this subscale
            # Estimate based on number of questions and typical max score per question
            max_per_question = self._estimate_max_score_per_question(question_ids)
            max_possible = len(question_ids) * max_per_question * multiplier if max_per_question else None
            
            percentage = (final_score / max_possible * 100) if max_possible else None
            
            # Get severity for subscale
            severity_ranges = subscale.get('severityRanges')
            severity, severity_label = self._get_severity(final_score, severity_ranges)
            
            subscale_results.append(SubscaleScoreResult(
                name=subscale_name,
                key=subscale_key,
                rawScore=raw_score,
                score=final_score,
                maxPossible=max_possible,
                percentage=percentage,
                severity=severity,
                severityLabel=severity_label,
                questionsAnswered=questions_answered,
                questionsTotal=len(question_ids)
            ))
            
            overall_total += final_score
            if max_possible:
                overall_max += max_possible
        
        # Overall scoring
        total_config = self.config.get('totalScore', {})
        if total_config.get('enabled', True):
            max_score = total_config.get('maxScore') or (overall_max if overall_max else None)
            percentage = (overall_total / max_score * 100) if max_score else None
            
            # Get overall severity
            severity_ranges = total_config.get('severityRanges')
            severity, severity_label = self._get_severity(overall_total, severity_ranges)
        else:
            max_score = None
            percentage = None
            severity = None
            severity_label = None
        
        # Check passing
        passing_score = self.config.get('passingScore')
        passed = None
        if passing_score is not None:
            passed = overall_total >= passing_score
        
        return ScoringResult(
            questionnaireId=self.questionnaire_id,
            scoringType=ScoringType.SUBSCALE,
            totalScore=overall_total,
            maxPossibleScore=max_score,
            percentage=percentage,
            passed=passed,
            severity=severity,
            severityLabel=severity_label,
            subscales=subscale_results,
            calculatedAt=datetime.utcnow(),
            warnings=self.warnings if self.warnings else None
        )
    
    def _calculate_weighted_scoring(self, responses: Dict[str, Any]) -> ScoringResult:
        """Calculate weighted scoring."""
        # Weighted scoring is similar to simple sum but uses weight from question config
        total_score = 0.0
        total_weight = 0.0
        answered_scores: List[float] = []
        questions_answered = 0
        
        for question in self.questions:
            q_id = question.get('id')
            weight = question.get('weight', 1.0)  # Default weight of 1
            
            if q_id and q_id in responses:
                score, was_answered = self._get_question_score(q_id, responses[q_id])
                if was_answered and score is not None:
                    weighted_score = score * weight
                    total_score += weighted_score
                    answered_scores.append(weighted_score)
                    total_weight += weight
                    questions_answered += 1
        
        # Get total score config
        total_config = self.config.get('totalScore', {})
        max_score = total_config.get('maxScore')
        percentage = (total_score / max_score * 100) if max_score else None
        
        # Check passing
        passing_score = self.config.get('passingScore')
        passed = None
        if passing_score is not None:
            passed = total_score >= passing_score
        
        # Get severity
        severity_ranges = total_config.get('severityRanges')
        severity, severity_label = self._get_severity(total_score, severity_ranges)
        
        return ScoringResult(
            questionnaireId=self.questionnaire_id,
            scoringType=ScoringType.WEIGHTED,
            totalScore=total_score,
            maxPossibleScore=max_score,
            percentage=percentage,
            passed=passed,
            severity=severity,
            severityLabel=severity_label,
            subscales=None,
            calculatedAt=datetime.utcnow(),
            warnings=self.warnings if self.warnings else None
        )
    
    def _estimate_max_score_per_question(self, question_ids: List[str]) -> Optional[float]:
        """Estimate the maximum score per question based on options."""
        max_scores = []
        
        for q_id in question_ids:
            question = self.questions_by_id.get(q_id)
            if not question:
                continue
                
            question_type = question.get('type', '')
            
            # For scale questions, use scaleMax
            if question_type == 'scale':
                scale_max = question.get('scaleMax')
                if scale_max is not None:
                    max_scores.append(float(scale_max))
                    continue
            
            # For choice questions, find max score in options
            options = question.get('options', [])
            if options:
                option_scores = [opt.get('score', 0) for opt in options if opt.get('score') is not None]
                if option_scores:
                    max_scores.append(max(option_scores))
        
        return max(max_scores) if max_scores else None


def calculate_score(
    questionnaire_id: int,
    scoring_config: Dict[str, Any],
    questions: List[Dict[str, Any]],
    responses: Dict[str, Any]
) -> ScoringResult:
    """
    Convenience function to calculate scores.
    
    Args:
        questionnaire_id: ID of the questionnaire
        scoring_config: The scoring configuration
        questions: List of questions
        responses: Dict mapping question ID to answer
        
    Returns:
        ScoringResult with calculated scores
    """
    service = ScoringService(questionnaire_id, scoring_config, questions)
    return service.calculate(responses)
