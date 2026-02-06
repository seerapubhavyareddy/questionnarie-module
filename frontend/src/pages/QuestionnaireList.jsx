import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  Plus,
  Search,
  Filter,
  MoreVertical,
  Edit,
  Trash2,
  Copy,
  Eye,
  ChevronLeft,
  ChevronRight,
  RefreshCw,
  CheckCircle,
  Clock,
  Archive,
} from 'lucide-react';
import { questionnaireApi } from '../services/api';

const statusColors = {
  draft: { bg: 'bg-yellow-100', text: 'text-yellow-800', icon: Clock },
  active: { bg: 'bg-green-100', text: 'text-green-800', icon: CheckCircle },
  archived: { bg: 'bg-gray-100', text: 'text-gray-800', icon: Archive },
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

export default function QuestionnaireList() {
  const navigate = useNavigate();
  const [questionnaires, setQuestionnaires] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [pagination, setPagination] = useState({
    page: 1,
    pageSize: 20,
    total: 0,
    totalPages: 0,
  });
  const [filters, setFilters] = useState({
    search: '',
    type: '',
    status: '',
  });
  const [showFilters, setShowFilters] = useState(false);
  const [selectedIds, setSelectedIds] = useState([]);
  const [actionMenuId, setActionMenuId] = useState(null);

  // Fetch questionnaires
  const fetchQuestionnaires = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await questionnaireApi.list({
        page: pagination.page,
        pageSize: pagination.pageSize,
        search: filters.search || undefined,
        type: filters.type || undefined,
        status: filters.status || undefined,
      });
      setQuestionnaires(data.items);
      setPagination({
        ...pagination,
        total: data.total,
        totalPages: data.total_pages,
      });
    } catch (err) {
      setError('Failed to load questionnaires. Please try again.');
      console.error('Error fetching questionnaires:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchQuestionnaires();
  }, [pagination.page, filters.type, filters.status]);

  // Search with debounce
  useEffect(() => {
    const timer = setTimeout(() => {
      if (pagination.page === 1) {
        fetchQuestionnaires();
      } else {
        setPagination({ ...pagination, page: 1 });
      }
    }, 300);
    return () => clearTimeout(timer);
  }, [filters.search]);

  // Handle delete
  const handleDelete = async (id) => {
    if (!window.confirm('Are you sure you want to delete this questionnaire?')) {
      return;
    }
    try {
      await questionnaireApi.delete(id);
      fetchQuestionnaires();
    } catch (err) {
      alert('Failed to delete questionnaire');
    }
    setActionMenuId(null);
  };

  // Handle clone
  const handleClone = async (id) => {
    try {
      const cloned = await questionnaireApi.clone(id);
      navigate(`/questionnaires/${cloned.id}/edit`);
    } catch (err) {
      alert('Failed to clone questionnaire');
    }
    setActionMenuId(null);
  };

  // Handle bulk delete
  const handleBulkDelete = async () => {
    if (!window.confirm(`Are you sure you want to delete ${selectedIds.length} questionnaires?`)) {
      return;
    }
    try {
      await questionnaireApi.bulkDelete(selectedIds);
      setSelectedIds([]);
      fetchQuestionnaires();
    } catch (err) {
      alert('Failed to delete questionnaires');
    }
  };

  // Toggle selection
  const toggleSelect = (id) => {
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((i) => i !== id) : [...prev, id]
    );
  };

  // Select all
  const toggleSelectAll = () => {
    if (selectedIds.length === questionnaires.length) {
      setSelectedIds([]);
    } else {
      setSelectedIds(questionnaires.map((q) => q.id));
    }
  };

  return (
    <div className="p-6 lg:p-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Questionnaires</h1>
          <p className="text-gray-600 mt-1">
            Manage your questionnaire library
          </p>
        </div>
        <Link
          to="/questionnaires/new"
          className="inline-flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
        >
          <Plus size={20} />
          <span>New Questionnaire</span>
        </Link>
      </div>

      {/* Search and Filters */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 mb-6">
        <div className="p-4 flex flex-col sm:flex-row gap-4">
          {/* Search */}
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={20} />
            <input
              type="text"
              placeholder="Search questionnaires..."
              value={filters.search}
              onChange={(e) => setFilters({ ...filters, search: e.target.value })}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
            />
          </div>

          {/* Filter toggle */}
          <button
            onClick={() => setShowFilters(!showFilters)}
            className={`inline-flex items-center gap-2 px-4 py-2 border rounded-lg transition-colors ${
              showFilters ? 'bg-gray-100 border-gray-300' : 'border-gray-300 hover:bg-gray-50'
            }`}
          >
            <Filter size={20} />
            <span>Filters</span>
          </button>

          {/* Refresh */}
          <button
            onClick={fetchQuestionnaires}
            className="inline-flex items-center gap-2 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
          >
            <RefreshCw size={20} className={loading ? 'animate-spin' : ''} />
          </button>
        </div>

        {/* Filter options */}
        {showFilters && (
          <div className="px-4 pb-4 flex flex-wrap gap-4 border-t border-gray-200 pt-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Type</label>
              <select
                value={filters.type}
                onChange={(e) => setFilters({ ...filters, type: e.target.value })}
                className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
              >
                <option value="">All Types</option>
                {Object.entries(typeLabels).map(([value, label]) => (
                  <option key={value} value={value}>{label}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
              <select
                value={filters.status}
                onChange={(e) => setFilters({ ...filters, status: e.target.value })}
                className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
              >
                <option value="">All Statuses</option>
                <option value="draft">Draft</option>
                <option value="active">Active</option>
                <option value="archived">Archived</option>
              </select>
            </div>
          </div>
        )}
      </div>

      {/* Bulk actions */}
      {selectedIds.length > 0 && (
        <div className="bg-primary-50 border border-primary-200 rounded-lg p-4 mb-6 flex items-center justify-between">
          <span className="text-primary-800">
            {selectedIds.length} questionnaire(s) selected
          </span>
          <button
            onClick={handleBulkDelete}
            className="inline-flex items-center gap-2 px-3 py-1.5 bg-red-600 text-white rounded-lg hover:bg-red-700 text-sm"
          >
            <Trash2 size={16} />
            Delete Selected
          </button>
        </div>
      )}

      {/* Error state */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6 text-red-800">
          {error}
        </div>
      )}

      {/* Table */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="px-4 py-3 text-left">
                  <input
                    type="checkbox"
                    checked={selectedIds.length === questionnaires.length && questionnaires.length > 0}
                    onChange={toggleSelectAll}
                    className="rounded border-gray-300"
                  />
                </th>
                <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900">Name</th>
                <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900">Type</th>
                <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900">Status</th>
                <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900">Questions</th>
                <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900">Updated</th>
                <th className="px-4 py-3 text-right text-sm font-semibold text-gray-900">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {loading ? (
                <tr>
                  <td colSpan="7" className="px-4 py-12 text-center text-gray-500">
                    <RefreshCw className="w-8 h-8 animate-spin mx-auto mb-2" />
                    Loading...
                  </td>
                </tr>
              ) : questionnaires.length === 0 ? (
                <tr>
                  <td colSpan="7" className="px-4 py-12 text-center text-gray-500">
                    No questionnaires found.{' '}
                    <Link to="/questionnaires/new" className="text-primary-600 hover:underline">
                      Create your first questionnaire
                    </Link>
                  </td>
                </tr>
              ) : (
                questionnaires.map((q) => {
                  const statusConfig = statusColors[q.status] || statusColors.draft;
                  const StatusIcon = statusConfig.icon;
                  
                  return (
                    <tr key={q.id} className="hover:bg-gray-50">
                      <td className="px-4 py-3">
                        <input
                          type="checkbox"
                          checked={selectedIds.includes(q.id)}
                          onChange={() => toggleSelect(q.id)}
                          className="rounded border-gray-300"
                        />
                      </td>
                      <td className="px-4 py-3">
                        <Link 
                          to={`/questionnaires/${q.id}`}
                          className="font-medium text-gray-900 hover:text-primary-600"
                        >
                          {q.name}
                        </Link>
                        {q.description && (
                          <p className="text-sm text-gray-500 truncate max-w-xs">
                            {q.description}
                          </p>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        <span className="text-sm text-gray-600">
                          {typeLabels[q.type] || q.type}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${statusConfig.bg} ${statusConfig.text}`}>
                          <StatusIcon size={12} />
                          {q.status.charAt(0).toUpperCase() + q.status.slice(1)}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-600">
                        {q.question_count}
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-600">
                        {new Date(q.updated_at).toLocaleDateString()}
                      </td>
                      <td className="px-4 py-3 text-right relative">
                        <button
                          onClick={() => setActionMenuId(actionMenuId === q.id ? null : q.id)}
                          className="p-1 hover:bg-gray-100 rounded"
                        >
                          <MoreVertical size={20} />
                        </button>
                        
                        {/* Action menu */}
                        {actionMenuId === q.id && (
                          <div className="absolute right-0 mt-1 w-48 bg-white rounded-lg shadow-lg border border-gray-200 py-1 z-10">
                            <Link
                              to={`/questionnaires/${q.id}`}
                              className="flex items-center gap-2 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
                              onClick={() => setActionMenuId(null)}
                            >
                              <Eye size={16} />
                              View
                            </Link>
                            <Link
                              to={`/questionnaires/${q.id}/edit`}
                              className="flex items-center gap-2 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
                              onClick={() => setActionMenuId(null)}
                            >
                              <Edit size={16} />
                              Edit
                            </Link>
                            <button
                              onClick={() => handleClone(q.id)}
                              className="w-full flex items-center gap-2 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
                            >
                              <Copy size={16} />
                              Clone
                            </button>
                            <hr className="my-1" />
                            <button
                              onClick={() => handleDelete(q.id)}
                              className="w-full flex items-center gap-2 px-4 py-2 text-sm text-red-600 hover:bg-red-50"
                            >
                              <Trash2 size={16} />
                              Delete
                            </button>
                          </div>
                        )}
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {pagination.totalPages > 1 && (
          <div className="px-4 py-3 border-t border-gray-200 flex items-center justify-between">
            <span className="text-sm text-gray-600">
              Showing {(pagination.page - 1) * pagination.pageSize + 1} to{' '}
              {Math.min(pagination.page * pagination.pageSize, pagination.total)} of{' '}
              {pagination.total} results
            </span>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setPagination({ ...pagination, page: pagination.page - 1 })}
                disabled={pagination.page === 1}
                className="p-2 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <ChevronLeft size={20} />
              </button>
              <span className="px-3 py-1 text-sm">
                Page {pagination.page} of {pagination.totalPages}
              </span>
              <button
                onClick={() => setPagination({ ...pagination, page: pagination.page + 1 })}
                disabled={pagination.page === pagination.totalPages}
                className="p-2 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <ChevronRight size={20} />
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Click outside to close menu */}
      {actionMenuId && (
        <div 
          className="fixed inset-0 z-0" 
          onClick={() => setActionMenuId(null)}
        />
      )}
    </div>
  );
}
