import { useEffect, useState, useCallback } from 'react';
import {
  Typography, Paper, Table, TableHead, TableBody, TableRow, TableCell,
  Chip, IconButton, CircularProgress, Alert, Tooltip, Snackbar,
} from '@mui/material';
import BlockIcon from '@mui/icons-material/Block';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import DeleteIcon from '@mui/icons-material/Delete';
import { listTeachers, updateUser, deleteUser, approveUser } from '../../services/api/adminApi';

export default function TeachersPage() {
  const [teachers, setTeachers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [toast, setToast] = useState('');

  const load = useCallback(() => {
    setLoading(true);
    listTeachers()
      .then(setTeachers)
      .catch(() => setError('Could not load teachers.'))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => { load(); }, [load]);

  const toggleStatus = async (teacher) => {
    const newStatus = teacher.status === 'active' ? 'inactive' : 'active';
    try {
      await updateUser(teacher.id, { status: newStatus });
      setToast(`${teacher.name} is now ${newStatus}`);
      load();
    } catch {
      setToast('Failed to update status');
    }
  };

  const handleApprove = async (teacher) => {
    try {
      await approveUser(teacher.id);
      setToast(`${teacher.name} approved — they can now log in`);
      load();
    } catch {
      setToast('Failed to approve teacher');
    }
  };

  const handleDelete = async (teacher) => {
    if (!window.confirm(`Delete ${teacher.name}? This cannot be undone.`)) return;
    try {
      await deleteUser(teacher.id);
      setToast(`${teacher.name} deleted`);
      load();
    } catch {
      setToast('Failed to delete teacher');
    }
  };

  return (
    <>
      <Typography variant="h4" fontWeight={700} mb={3}>Teachers</Typography>

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
                <TableCell>Assigned Courses</TableCell>
                <TableCell align="right">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {teachers.length === 0 && (
                <TableRow>
                  <TableCell colSpan={6} align="center">
                    <Typography color="text.secondary" py={3}>No teachers have signed up yet.</Typography>
                  </TableCell>
                </TableRow>
              )}
              {teachers.map((t) => (
                <TableRow key={t.id} hover>
                  <TableCell>{t.name}</TableCell>
                  <TableCell>{t.email}</TableCell>
                  <TableCell>{t.phone || '-'}</TableCell>
                  <TableCell>
                    <Chip
                      label={t.status}
                      color={t.status === 'active' ? 'success' : t.status === 'pending' ? 'warning' : 'default'}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>{t.assigned_courses_count ?? 0}</TableCell>
                  <TableCell align="right">
                    {t.status === 'pending' ? (
                      <Tooltip title="Approve this signup">
                        <IconButton onClick={() => handleApprove(t)} size="small" color="success">
                          <CheckCircleIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                    ) : (
                      <Tooltip title={t.status === 'active' ? 'Deactivate' : 'Activate'}>
                        <IconButton onClick={() => toggleStatus(t)} size="small">
                          {t.status === 'active' ? <BlockIcon fontSize="small" /> : <CheckCircleIcon fontSize="small" />}
                        </IconButton>
                      </Tooltip>
                    )}
                    <Tooltip title="Delete">
                      <IconButton onClick={() => handleDelete(t)} size="small" color="error">
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
