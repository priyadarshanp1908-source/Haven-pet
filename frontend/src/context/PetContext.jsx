import React, { createContext, useContext, useState, useEffect } from 'react';
import api from '../services/api';
import { useAuth } from './AuthContext';

const PetContext = createContext();

export const PetProvider = ({ children }) => {
  const { user } = useAuth();
  const [pets, setPets] = useState([]);
  const [activePet, setActivePet] = useState(null);
  const [loadingPets, setLoadingPets] = useState(false);

  const fetchPets = async () => {
    if (!user) {
      setPets([]);
      setActivePet(null);
      return;
    }
    setLoadingPets(true);
    try {
      const res = await api.get('/pets');
      setPets(res.data);
      if (res.data.length > 0) {
        // Keep existing active pet if still in list, else pick first
        setActivePet((prev) => {
          if (prev && res.data.some((p) => p.id === prev.id)) {
            return res.data.find((p) => p.id === prev.id);
          }
          return res.data[0];
        });
      } else {
        setActivePet(null);
      }
    } catch (err) {
      console.error('Error loading pets:', err);
    } finally {
      setLoadingPets(false);
    }
  };

  useEffect(() => {
    fetchPets();
  }, [user]);

  const selectPet = (petId) => {
    const found = pets.find((p) => p.id === petId);
    if (found) setActivePet(found);
  };

  return (
    <PetContext.Provider value={{ pets, activePet, loadingPets, fetchPets, selectPet, setActivePet }}>
      {children}
    </PetContext.Provider>
  );
};

export const usePet = () => useContext(PetContext);
