import { useEffect, useState, useCallback } from 'react';
import {
  Typography, Paper, Table, TableHead, TableBody, TableRow, TableCell,
  Chip, CircularProgress, Alert, Button, Box,
} from '@mui/material';
import { listAuditLogs } from '../../services/api/auditLogApi';

const PAGE_SIZE = 50;

const ACTION_LABEL = {
  'invitation.created': 'Invitation created',
  'invitation.accepted': 'Invitation accepted',
  'invitation.revoked': 'Invitation revoked',
  'invitation.regenerated': 'Invitation regenerated',
  'institute.updated': 'Institute settings updated',
  'institute.created': 'Institute created',
  'user.approved': 'User approved',
  'user.rejected': 'User rejected',
  'user.updated': 'User updated',
  'user.deleted': 'User deleted',
  'course.created': 'Course created',
  'course.updated': 'Course updated',
  'course.deleted': 'Course deleted',
  'enrollment.created': 'Student enrolled',
  'enrollment.deleted': 'Student unenrolled',
};

function describe(entry) {
  return ACTION_LABEL[entry.action] || entry.action;
}

export default function AuditLogPage() {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [error, setError] = useState('');
  const [hasMore, setHasMore] = useState(true);

  const load = useCallback((skip = 0) => {
    const setBusy = skip === 0 ? setLoading : setLoadingMore;
    setBusy(true);
    listAuditLogs({ limit: PAGE_SIZE, skip })
      .then((data) => {
        setLogs((prev) => (skip === 0 ? data : [...prev, ...data]));
        setHasMore(data.length === PAGE_SIZE);
      })
      .catch(() => setError('Could not load the activity log.'))
      .finally(() => setBusy(false));
  }, []);

  useEffect(() => { load(0); }, [load]);

  return (
    <>
      <Typography variant="h4" fontWeight={700} mb={3}>Activity & Audit Log</Typography>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      {loading ? (
        <CircularProgress />
      ) : (
        <Paper>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>When</TableCell>
                <TableCell>Actor</TableCell>
                <TableCell>Action</TableCell>
                <TableCell>Details</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {logs.length === 0 && (
                <TableRow>
                  <TableCell colSpan={4} align="center">
                    <Typography color="text.secondary" py={3}>No activity recorded yet.</Typography>
                  </TableCell>
                </TableRow>
              )}
              {logs.map((entry) => (
                <TableRow key={entry.id} hover>
                  <TableCell>{new Date(entry.created_at).toLocaleString()}</TableCell>
                  <TableCell>{entry.actor_name}</TableCell>
                  <TableCell><Chip label={describe(entry)} size="small" /></TableCell>
                  <TableCell>
                    <Typography variant="caption" color="text.secondary" sx={{ wordBreak: 'break-word' }}>
                      {Object.keys(entry.details || {}).length
                        ? Object.entries(entry.details).map(([k, v]) => `${k}: ${v}`).join(', ')
                        : '—'}
                    </Typography>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </Paper>
      )}

      {hasMore && !loading && (
        <Box sx={{ display: 'flex', justifyContent: 'center', mt: 2 }}>
          <Button onClick={() => load(logs.length)} disabled={loadingMore}>
            {loadingMore ? 'Loading...' : 'Load more'}
          </Button>
        </Box>
      )}
    </>
  );
}
