import React, { useState } from 'react';
import { usePet } from '../context/PetContext';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import { Dog, Sparkles, Upload, ArrowRight, Check } from 'lucide-react';
import styles from './AddPet.module.css';

export default function AddPet() {
  const { fetchPets, selectPet } = usePet();
  const navigate = useNavigate();

  const [formData, setFormData] = useState({
    name: '',
    species: 'dog',
    breed: '',
    weight: '',
    gender: 'male',
    dob: '',
    medical_history: '',
  });

  const [photoFile, setPhotoFile] = useState(null);
  const [photoPreview, setPhotoPreview] = useState(null);
  const [analyzingML, setAnalyzingML] = useState(false);
  const [mlTags, setMlTags] = useState(null);
  const [loading, setLoading] = useState(false);

  const handlePhotoSelect = (e) => {
    const file = e.target.files[0];
    if (file) {
      setPhotoFile(file);
      setPhotoPreview(URL.createObjectURL(file));
    }
  };

  const handleRunAIIdentify = async () => {
    if (!photoFile) {
      alert('Please upload a photo first to run AI recognition.');
      return;
    }
    setAnalyzingML(true);
    try {
      const data = new FormData();
      data.append('file', photoFile);
      const res = await api.post('/ml/recognize', data, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setMlTags(res.data);
      if (res.data.species) {
        const spec = res.data.species.toLowerCase();
        let matchedSpecies = 'other';
        if (spec.includes('dog')) matchedSpecies = 'dog';
        else if (spec.includes('cat')) matchedSpecies = 'cat';
        else if (spec.includes('bird') || spec.includes('parrot')) matchedSpecies = 'bird';
        else if (spec.includes('lizard') || spec.includes('gecko') || spec.includes('dragon')) matchedSpecies = 'lizard';
        else if (spec.includes('reptile') || spec.includes('snake') || spec.includes('turtle')) matchedSpecies = 'reptile';
        else if (spec.includes('rabbit') || spec.includes('bunny')) matchedSpecies = 'rabbit';
        else if (spec.includes('insect') || spec.includes('tarantula') || spec.includes('beetle') || spec.includes('mantis')) matchedSpecies = 'insect';
        else if (spec.includes('fish') || spec.includes('aquatic') || spec.includes('betta')) matchedSpecies = 'fish';

        setFormData((prev) => ({
          ...prev,
          species: matchedSpecies,
          breed: res.data.breed || prev.breed,
        }));
      }
    } catch (err) {
      console.error('ML error:', err);
    } finally {
      setAnalyzingML(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const res = await api.post('/pets', {
        ...formData,
        weight: formData.weight ? parseFloat(formData.weight) : null,
      });
      const newPet = res.data;

      if (photoFile) {
        const photoData = new FormData();
        photoData.append('file', photoFile);
        await api.post(`/pets/${newPet.id}/photo`, photoData, {
          headers: { 'Content-Type': 'multipart/form-data' },
        });
      }

      await fetchPets();
      selectPet(newPet.id);
      navigate('/pets');
    } catch (err) {
      alert('Failed to add pet.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.addPetContainer}>
      <div className="glass-card" style={{ padding: '2.5rem', maxWidth: '720px', margin: '0 auto' }}>
        <div className={styles.header}>
          <div className={styles.iconCircle}>
            <Dog size={28} />
          </div>
          <h2>Add New Pet Profile</h2>
          <p>Tell us about your pet so our AI can provide personalized care advice.</p>
        </div>

        <form onSubmit={handleSubmit} className={styles.form}>
          {/* Photo Upload & AI Scan Section */}
          <div className={styles.photoSection}>
            <div className={styles.photoBox}>
              {photoPreview ? (
                <img src={photoPreview} alt="Preview" />
              ) : (
                <div className={styles.photoPlaceholder}>
                  <Upload size={28} />
                  <span>Upload Photo</span>
                </div>
              )}
              <input type="file" accept="image/*" onChange={handlePhotoSelect} className={styles.hiddenInput} />
            </div>

            <div className={styles.aiRecognizeBox}>
              <h4>✨ AI Breed & Species Detection</h4>
              <p>Upload a photo and let our ML model auto-identify species & breed tags.</p>
              <button
                type="button"
                onClick={handleRunAIIdentify}
                disabled={!photoFile || analyzingML}
                className="btn-secondary"
                style={{ marginTop: '0.5rem', fontSize: '0.85rem' }}
              >
                <Sparkles size={14} /> {analyzingML ? 'Analyzing...' : 'Auto-Detect with AI'}
              </button>

              {mlTags && (
                <div className={styles.mlResult}>
                  <Check size={16} color="var(--accent-emerald)" />
                  <span>Detected: <strong>{mlTags.species}</strong> ({mlTags.breed})</span>
                </div>
              )}
            </div>
          </div>

          <div className={styles.fieldsGrid}>
            <div className="input-group">
              <label className="input-label">Pet Name *</label>
              <input
                type="text"
                required
                placeholder="e.g. Luna"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="input-field"
              />
            </div>

            <div className="input-group">
              <label className="input-label">Species *</label>
              <select
                value={formData.species}
                onChange={(e) => setFormData({ ...formData, species: e.target.value })}
                className="input-field"
              >
                <option value="dog">Dog 🐕</option>
                <option value="cat">Cat 🐱</option>
                <option value="bird">Bird 🦜</option>
                <option value="lizard">Lizard 🦎</option>
                <option value="reptile">Reptile 🐍</option>
                <option value="rabbit">Rabbit 🐇</option>
                <option value="insect">Insect / Spider 🦗</option>
                <option value="fish">Fish / Aquatic 🐠</option>
                <option value="other">Other 🐾</option>
              </select>
            </div>

            <div className="input-group">
              <label className="input-label">Breed</label>
              <input
                type="text"
                placeholder="e.g. Golden Retriever"
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
                placeholder="e.g. 14.5"
                value={formData.weight}
                onChange={(e) => setFormData({ ...formData, weight: e.target.value })}
                className="input-field"
              />
            </div>

            <div className="input-group">
              <label className="input-label">Gender</label>
              <select
                value={formData.gender}
                onChange={(e) => setFormData({ ...formData, gender: e.target.value })}
                className="input-field"
              >
                <option value="male">Male</option>
                <option value="female">Female</option>
              </select>
            </div>

            <div className="input-group">
              <label className="input-label">Date of Birth</label>
              <input
                type="date"
                value={formData.dob}
                onChange={(e) => setFormData({ ...formData, dob: e.target.value })}
                className="input-field"
              />
            </div>

            <div className="input-group" style={{ gridColumn: '1 / -1' }}>
              <label className="input-label">Initial Medical History & Notes</label>
              <textarea
                rows={3}
                placeholder="Vaccinations, known allergies, pre-existing conditions..."
                value={formData.medical_history}
                onChange={(e) => setFormData({ ...formData, medical_history: e.target.value })}
                className="input-field"
              />
            </div>
          </div>

          <div className={styles.actions}>
            <button type="button" onClick={() => navigate('/pets')} className="btn-secondary">
              Cancel
            </button>
            <button type="submit" disabled={loading} className="btn-primary">
              {loading ? 'Creating...' : 'Create Pet Profile'} <ArrowRight size={16} />
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
