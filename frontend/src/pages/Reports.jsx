import React, { useState, useEffect } from 'react';
import { usePet } from '../context/PetContext';
import api from '../services/api';
import { FileText, Download, Calendar, Syringe, Pill, Activity, FileSpreadsheet } from 'lucide-react';
import styles from './Reports.module.css';

export default function Reports() {
  const { activePet } = usePet();
  const [downloading, setDownloading] = useState(false);
  const [vaxes, setVaxes] = useState([]);
  const [meds, setMeds] = useState([]);
  const [logs, setLogs] = useState([]);

  useEffect(() => {
    if (activePet) {
      loadTimeline(activePet.id);
    }
  }, [activePet]);

  const loadTimeline = async (petId) => {
    try {
      const [vRes, mRes, lRes] = await Promise.all([
        api.get(`/pets/${petId}/vaccinations`),
        api.get(`/pets/${petId}/medications`),
        api.get(`/pets/${petId}/behavior-logs?limit=30`),
      ]);
      setVaxes(vRes.data);
      setMeds(mRes.data);
      setLogs(lRes.data);
    } catch (e) {
      console.error('Error loading report timeline:', e);
    }
  };

  const handleExport = async (format) => {
    if (!activePet) return;
    setDownloading(true);
    try {
      const response = await api.get(`/pets/${activePet.id}/report?format=${format}`, {
        responseType: 'blob',
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `${activePet.name}_health_report.${format}`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      alert('Failed to generate export file.');
    } finally {
      setDownloading(false);
    }
  };

  if (!activePet) {
    return (
      <div className={styles.emptyState}>
        <h2>No Active Pet Selected</h2>
        <p>Please select a pet profile to view and export health reports.</p>
      </div>
    );
  }

  // Combine events into timeline
  const timelineEvents = [
    ...vaxes.map((v) => ({
      id: `vax-${v.id}`,
      type: 'vaccine',
      title: `Vaccination: ${v.vaccine_name}`,
      date: v.date_administered,
      details: v.next_due_date ? `Next Due: ${v.next_due_date}` : 'Completed',
    })),
    ...meds.map((m) => ({
      id: `med-${m.id}`,
      type: 'medication',
      title: `Medication: ${m.name} (${m.dosage})`,
      date: m.start_date,
      details: `Schedule: ${m.schedule}`,
    })),
    ...logs.map((l) => ({
      id: `log-${l.id}`,
      type: 'behavior',
      title: `Behavior Log: ${l.category}`,
      date: l.logged_at,
      details: `${l.value || ''} ${l.flagged_anomaly ? '⚠️ Anomaly Flagged' : ''}`,
    })),
  ].sort((a, b) => new Date(b.date) - new Date(a.date));

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <div>
          <h1>Health & Medical Reports</h1>
          <p>Full exportable history and timeline for <strong>{activePet.name}</strong>.</p>
        </div>

        <div className={styles.exportGroup}>
          <button
            onClick={() => handleExport('csv')}
            disabled={downloading}
            className="btn-secondary"
          >
            <FileSpreadsheet size={16} /> Export CSV
          </button>
          <button
            onClick={() => handleExport('pdf')}
            disabled={downloading}
            className="btn-primary"
          >
            <Download size={16} /> Export PDF Report
          </button>
        </div>
      </div>

      <div className="glass-card" style={{ padding: '2rem' }}>
        <h3 style={{ marginBottom: '1.5rem' }}>🗓️ Complete Health Timeline</h3>

        {timelineEvents.length > 0 ? (
          <div className={styles.timeline}>
            {timelineEvents.map((item) => (
              <div key={item.id} className={styles.timelineItem}>
                <div className={styles.timelineIcon}>
                  {item.type === 'vaccine' && <Syringe size={16} />}
                  {item.type === 'medication' && <Pill size={16} />}
                  {item.type === 'behavior' && <Activity size={16} />}
                </div>

                <div className={styles.timelineContent}>
                  <div className={styles.timelineHeader}>
                    <strong>{item.title}</strong>
                    <span className={styles.timelineDate}>
                      {new Date(item.date).toLocaleDateString(undefined, {
                        month: 'short',
                        day: 'numeric',
                        year: 'numeric',
                      })}
                    </span>
                  </div>
                  <p className={styles.timelineDetails}>{item.details}</p>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className={styles.noEvents}>No records logged in pet history yet.</p>
        )}
      </div>
    </div>
  );
}
