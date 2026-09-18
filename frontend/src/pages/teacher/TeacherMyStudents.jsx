import { useEffect, useState } from 'react';
import {
  Typography, Paper, Table, TableHead, TableBody, TableRow, TableCell,
  Chip, CircularProgress, Alert, Box,
} from '@mui/material';
import { listMyStudents } from '../../services/api/enrollmentApi';

export default function TeacherMyStudents() {
  const [students, setStudents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    listMyStudents()
      .then(setStudents)
      .catch(() => setError('Could not load your students.'))
      .finally(() => setLoading(false));
  }, []);

  return (
    <>
      <Typography variant="h4" mb={3}>My Students</Typography>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      {loading ? (
        <CircularProgress />
      ) : (
        <Paper>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Name</TableCell>
                <TableCell>Email</TableCell>
                <TableCell>Enrolled Courses</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {students.length === 0 && (
                <TableRow>
                  <TableCell colSpan={3} align="center">
                    <Typography color="text.secondary" py={3}>
                      No students are enrolled in your courses yet. Ask an admin to enroll students.
                    </Typography>
                  </TableCell>
                </TableRow>
              )}
              {students.map((s) => (
                <TableRow key={s.id} hover>
                  <TableCell>{s.name}</TableCell>
                  <TableCell>{s.email}</TableCell>
                  <TableCell>
                    <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                      {s.course_titles.map((title) => (
                        <Chip key={title} label={title} size="small" variant="outlined" />
                      ))}
                    </Box>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </Paper>
      )}
    </>
  );
}
