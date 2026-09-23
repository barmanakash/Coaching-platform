import { useEffect, useState } from 'react';
import { useNavigate, useSearchParams, Link as RouterLink } from 'react-router-dom';
import { Box, TextField, Button, Typography, Alert, Link, CircularProgress } from '@mui/material';
import { motion, useMotionValue, useSpring, useTransform } from 'framer-motion';
import MarkEmailReadIcon from '@mui/icons-material/MarkEmailRead';
import { previewInvitation, acceptInvite } from '../../services/api/authApi';
import { useAuth } from '../../context/AuthContext';
import { ROLE_HOME, apiErrorMessage } from '../../utils/roleHome';
import AuthShell from './AuthShell';

const ROLE_LABEL = { admin: 'Institute Admin', teacher: 'Teacher', student: 'Student' };

/**
 * Landing page for an invite link (admin-invite-only onboarding — there is
 * no public signup). Previews who/what the invite is for, then lets the
 * invitee set a password and correct their name before their account is
 * created and they're signed straight in.
 */
export default function AcceptInvitePage() {
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token') || '';
  const navigate = useNavigate();
  const { setSessionFromInvite } = useAuth();

  const [preview, setPreview] = useState(null);
  const [previewError, setPreviewError] = useState('');
  const [loadingPreview, setLoadingPreview] = useState(true);

  const [name, setName] = useState('');
  const [phone, setPhone] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

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

  useEffect(() => {
    if (!token) {
      setPreviewError('This invite link is missing its token.');
      setLoadingPreview(false);
      return;
    }
    previewInvitation(token)
      .then((data) => {
        setPreview(data);
        setName(data.name);
      })
      .catch((err) => setPreviewError(apiErrorMessage(err, 'This invitation link is invalid or has expired.')))
      .finally(() => setLoadingPreview(false));
  }, [token]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }
    if (password.length < 8) {
      setError('Password must be at least 8 characters');
      return;
    }

    setSubmitting(true);
    try {
      const data = await acceptInvite({ token, password, name, phone: phone || undefined });
      const user = setSessionFromInvite(data);
      navigate(ROLE_HOME[user.role] || '/login');
    } catch (err) {
      setError(apiErrorMessage(err, 'Could not set up your account. Please try again.'));
    } finally {
      setSubmitting(false);
    }
  };

  const cardSx = {
    width: 420, p: 4.5, borderRadius: 4,
    bgcolor: 'rgba(255,255,255,0.92)', backdropFilter: 'blur(20px)',
    border: '1px solid rgba(255,255,255,0.6)',
    boxShadow: '0 24px 60px rgba(30, 27, 75, 0.25)',
  };

  if (loadingPreview) {
    return (
      <AuthShell>
        <Box sx={{ ...cardSx, textAlign: 'center' }}>
          <CircularProgress />
        </Box>
      </AuthShell>
    );
  }

  if (previewError) {
    return (
      <AuthShell>
        <motion.div initial={{ opacity: 0, y: 24 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}>
          <Box sx={{ ...cardSx, textAlign: 'center' }}>
            <Typography variant="h5" fontWeight={800} mb={1}>Invite link not valid</Typography>
            <Typography variant="body1" color="text.secondary" mb={3}>{previewError}</Typography>
            <Typography variant="body2" color="text.secondary" mb={2}>
              Ask your institute admin to send you a new invitation.
            </Typography>
            <Button component={RouterLink} to="/login" variant="contained" fullWidth>Back to Login</Button>
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
        <Box sx={cardSx}>
          <motion.div initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ delay: 0.1, type: 'spring', stiffness: 300, damping: 15 }}>
            <MarkEmailReadIcon color="success" sx={{ fontSize: 44, mb: 1.5 }} />
          </motion.div>
          <Typography variant="h4" fontWeight={800} mb={0.5}>You're invited!</Typography>
          <Typography variant="body2" color="text.secondary" mb={3}>
            Join <strong>{preview.institute_name}</strong> as a {ROLE_LABEL[preview.role] || preview.role}.
            Set a password to activate your account for <strong>{preview.email}</strong>.
          </Typography>

          {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

          <Box component="form" onSubmit={handleSubmit}>
            <TextField
              label="Full Name" fullWidth required margin="normal"
              value={name} onChange={(e) => setName(e.target.value)}
            />
            <TextField
              label="Phone (optional)" fullWidth margin="normal"
              value={phone} onChange={(e) => setPhone(e.target.value)}
            />
            <TextField
              label="Password" type="password" fullWidth required margin="normal"
              value={password} onChange={(e) => setPassword(e.target.value)}
              helperText="At least 8 characters"
            />
            <TextField
              label="Confirm Password" type="password" fullWidth required margin="normal"
              value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)}
            />
            <motion.div whileTap={{ scale: 0.98 }} style={{ marginTop: 20 }}>
              <Button type="submit" variant="contained" fullWidth size="large" disabled={submitting}>
                {submitting ? 'Setting up your account...' : 'Activate Account'}
              </Button>
            </motion.div>
          </Box>

          <Typography variant="body2" mt={3} textAlign="center" color="text.secondary">
            Already activated?{' '}
            <Link component={RouterLink} to="/login" underline="hover" fontWeight={600}>Log in</Link>
          </Typography>
        </Box>
      </motion.div>
    </AuthShell>
  );
}
