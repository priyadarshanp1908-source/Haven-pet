import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { PetProvider } from './context/PetContext';
import Layout from './components/Layout/Layout';

import Login from './pages/Login';
import Signup from './pages/Signup';
import ForgotPassword from './pages/ForgotPassword';
import Dashboard from './pages/Dashboard';
import PetProfile from './pages/PetProfile';
import AddPet from './pages/AddPet';
import BehaviorLog from './pages/BehaviorLog';
import Chat from './pages/Chat';
import Notifications from './pages/Notifications';
import Reports from './pages/Reports';

const ProtectedRoute = ({ children }) => {
  const { user, loading } = useAuth();
  if (loading) return <div style={{ color: '#fff', padding: '2rem', textAlign: 'center' }}>Loading application...</div>;
  if (!user) return <Navigate to="/login" replace />;
  return children;
};

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <PetProvider>
          <Routes>
            {/* Public Auth Routes */}
            <Route path="/login" element={<Login />} />
            <Route path="/signup" element={<Signup />} />
            <Route path="/forgot-password" element={<ForgotPassword />} />


            {/* Protected App Routes */}
            <Route
              path="/"
              element={
                <ProtectedRoute>
                  <Layout />
                </ProtectedRoute>
              }
            >
              <Route index element={<Dashboard />} />
              <Route path="pets" element={<PetProfile />} />
              <Route path="pets/new" element={<AddPet />} />
              <Route path="behavior" element={<BehaviorLog />} />
              <Route path="chat" element={<Chat />} />
              <Route path="notifications" element={<Notifications />} />
              <Route path="reports" element={<Reports />} />
            </Route>

            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </PetProvider>
      </AuthProvider>
    </BrowserRouter>
  );
}
