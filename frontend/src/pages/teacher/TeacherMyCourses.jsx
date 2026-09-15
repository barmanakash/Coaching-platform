import { useEffect, useState } from 'react';
import { Typography, Grid, Card, CardContent, Chip, CircularProgress, Alert } from '@mui/material';
import { listCourses } from '../../services/api/courseApi';

export default function TeacherMyCourses() {
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
      <Typography variant="h4" fontWeight={700} mb={3}>My Courses</Typography>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      {loading ? (
        <CircularProgress />
      ) : courses.length === 0 ? (
        <Alert severity="info">
          You haven't been assigned to any course yet. Ask an admin to assign you as a teacher on a course.
        </Alert>
      ) : (
        <Grid container spacing={2}>
          {courses.map((c) => (
            <Grid item xs={12} sm={6} md={4} key={c.id}>
              <Card>
                <CardContent>
                  <Typography variant="h6" fontWeight={600}>{c.title}</Typography>
                  <Typography variant="body2" color="text.secondary" mb={1}>
                    {c.description || 'No description yet.'}
                  </Typography>
                  <Chip label={c.status} size="small" color={c.status === 'published' ? 'success' : 'default'} sx={{ mr: 1 }} />
                  <Chip label={`${c.student_count} students`} size="small" variant="outlined" />
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}
    </>
  );
}
