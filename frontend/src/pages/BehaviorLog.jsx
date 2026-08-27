import React, { useState, useEffect } from 'react';
import { usePet } from '../context/PetContext';
import api from '../services/api';
import { Activity, Plus, Filter, AlertTriangle, Calendar, Search, Edit2, Trash2, Check, X } from 'lucide-react';
import styles from './BehaviorLog.module.css';

export default function BehaviorLog() {
  const { activePet } = usePet();
  
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(false);

  // Form state (New entry)
  const [category, setCategory] = useState('eating');
  const [value, setValue] = useState('');
  const [notes, setNotes] = useState('');
  const [submitting, setSubmitting] = useState(false);

  // Filter state
  const [filterCategory, setFilterCategory] = useState('');
  const [fromDate, setFromDate] = useState('');
  const [toDate, setToDate] = useState('');

  // Edit state
  const [editingId, setEditingId] = useState(null);
  const [editCategory, setEditCategory] = useState('');
  const [editValue, setEditValue] = useState('');
  const [editNotes, setEditNotes] = useState('');
  const [updating, setUpdating] = useState(false);

  useEffect(() => {
    if (activePet) {
      fetchLogs();
    }
  }, [activePet, filterCategory, fromDate, toDate]);

  const fetchLogs = async () => {
    if (!activePet) return;
    setLoading(true);
    try {
      let url = `/pets/${activePet.id}/behavior-logs?`;
      if (filterCategory) url += `category=${filterCategory}&`;
      if (fromDate) url += `from=${new Date(fromDate).toISOString()}&`;
      if (toDate) url += `to=${new Date(toDate).toISOString()}&`;

      const res = await api.get(url);
      setLogs(res.data);
    } catch (err) {
      console.error('Failed to load logs:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateLog = async (e) => {
    e.preventDefault();
    if (!activePet) return;
    setSubmitting(true);
    try {
      await api.post(`/pets/${activePet.id}/behavior-logs`, {
        category,
        value,
        notes,
      });
      setValue('');
      setNotes('');
      fetchLogs();
    } catch (err) {
      alert('Error creating log entry.');
    } finally {
      setSubmitting(false);
    }
  };

  const startEdit = (log) => {
    setEditingId(log.id);
    setEditCategory(log.category);
    setEditValue(log.value || '');
    setEditNotes(log.notes || '');
  };

  const cancelEdit = () => {
    setEditingId(null);
    setEditCategory('');
    setEditValue('');
    setEditNotes('');
  };

  const handleUpdateLog = async (logId) => {
    if (!activePet) return;
    setUpdating(true);
    try {
      await api.put(`/pets/${activePet.id}/behavior-logs/${logId}`, {
        category: editCategory,
        value: editValue,
        notes: editNotes,
      });
      setEditingId(null);
      fetchLogs();
    } catch (err) {
      alert('Error updating log entry.');
    } finally {
      setUpdating(false);
    }
  };

  const handleDeleteLog = async (logId) => {
    if (!activePet) return;
    if (!window.confirm('Are you sure you want to delete this log entry?')) return;
    try {
      await api.delete(`/pets/${activePet.id}/behavior-logs/${logId}`);
      fetchLogs();
    } catch (err) {
      alert('Error deleting log entry.');
    }
  };

  if (!activePet) {
    return (
      <div className={styles.emptyContainer}>
        <h2>No Active Pet Selected</h2>
        <p>Please select a pet from the top dropdown to view or record behavior logs.</p>
      </div>
    );
  }

  const categoryIcons = {
    eating: '🍽️',
    sleep: '😴',
    activity: '🏃',
    mood: '😊',
    bathroom: '🚾',
    other: '📌',
  };

  return (
    <div className={styles.container}>
      {/* Top Header */}
      <div className={styles.header}>
        <div>
          <h1>Routine & Behavior Log</h1>
          <p>Track daily habits, feeding, and activity for <strong>{activePet.name}</strong>.</p>
        </div>
      </div>

      <div className={styles.grid}>
        {/* Form Card */}
        <div className="glass-card" style={{ padding: '1.75rem' }}>
          <h3>📝 Log Daily Entry</h3>
          <form onSubmit={handleCreateLog} className={styles.form}>
            <div className="input-group">
              <label className="input-label">Category</label>
              <select
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                className="input-field"
              >
                <option value="eating">🍽️ Eating / Meal Portion</option>
                <option value="sleep">😴 Sleep & Rest Duration</option>
                <option value="activity">🏃 Physical Exercise / Play</option>
                <option value="mood">😊 Emotional Mood & Behavior</option>
                <option value="bathroom">🚾 Bathroom & Digestion</option>
                <option value="other">📌 Other Note / Observation</option>
              </select>
            </div>

            <div className="input-group">
              <label className="input-label">Value / Quantity</label>
              <input
                type="text"
                placeholder="e.g. 2 cups kibble, 45 min walk, High energy"
                value={value}
                onChange={(e) => setValue(e.target.value)}
                className="input-field"
              />
            </div>

            <div className="input-group">
              <label className="input-label">Detailed Notes</label>
              <textarea
                rows={3}
                placeholder="Describe food, appetite, mood, or activities..."
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                className="input-field"
              />
            </div>

            <button type="submit" disabled={submitting} className="btn-primary" style={{ width: '100%' }}>
              <Plus size={16} /> {submitting ? 'Saving...' : 'Save Log Entry'}
            </button>
          </form>
        </div>

        {/* History & Filters Card */}
        <div className="glass-card" style={{ padding: '1.75rem' }}>
          <div className={styles.historyHeader}>
            <h3>📊 Log History</h3>
            <div className={styles.filters}>
              <select
                value={filterCategory}
                onChange={(e) => setFilterCategory(e.target.value)}
                className={styles.filterSelect}
              >
                <option value="">All Categories</option>
                <option value="eating">Eating</option>
                <option value="sleep">Sleep</option>
                <option value="activity">Activity</option>
                <option value="mood">Mood</option>
                <option value="bathroom">Bathroom</option>
                <option value="other">Other</option>
              </select>

              <input
                type="date"
                value={fromDate}
                onChange={(e) => setFromDate(e.target.value)}
                className={styles.dateInput}
                title="From Date"
              />
              <input
                type="date"
                value={toDate}
                onChange={(e) => setToDate(e.target.value)}
                className={styles.dateInput}
                title="To Date"
              />
            </div>
          </div>

          {loading ? (
            <div className={styles.loading}>Loading log history...</div>
          ) : logs.length > 0 ? (
            <div className={styles.logList}>
              {logs.map((log) => (
                <div key={log.id} className={styles.logCard}>
                  {editingId === log.id ? (
                    /* Inline Edit Mode */
                    <div className={styles.editForm}>
                      <div className={styles.editRow}>
                        <select
                          value={editCategory}
                          onChange={(e) => setEditCategory(e.target.value)}
                          className={styles.editSelect}
                        >
                          <option value="eating">🍽️ Eating</option>
                          <option value="sleep">😴 Sleep</option>
                          <option value="activity">🏃 Activity</option>
                          <option value="mood">😊 Mood</option>
                          <option value="bathroom">🚾 Bathroom</option>
                          <option value="other">📌 Other</option>
                        </select>
                        <input
                          type="text"
                          value={editValue}
                          onChange={(e) => setEditValue(e.target.value)}
                          placeholder="Value / Quantity"
                          className={styles.editInput}
                        />
                      </div>
                      <textarea
                        rows={2}
                        value={editNotes}
                        onChange={(e) => setEditNotes(e.target.value)}
                        placeholder="Notes..."
                        className={styles.editTextarea}
                      />
                      <div className={styles.editActions}>
                        <button
                          onClick={() => handleUpdateLog(log.id)}
                          disabled={updating}
                          className={styles.saveBtn}
                          title="Save Changes"
                        >
                          <Check size={14} /> Save
                        </button>
                        <button
                          onClick={cancelEdit}
                          className={styles.cancelBtn}
                          title="Cancel"
                        >
                          <X size={14} /> Cancel
                        </button>
                      </div>
                    </div>
                  ) : (
                    /* View Mode */
                    <>
                      <div className={styles.logCardHeader}>
                        <span className={styles.catTitle}>
                          {categoryIcons[log.category] || '📌'} {log.category}
                        </span>
                        <div className={styles.rightHeaderControls}>
                          <span className={styles.logDate}>
                            {new Date(log.logged_at).toLocaleString([], {
                              month: 'short',
                              day: 'numeric',
                              hour: '2-digit',
                              minute: '2-digit',
                            })}
                          </span>
                          <button
                            onClick={() => startEdit(log)}
                            className={styles.actionBtn}
                            title="Edit entry"
                          >
                            <Edit2 size={14} />
                          </button>
                          <button
                            onClick={() => handleDeleteLog(log.id)}
                            className={`${styles.actionBtn} ${styles.deleteAction}`}
                            title="Delete entry"
                          >
                            <Trash2 size={14} />
                          </button>
                        </div>
                      </div>

                      <div className={styles.logBody}>
                        <p className={styles.logVal}>{log.value || 'No value recorded'}</p>
                        {log.notes && <p className={styles.logNotes}>{log.notes}</p>}
                      </div>
                    </>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <p className={styles.noLogs}>No behavior entries match the selected filters.</p>
          )}
        </div>
      </div>
    </div>
  );
}

