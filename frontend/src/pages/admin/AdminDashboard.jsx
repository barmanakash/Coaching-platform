import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Typography, Grid, CircularProgress, Alert, Box } from '@mui/material';
import { motion } from 'framer-motion';
import GroupsIcon from '@mui/icons-material/Groups';
import SchoolIcon from '@mui/icons-material/School';
import MenuBookIcon from '@mui/icons-material/MenuBook';
import SensorsIcon from '@mui/icons-material/Sensors';
import EventAvailableIcon from '@mui/icons-material/EventAvailable';
import HelpCenterIcon from '@mui/icons-material/HelpCenter';
import { getDashboardStats } from '../../services/api/adminApi';
import TiltCard from '../../components/TiltCard';

const STAT_LABELS = [
  { key: 'total_students', label: 'Total Students', icon: GroupsIcon, color: '#4338CA' },
  { key: 'total_teachers', label: 'Total Teachers', icon: SchoolIcon, color: '#0EA5E9' },
  { key: 'total_courses', label: 'Total Courses', icon: MenuBookIcon, color: '#059669' },
  { key: 'active_classes', label: 'Active Classes', icon: SensorsIcon, color: '#DC2626' },
  { key: 'upcoming_classes', label: 'Upcoming Classes', icon: EventAvailableIcon, color: '#F59E0B' },
  { key: 'pending_doubts', label: 'Pending Doubts', icon: HelpCenterIcon, color: '#7C3AED' },
];

export default function AdminDashboard() {
  const navigate = useNavigate();
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
      <Typography variant="h4" mb={3}>Admin Dashboard</Typography>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      {loading ? (
        <CircularProgress />
      ) : (
        <Grid container spacing={2.5}>
          {!!stats?.pending_approvals && (
            <Grid item xs={12}>
              <motion.div whileHover={{ y: -2 }} transition={{ type: 'spring', stiffness: 300 }}>
                <Box
                  onClick={() => navigate('/admin/approvals')}
                  sx={{
                    p: 3, borderRadius: 3, cursor: 'pointer',
                    background: 'linear-gradient(135deg, #FEF3C7, #FDE68A)',
                    border: '1px solid #F59E0B',
                    transition: 'box-shadow 0.2s ease',
                    '&:hover': { boxShadow: '0 12px 28px rgba(245, 158, 11, 0.25)' },
                  }}
                >
                  <Typography variant="body1" fontWeight={700} color="#78350F">
                    {stats.pending_approvals} signup{stats.pending_approvals > 1 ? 's' : ''} waiting for approval
                  </Typography>
                  <Typography variant="body2" color="#92400E">
                    Click to review and approve or reject pending Teacher/Student accounts
                  </Typography>
                </Box>
              </motion.div>
            </Grid>
          )}

          {STAT_LABELS.map(({ key, label, icon: Icon, color }, i) => (
            <Grid item xs={12} sm={6} md={4} key={key}>
              <motion.div
                initial={{ opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.05, duration: 0.4 }}
              >
                <TiltCard>
                  <Box sx={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
                    <Box>
                      <Typography variant="body2" color="text.secondary" mb={0.5}>{label}</Typography>
                      <Typography variant="h3">{stats?.[key] ?? 0}</Typography>
                    </Box>
                    <Box
                      sx={{
                        width: 44, height: 44, borderRadius: 2.5,
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        bgcolor: `${color}18`, color,
                      }}
                    >
                      <Icon />
                    </Box>
                  </Box>
                </TiltCard>
              </motion.div>
            </Grid>
          ))}
        </Grid>
      )}
    </>
  );
}
