import { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import {
  ArrowLeft,
  Save,
  Eye,
  Plus,
  Trash2,
  GripVertical,
  Settings,
  ChevronDown,
  ChevronUp,
  Copy,
  AlertCircle,
} from 'lucide-react';
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
} from '@dnd-kit/core';
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  useSortable,
  verticalListSortingStrategy,
} from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { v4 as uuidv4 } from 'uuid';
import { questionnaireApi } from '../services/api';
import QuestionEditor from '../components/QuestionEditor';
import QuestionPreview from '../components/QuestionPreview';

const questionTypeIcons = {
  text: '📝',
  textarea: '📄',
  number: '🔢',
  email: '📧',
  phone: '📱',
  date: '📅',
  time: '🕐',
  datetime: '📆',
  single_choice: '⭕',
  multiple_choice: '☑️',
  dropdown: '📋',
  rating: '⭐',
  scale: '📊',
  yes_no: '✅',
  file_upload: '📎',
  section_header: '📑',
};

const questionTypes = [
  { value: 'text', label: 'Short Text', icon: '📝' },
  { value: 'textarea', label: 'Long Text', icon: '📄' },
  { value: 'number', label: 'Number', icon: '🔢' },
  { value: 'email', label: 'Email', icon: '📧' },
  { value: 'phone', label: 'Phone', icon: '📱' },
  { value: 'date', label: 'Date', icon: '📅' },
  { value: 'single_choice', label: 'Single Choice', icon: '⭕' },
  { value: 'multiple_choice', label: 'Multiple Choice', icon: '☑️' },
  { value: 'dropdown', label: 'Dropdown', icon: '📋' },
  { value: 'rating', label: 'Rating', icon: '⭐' },
  { value: 'scale', label: 'Scale', icon: '📊' },
  { value: 'yes_no', label: 'Yes/No', icon: '✅' },
  { value: 'section_header', label: 'Section Header', icon: '📑' },
];

const questionnaireTypes = [
  { value: 'eligibility', label: 'Eligibility' },
  { value: 'screening', label: 'Screening' },
  { value: 'baseline', label: 'Baseline' },
  { value: 'follow_up', label: 'Follow-Up' },
  { value: 'adverse_event', label: 'Adverse Event' },
  { value: 'quality_of_life', label: 'Quality of Life' },
  { value: 'custom', label: 'Custom' },
];

// Sortable Question Item
function SortableQuestion({ question, index, onEdit, onDelete, onDuplicate, isExpanded, onToggle }) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: question.id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  };

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={`bg-white border rounded-lg mb-3 ${isDragging ? 'shadow-lg' : 'shadow-sm'}`}
    >
      {/* Question header */}
      <div className="flex items-center gap-3 p-4 border-b border-gray-100">
        <button
          {...attributes}
          {...listeners}
          className="cursor-grab active:cursor-grabbing text-gray-400 hover:text-gray-600"
        >
          <GripVertical size={20} />
        </button>
        
        <span className="text-xl">{questionTypeIcons[question.type] || '❓'}</span>
        
        <div className="flex-1 min-w-0">
          <p className="font-medium text-gray-900 truncate">
            {question.text || 'Untitled Question'}
          </p>
          <p className="text-sm text-gray-500">
            {questionTypes.find(t => t.value === question.type)?.label || question.type}
            {question.isRequired && <span className="text-red-500 ml-1">*</span>}
          </p>
        </div>
        
        <div className="flex items-center gap-1">
          <button
            onClick={() => onDuplicate(question)}
            className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded"
            title="Duplicate"
          >
            <Copy size={18} />
          </button>
          <button
            onClick={() => onDelete(question.id)}
            className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded"
            title="Delete"
          >
            <Trash2 size={18} />
          </button>
          <button
            onClick={() => onToggle(question.id)}
            className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded"
          >
            {isExpanded ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
          </button>
        </div>
      </div>
      
      {/* Expanded editor */}
      {isExpanded && (
        <div className="p-4">
          <QuestionEditor
            question={question}
            onChange={(updated) => onEdit(question.id, updated)}
          />
        </div>
      )}
    </div>
  );
}

export default function QuestionnaireBuilder() {
  const { id } = useParams();
  const navigate = useNavigate();
  const isEditing = Boolean(id);

  const [questionnaire, setQuestionnaire] = useState({
    name: '',
    description: '',
    type: 'custom',
    status: 'draft',
    questions: [],
    settings: {
      allowSaveProgress: true,
      showProgressBar: true,
      randomizeQuestions: false,
      timeLimit: null,
      submitButtonText: 'Submit',
      successMessage: 'Thank you for completing the questionnaire.',
    },
  });

  const [loading, setLoading] = useState(isEditing);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [expandedQuestions, setExpandedQuestions] = useState(new Set());
  const [showPreview, setShowPreview] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [showAddQuestion, setShowAddQuestion] = useState(false);

  // DnD sensors
  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

  // Load existing questionnaire
  useEffect(() => {
    if (isEditing) {
      loadQuestionnaire();
    }
  }, [id]);

  const loadQuestionnaire = async () => {
    try {
      const data = await questionnaireApi.get(id);
      setQuestionnaire({
        id: data.id,  // Preserve ID for scoring calculations in preview
        name: data.name,
        description: data.description || '',
        type: data.type,
        status: data.status,
        questions: data.questions || [],
        settings: data.settings || questionnaire.settings,
        scoring_config: data.scoring_config,  // Preserve scoring config
      });
    } catch (err) {
      setError('Failed to load questionnaire');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // Save questionnaire
  const handleSave = async (status = questionnaire.status) => {
    if (!questionnaire.name.trim()) {
      setError('Please enter a questionnaire name');
      return;
    }

    setSaving(true);
    setError(null);

    try {
      const data = {
        name: questionnaire.name,
        description: questionnaire.description,
        type: questionnaire.type,
        status: status,
        questions: questionnaire.questions.map((q, idx) => ({
          ...q,
          order: idx,
        })),
        settings: questionnaire.settings,
      };

      if (isEditing) {
        await questionnaireApi.update(id, data);
      } else {
        const created = await questionnaireApi.create(data);
        navigate(`/questionnaires/${created.id}/edit`, { replace: true });
      }
    } catch (err) {
      setError('Failed to save questionnaire');
      console.error(err);
    } finally {
      setSaving(false);
    }
  };

  // Add new question
  const addQuestion = (type) => {
    const newQuestion = {
      id: uuidv4(),
      text: '',
      type: type,
      isRequired: false,
      order: questionnaire.questions.length,
      options: ['single_choice', 'multiple_choice', 'dropdown'].includes(type)
        ? [
            { label: 'Option 1', value: 'option_1' },
            { label: 'Option 2', value: 'option_2' },
          ]
        : null,
      validation: null,
      conditionalLogic: null,
      helpText: '',
      placeholder: '',
      scaleMin: type === 'scale' ? 1 : null,
      scaleMax: type === 'scale' ? 5 : null,
      scaleMinLabel: type === 'scale' ? 'Low' : null,
      scaleMaxLabel: type === 'scale' ? 'High' : null,
    };

    setQuestionnaire({
      ...questionnaire,
      questions: [...questionnaire.questions, newQuestion],
    });
    setExpandedQuestions(new Set([...expandedQuestions, newQuestion.id]));
    setShowAddQuestion(false);
  };

  // Edit question
  const editQuestion = (questionId, updates) => {
    setQuestionnaire({
      ...questionnaire,
      questions: questionnaire.questions.map((q) =>
        q.id === questionId ? { ...q, ...updates } : q
      ),
    });
  };

  // Delete question
  const deleteQuestion = (questionId) => {
    if (!window.confirm('Are you sure you want to delete this question?')) {
      return;
    }
    setQuestionnaire({
      ...questionnaire,
      questions: questionnaire.questions.filter((q) => q.id !== questionId),
    });
    expandedQuestions.delete(questionId);
    setExpandedQuestions(new Set(expandedQuestions));
  };

  // Duplicate question
  const duplicateQuestion = (question) => {
    const newQuestion = {
      ...question,
      id: uuidv4(),
      text: `${question.text} (Copy)`,
    };
    const index = questionnaire.questions.findIndex((q) => q.id === question.id);
    const newQuestions = [...questionnaire.questions];
    newQuestions.splice(index + 1, 0, newQuestion);
    setQuestionnaire({ ...questionnaire, questions: newQuestions });
    setExpandedQuestions(new Set([...expandedQuestions, newQuestion.id]));
  };

  // Toggle question expand/collapse
  const toggleQuestion = (questionId) => {
    const newExpanded = new Set(expandedQuestions);
    if (newExpanded.has(questionId)) {
      newExpanded.delete(questionId);
    } else {
      newExpanded.add(questionId);
    }
    setExpandedQuestions(newExpanded);
  };

  // Handle drag end
  const handleDragEnd = (event) => {
    const { active, over } = event;
    if (active.id !== over?.id) {
      const oldIndex = questionnaire.questions.findIndex((q) => q.id === active.id);
      const newIndex = questionnaire.questions.findIndex((q) => q.id === over.id);
      setQuestionnaire({
        ...questionnaire,
        questions: arrayMove(questionnaire.questions, oldIndex, newIndex),
      });
    }
  };

  if (loading) {
    return (
      <div className="p-8 flex items-center justify-center">
        <div className="animate-spin w-8 h-8 border-4 border-primary-500 border-t-transparent rounded-full" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-20">
        <div className="px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link
              to="/questionnaires"
              className="p-2 hover:bg-gray-100 rounded-lg"
            >
              <ArrowLeft size={20} />
            </Link>
            <div>
              <h1 className="text-lg font-semibold text-gray-900">
                {isEditing ? 'Edit Questionnaire' : 'New Questionnaire'}
              </h1>
              <p className="text-sm text-gray-500">
                {questionnaire.questions.length} question(s)
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={() => setShowPreview(true)}
              className="inline-flex items-center gap-2 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
            >
              <Eye size={18} />
              Preview
            </button>
            <button
              onClick={() => handleSave('draft')}
              disabled={saving}
              className="inline-flex items-center gap-2 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50"
            >
              Save Draft
            </button>
            <button
              onClick={() => handleSave('active')}
              disabled={saving}
              className="inline-flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50"
            >
              <Save size={18} />
              {saving ? 'Saving...' : 'Publish'}
            </button>
          </div>
        </div>
      </header>

      {/* Error banner */}
      {error && (
        <div className="mx-6 mt-4 p-4 bg-red-50 border border-red-200 rounded-lg flex items-center gap-3 text-red-800">
          <AlertCircle size={20} />
          {error}
          <button onClick={() => setError(null)} className="ml-auto text-red-600 hover:text-red-800">
            ×
          </button>
        </div>
      )}

      <div className="p-6 grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left sidebar - Questionnaire settings */}
        <div className="lg:col-span-1">
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-5 sticky top-24">
            <h2 className="font-semibold text-gray-900 mb-4">Questionnaire Details</h2>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Name <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={questionnaire.name}
                  onChange={(e) => setQuestionnaire({ ...questionnaire, name: e.target.value })}
                  placeholder="Enter questionnaire name"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Description
                </label>
                <textarea
                  value={questionnaire.description}
                  onChange={(e) => setQuestionnaire({ ...questionnaire, description: e.target.value })}
                  placeholder="Optional description"
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none resize-none"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Type
                </label>
                <select
                  value={questionnaire.type}
                  onChange={(e) => setQuestionnaire({ ...questionnaire, type: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
                >
                  {questionnaireTypes.map((type) => (
                    <option key={type.value} value={type.value}>
                      {type.label}
                    </option>
                  ))}
                </select>
              </div>

              {/* Settings toggle */}
              <button
                onClick={() => setShowSettings(!showSettings)}
                className="w-full flex items-center justify-between px-3 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                <span className="flex items-center gap-2">
                  <Settings size={18} />
                  Advanced Settings
                </span>
                {showSettings ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
              </button>

              {showSettings && (
                <div className="space-y-3 p-3 bg-gray-50 rounded-lg">
                  <label className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={questionnaire.settings.allowSaveProgress}
                      onChange={(e) =>
                        setQuestionnaire({
                          ...questionnaire,
                          settings: { ...questionnaire.settings, allowSaveProgress: e.target.checked },
                        })
                      }
                      className="rounded"
                    />
                    <span className="text-sm text-gray-700">Allow save progress</span>
                  </label>
                  <label className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={questionnaire.settings.showProgressBar}
                      onChange={(e) =>
                        setQuestionnaire({
                          ...questionnaire,
                          settings: { ...questionnaire.settings, showProgressBar: e.target.checked },
                        })
                      }
                      className="rounded"
                    />
                    <span className="text-sm text-gray-700">Show progress bar</span>
                  </label>
                  <label className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={questionnaire.settings.randomizeQuestions}
                      onChange={(e) =>
                        setQuestionnaire({
                          ...questionnaire,
                          settings: { ...questionnaire.settings, randomizeQuestions: e.target.checked },
                        })
                      }
                      className="rounded"
                    />
                    <span className="text-sm text-gray-700">Randomize question order</span>
                  </label>
                  <div>
                    <label className="block text-sm text-gray-700 mb-1">Submit button text</label>
                    <input
                      type="text"
                      value={questionnaire.settings.submitButtonText}
                      onChange={(e) =>
                        setQuestionnaire({
                          ...questionnaire,
                          settings: { ...questionnaire.settings, submitButtonText: e.target.value },
                        })
                      }
                      className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg"
                    />
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Main content - Questions */}
        <div className="lg:col-span-2">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="font-semibold text-gray-900">Questions</h2>
            <div className="relative">
              <button
                onClick={() => setShowAddQuestion(!showAddQuestion)}
                className="inline-flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
              >
                <Plus size={18} />
                Add Question
                <ChevronDown size={16} />
              </button>

              {showAddQuestion && (
                <div className="absolute right-0 mt-2 w-56 bg-white rounded-lg shadow-lg border border-gray-200 py-2 z-10 max-h-80 overflow-y-auto">
                  {questionTypes.map((type) => (
                    <button
                      key={type.value}
                      onClick={() => addQuestion(type.value)}
                      className="w-full flex items-center gap-3 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
                    >
                      <span>{type.icon}</span>
                      {type.label}
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Questions list */}
          {questionnaire.questions.length === 0 ? (
            <div className="bg-white border-2 border-dashed border-gray-300 rounded-lg p-12 text-center">
              <div className="text-5xl mb-4">📋</div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                No questions yet
              </h3>
              <p className="text-gray-500 mb-4">
                Click "Add Question" to start building your questionnaire
              </p>
            </div>
          ) : (
            <DndContext
              sensors={sensors}
              collisionDetection={closestCenter}
              onDragEnd={handleDragEnd}
            >
              <SortableContext
                items={questionnaire.questions.map((q) => q.id)}
                strategy={verticalListSortingStrategy}
              >
                {questionnaire.questions.map((question, index) => (
                  <SortableQuestion
                    key={question.id}
                    question={question}
                    index={index}
                    onEdit={editQuestion}
                    onDelete={deleteQuestion}
                    onDuplicate={duplicateQuestion}
                    isExpanded={expandedQuestions.has(question.id)}
                    onToggle={toggleQuestion}
                  />
                ))}
              </SortableContext>
            </DndContext>
          )}
        </div>
      </div>

      {/* Close add question dropdown when clicking outside */}
      {showAddQuestion && (
        <div className="fixed inset-0 z-0" onClick={() => setShowAddQuestion(false)} />
      )}

      {/* Preview Modal */}
      {showPreview && (
        <QuestionPreview
          questionnaire={questionnaire}
          onClose={() => setShowPreview(false)}
        />
      )}
    </div>
  );
}
