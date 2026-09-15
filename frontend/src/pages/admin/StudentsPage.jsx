import { useEffect, useState, useCallback } from 'react';
import {
  Typography, Paper, Table, TableHead, TableBody, TableRow, TableCell,
  Chip, IconButton, CircularProgress, Alert, Tooltip, Snackbar,
} from '@mui/material';
import BlockIcon from '@mui/icons-material/Block';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import DeleteIcon from '@mui/icons-material/Delete';
import { listStudents, updateUser, deleteUser } from '../../services/api/adminApi';

export default function StudentsPage() {
  const [students, setStudents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [toast, setToast] = useState('');

  const load = useCallback(() => {
    setLoading(true);
    listStudents()
      .then(setStudents)
      .catch(() => setError('Could not load students.'))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => { load(); }, [load]);

  const toggleStatus = async (student) => {
    const newStatus = student.status === 'active' ? 'inactive' : 'active';
    try {
      await updateUser(student.id, { status: newStatus });
      setToast(`${student.name} is now ${newStatus}`);
      load();
    } catch {
      setToast('Failed to update status');
    }
  };

  const handleDelete = async (student) => {
    if (!window.confirm(`Delete ${student.name}? This cannot be undone.`)) return;
    try {
      await deleteUser(student.id);
      setToast(`${student.name} deleted`);
      load();
    } catch {
      setToast('Failed to delete student');
    }
  };

  return (
    <>
      <Typography variant="h4" fontWeight={700} mb={3}>Students</Typography>

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
                <TableCell>Phone</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Enrolled Courses</TableCell>
                <TableCell align="right">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {students.length === 0 && (
                <TableRow>
                  <TableCell colSpan={6} align="center">
                    <Typography color="text.secondary" py={3}>No students have signed up yet.</Typography>
                  </TableCell>
                </TableRow>
              )}
              {students.map((s) => (
                <TableRow key={s.id} hover>
                  <TableCell>{s.name}</TableCell>
                  <TableCell>{s.email}</TableCell>
                  <TableCell>{s.phone || '-'}</TableCell>
                  <TableCell>
                    <Chip
                      label={s.status}
                      color={s.status === 'active' ? 'success' : 'default'}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>{s.enrolled_courses_count ?? 0}</TableCell>
                  <TableCell align="right">
                    <Tooltip title={s.status === 'active' ? 'Deactivate' : 'Activate'}>
                      <IconButton onClick={() => toggleStatus(s)} size="small">
                        {s.status === 'active' ? <BlockIcon fontSize="small" /> : <CheckCircleIcon fontSize="small" />}
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Delete">
                      <IconButton onClick={() => handleDelete(s)} size="small" color="error">
                        <DeleteIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </Paper>
      )}

      <Snackbar
        open={!!toast}
        autoHideDuration={3000}
        onClose={() => setToast('')}
        message={toast}
      />
    </>
  );
}
