import { useState } from 'react';
import { Plus, Trash2, GripVertical } from 'lucide-react';
import { v4 as uuidv4 } from 'uuid';

export default function QuestionEditor({ question, onChange }) {
  const hasOptions = ['single_choice', 'multiple_choice', 'dropdown'].includes(question.type);
  const isScale = question.type === 'scale';
  const isRating = question.type === 'rating';
  const isSectionHeader = question.type === 'section_header';

  // Handle option changes
  const updateOption = (index, field, value) => {
    const newOptions = [...(question.options || [])];
    newOptions[index] = { ...newOptions[index], [field]: value };
    
    // Auto-generate value from label if needed
    if (field === 'label') {
      newOptions[index].value = value.toLowerCase().replace(/\s+/g, '_');
    }
    
    onChange({ options: newOptions });
  };

  const addOption = () => {
    const newOptions = [
      ...(question.options || []),
      { label: `Option ${(question.options?.length || 0) + 1}`, value: `option_${(question.options?.length || 0) + 1}` },
    ];
    onChange({ options: newOptions });
  };

  const removeOption = (index) => {
    const newOptions = (question.options || []).filter((_, i) => i !== index);
    onChange({ options: newOptions });
  };

  return (
    <div className="space-y-4">
      {/* Question text */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          {isSectionHeader ? 'Section Title' : 'Question Text'}
        </label>
        <input
          type="text"
          value={question.text || ''}
          onChange={(e) => onChange({ text: e.target.value })}
          placeholder={isSectionHeader ? 'Enter section title...' : 'Enter your question...'}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
        />
      </div>

      {/* Help text (not for section header) */}
      {!isSectionHeader && (
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Help Text
            <span className="text-gray-400 font-normal ml-1">(optional)</span>
          </label>
          <input
            type="text"
            value={question.helpText || ''}
            onChange={(e) => onChange({ helpText: e.target.value })}
            placeholder="Additional instructions or hints"
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
          />
        </div>
      )}

      {/* Placeholder (for text inputs) */}
      {['text', 'textarea', 'number', 'email', 'phone'].includes(question.type) && (
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Placeholder
            <span className="text-gray-400 font-normal ml-1">(optional)</span>
          </label>
          <input
            type="text"
            value={question.placeholder || ''}
            onChange={(e) => onChange({ placeholder: e.target.value })}
            placeholder="Placeholder text"
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
          />
        </div>
      )}

      {/* Options for choice questions */}
      {hasOptions && (
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Options</label>
          <div className="space-y-2">
            {(question.options || []).map((option, index) => (
              <div key={index} className="flex items-center gap-2">
                <span className="text-gray-400 cursor-move">
                  <GripVertical size={16} />
                </span>
                <input
                  type="text"
                  value={option.label}
                  onChange={(e) => updateOption(index, 'label', e.target.value)}
                  placeholder={`Option ${index + 1}`}
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
                />
                <input
                  type="number"
                  value={option.score ?? ''}
                  onChange={(e) => updateOption(index, 'score', e.target.value === '' ? null : parseInt(e.target.value))}
                  placeholder="Score"
                  title="Score value for this option"
                  className="w-20 px-2 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none text-center"
                />
                <button
                  onClick={() => removeOption(index)}
                  disabled={(question.options?.length || 0) <= 1}
                  className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <Trash2 size={16} />
                </button>
              </div>
            ))}
          </div>
          <button
            onClick={addOption}
            className="mt-2 inline-flex items-center gap-1 text-sm text-primary-600 hover:text-primary-700"
          >
            <Plus size={16} />
            Add Option
          </button>
          <p className="text-xs text-gray-500 mt-1">Enter score values to enable scoring (e.g., 0, 1, 2, 3)</p>
        </div>
      )}

      {/* Scale settings */}
      {isScale && (
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Min Value</label>
            <input
              type="number"
              value={question.scaleMin ?? 0}
              onChange={(e) => onChange({ scaleMin: e.target.value === '' ? 0 : parseInt(e.target.value) })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Max Value</label>
            <input
              type="number"
              value={question.scaleMax ?? 5}
              onChange={(e) => onChange({ scaleMax: e.target.value === '' ? 5 : parseInt(e.target.value) })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Min Label</label>
            <input
              type="text"
              value={question.scaleMinLabel || ''}
              onChange={(e) => onChange({ scaleMinLabel: e.target.value })}
              placeholder="e.g., Strongly Disagree"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Max Label</label>
            <input
              type="text"
              value={question.scaleMaxLabel || ''}
              onChange={(e) => onChange({ scaleMaxLabel: e.target.value })}
              placeholder="e.g., Strongly Agree"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
            />
          </div>
        </div>
      )}

      {/* Rating settings */}
      {isRating && (
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Max Stars</label>
            <select
              value={question.scaleMax ?? 5}
              onChange={(e) => onChange({ scaleMax: parseInt(e.target.value) })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
            >
              <option value={3}>3 Stars</option>
              <option value={5}>5 Stars</option>
              <option value={10}>10 Stars</option>
            </select>
          </div>
        </div>
      )}

      {/* Required checkbox (not for section header) */}
      {!isSectionHeader && (
        <div className="pt-2 border-t border-gray-200">
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={question.isRequired || false}
              onChange={(e) => onChange({ isRequired: e.target.checked })}
              className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
            />
            <span className="text-sm text-gray-700">Required question</span>
          </label>
        </div>
      )}

      {/* Validation settings (for text inputs) */}
      {['text', 'textarea', 'number'].includes(question.type) && (
        <div className="pt-2 border-t border-gray-200">
          <label className="block text-sm font-medium text-gray-700 mb-2">Validation</label>
          <div className="grid grid-cols-2 gap-4">
            {['text', 'textarea'].includes(question.type) && (
              <>
                <div>
                  <label className="block text-xs text-gray-500 mb-1">Min Length</label>
                  <input
                    type="number"
                    min={0}
                    value={question.validation?.minLength || ''}
                    onChange={(e) =>
                      onChange({
                        validation: {
                          ...question.validation,
                          minLength: e.target.value ? parseInt(e.target.value) : null,
                        },
                      })
                    }
                    placeholder="0"
                    className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg"
                  />
                </div>
                <div>
                  <label className="block text-xs text-gray-500 mb-1">Max Length</label>
                  <input
                    type="number"
                    min={1}
                    value={question.validation?.maxLength || ''}
                    onChange={(e) =>
                      onChange({
                        validation: {
                          ...question.validation,
                          maxLength: e.target.value ? parseInt(e.target.value) : null,
                        },
                      })
                    }
                    placeholder="Unlimited"
                    className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg"
                  />
                </div>
              </>
            )}
            {question.type === 'number' && (
              <>
                <div>
                  <label className="block text-xs text-gray-500 mb-1">Min Value</label>
                  <input
                    type="number"
                    value={question.validation?.min ?? ''}
                    onChange={(e) =>
                      onChange({
                        validation: {
                          ...question.validation,
                          min: e.target.value ? parseFloat(e.target.value) : null,
                        },
                      })
                    }
                    placeholder="No min"
                    className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg"
                  />
                </div>
                <div>
                  <label className="block text-xs text-gray-500 mb-1">Max Value</label>
                  <input
                    type="number"
                    value={question.validation?.max ?? ''}
                    onChange={(e) =>
                      onChange({
                        validation: {
                          ...question.validation,
                          max: e.target.value ? parseFloat(e.target.value) : null,
                        },
                      })
                    }
                    placeholder="No max"
                    className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg"
                  />
                </div>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
