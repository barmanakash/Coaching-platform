import { useEffect, useState } from 'react';
import { Typography, Grid, Paper, CircularProgress, Alert } from '@mui/material';
import { getDashboardStats } from '../../services/api/adminApi';

const STAT_LABELS = [
  { key: 'total_students', label: 'Total Students' },
  { key: 'total_teachers', label: 'Total Teachers' },
  { key: 'total_courses', label: 'Total Courses' },
  { key: 'active_classes', label: 'Active Classes' },
  { key: 'upcoming_classes', label: 'Upcoming Classes' },
  { key: 'pending_doubts', label: 'Pending Doubts' },
];

export default function AdminDashboard() {
  const [stats, setStats] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getDashboardStats()
      .then(setStats)
      .catch(() => setError('Could not load dashboard stats.'))
      .finally(() => setLoading(false));
  }, []);

  return (
    <>
      <Typography variant="h4" fontWeight={700} mb={3}>Admin Dashboard</Typography>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      {loading ? (
        <CircularProgress />
      ) : (
        <Grid container spacing={2}>
          {STAT_LABELS.map(({ key, label }) => (
            <Grid item xs={12} sm={6} md={4} key={key}>
              <Paper sx={{ p: 3 }}>
                <Typography variant="body2" color="text.secondary">{label}</Typography>
                <Typography variant="h4" fontWeight={700}>{stats?.[key] ?? 0}</Typography>
              </Paper>
            </Grid>
          ))}
        </Grid>
      )}
    </>
  );
}
