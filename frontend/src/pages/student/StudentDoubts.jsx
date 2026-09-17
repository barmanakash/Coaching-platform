import { useEffect, useState, useCallback } from 'react';
import {
  Typography, Box, Button, Paper, Table, TableHead, TableBody, TableRow,
  TableCell, Chip, CircularProgress, Alert, Dialog, DialogTitle, DialogContent,
  DialogActions, TextField, MenuItem,
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import { listDoubts, createDoubt } from '../../services/api/doubtApi';
import { listCourses } from '../../services/api/courseApi';
import DoubtDetailDialog, { STATUS_COLOR } from '../../components/DoubtDetailDialog';

export default function StudentDoubts() {
  const [doubts, setDoubts] = useState([]);
  const [courses, setCourses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const [createOpen, setCreateOpen] = useState(false);
  const [form, setForm] = useState({ subject: '', question: '', course_id: '', attachment_url: '' });
  const [saving, setSaving] = useState(false);

  const [activeDoubtId, setActiveDoubtId] = useState(null);

  const load = useCallback(() => {
    setLoading(true);
    Promise.all([listDoubts(), listCourses()])
      .then(([d, c]) => { setDoubts(d); setCourses(c); })
      .catch(() => setError('Could not load your doubts.'))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => { load(); }, [load]);

  const handleCreate = async () => {
    if (!form.subject.trim() || !form.question.trim()) return;
    setSaving(true);
    try {
      await createDoubt({
        subject: form.subject,
        question: form.question,
        course_id: form.course_id || null,
        attachment_url: form.attachment_url || null,
      });
      setCreateOpen(false);
      setForm({ subject: '', question: '', course_id: '', attachment_url: '' });
      load();
    } finally {
      setSaving(false);
    }
  };

  return (
    <>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">My Doubts</Typography>
        <Button variant="contained" startIcon={<AddIcon />} onClick={() => setCreateOpen(true)}>
          Ask a Doubt
        </Button>
      </Box>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      {loading ? (
        <CircularProgress />
      ) : (
        <Paper>
          <Table>
            <TableHead>
              <TableRow>
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
                  <TableCell colSpan={5} align="center">
                    <Typography color="text.secondary" py={3}>
                      You haven't asked any doubts yet.
                    </Typography>
                  </TableCell>
                </TableRow>
              )}
              {doubts.map((d) => (
                <TableRow key={d.id} hover sx={{ cursor: 'pointer' }} onClick={() => setActiveDoubtId(d.id)}>
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

      <Dialog open={createOpen} onClose={() => setCreateOpen(false)} fullWidth maxWidth="sm">
        <DialogTitle>Ask a Doubt</DialogTitle>
        <DialogContent>
          <TextField
            label="Subject" fullWidth required margin="normal"
            value={form.subject} onChange={(e) => setForm((f) => ({ ...f, subject: e.target.value }))}
          />
          <TextField
            select label="Course (optional)" fullWidth margin="normal"
            value={form.course_id} onChange={(e) => setForm((f) => ({ ...f, course_id: e.target.value }))}
          >
            <MenuItem value="">General (no course)</MenuItem>
            {courses.map((c) => <MenuItem key={c.id} value={c.id}>{c.title}</MenuItem>)}
          </TextField>
          <TextField
            label="Your Question" fullWidth required multiline rows={4} margin="normal"
            value={form.question} onChange={(e) => setForm((f) => ({ ...f, question: e.target.value }))}
          />
          <TextField
            label="Attachment URL (optional)" fullWidth margin="normal"
            value={form.attachment_url} onChange={(e) => setForm((f) => ({ ...f, attachment_url: e.target.value }))}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleCreate} disabled={saving || !form.subject.trim() || !form.question.trim()}>
            {saving ? 'Submitting...' : 'Submit'}
          </Button>
        </DialogActions>
      </Dialog>

      <DoubtDetailDialog
        doubtId={activeDoubtId}
        open={!!activeDoubtId}
        onClose={() => setActiveDoubtId(null)}
        onUpdated={load}
      />
    </>
  );
}
