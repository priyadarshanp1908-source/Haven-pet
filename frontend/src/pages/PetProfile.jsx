import React, { useState, useEffect } from 'react';
import { usePet } from '../context/PetContext';
import api, { API_URL } from '../services/api';
import { Dog, Upload, Plus, Calendar, Weight, Syringe, Pill, Edit2, Save, Trash2 } from 'lucide-react';
import styles from './PetProfile.module.css';

export default function PetProfile() {
  const { activePet, fetchPets, selectPet, pets } = usePet();
  
  const [editing, setEditing] = useState(false);
  const [formData, setFormData] = useState({
    name: '', species: '', breed: '', weight: '', gender: '', dob: '', medical_history: ''
  });
  const [vaccinations, setVaccinations] = useState([]);
  const [medications, setMedications] = useState([]);
  
  // New modal forms
  const [showVaxModal, setShowVaxModal] = useState(false);
  const [vaxForm, setVaxForm] = useState({ vaccine_name: '', date_administered: '', next_due_date: '' });
  
  const [showMedModal, setShowMedModal] = useState(false);
  const [medForm, setMedForm] = useState({ name: '', dosage: '', schedule: '', start_date: '', end_date: '', notes: '' });

  const [uploading, setUploading] = useState(false);

  useEffect(() => {
    if (activePet) {
      setFormData({
        name: activePet.name || '',
        species: activePet.species || '',
        breed: activePet.breed || '',
        weight: activePet.weight || '',
        gender: activePet.gender || '',
        dob: activePet.dob || '',
        medical_history: activePet.medical_history || '',
      });
      loadPetSubResources(activePet.id);
    }
  }, [activePet]);

  const loadPetSubResources = async (petId) => {
    try {
      const [vaxRes, medRes] = await Promise.all([
        api.get(`/pets/${petId}/vaccinations`),
        api.get(`/pets/${petId}/medications`),
      ]);
      setVaccinations(vaxRes.data);
      setMedications(medRes.data);
    } catch (e) {
      console.error('Error loading sub-resources:', e);
    }
  };

  const handleProfileSave = async (e) => {
    e.preventDefault();
    if (!activePet) return;
    try {
      await api.put(`/pets/${activePet.id}`, {
        ...formData,
        weight: formData.weight ? parseFloat(formData.weight) : null,
      });
      await fetchPets();
      setEditing(false);
    } catch (err) {
      alert('Failed to update pet profile.');
    }
  };

  const handlePhotoUpload = async (e) => {
    const file = e.target.files[0];
    if (!file || !activePet) return;
    const data = new FormData();
    data.append('file', file);
    setUploading(true);
    try {
      await api.post(`/pets/${activePet.id}/photo`, data, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      await fetchPets();
    } catch (err) {
      alert('Photo upload failed.');
    } finally {
      setUploading(false);
    }
  };

  const handleAddVax = async (e) => {
    e.preventDefault();
    if (!activePet) return;
    try {
      await api.post(`/pets/${activePet.id}/vaccinations`, vaxForm);
      setShowVaxModal(false);
      setVaxForm({ vaccine_name: '', date_administered: '', next_due_date: '' });
      loadPetSubResources(activePet.id);
    } catch (err) {
      alert('Failed to add vaccination.');
    }
  };

  const handleAddMed = async (e) => {
    e.preventDefault();
    if (!activePet) return;
    try {
      await api.post(`/pets/${activePet.id}/medications`, medForm);
      setShowMedModal(false);
      setMedForm({ name: '', dosage: '', schedule: '', start_date: '', end_date: '', notes: '' });
      loadPetSubResources(activePet.id);
    } catch (err) {
      alert('Failed to add medication.');
    }
  };

  const handleDeletePet = async () => {
    if (!activePet) return;
    if (window.confirm(`Are you sure you want to delete ${activePet.name}? This cannot be undone.`)) {
      try {
        await api.delete(`/pets/${activePet.id}`);
        await fetchPets();
      } catch (e) {
        alert('Failed to delete pet.');
      }
    }
  };

  if (!activePet) {
    return (
      <div className={styles.emptyContainer}>
        <h2>No Pet Selected</h2>
        <p>Please select or add a pet profile first.</p>
      </div>
    );
  }

  return (
    <div className={styles.profileContainer}>
      {/* Header / Avatar Card */}
      <div className="glass-card" style={{ padding: '2rem' }}>
        <div className={styles.headerFlex}>
          <div className={styles.avatarWrapper}>
            <div className={styles.avatar}>
              {activePet.photo_url ? (
                <img src={`${API_URL}${activePet.photo_url}`} alt={activePet.name} />
              ) : (
                <Dog size={48} />
              )}
            </div>
            <label className={styles.uploadBtn} title="Upload Photo">
              <Upload size={14} />
              <input type="file" accept="image/*" onChange={handlePhotoUpload} style={{ display: 'none' }} />
            </label>
          </div>

          <div className={styles.petHeaderMeta}>
            <div className={styles.titleRow}>
              <h1>{activePet.name}</h1>
              <span className={styles.speciesBadge}>{activePet.species}</span>
            </div>
            <p className={styles.subtitle}>
              {activePet.breed || 'Breed unspecified'} • {activePet.gender || 'Gender unspecified'}
            </p>
          </div>

          <div className={styles.headerActions}>
            {!editing ? (
              <button onClick={() => setEditing(true)} className="btn-secondary">
                <Edit2 size={16} /> Edit Profile
              </button>
            ) : (
              <button onClick={() => setEditing(false)} className="btn-secondary">
                Cancel
              </button>
            )}
            <button onClick={handleDeletePet} className={styles.deleteBtn} title="Delete Pet">
              <Trash2 size={16} />
            </button>
          </div>
        </div>
      </div>

      {/* Main Form & Sub-resources Grid */}
      <div className={styles.gridTwoCol}>
        {/* Profile Info Form */}
        <div className="glass-card" style={{ padding: '1.75rem' }}>
          <h3>📋 General Information</h3>

          <form onSubmit={handleProfileSave} className={styles.formGrid}>
            <div className="input-group">
              <label className="input-label">Pet Name</label>
              <input
                type="text"
                disabled={!editing}
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="input-field"
              />
            </div>

            <div className="input-group">
              <label className="input-label">Species</label>
              <input
                type="text"
                disabled={!editing}
                value={formData.species}
                onChange={(e) => setFormData({ ...formData, species: e.target.value })}
                className="input-field"
              />
            </div>

            <div className="input-group">
              <label className="input-label">Breed</label>
              <input
                type="text"
                disabled={!editing}
                value={formData.breed}
                onChange={(e) => setFormData({ ...formData, breed: e.target.value })}
                className="input-field"
              />
            </div>

            <div className="input-group">
              <label className="input-label">Weight (kg)</label>
              <input
                type="number"
                step="0.1"
                disabled={!editing}
                value={formData.weight}
                onChange={(e) => setFormData({ ...formData, weight: e.target.value })}
                className="input-field"
              />
            </div>

            <div className="input-group">
              <label className="input-label">Date of Birth</label>
              <input
                type="date"
                disabled={!editing}
                value={formData.dob}
                onChange={(e) => setFormData({ ...formData, dob: e.target.value })}
                className="input-field"
              />
            </div>

            <div className="input-group">
              <label className="input-label">Gender</label>
              <select
                disabled={!editing}
                value={formData.gender}
                onChange={(e) => setFormData({ ...formData, gender: e.target.value })}
                className="input-field"
              >
                <option value="">Select Gender</option>
                <option value="male">Male</option>
                <option value="female">Female</option>
              </select>
            </div>

            <div className="input-group" style={{ gridColumn: '1 / -1' }}>
              <label className="input-label">Medical History & Allergy Notes</label>
              <textarea
                rows={3}
                disabled={!editing}
                value={formData.medical_history}
                onChange={(e) => setFormData({ ...formData, medical_history: e.target.value })}
                className="input-field"
              />
            </div>

            {editing && (
              <div style={{ gridColumn: '1 / -1', display: 'flex', justifyContent: 'flex-end' }}>
                <button type="submit" className="btn-primary">
                  <Save size={16} /> Save Changes
                </button>
              </div>
            )}
          </form>
        </div>

        {/* Right Col: Vaccinations & Medications */}
        <div className={styles.rightCol}>
          {/* Vaccinations */}
          <div className="glass-card" style={{ padding: '1.5rem' }}>
            <div className={styles.sectionHeader}>
              <h3>💉 Vaccinations ({vaccinations.length})</h3>
              <button onClick={() => setShowVaxModal(true)} className={styles.addSmallBtn}>
                <Plus size={14} /> Add
              </button>
            </div>

            {vaccinations.length > 0 ? (
              <div className={styles.recordList}>
                {vaccinations.map((v) => (
                  <div key={v.id} className={styles.recordItem}>
                    <div className={styles.recordMain}>
                      <strong>{v.vaccine_name}</strong>
                      <span className={styles.recordSub}>Administered: {v.date_administered}</span>
                    </div>
                    {v.next_due_date && (
                      <span className={styles.dueBadge}>Due: {v.next_due_date}</span>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <p className={styles.emptyNote}>No vaccination records added.</p>
            )}
          </div>

          {/* Medications */}
          <div className="glass-card" style={{ padding: '1.5rem', marginTop: '1.5rem' }}>
            <div className={styles.sectionHeader}>
              <h3>💊 Medication Schedule ({medications.length})</h3>
              <button onClick={() => setShowMedModal(true)} className={styles.addSmallBtn}>
                <Plus size={14} /> Add
              </button>
            </div>

            {medications.length > 0 ? (
              <div className={styles.recordList}>
                {medications.map((m) => (
                  <div key={m.id} className={styles.recordItem}>
                    <div className={styles.recordMain}>
                      <strong>{m.name}</strong> ({m.dosage})
                      <span className={styles.recordSub}>{m.schedule} • Starts: {m.start_date}</span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className={styles.emptyNote}>No medication schedules added.</p>
            )}
          </div>
        </div>
      </div>

      {/* Add Vaccination Modal */}
      {showVaxModal && (
        <div className={styles.modalOverlay}>
          <div className={styles.modalContent}>
            <h3>Add Vaccination Record</h3>
            <form onSubmit={handleAddVax} className={styles.modalForm}>
              <div className="input-group">
                <label className="input-label">Vaccine Name</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Rabies, DHPP"
                  value={vaxForm.vaccine_name}
                  onChange={(e) => setVaxForm({ ...vaxForm, vaccine_name: e.target.value })}
                  className="input-field"
                />
              </div>
              <div className="input-group">
                <label className="input-label">Date Administered</label>
                <input
                  type="date"
                  required
                  value={vaxForm.date_administered}
                  onChange={(e) => setVaxForm({ ...vaxForm, date_administered: e.target.value })}
                  className="input-field"
                />
              </div>
              <div className="input-group">
                <label className="input-label">Next Due Date (Optional)</label>
                <input
                  type="date"
                  value={vaxForm.next_due_date}
                  onChange={(e) => setVaxForm({ ...vaxForm, next_due_date: e.target.value })}
                  className="input-field"
                />
              </div>
              <div className={styles.modalActions}>
                <button type="button" onClick={() => setShowVaxModal(false)} className="btn-secondary">
                  Cancel
                </button>
                <button type="submit" className="btn-primary">
                  Save Vaccine
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Add Medication Modal */}
      {showMedModal && (
        <div className={styles.modalOverlay}>
          <div className={styles.modalContent}>
            <h3>Add Medication Schedule</h3>
            <form onSubmit={handleAddMed} className={styles.modalForm}>
              <div className="input-group">
                <label className="input-label">Medication Name</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Amoxicillin"
                  value={medForm.name}
                  onChange={(e) => setMedForm({ ...medForm, name: e.target.value })}
                  className="input-field"
                />
              </div>
              <div className="input-group">
                <label className="input-label">Dosage</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. 250mg"
                  value={medForm.dosage}
                  onChange={(e) => setMedForm({ ...medForm, dosage: e.target.value })}
                  className="input-field"
                />
              </div>
              <div className="input-group">
                <label className="input-label">Schedule</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Twice daily with food"
                  value={medForm.schedule}
                  onChange={(e) => setMedForm({ ...medForm, schedule: e.target.value })}
                  className="input-field"
                />
              </div>
              <div className="input-group">
                <label className="input-label">Start Date</label>
                <input
                  type="date"
                  required
                  value={medForm.start_date}
                  onChange={(e) => setMedForm({ ...medForm, start_date: e.target.value })}
                  className="input-field"
                />
              </div>
              <div className="input-group">
                <label className="input-label">End Date (Optional)</label>
                <input
                  type="date"
                  value={medForm.end_date}
                  onChange={(e) => setMedForm({ ...medForm, end_date: e.target.value })}
                  className="input-field"
                />
              </div>
              <div className={styles.modalActions}>
                <button type="button" onClick={() => setShowMedModal(false)} className="btn-secondary">
                  Cancel
                </button>
                <button type="submit" className="btn-primary">
                  Save Medication
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
