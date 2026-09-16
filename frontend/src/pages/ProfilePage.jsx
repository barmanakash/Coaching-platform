import { Typography, Paper, Avatar, Box, Chip } from '@mui/material';
import { useAuth } from '../context/AuthContext';

export default function ProfilePage() {
  const { user } = useAuth();

  return (
    <>
      <Typography variant="h4" fontWeight={700} mb={3}>Profile</Typography>
      <Paper sx={{ p: 4, maxWidth: 480 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
          <Avatar sx={{ width: 64, height: 64, bgcolor: 'primary.main', fontSize: 24 }}>
            {user?.name?.[0]?.toUpperCase() || '?'}
          </Avatar>
          <Box>
            <Typography variant="h6" fontWeight={600}>{user?.name}</Typography>
            <Chip label={user?.role} size="small" sx={{ textTransform: 'capitalize' }} />
          </Box>
        </Box>
        <Typography variant="body2" color="text.secondary">User ID</Typography>
        <Typography variant="body1" mb={2}>{user?.userId}</Typography>
        <Typography variant="body2" color="text.disabled" mt={2}>
          Editing your profile (photo, bio, password change) is coming in a future update.
        </Typography>
      </Paper>
    </>
  );
}
