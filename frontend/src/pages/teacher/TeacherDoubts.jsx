import { useEffect, useState, useCallback } from 'react';
import {
  Typography, Box, Paper, Table, TableHead, TableBody, TableRow,
  TableCell, Chip, CircularProgress, Alert,
} from '@mui/material';
import { listDoubts } from '../../services/api/doubtApi';
import DoubtDetailDialog, { STATUS_COLOR } from '../../components/DoubtDetailDialog';

export default function TeacherDoubts() {
  const [doubts, setDoubts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [activeDoubtId, setActiveDoubtId] = useState(null);

  const load = useCallback(() => {
    setLoading(true);
    listDoubts()
      .then(setDoubts)
      .catch(() => setError('Could not load doubts.'))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => { load(); }, [load]);

  return (
    <>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">Doubts</Typography>
        {doubts.filter((d) => d.status === 'OPEN').length > 0 && (
          <Chip
            label={`${doubts.filter((d) => d.status === 'OPEN').length} open`}
            color="warning"
          />
        )}
      </Box>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      {loading ? (
        <CircularProgress />
      ) : (
        <Paper>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Student</TableCell>
                <TableCell>Subject</TableCell>
                <TableCell>Course</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Replies</TableCell>
                <TableCell>Last update</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {doubts.length === 0 && (
                <TableRow>
                  <TableCell colSpan={6} align="center">
                    <Typography color="text.secondary" py={3}>
                      No doubts have been raised on your courses yet.
                    </Typography>
                  </TableCell>
                </TableRow>
              )}
              {doubts.map((d) => (
                <TableRow key={d.id} hover sx={{ cursor: 'pointer' }} onClick={() => setActiveDoubtId(d.id)}>
                  <TableCell>{d.student_name}</TableCell>
                  <TableCell>{d.subject}</TableCell>
                  <TableCell>{d.course_title || '-'}</TableCell>
                  <TableCell>
                    <Chip label={d.status.replace('_', ' ')} size="small" color={STATUS_COLOR[d.status]} />
                  </TableCell>
                  <TableCell>{d.replies.length}</TableCell>
                  <TableCell>{new Date(d.updated_at).toLocaleString()}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </Paper>
      )}

      <DoubtDetailDialog
        doubtId={activeDoubtId}
        open={!!activeDoubtId}
        onClose={() => setActiveDoubtId(null)}
        onUpdated={load}
      />
    </>
  );
}
