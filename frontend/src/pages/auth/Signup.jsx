import { useState } from 'react';
import { Link as RouterLink } from 'react-router-dom';
import {
  Box, TextField, Button, Typography, Alert,
  ToggleButtonGroup, ToggleButton, Link,
} from '@mui/material';
import { motion, useMotionValue, useSpring, useTransform } from 'framer-motion';
import MarkEmailReadIcon from '@mui/icons-material/MarkEmailRead';
import { useAuth } from '../../context/AuthContext';
import AuthShell from './AuthShell';

export default function Signup() {
  const { signup } = useAuth();

  const [role, setRole] = useState('student');
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  const x = useMotionValue(0);
  const y = useMotionValue(0);
  const rotateX = useSpring(useTransform(y, [-0.5, 0.5], [6, -6]), { stiffness: 250, damping: 20 });
  const rotateY = useSpring(useTransform(x, [-0.5, 0.5], [-6, 6]), { stiffness: 250, damping: 20 });

  const handleMouseMove = (e) => {
    const rect = e.currentTarget.getBoundingClientRect();
    x.set((e.clientX - rect.left) / rect.width - 0.5);
    y.set((e.clientY - rect.top) / rect.height - 0.5);
  };
  const handleMouseLeave = () => { x.set(0); y.set(0); };

  const handleRoleChange = (_e, newRole) => {
    if (newRole) setRole(newRole);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }
    if (password.length < 6) {
      setError('Password must be at least 6 characters');
      return;
    }

    setLoading(true);
    try {
      await signup({ name, email, password, role, phone });
      setSubmitted(true);
    } catch (err) {
      setError(err.response?.data?.detail || 'Signup failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  if (submitted) {
    return (
      <AuthShell>
        <motion.div
          initial={{ opacity: 0, y: 24, scale: 0.97 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
        >
          <Box
            sx={{
              width: 420, p: 4.5, borderRadius: 4, textAlign: 'center',
              bgcolor: 'rgba(255,255,255,0.92)', backdropFilter: 'blur(20px)',
              border: '1px solid rgba(255,255,255,0.6)',
              boxShadow: '0 24px 60px rgba(30, 27, 75, 0.25)',
            }}
          >
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ delay: 0.2, type: 'spring', stiffness: 300, damping: 15 }}
            >
              <MarkEmailReadIcon color="success" sx={{ fontSize: 56, mb: 2 }} />
            </motion.div>
            <Typography variant="h5" fontWeight={800} mb={1}>Account created</Typography>
            <Typography variant="body1" color="text.secondary" mb={3}>
              Your {role} account for <strong>{email}</strong> is pending admin approval.
              You'll be able to log in as soon as an admin verifies your account.
            </Typography>
            <Button component={RouterLink} to="/login" variant="contained" fullWidth>
              Back to Login
            </Button>
          </Box>
        </motion.div>
      </AuthShell>
    );
  }

  return (
    <AuthShell>
      <motion.div
        onMouseMove={handleMouseMove}
        onMouseLeave={handleMouseLeave}
        style={{ rotateX, rotateY, transformPerspective: 1000 }}
        initial={{ opacity: 0, y: 24, scale: 0.97 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
      >
        <Box
          sx={{
            width: 420, p: 4.5, borderRadius: 4,
            bgcolor: 'rgba(255,255,255,0.92)', backdropFilter: 'blur(20px)',
            border: '1px solid rgba(255,255,255,0.6)',
            boxShadow: '0 24px 60px rgba(30, 27, 75, 0.25)',
          }}
        >
          <Typography variant="h4" fontWeight={800} mb={0.5}>Create your account</Typography>
          <Typography variant="body2" color="text.secondary" mb={3}>
            Sign up to start learning or teaching on the platform
          </Typography>

          {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

          <Typography variant="body2" fontWeight={600} mb={1}>I am a</Typography>
          <ToggleButtonGroup
            value={role}
            exclusive
            onChange={handleRoleChange}
            fullWidth
            sx={{ mb: 2 }}
          >
            <ToggleButton value="student">Student</ToggleButton>
            <ToggleButton value="teacher">Teacher</ToggleButton>
          </ToggleButtonGroup>

          <Box component="form" onSubmit={handleSubmit}>
            <TextField
              label="Full Name" fullWidth required margin="normal"
              value={name} onChange={(e) => setName(e.target.value)}
            />
            <TextField
              label="Email" type="email" fullWidth required margin="normal"
              value={email} onChange={(e) => setEmail(e.target.value)}
            />
            <TextField
              label="Phone (optional)" fullWidth margin="normal"
              value={phone} onChange={(e) => setPhone(e.target.value)}
            />
            <TextField
              label="Password" type="password" fullWidth required margin="normal"
              value={password} onChange={(e) => setPassword(e.target.value)}
              helperText="At least 6 characters"
            />
            <TextField
              label="Confirm Password" type="password" fullWidth required margin="normal"
              value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)}
            />
            <motion.div whileTap={{ scale: 0.98 }} style={{ marginTop: 20 }}>
              <Button type="submit" variant="contained" fullWidth size="large" disabled={loading}>
                {loading ? 'Creating account...' : `Sign Up as ${role === 'student' ? 'Student' : 'Teacher'}`}
              </Button>
            </motion.div>
          </Box>

          <Typography variant="body2" mt={3} textAlign="center" color="text.secondary">
            Already have an account?{' '}
            <Link component={RouterLink} to="/login" underline="hover" fontWeight={600}>Log in</Link>
          </Typography>
        </Box>
      </motion.div>
    </AuthShell>
  );
}
