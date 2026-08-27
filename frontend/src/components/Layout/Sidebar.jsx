import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { 
  LayoutDashboard, 
  Dog, 
  Activity, 
  MessageSquare, 
  Bell, 
  FileText, 
  LogOut, 
  PlusCircle,
  Sparkles
} from 'lucide-react';
import styles from './Sidebar.module.css';

export default function Sidebar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const navItems = [
    { label: 'Dashboard', path: '/', icon: LayoutDashboard },
    { label: 'Pet Profiles', path: '/pets', icon: Dog },
    { label: 'Behavior Log', path: '/behavior', icon: Activity },
    { label: 'AI Chat Assistant', path: '/chat', icon: MessageSquare, badge: 'AI' },
    { label: 'Reminders', path: '/notifications', icon: Bell },
    { label: 'Health Reports', path: '/reports', icon: FileText },
  ];

  return (
    <aside className={styles.sidebar}>
      {/* Brand Header */}
      <div className={styles.brand}>
        <div className={styles.logoIcon}>
          <img src="/haven_pet_logo.svg" alt="Haven Pet Logo" className={styles.logoImg} />
        </div>
        <div className={styles.brandText}>
          <h2>Haven Pet</h2>
          <span className={styles.brandSubtitle}>AI Care Companion</span>
        </div>
      </div>


      {/* Navigation */}
      <nav className={styles.nav}>
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                `${styles.navItem} ${isActive ? styles.active : ''}`
              }
            >
              <Icon size={20} />
              <span>{item.label}</span>
              {item.badge && <span className={styles.navBadge}>{item.badge}</span>}
            </NavLink>
          );
        })}
      </nav>

      {/* Quick Action */}
      <div className={styles.quickAction}>
        <NavLink to="/pets/new" className={styles.addPetBtn}>
          <PlusCircle size={18} />
          <span>Add New Pet</span>
        </NavLink>
      </div>

      {/* User Footer */}
      <div className={styles.footer}>
        <div className={styles.userInfo}>
          <div className={styles.avatar}>{user?.name?.charAt(0) || 'U'}</div>
          <div className={styles.userMeta}>
            <span className={styles.userName}>{user?.name || 'User'}</span>
            <span className={styles.userEmail}>{user?.email}</span>
          </div>
        </div>
        <button onClick={handleLogout} className={styles.logoutBtn} title="Sign Out">
          <LogOut size={18} />
        </button>
      </div>
    </aside>
  );
}
