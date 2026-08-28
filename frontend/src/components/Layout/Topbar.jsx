import React, { useEffect, useState } from 'react';
import { usePet } from '../../context/PetContext';
import { useNavigate } from 'react-router-dom';
import { Dog, Bell, ChevronDown, Plus } from 'lucide-react';
import api, { API_URL } from '../../services/api';
import styles from './Topbar.module.css';

export default function Topbar() {
  const { pets, activePet, selectPet } = usePet();
  const navigate = useNavigate();
  const [unreadCount, setUnreadCount] = useState(0);

  useEffect(() => {
    const fetchUnread = async () => {
      try {
        const res = await api.get('/notifications?unread_only=true');
        setUnreadCount(res.data.length);
      } catch (e) {
        // ignore auth error during init
      }
    };
    fetchUnread();
    const interval = setInterval(fetchUnread, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header className={styles.topbar}>
      {/* Active Pet Selector */}
      <div className={styles.petSelectorContainer}>
        <span className={styles.selectorLabel}>Active Pet:</span>
        {pets.length > 0 ? (
          <div className={styles.customSelect}>
            <select
              value={activePet?.id || ''}
              onChange={(e) => selectPet(e.target.value)}
              className={styles.petSelect}
            >
              {pets.map((pet) => (
                <option key={pet.id} value={pet.id}>
                  🐾 {pet.name} ({pet.species} - {pet.breed || 'Mix'})
                </option>
              ))}
            </select>
            <ChevronDown size={16} className={styles.selectArrow} />
          </div>
        ) : (
          <button onClick={() => navigate('/pets/new')} className={styles.noPetBtn}>
            <Plus size={16} /> Add First Pet
          </button>
        )}
      </div>

      {/* Actions */}
      <div className={styles.actions}>
        <button
          onClick={() => navigate('/notifications')}
          className={styles.iconBtn}
          title="Notifications"
        >
          <Bell size={20} />
          {unreadCount > 0 && <span className={styles.badge}>{unreadCount}</span>}
        </button>

        {activePet && (
          <div className={styles.activePetChip} onClick={() => navigate(`/pets`)}>
            <div className={styles.chipAvatar}>
              {activePet.photo_url ? (
                <img src={`${API_URL}${activePet.photo_url}`} alt={activePet.name} />
              ) : (
                <Dog size={16} />
              )}
            </div>
            <div className={styles.chipMeta}>
              <span className={styles.chipName}>{activePet.name}</span>
              <span className={styles.chipSpec}>{activePet.species}</span>
            </div>
          </div>
        )}
      </div>
    </header>
  );
}
