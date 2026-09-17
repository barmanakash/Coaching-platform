import { useEffect, useState, useCallback } from 'react';
import {
  Dialog, DialogTitle, DialogContent, DialogActions, Typography, Box, Chip,
  TextField, Button, Divider, Avatar, Stack, CircularProgress, MenuItem, Select,
} from '@mui/material';
import { getDoubt, addReply, updateDoubtStatus } from '../services/api/doubtApi';
import { useAuth } from '../context/AuthContext';

const STATUS_COLOR = { OPEN: 'warning', IN_PROGRESS: 'info', RESOLVED: 'success' };

export default function DoubtDetailDialog({ doubtId, open, onClose, onUpdated }) {
  const { user } = useAuth();
  const [doubt, setDoubt] = useState(null);
  const [loading, setLoading] = useState(true);
  const [reply, setReply] = useState('');
  const [sending, setSending] = useState(false);

  const load = useCallback(() => {
    if (!doubtId) return;
    setLoading(true);
    getDoubt(doubtId).then(setDoubt).finally(() => setLoading(false));
  }, [doubtId]);

  useEffect(() => { if (open) load(); }, [open, load]);

  const handleReply = async () => {
    if (!reply.trim()) return;
    setSending(true);
    try {
      const updated = await addReply(doubtId, reply);
      setDoubt(updated);
      setReply('');
      onUpdated?.();
    } finally {
      setSending(false);
    }
  };

  const handleStatusChange = async (newStatus) => {
    const updated = await updateDoubtStatus(doubtId, newStatus);
    setDoubt(updated);
    onUpdated?.();
  };

  return (
    <Dialog open={open} onClose={onClose} fullWidth maxWidth="sm">
      {loading || !doubt ? (
        <DialogContent sx={{ display: 'flex', justifyContent: 'center', py: 6 }}>
          <CircularProgress />
        </DialogContent>
      ) : (
        <>
          <DialogTitle>
            <Typography variant="h6">{doubt.subject}</Typography>
            {doubt.course_title && (
              <Typography variant="caption" color="text.secondary">Course: {doubt.course_title}</Typography>
            )}
          </DialogTitle>
          <DialogContent dividers>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="body2" color="text.secondary">
                Asked by {doubt.student_name}
              </Typography>
              <Select
                size="small"
                value={doubt.status}
                onChange={(e) => handleStatusChange(e.target.value)}
              >
                <MenuItem value="OPEN">Open</MenuItem>
                <MenuItem value="IN_PROGRESS">In Progress</MenuItem>
                <MenuItem value="RESOLVED">Resolved</MenuItem>
              </Select>
            </Box>

            <Typography variant="body1" sx={{ mb: 2, whiteSpace: 'pre-wrap' }}>{doubt.question}</Typography>
            {doubt.attachment_url && (
              <Typography variant="body2" mb={2}>
                Attachment: <a href={doubt.attachment_url} target="_blank" rel="noopener noreferrer">{doubt.attachment_url}</a>
              </Typography>
            )}

            <Divider sx={{ my: 2 }} />

            <Stack spacing={2}>
              {doubt.replies.length === 0 && (
                <Typography variant="body2" color="text.secondary">No replies yet.</Typography>
              )}
              {doubt.replies.map((r, i) => (
                <Box key={i} sx={{ display: 'flex', gap: 1.5 }}>
                  <Avatar sx={{ width: 32, height: 32, fontSize: 13, bgcolor: r.author_role === 'teacher' ? 'primary.main' : 'secondary.main' }}>
                    {r.author_name[0]?.toUpperCase()}
                  </Avatar>
                  <Box>
                    <Typography variant="body2" fontWeight={700}>
                      {r.author_name} <Chip label={r.author_role} size="small" sx={{ ml: 0.5, height: 18, fontSize: 10 }} />
                    </Typography>
                    <Typography variant="body2">{r.message}</Typography>
                    <Typography variant="caption" color="text.disabled">
                      {new Date(r.created_at).toLocaleString()}
                    </Typography>
                  </Box>
                </Box>
              ))}
            </Stack>
          </DialogContent>
          <DialogActions sx={{ flexDirection: 'column', alignItems: 'stretch', p: 2, gap: 1 }}>
            <TextField
              placeholder={`Reply as ${user?.role}...`}
              fullWidth
              multiline
              minRows={2}
              value={reply}
              onChange={(e) => setReply(e.target.value)}
            />
            <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
              <Button onClick={onClose}>Close</Button>
              <Button variant="contained" onClick={handleReply} disabled={sending || !reply.trim()}>
                {sending ? 'Sending...' : 'Send Reply'}
              </Button>
            </Box>
          </DialogActions>
        </>
      )}
    </Dialog>
  );
}

export { STATUS_COLOR };
