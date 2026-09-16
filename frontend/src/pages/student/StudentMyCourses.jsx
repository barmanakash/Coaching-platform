import { useEffect, useState } from 'react';
import { Typography, Grid, Chip, CircularProgress, Alert } from '@mui/material';
import { motion } from 'framer-motion';
import { listCourses } from '../../services/api/courseApi';
import TiltCard from '../../components/TiltCard';

export default function StudentMyCourses() {
  const [courses, setCourses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    listCourses()
      .then(setCourses)
      .catch(() => setError('Could not load courses.'))
      .finally(() => setLoading(false));
  }, []);

  return (
    <>
      <Typography variant="h4" mb={3}>My Courses</Typography>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      {loading ? (
        <CircularProgress />
      ) : courses.length === 0 ? (
        <Alert severity="info">
          No published courses are available yet. Check back once your institute publishes one.
        </Alert>
      ) : (
        <Grid container spacing={2.5}>
          {courses.map((c, i) => (
            <Grid item xs={12} sm={6} md={4} key={c.id}>
              <motion.div
                initial={{ opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.05, duration: 0.4 }}
              >
                <TiltCard sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                  <Typography variant="h6">{c.title}</Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ flexGrow: 1 }}>
                    {c.description || 'No description yet.'}
                  </Typography>
                  <Chip
                    label={c.teacher_names?.length ? `Taught by ${c.teacher_names.join(', ')}` : 'Teacher unassigned'}
                    size="small"
                    variant="outlined"
                    sx={{ alignSelf: 'flex-start', mt: 1 }}
                  />
                </TiltCard>
              </motion.div>
            </Grid>
          ))}
        </Grid>
      )}
    </>
  );
}
