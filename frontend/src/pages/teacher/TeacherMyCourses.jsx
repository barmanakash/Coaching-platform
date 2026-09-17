import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Typography, Grid, Chip, CircularProgress, Alert, Box } from '@mui/material';
import { motion } from 'framer-motion';
import { listCourses } from '../../services/api/courseApi';
import TiltCard from '../../components/TiltCard';

export default function TeacherMyCourses() {
  const navigate = useNavigate();
  const [courses, setCourses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    listCourses()
      .then(setCourses)
      .catch(() => setError('Could not load your courses.'))
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
          You haven't been assigned to any course yet. Ask an admin to assign you as a teacher on a course.
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
                <TiltCard onClick={() => navigate(`/teacher/courses/${c.id}`)} sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                  <Typography variant="h6">{c.title}</Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ flexGrow: 1 }}>
                    {c.description || 'No description yet.'}
                  </Typography>
                  <Box sx={{ display: 'flex', gap: 1, mt: 1 }}>
                    <Chip label={c.status} size="small" color={c.status === 'published' ? 'success' : 'default'} />
                    <Chip label={`${c.student_count} students`} size="small" variant="outlined" />
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
