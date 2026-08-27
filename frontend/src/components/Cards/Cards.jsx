import React from 'react';
import styles from './Cards.module.css';

export function StatCard({ title, value, subtitle, icon: Icon, color = 'primary', trend }) {
  return (
    <div className={`${styles.statCard} ${styles[color]}`}>
      <div className={styles.statHeader}>
        <span className={styles.statTitle}>{title}</span>
        {Icon && (
          <div className={styles.statIconWrapper}>
            <Icon size={20} />
          </div>
        )}
      </div>
      <div className={styles.statValueGroup}>
        <span className={styles.statValue}>{value}</span>
        {trend && <span className={styles.statTrend}>{trend}</span>}
      </div>
      {subtitle && <span className={styles.statSubtitle}>{subtitle}</span>}
    </div>
  );
}

export function ReminderCard({ reminder, onRead }) {
  return (
    <div className={`${styles.reminderCard} ${reminder.is_read ? styles.read : styles.unread}`}>
      <div className={styles.reminderDot} />
      <div className={styles.reminderContent}>
        <p className={styles.reminderMessage}>{reminder.message}</p>
        <span className={styles.reminderTime}>
          {new Date(reminder.created_at).toLocaleDateString(undefined, {
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
          })}
        </span>
      </div>
      {!reminder.is_read && onRead && (
        <button onClick={() => onRead(reminder.id)} className={styles.markReadBtn}>
          Mark Read
        </button>
      )}
    </div>
  );
}

export function RecommendationCard({ recommendation }) {
  return (
    <div className={styles.recommendationCard}>
      <div className={styles.recHeader}>
        <span className={styles.recAgent}>✨ {recommendation.agent_source}</span>
        <span className={styles.recDate}>
          {new Date(recommendation.created_at).toLocaleDateString()}
        </span>
      </div>
      <div className={styles.recBody}>
        {recommendation.content.split('\n').map((line, idx) => (
          <p key={idx}>{line}</p>
        ))}
      </div>
    </div>
  );
}
