import { useState } from 'react';
import { useNavigate, Link as RouterLink } from 'react-router-dom';
import {
  Box, Paper, TextField, Button, Typography, Alert,
  ToggleButtonGroup, ToggleButton, Link,
} from '@mui/material';
import { useAuth } from '../../context/AuthContext';

const ROLE_HOME = {
  teacher: '/teacher',
  student: '/student',
};

export default function Signup() {
  const { signup } = useAuth();
  const navigate = useNavigate();

  const [role, setRole] = useState('student');
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

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
      const user = await signup({ name, email, password, role, phone });
      navigate(ROLE_HOME[user.role] || '/login');
    } catch (err) {
      setError(err.response?.data?.detail || 'Signup failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box
      sx={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        bgcolor: 'background.default',
        py: 4,
      }}
    >
      <Paper elevation={3} sx={{ p: 4, width: 400 }}>
        <Typography variant="h5" fontWeight={700} mb={1}>Create your account</Typography>
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
            label="Full Name"
            fullWidth
            required
            margin="normal"
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
          <TextField
            label="Email"
            type="email"
            fullWidth
            required
            margin="normal"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
          <TextField
            label="Phone (optional)"
            fullWidth
            margin="normal"
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
          />
          <TextField
            label="Password"
            type="password"
            fullWidth
            required
            margin="normal"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            helperText="At least 6 characters"
          />
          <TextField
            label="Confirm Password"
            type="password"
            fullWidth
            required
            margin="normal"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
          />
          <Button
            type="submit"
            variant="contained"
            fullWidth
            size="large"
            sx={{ mt: 3 }}
            disabled={loading}
          >
            {loading ? 'Creating account...' : `Sign Up as ${role === 'student' ? 'Student' : 'Teacher'}`}
          </Button>
        </Box>

        <Typography variant="body2" mt={3} textAlign="center">
          Already have an account?{' '}
          <Link component={RouterLink} to="/login">Log in</Link>
        </Typography>
      </Paper>
    </Box>
  );
}
