import { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  Edit,
  Copy,
  Trash2,
  Clock,
  CheckCircle,
  Archive,
  Calendar,
  User,
  FileText,
  History,
} from 'lucide-react';
import { questionnaireApi } from '../services/api';

const statusConfig = {
  draft: { bg: 'bg-yellow-100', text: 'text-yellow-800', icon: Clock, label: 'Draft' },
  active: { bg: 'bg-green-100', text: 'text-green-800', icon: CheckCircle, label: 'Active' },
  archived: { bg: 'bg-gray-100', text: 'text-gray-800', icon: Archive, label: 'Archived' },
};

const typeLabels = {
  eligibility: 'Eligibility',
  screening: 'Screening',
  baseline: 'Baseline',
  follow_up: 'Follow-Up',
  adverse_event: 'Adverse Event',
  quality_of_life: 'Quality of Life',
  custom: 'Custom',
};

const questionTypeLabels = {
  text: 'Short Text',
  textarea: 'Long Text',
  number: 'Number',
  email: 'Email',
  phone: 'Phone',
  date: 'Date',
  time: 'Time',
  datetime: 'Date & Time',
  single_choice: 'Single Choice',
  multiple_choice: 'Multiple Choice',
  dropdown: 'Dropdown',
  rating: 'Rating',
  scale: 'Scale',
  yes_no: 'Yes/No',
  file_upload: 'File Upload',
  section_header: 'Section Header',
};

export default function QuestionnaireView() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [questionnaire, setQuestionnaire] = useState(null);
  const [versions, setVersions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('questions');

  useEffect(() => {
    loadQuestionnaire();
    loadVersions();
  }, [id]);

  const loadQuestionnaire = async () => {
    try {
      const data = await questionnaireApi.get(id);
      setQuestionnaire(data);
    } catch (err) {
      setError('Failed to load questionnaire');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const loadVersions = async () => {
    try {
      const data = await questionnaireApi.getVersions(id);
      setVersions(data);
    } catch (err) {
      console.error('Failed to load versions:', err);
    }
  };

  const handleDelete = async () => {
    if (!window.confirm('Are you sure you want to delete this questionnaire?')) {
      return;
    }
    try {
      await questionnaireApi.delete(id);
      navigate('/questionnaires');
    } catch (err) {
      alert('Failed to delete questionnaire');
    }
  };

  const handleClone = async () => {
    try {
      const cloned = await questionnaireApi.clone(id);
      navigate(`/questionnaires/${cloned.id}/edit`);
    } catch (err) {
      alert('Failed to clone questionnaire');
    }
  };

  if (loading) {
    return (
      <div className="p-8 flex items-center justify-center">
        <div className="animate-spin w-8 h-8 border-4 border-primary-500 border-t-transparent rounded-full" />
      </div>
    );
  }

  if (error || !questionnaire) {
    return (
      <div className="p-8">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-800">
          {error || 'Questionnaire not found'}
        </div>
        <Link
          to="/questionnaires"
          className="inline-flex items-center gap-2 mt-4 text-primary-600 hover:text-primary-700"
        >
          <ArrowLeft size={18} />
          Back to Questionnaires
        </Link>
      </div>
    );
  }

  const status = statusConfig[questionnaire.status] || statusConfig.draft;
  const StatusIcon = status.icon;

  return (
    <div className="p-6 lg:p-8">
      {/* Header */}
      <div className="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-4 mb-6">
        <div className="flex items-start gap-4">
          <Link
            to="/questionnaires"
            className="p-2 hover:bg-gray-100 rounded-lg mt-1"
          >
            <ArrowLeft size={20} />
          </Link>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{questionnaire.name}</h1>
            {questionnaire.description && (
              <p className="text-gray-600 mt-1">{questionnaire.description}</p>
            )}
            <div className="flex flex-wrap items-center gap-3 mt-3">
              <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${status.bg} ${status.text}`}>
                <StatusIcon size={12} />
                {status.label}
              </span>
              <span className="text-sm text-gray-500">
                {typeLabels[questionnaire.type] || questionnaire.type}
              </span>
              <span className="text-sm text-gray-500">
                Version {questionnaire.version}
              </span>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2 pl-12 lg:pl-0">
          <Link
            to={`/questionnaires/${id}/edit`}
            className="inline-flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
          >
            <Edit size={18} />
            Edit
          </Link>
          <button
            onClick={handleClone}
            className="inline-flex items-center gap-2 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
          >
            <Copy size={18} />
            Clone
          </button>
          <button
            onClick={handleDelete}
            className="inline-flex items-center gap-2 px-4 py-2 border border-red-300 text-red-600 rounded-lg hover:bg-red-50"
          >
            <Trash2 size={18} />
            Delete
          </button>
        </div>
      </div>

      {/* Metadata cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-100 rounded-lg">
              <FileText className="w-5 h-5 text-blue-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Questions</p>
              <p className="text-xl font-semibold text-gray-900">
                {questionnaire.questions?.length || 0}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-green-100 rounded-lg">
              <CheckCircle className="w-5 h-5 text-green-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Required</p>
              <p className="text-xl font-semibold text-gray-900">
                {questionnaire.questions?.filter((q) => q.isRequired).length || 0}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-purple-100 rounded-lg">
              <Calendar className="w-5 h-5 text-purple-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Created</p>
              <p className="text-sm font-medium text-gray-900">
                {new Date(questionnaire.created_at).toLocaleDateString()}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-orange-100 rounded-lg">
              <Clock className="w-5 h-5 text-orange-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Updated</p>
              <p className="text-sm font-medium text-gray-900">
                {new Date(questionnaire.updated_at).toLocaleDateString()}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="bg-white rounded-lg border border-gray-200">
        <div className="border-b border-gray-200">
          <nav className="flex gap-4 px-4">
            <button
              onClick={() => setActiveTab('questions')}
              className={`py-3 px-2 border-b-2 font-medium text-sm transition-colors ${
                activeTab === 'questions'
                  ? 'border-primary-500 text-primary-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              Questions ({questionnaire.questions?.length || 0})
            </button>
            <button
              onClick={() => setActiveTab('settings')}
              className={`py-3 px-2 border-b-2 font-medium text-sm transition-colors ${
                activeTab === 'settings'
                  ? 'border-primary-500 text-primary-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              Settings
            </button>
            <button
              onClick={() => setActiveTab('history')}
              className={`py-3 px-2 border-b-2 font-medium text-sm transition-colors ${
                activeTab === 'history'
                  ? 'border-primary-500 text-primary-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              Version History
            </button>
          </nav>
        </div>

        <div className="p-6">
          {/* Questions tab */}
          {activeTab === 'questions' && (
            <div className="space-y-4">
              {questionnaire.questions?.length === 0 ? (
                <p className="text-gray-500 text-center py-8">
                  No questions in this questionnaire
                </p>
              ) : (
                questionnaire.questions?.map((question, index) => (
                  <div
                    key={question.id}
                    className="border border-gray-200 rounded-lg p-4"
                  >
                    <div className="flex items-start gap-3">
                      <span className="flex-shrink-0 w-8 h-8 bg-gray-100 rounded-full flex items-center justify-center text-sm font-medium text-gray-600">
                        {index + 1}
                      </span>
                      <div className="flex-1 min-w-0">
                        <p className="font-medium text-gray-900">
                          {question.text || 'Untitled Question'}
                          {question.isRequired && (
                            <span className="text-red-500 ml-1">*</span>
                          )}
                        </p>
                        <div className="flex flex-wrap items-center gap-2 mt-2">
                          <span className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded">
                            {questionTypeLabels[question.type] || question.type}
                          </span>
                          {question.helpText && (
                            <span className="text-xs text-gray-500">
                              Help text: "{question.helpText}"
                            </span>
                          )}
                        </div>
                        {/* Show options for choice questions */}
                        {question.options && question.options.length > 0 && (
                          <div className="mt-3 pl-4 border-l-2 border-gray-200">
                            <p className="text-xs text-gray-500 mb-1">Options:</p>
                            <ul className="space-y-1">
                              {question.options.map((opt, optIdx) => (
                                <li key={optIdx} className="text-sm text-gray-600">
                                  • {opt.label}
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          )}

          {/* Settings tab */}
          {activeTab === 'settings' && (
            <div className="max-w-lg">
              <h3 className="font-medium text-gray-900 mb-4">Questionnaire Settings</h3>
              <dl className="space-y-4">
                <div className="flex justify-between py-2 border-b border-gray-100">
                  <dt className="text-gray-600">Allow save progress</dt>
                  <dd className="font-medium text-gray-900">
                    {questionnaire.settings?.allowSaveProgress ? 'Yes' : 'No'}
                  </dd>
                </div>
                <div className="flex justify-between py-2 border-b border-gray-100">
                  <dt className="text-gray-600">Show progress bar</dt>
                  <dd className="font-medium text-gray-900">
                    {questionnaire.settings?.showProgressBar ? 'Yes' : 'No'}
                  </dd>
                </div>
                <div className="flex justify-between py-2 border-b border-gray-100">
                  <dt className="text-gray-600">Randomize questions</dt>
                  <dd className="font-medium text-gray-900">
                    {questionnaire.settings?.randomizeQuestions ? 'Yes' : 'No'}
                  </dd>
                </div>
                <div className="flex justify-between py-2 border-b border-gray-100">
                  <dt className="text-gray-600">Time limit</dt>
                  <dd className="font-medium text-gray-900">
                    {questionnaire.settings?.timeLimit
                      ? `${questionnaire.settings.timeLimit} minutes`
                      : 'None'}
                  </dd>
                </div>
                <div className="flex justify-between py-2 border-b border-gray-100">
                  <dt className="text-gray-600">Submit button text</dt>
                  <dd className="font-medium text-gray-900">
                    {questionnaire.settings?.submitButtonText || 'Submit'}
                  </dd>
                </div>
                <div className="py-2">
                  <dt className="text-gray-600 mb-1">Success message</dt>
                  <dd className="text-gray-900 bg-gray-50 p-3 rounded-lg text-sm">
                    {questionnaire.settings?.successMessage ||
                      'Thank you for completing the questionnaire.'}
                  </dd>
                </div>
              </dl>
            </div>
          )}

          {/* Version history tab */}
          {activeTab === 'history' && (
            <div className="space-y-4">
              {versions.length === 0 ? (
                <p className="text-gray-500 text-center py-8">
                  No version history available
                </p>
              ) : (
                versions.map((version) => (
                  <div
                    key={version.id}
                    className="flex items-start gap-4 p-4 border border-gray-200 rounded-lg"
                  >
                    <div className="p-2 bg-gray-100 rounded-lg">
                      <History className="w-5 h-5 text-gray-600" />
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <span className="font-medium text-gray-900">
                          Version {version.version_number}
                        </span>
                        {version.version_number === questionnaire.version && (
                          <span className="text-xs bg-primary-100 text-primary-700 px-2 py-0.5 rounded">
                            Current
                          </span>
                        )}
                      </div>
                      <p className="text-sm text-gray-600 mt-1">
                        {version.change_summary || 'No description'}
                      </p>
                      <p className="text-xs text-gray-400 mt-1">
                        {new Date(version.created_at).toLocaleString()}
                      </p>
                    </div>
                  </div>
                ))
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
