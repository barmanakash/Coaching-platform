import { useEffect, useState, useCallback } from 'react';
import {
  Typography, Paper, Table, TableHead, TableBody, TableRow, TableCell,
  Chip, Button, CircularProgress, Alert, Snackbar, Box, Stack,
} from '@mui/material';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import CancelIcon from '@mui/icons-material/Cancel';
import { listPendingUsers, approveUser, rejectUser } from '../../services/api/adminApi';

export default function ApprovalsPage() {
  const [pending, setPending] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [toast, setToast] = useState('');
  const [actingOn, setActingOn] = useState(null);

  const load = useCallback(() => {
    setLoading(true);
    listPendingUsers()
      .then(setPending)
      .catch(() => setError('Could not load pending signups.'))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => { load(); }, [load]);

  const handleApprove = async (user) => {
    setActingOn(user.id);
    try {
      await approveUser(user.id);
      setToast(`${user.name} approved — they can now log in`);
      load();
    } catch {
      setToast('Failed to approve user');
    } finally {
      setActingOn(null);
    }
  };

  const handleReject = async (user) => {
    if (!window.confirm(`Reject and delete ${user.name}'s signup request? This cannot be undone.`)) return;
    setActingOn(user.id);
    try {
      await rejectUser(user.id);
      setToast(`${user.name}'s signup was rejected`);
      load();
    } catch {
      setToast('Failed to reject user');
    } finally {
      setActingOn(null);
    }
  };

  return (
    <>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" fontWeight={700}>Pending Approvals</Typography>
        {pending.length > 0 && <Chip label={`${pending.length} waiting`} color="warning" />}
      </Box>

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
                <TableCell>Role</TableCell>
                <TableCell>Signed up</TableCell>
                <TableCell align="right">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {pending.length === 0 && (
                <TableRow>
                  <TableCell colSpan={6} align="center">
                    <Typography color="text.secondary" py={3}>
                      No signups waiting for approval right now.
                    </Typography>
                  </TableCell>
                </TableRow>
              )}
              {pending.map((u) => (
                <TableRow key={u.id} hover>
                  <TableCell>{u.name}</TableCell>
                  <TableCell>{u.email}</TableCell>
                  <TableCell>{u.phone || '-'}</TableCell>
                  <TableCell>
                    <Chip label={u.role} size="small" sx={{ textTransform: 'capitalize' }} />
                  </TableCell>
                  <TableCell>
                    {u.created_at ? new Date(u.created_at).toLocaleString() : '-'}
                  </TableCell>
                  <TableCell align="right">
                    <Stack direction="row" spacing={1} justifyContent="flex-end">
                      <Button
                        size="small"
                        variant="contained"
                        color="success"
                        startIcon={<CheckCircleIcon />}
                        disabled={actingOn === u.id}
                        onClick={() => handleApprove(u)}
                      >
                        Approve
                      </Button>
                      <Button
                        size="small"
                        variant="outlined"
                        color="error"
                        startIcon={<CancelIcon />}
                        disabled={actingOn === u.id}
                        onClick={() => handleReject(u)}
                      >
                        Reject
                      </Button>
                    </Stack>
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
