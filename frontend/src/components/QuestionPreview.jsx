import { useState } from 'react';
import { X, Star, ChevronLeft, ChevronRight, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';
import { questionnaireApi } from '../services/api';

export default function QuestionPreview({ questionnaire, onClose }) {
  const [responses, setResponses] = useState({});
  const [currentPage, setCurrentPage] = useState(0);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [scoringResult, setScoringResult] = useState(null);
  const [submitError, setSubmitError] = useState(null);
  const [validationErrors, setValidationErrors] = useState({});
  const questionsPerPage = 5;

  const questions = questionnaire.questions || [];
  const totalPages = Math.ceil(questions.length / questionsPerPage);
  const startIndex = currentPage * questionsPerPage;
  const currentQuestions = questions.slice(startIndex, startIndex + questionsPerPage);

  const updateResponse = (questionId, value) => {
    setResponses({ ...responses, [questionId]: value });
    // Clear validation error when user answers
    if (validationErrors[questionId]) {
      setValidationErrors({ ...validationErrors, [questionId]: null });
    }
  };

  // Validate required questions
  const validateRequiredQuestions = () => {
    const errors = {};
    let firstErrorPage = null;

    questions.forEach((question, index) => {
      if (question.isRequired && question.type !== 'section_header') {
        const response = responses[question.id];
        const isEmpty = 
          response === undefined || 
          response === null || 
          response === '' ||
          (Array.isArray(response) && response.length === 0);

        if (isEmpty) {
          errors[question.id] = 'This question is required';
          const questionPage = Math.floor(index / questionsPerPage);
          if (firstErrorPage === null) {
            firstErrorPage = questionPage;
          }
        }
      }
    });

    return { errors, firstErrorPage };
  };

  const handleSubmit = async () => {
    // Validate required questions first
    const { errors, firstErrorPage } = validateRequiredQuestions();
    
    if (Object.keys(errors).length > 0) {
      setValidationErrors(errors);
      setSubmitError(`Please answer all required questions (${Object.keys(errors).length} unanswered)`);
      // Navigate to the first page with an error
      if (firstErrorPage !== null) {
        setCurrentPage(firstErrorPage);
      }
      return;
    }

    setIsSubmitting(true);
    setSubmitError(null);
    setValidationErrors({});
    
    try {
      // Calculate score if questionnaire has an ID (saved questionnaire)
      if (questionnaire.id) {
        // Pass current questions to API so it uses the current state, not the saved state
        const result = await questionnaireApi.calculateScore(
          questionnaire.id, 
          responses, 
          questions // Pass current questions for accurate scoring
        );
        setScoringResult(result);
      } else {
        // For unsaved questionnaires, just show a success message
        setScoringResult({
          message: 'Preview submitted successfully!',
          note: 'Save the questionnaire and configure scoring to see actual scores.',
          responses: responses
        });
      }
    } catch (error) {
      console.error('Error calculating score:', error);
      setSubmitError(error.response?.data?.detail || 'Failed to calculate score');
    } finally {
      setIsSubmitting(false);
    }
  };

  const renderQuestion = (question, index) => {
    const questionNumber = startIndex + index + 1;

    // Section header
    if (question.type === 'section_header') {
      return (
        <div key={question.id} className="border-b border-gray-200 pb-4 mb-6">
          <h3 className="text-lg font-semibold text-gray-900">{question.text}</h3>
          {question.helpText && (
            <p className="text-gray-600 mt-1">{question.helpText}</p>
          )}
        </div>
      );
    }

    return (
      <div key={question.id} className="mb-6">
        <label className="block mb-2">
          <span className="text-gray-900 font-medium">
            {questionNumber}. {question.text}
            {question.isRequired && <span className="text-red-500 ml-1">*</span>}
          </span>
          {question.helpText && (
            <span className="block text-sm text-gray-500 mt-1">{question.helpText}</span>
          )}
        </label>

        {/* Text input */}
        {question.type === 'text' && (
          <input
            type="text"
            value={responses[question.id] || ''}
            onChange={(e) => updateResponse(question.id, e.target.value)}
            placeholder={question.placeholder || ''}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
          />
        )}

        {/* Textarea */}
        {question.type === 'textarea' && (
          <textarea
            value={responses[question.id] || ''}
            onChange={(e) => updateResponse(question.id, e.target.value)}
            placeholder={question.placeholder || ''}
            rows={4}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none resize-none"
          />
        )}

        {/* Number input */}
        {question.type === 'number' && (
          <input
            type="number"
            value={responses[question.id] || ''}
            onChange={(e) => updateResponse(question.id, e.target.value)}
            placeholder={question.placeholder || ''}
            min={question.validation?.min}
            max={question.validation?.max}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
          />
        )}

        {/* Email input */}
        {question.type === 'email' && (
          <input
            type="email"
            value={responses[question.id] || ''}
            onChange={(e) => updateResponse(question.id, e.target.value)}
            placeholder={question.placeholder || 'email@example.com'}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
          />
        )}

        {/* Phone input */}
        {question.type === 'phone' && (
          <input
            type="tel"
            value={responses[question.id] || ''}
            onChange={(e) => updateResponse(question.id, e.target.value)}
            placeholder={question.placeholder || '+1 (555) 123-4567'}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
          />
        )}

        {/* Date input */}
        {question.type === 'date' && (
          <input
            type="date"
            value={responses[question.id] || ''}
            onChange={(e) => updateResponse(question.id, e.target.value)}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
          />
        )}

        {/* Single choice (radio) */}
        {question.type === 'single_choice' && (
          <div className="space-y-2">
            {(question.options || []).map((option, optIndex) => (
              <label
                key={optIndex}
                className="flex items-center gap-3 p-3 border border-gray-200 rounded-lg cursor-pointer hover:bg-gray-50 transition-colors"
              >
                <input
                  type="radio"
                  name={`question-${question.id}`}
                  value={option.value}
                  checked={responses[question.id] === option.value}
                  onChange={(e) => updateResponse(question.id, e.target.value)}
                  className="text-primary-600 focus:ring-primary-500"
                />
                <span className="text-gray-700">{option.label}</span>
              </label>
            ))}
          </div>
        )}

        {/* Multiple choice (checkbox) */}
        {question.type === 'multiple_choice' && (
          <div className="space-y-2">
            {(question.options || []).map((option, optIndex) => (
              <label
                key={optIndex}
                className="flex items-center gap-3 p-3 border border-gray-200 rounded-lg cursor-pointer hover:bg-gray-50 transition-colors"
              >
                <input
                  type="checkbox"
                  value={option.value}
                  checked={(responses[question.id] || []).includes(option.value)}
                  onChange={(e) => {
                    const current = responses[question.id] || [];
                    if (e.target.checked) {
                      updateResponse(question.id, [...current, option.value]);
                    } else {
                      updateResponse(question.id, current.filter((v) => v !== option.value));
                    }
                  }}
                  className="rounded text-primary-600 focus:ring-primary-500"
                />
                <span className="text-gray-700">{option.label}</span>
              </label>
            ))}
          </div>
        )}

        {/* Dropdown */}
        {question.type === 'dropdown' && (
          <select
            value={responses[question.id] || ''}
            onChange={(e) => updateResponse(question.id, e.target.value)}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
          >
            <option value="">Select an option...</option>
            {(question.options || []).map((option, optIndex) => (
              <option key={optIndex} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        )}

        {/* Yes/No */}
        {question.type === 'yes_no' && (
          <div className="flex gap-4">
            <label className="flex-1">
              <input
                type="radio"
                name={`question-${question.id}`}
                value="yes"
                checked={responses[question.id] === 'yes'}
                onChange={(e) => updateResponse(question.id, e.target.value)}
                className="sr-only"
              />
              <div
                className={`p-4 text-center border-2 rounded-lg cursor-pointer transition-colors ${
                  responses[question.id] === 'yes'
                    ? 'border-green-500 bg-green-50 text-green-700'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                Yes
              </div>
            </label>
            <label className="flex-1">
              <input
                type="radio"
                name={`question-${question.id}`}
                value="no"
                checked={responses[question.id] === 'no'}
                onChange={(e) => updateResponse(question.id, e.target.value)}
                className="sr-only"
              />
              <div
                className={`p-4 text-center border-2 rounded-lg cursor-pointer transition-colors ${
                  responses[question.id] === 'no'
                    ? 'border-red-500 bg-red-50 text-red-700'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                No
              </div>
            </label>
          </div>
        )}

        {/* Rating */}
        {question.type === 'rating' && (
          <div className="flex gap-2">
            {Array.from({ length: question.scaleMax || 5 }, (_, i) => i + 1).map((star) => (
              <button
                key={star}
                type="button"
                onClick={() => updateResponse(question.id, star)}
                className="p-1"
              >
                <Star
                  size={32}
                  className={`transition-colors ${
                    star <= (responses[question.id] || 0)
                      ? 'fill-yellow-400 text-yellow-400'
                      : 'text-gray-300 hover:text-yellow-400'
                  }`}
                />
              </button>
            ))}
          </div>
        )}

        {/* Scale */}
        {question.type === 'scale' && (
          <div>
            <div className="flex justify-between text-sm text-gray-500 mb-2">
              <span>{question.scaleMinLabel || (question.scaleMin ?? 0)}</span>
              <span>{question.scaleMaxLabel || (question.scaleMax ?? 3)}</span>
            </div>
            <div className="flex gap-2">
              {Array.from(
                { length: (question.scaleMax ?? 3) - (question.scaleMin ?? 0) + 1 },
                (_, i) => (question.scaleMin ?? 0) + i
              ).map((value) => (
                <button
                  key={value}
                  type="button"
                  onClick={() => updateResponse(question.id, value)}
                  className={`flex-1 py-2 border-2 rounded-lg font-medium transition-colors ${
                    responses[question.id] === value
                      ? 'border-primary-500 bg-primary-50 text-primary-700'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  {value}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Validation error */}
        {validationErrors[question.id] && (
          <p className="mt-2 text-sm text-red-600 flex items-center gap-1">
            <AlertCircle size={14} />
            {validationErrors[question.id]}
          </p>
        )}
      </div>
    );
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-2xl max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">Preview</h2>
            <p className="text-sm text-gray-500">{questionnaire.name || 'Untitled'}</p>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-lg"
          >
            <X size={20} />
          </button>
        </div>

        {/* Progress bar */}
        {questionnaire.settings?.showProgressBar && questions.length > 0 && (
          <div className="px-6 pt-4">
            <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
              <div
                className="h-full bg-primary-500 transition-all duration-300"
                style={{
                  width: `${((currentPage + 1) / totalPages) * 100}%`,
                }}
              />
            </div>
            <p className="text-sm text-gray-500 mt-1">
              Page {currentPage + 1} of {totalPages}
            </p>
          </div>
        )}

        {/* Body */}
        <div className="flex-1 overflow-y-auto px-6 py-4">
          {questionnaire.description && (
            <p className="text-gray-600 mb-6">{questionnaire.description}</p>
          )}

          {questions.length === 0 ? (
            <p className="text-gray-500 text-center py-8">
              No questions to preview
            </p>
          ) : (
            currentQuestions.map((question, index) => renderQuestion(question, index))
          )}
        </div>

        {/* Footer with navigation */}
        <div className="flex items-center justify-between px-6 py-4 border-t border-gray-200">
          <button
            onClick={() => setCurrentPage((p) => Math.max(0, p - 1))}
            disabled={currentPage === 0}
            className="inline-flex items-center gap-2 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <ChevronLeft size={18} />
            Previous
          </button>

          {currentPage === totalPages - 1 ? (
            <button
              type="button"
              onClick={handleSubmit}
              disabled={isSubmitting}
              className="inline-flex items-center gap-2 px-6 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50"
            >
              {isSubmitting ? (
                <>
                  <Loader2 size={18} className="animate-spin" />
                  Calculating...
                </>
              ) : (
                questionnaire.settings?.submitButtonText || 'Submit'
              )}
            </button>
          ) : (
            <button
              onClick={() => setCurrentPage((p) => Math.min(totalPages - 1, p + 1))}
              className="inline-flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
            >
              Next
              <ChevronRight size={18} />
            </button>
          )}
        </div>

        {/* Scoring Result Modal */}
        {scoringResult && (
          <div className="absolute inset-0 bg-black/30 flex items-center justify-center p-4">
            <div className="bg-white rounded-xl shadow-2xl max-w-lg w-full max-h-[80vh] overflow-y-auto">
              <div className="p-6">
                <div className="flex items-center gap-3 mb-4">
                  <CheckCircle className="text-green-500" size={28} />
                  <h3 className="text-xl font-semibold text-gray-900">
                    {scoringResult.message || 'Scoring Results'}
                  </h3>
                </div>

                {scoringResult.note ? (
                  <p className="text-gray-600 mb-4">{scoringResult.note}</p>
                ) : scoringResult.warnings?.includes('Scoring is not enabled') ? (
                  <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-4">
                    <p className="text-yellow-800">
                      Scoring is not enabled for this questionnaire. Configure scoring in the API to see results.
                    </p>
                  </div>
                ) : (
                  <>
                    {/* Total Score */}
                    {scoringResult.totalScore !== null && scoringResult.totalScore !== undefined && (
                      <div className="bg-gray-50 rounded-lg p-4 mb-4">
                        <div className="text-sm text-gray-500">Total Score</div>
                        <div className="text-3xl font-bold text-gray-900">
                          {scoringResult.totalScore}
                          {scoringResult.maxPossibleScore && (
                            <span className="text-lg font-normal text-gray-500">
                              {' '}/ {scoringResult.maxPossibleScore}
                            </span>
                          )}
                        </div>
                        {scoringResult.percentage !== null && (
                          <div className="text-sm text-gray-500">
                            ({scoringResult.percentage.toFixed(1)}%)
                          </div>
                        )}
                        {scoringResult.severityLabel && (
                          <div className={`inline-block mt-2 px-3 py-1 rounded-full text-sm font-medium ${
                            scoringResult.severity === 'normal' ? 'bg-green-100 text-green-800' :
                            scoringResult.severity === 'mild' ? 'bg-yellow-100 text-yellow-800' :
                            scoringResult.severity === 'moderate' ? 'bg-orange-100 text-orange-800' :
                            scoringResult.severity === 'severe' ? 'bg-red-100 text-red-800' :
                            'bg-red-200 text-red-900'
                          }`}>
                            {scoringResult.severityLabel}
                          </div>
                        )}
                      </div>
                    )}

                    {/* Pass/Fail */}
                    {scoringResult.passed !== null && scoringResult.passed !== undefined && (
                      <div className={`rounded-lg p-4 mb-4 ${
                        scoringResult.passed ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'
                      }`}>
                        <div className="flex items-center gap-2">
                          {scoringResult.passed ? (
                            <>
                              <CheckCircle className="text-green-500" size={20} />
                              <span className="font-medium text-green-800">Passed</span>
                            </>
                          ) : (
                            <>
                              <AlertCircle className="text-red-500" size={20} />
                              <span className="font-medium text-red-800">Did not meet passing score</span>
                            </>
                          )}
                        </div>
                      </div>
                    )}

                    {/* Subscales */}
                    {scoringResult.subscales && scoringResult.subscales.length > 0 && (
                      <div className="space-y-3">
                        <h4 className="font-medium text-gray-700">Subscale Scores</h4>
                        {scoringResult.subscales.map((subscale, idx) => (
                          <div key={idx} className="border border-gray-200 rounded-lg p-3">
                            <div className="flex justify-between items-center">
                              <span className="font-medium text-gray-800">{subscale.name}</span>
                              <span className="text-lg font-bold text-gray-900">
                                {subscale.score}
                                {subscale.maxPossible && (
                                  <span className="text-sm font-normal text-gray-500">
                                    {' '}/ {subscale.maxPossible}
                                  </span>
                                )}
                              </span>
                            </div>
                            {subscale.severityLabel && (
                              <div className={`inline-block mt-1 px-2 py-0.5 rounded text-xs font-medium ${
                                subscale.severity === 'normal' ? 'bg-green-100 text-green-700' :
                                subscale.severity === 'mild' ? 'bg-yellow-100 text-yellow-700' :
                                subscale.severity === 'moderate' ? 'bg-orange-100 text-orange-700' :
                                subscale.severity === 'severe' ? 'bg-red-100 text-red-700' :
                                'bg-red-200 text-red-800'
                              }`}>
                                {subscale.severityLabel}
                              </div>
                            )}
                            <div className="text-xs text-gray-500 mt-1">
                              {subscale.questionsAnswered} of {subscale.questionsTotal} questions answered
                            </div>
                          </div>
                        ))}
                      </div>
                    )}

                    {/* Warnings */}
                    {scoringResult.warnings && scoringResult.warnings.length > 0 && (
                      <div className="mt-4 bg-yellow-50 border border-yellow-200 rounded-lg p-3">
                        <div className="text-sm font-medium text-yellow-800 mb-1">Warnings</div>
                        <ul className="text-sm text-yellow-700 list-disc list-inside">
                          {scoringResult.warnings.map((warning, idx) => (
                            <li key={idx}>{warning}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </>
                )}

                <button
                  onClick={() => {
                    setScoringResult(null);
                    setResponses({});
                    setCurrentPage(0);
                  }}
                  className="mt-6 w-full px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
                >
                  Start Over
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Error Display */}
        {submitError && (
          <div className="absolute inset-0 bg-black/30 flex items-center justify-center p-4">
            <div className="bg-white rounded-xl shadow-2xl max-w-md w-full p-6">
              <div className="flex items-center gap-3 mb-4">
                <AlertCircle className="text-red-500" size={28} />
                <h3 className="text-xl font-semibold text-gray-900">Error</h3>
              </div>
              <p className="text-gray-600 mb-4">{submitError}</p>
              <button
                onClick={() => setSubmitError(null)}
                className="w-full px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700"
              >
                Close
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
