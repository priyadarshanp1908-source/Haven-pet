import React, { useEffect, useState } from 'react';
import { usePet } from '../context/PetContext';
import { useNavigate, Link } from 'react-router-dom';
import api from '../services/api';
import { StatCard, ReminderCard, RecommendationCard } from '../components/Cards/Cards';
import { 
  Dog, 
  Weight, 
  Calendar, 
  Activity, 
  AlertTriangle, 
  Sparkles, 
  Plus, 
  MessageSquare, 
  ArrowRight,
  TrendingUp
} from 'lucide-react';
import styles from './Dashboard.module.css';

export default function Dashboard() {
  const { activePet, pets, loadingPets } = usePet();
  const navigate = useNavigate();

  const [reminders, setReminders] = useState([]);
  const [recommendations, setRecommendations] = useState([]);
  const [behaviorLogs, setBehaviorLogs] = useState([]);
  const [generatingRec, setGeneratingRec] = useState(false);
  const [loadingData, setLoadingData] = useState(false);

  useEffect(() => {
    if (activePet) {
      loadPetDashboardData(activePet.id);
    }
  }, [activePet]);

  const loadPetDashboardData = async (petId) => {
    setLoadingData(true);
    try {
      const [remRes, recRes, logRes] = await Promise.all([
        api.get('/notifications?unread_only=true'),
        api.get(`/pets/${petId}/recommendations`),
        api.get(`/pets/${petId}/behavior-logs?limit=10`),
      ]);
      setReminders(remRes.data.filter((r) => !r.pet_id || r.pet_id === petId));
      setRecommendations(recRes.data);
      setBehaviorLogs(logRes.data);
    } catch (err) {
      console.error('Error loading dashboard data:', err);
    } finally {
      setLoadingData(false);
    }
  };

  const handleGenerateRec = async () => {
    if (!activePet) return;
    setGeneratingRec(true);
    try {
      const res = await api.post(`/pets/${activePet.id}/recommendations`);
      setRecommendations((prev) => [res.data, ...prev]);
    } catch (err) {
      console.error('Error generating recommendation:', err);
    } finally {
      setGeneratingRec(false);
    }
  };

  if (loadingPets) {
    return <div className={styles.loadingState}>Loading pet profiles...</div>;
  }

  if (!activePet && pets.length === 0) {
    return (
      <div className={styles.emptyState}>
        <div className={styles.emptyIcon}>🐾</div>
        <h2>Welcome to Haven Pet!</h2>
        <p>You haven't added any pets yet. Let's create your first pet profile to get started.</p>
        <button onClick={() => navigate('/pets/new')} className="btn-primary" style={{ marginTop: '1rem' }}>
          <Plus size={18} /> Add Your First Pet
        </button>
      </div>
    );
  }

  return (
    <div className={styles.dashboardGrid}>
      {/* Pet Header Banner */}
      <div className={styles.petBanner}>
        <div className={styles.bannerAvatar}>
          {activePet?.photo_url ? (
            <img src={`http://localhost:8000${activePet.photo_url}`} alt={activePet.name} />
          ) : (
            <Dog size={36} />
          )}
        </div>
        <div className={styles.bannerInfo}>
          <h1>{activePet?.name}</h1>
          <div className={styles.bannerBadges}>
            <span className={styles.badgeChip}>{activePet?.species}</span>
            <span className={styles.badgeChip}>{activePet?.breed || 'Mix Breed'}</span>
            <span className={styles.badgeChip}>{activePet?.gender || 'Pet'}</span>
          </div>
        </div>
        <div className={styles.bannerActions}>
          <button onClick={() => navigate('/behavior')} className="btn-secondary">
            <Plus size={16} /> Log Activity
          </button>
          <button onClick={() => navigate('/chat')} className="btn-primary">
            <MessageSquare size={16} /> Ask AI Assistant
          </button>
        </div>
      </div>

      {/* Metrics Row */}
      <div className={styles.metricsRow}>
        <StatCard
          title="Weight"
          value={activePet?.weight ? `${activePet.weight} kg` : 'N/A'}
          subtitle="Last recorded weight"
          icon={Weight}
          color="primary"
        />
        <StatCard
          title="Behavior Entries"
          value={behaviorLogs.length}
          subtitle="Total logged routines"
          icon={Activity}
          color="teal"
        />
        <StatCard
          title="Pending Reminders"
          value={reminders.length}
          subtitle={reminders.length > 0 ? 'Upcoming tasks' : 'All clear'}
          icon={TrendingUp}
          color="pink"
        />
        <StatCard
          title="Date of Birth"
          value={activePet?.dob ? new Date(activePet.dob).toLocaleDateString() : 'Unknown'}
          subtitle="Age tracker"
          icon={Calendar}
          color="amber"
        />
      </div>

      {/* Main Two-Column Layout */}
      <div className={styles.mainGrid}>
        {/* Left Column: Reminders & Behavior Trend */}
        <div className={styles.leftCol}>
          {/* Upcoming Reminders Card */}
          <div className="glass-card" style={{ padding: '1.5rem' }}>
            <div className={styles.cardHeader}>
              <h3>🔔 Active Reminders</h3>
              <Link to="/notifications" className={styles.linkText}>
                View All <ArrowRight size={14} />
              </Link>
            </div>
            {reminders.length > 0 ? (
              <div className={styles.reminderList}>
                {reminders.slice(0, 4).map((rem) => (
                  <ReminderCard key={rem.id} reminder={rem} />
                ))}
              </div>
            ) : (
              <p className={styles.noData}>No pending reminders. All vaccination and medication schedules are up to date!</p>
            )}
          </div>

          {/* Recent Behavior Logs */}
          <div className="glass-card" style={{ padding: '1.5rem', marginTop: '1.5rem' }}>
            <div className={styles.cardHeader}>
              <h3>📊 Recent Routine Activity</h3>
              <Link to="/behavior" className={styles.linkText}>
                Full Log <ArrowRight size={14} />
              </Link>
            </div>
            {behaviorLogs.length > 0 ? (
              <div className={styles.logList}>
                {behaviorLogs.slice(0, 5).map((log) => (
                  <div key={log.id} className={styles.logItem}>
                    <span className={styles.logCat}>
                      {log.category === 'eating' && '🍽️'}
                      {log.category === 'sleep' && '😴'}
                      {log.category === 'activity' && '🏃'}
                      {log.category === 'mood' && '😊'}
                      {log.category === 'bathroom' && '🚾'}
                      {log.category === 'other' && '📌'}{' '}
                      <strong>{log.category}</strong>
                    </span>
                    <span className={styles.logVal}>{log.value || 'Logged'}</span>
                  </div>
                ))}
              </div>
            ) : (
              <p className={styles.noData}>No behavior logs added yet. Click "Log Activity" to start tracking daily habits.</p>
            )}
          </div>
        </div>

        {/* Right Column: AI Recommendations */}
        <div className={styles.rightCol}>
          <div className="glass-card" style={{ padding: '1.5rem' }}>
            <div className={styles.cardHeader}>
              <h3>✨ AI Care Recommendations</h3>
              <button
                onClick={handleGenerateRec}
                disabled={generatingRec}
                className={styles.genBtn}
              >
                <Sparkles size={14} /> {generatingRec ? 'Analyzing...' : 'Refresh AI Advice'}
              </button>
            </div>

            {recommendations.length > 0 ? (
              <div className={styles.recList}>
                {recommendations.slice(0, 2).map((rec) => (
                  <RecommendationCard key={rec.id} recommendation={rec} />
                ))}
              </div>
            ) : (
              <div className={styles.emptyRec}>
                <Sparkles size={32} className={styles.sparkleIcon} />
                <p>No recommendations generated yet. Click "Refresh AI Advice" to analyze your pet's breed and logs!</p>
                <button onClick={handleGenerateRec} disabled={generatingRec} className="btn-primary" style={{ marginTop: '0.75rem' }}>
                  Generate Recommendations
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
