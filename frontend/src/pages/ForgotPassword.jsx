import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { ArrowRight, Lock, Mail, KeyRound, CheckCircle, ArrowLeft, RotateCcw } from 'lucide-react';
import api from '../services/api';
import styles from './Auth.module.css';

export default function ForgotPassword() {
  const navigate = useNavigate();

  const [email, setEmail] = useState('');
  const [otpSent, setOtpSent] = useState(false);
  const [otp, setOtp] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [resending, setResending] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const handleSendOtp = async (e) => {
    if (e) e.preventDefault();
    setError('');
    setSuccess('');

    if (!email || !email.includes('@')) {
      setError('Please enter a valid email address.');
      return;
    }

    setLoading(true);
    try {
      const res = await api.post('/auth/forgot-password', { email: email.trim() });
      setOtpSent(true);
      setSuccess(res.data.message || `OTP verification code sent to your email (${email}). Please check your inbox.`);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to send OTP. Please check your email address.');
    } finally {
      setLoading(false);
    }
  };

  const handleResendOtp = async () => {
    setError('');
    setSuccess('');
    setResending(true);
    try {
      const res = await api.post('/auth/forgot-password', { email: email.trim() });
      setSuccess(`A new OTP verification code has been sent to your email (${email}).`);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to resend OTP code.');
    } finally {
      setResending(false);
    }
  };

  const handleResetPassword = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    if (newPassword.length < 6) {
      setError('New password must be at least 6 characters long.');
      return;
    }

    if (newPassword !== confirmPassword) {
      setError('Passwords do not match. Please verify.');
      return;
    }

    setLoading(true);
    try {
      const res = await api.post('/auth/reset-password', {
        email: email.trim(),
        otp: otp.trim(),
        new_password: newPassword,
      });
      setSuccess(res.data.message || 'Password updated successfully!');
      setTimeout(() => {
        navigate('/login');
      }, 2000);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to update password. Invalid or expired OTP code.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.authContainer}>
      <div className={styles.authCard}>
        <div className={styles.brandHeader}>
          <div className={styles.logoContainer}>
            <img src="/haven_pet_logo.svg" alt="Haven Pet Logo" className={styles.authLogoImg} />
          </div>
          <h1>Update Password</h1>
          <p>
            {!otpSent
              ? 'Enter your registered email address to receive an OTP verification code'
              : `Enter the OTP code sent to your email (${email}) and set your new password`}
          </p>
        </div>

        {error && <div className={styles.errorAlert}>{error}</div>}
        {success && (
          <div className={styles.successAlert}>
            <CheckCircle size={18} />
            <span>{success}</span>
          </div>
        )}

        {!otpSent ? (
          <form onSubmit={handleSendOtp} className={styles.authForm}>
            <div className={styles.fieldGroup}>
              <label>Email Address</label>
              <div className={styles.inputWrapper}>
                <Mail size={18} className={styles.inputIcon} />
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="name@example.com"
                />
              </div>
            </div>

            <button type="submit" disabled={loading} className={styles.submitBtn}>
              {loading ? 'Sending Email OTP...' : 'Send OTP to Email'} <ArrowRight size={18} />
            </button>
          </form>
        ) : (
          <form onSubmit={handleResetPassword} className={styles.authForm}>
            <div className={styles.fieldGroup}>
              <label>6-Digit Email OTP Code</label>
              <div className={styles.inputWrapper}>
                <KeyRound size={18} className={styles.inputIcon} />
                <input
                  type="text"
                  required
                  maxLength={6}
                  value={otp}
                  onChange={(e) => setOtp(e.target.value)}
                  placeholder="Enter code from Email"
                  className={styles.otpInput}
                />
              </div>
            </div>

            <div className={styles.fieldGroup}>
              <label>New Password</label>
              <div className={styles.inputWrapper}>
                <Lock size={18} className={styles.inputIcon} />
                <input
                  type="password"
                  required
                  minLength={6}
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  placeholder="At least 6 characters"
                />
              </div>
            </div>

            <div className={styles.fieldGroup}>
              <label>Confirm New Password</label>
              <div className={styles.inputWrapper}>
                <Lock size={18} className={styles.inputIcon} />
                <input
                  type="password"
                  required
                  minLength={6}
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="Confirm new password"
                />
              </div>
            </div>

            <div className={styles.resendRow}>
              <span>Didn't receive the email code?</span>
              <button
                type="button"
                onClick={handleResendOtp}
                disabled={resending}
                className={styles.resendBtn}
              >
                <RotateCcw size={14} /> {resending ? 'Resending...' : 'Resend OTP'}
              </button>
            </div>

            <div className={styles.modalActionButtons}>
              <button
                type="button"
                onClick={() => setOtpSent(false)}
                className={styles.secondaryModalBtn}
              >
                Change Email
              </button>
              <button type="submit" disabled={loading} className={styles.submitBtn}>
                {loading ? 'Updating Password...' : 'Update Password'}
              </button>
            </div>
          </form>
        )}

        <div className={styles.authFooter}>
          <Link to="/login" style={{ display: 'inline-flex', alignItems: 'center', gap: '0.35rem' }}>
            <ArrowLeft size={16} /> Back to Sign In
          </Link>
        </div>
      </div>
    </div>
  );
}

