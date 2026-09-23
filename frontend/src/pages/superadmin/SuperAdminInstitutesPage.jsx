import { useEffect, useState, useCallback } from 'react';
import {
  Typography, Paper, Table, TableHead, TableBody, TableRow, TableCell,
  Chip, Button, CircularProgress, Alert, Box, Dialog, DialogTitle,
  DialogContent, DialogActions, TextField, InputAdornment, IconButton,
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import { listInstitutes, createInstitute } from '../../services/api/superAdminApi';
import { apiErrorMessage } from '../../utils/roleHome';

const EMPTY_FORM = { name: '', code: '', adminName: '', adminEmail: '' };

export default function SuperAdminInstitutesPage() {
  const [institutes, setInstitutes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const [dialogOpen, setDialogOpen] = useState(false);
  const [form, setForm] = useState(EMPTY_FORM);
  const [formError, setFormError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const [result, setResult] = useState(null); // { institute, admin_invitation }

  const load = useCallback(() => {
    setLoading(true);
    listInstitutes()
      .then(setInstitutes)
      .catch(() => setError('Could not load institutes.'))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => { load(); }, [load]);

  const openDialog = () => {
    setForm(EMPTY_FORM);
    setFormError('');
    setDialogOpen(true);
  };

  const handleCreate = async (e) => {
    e.preventDefault();
    setFormError('');
    setSubmitting(true);
    try {
      const created = await createInstitute(form);
      setDialogOpen(false);
      setResult(created);
      load();
    } catch (err) {
      setFormError(apiErrorMessage(err, 'Could not create the institute.'));
    } finally {
      setSubmitting(false);
    }
  };

  const handleCopy = async (url) => {
    try { await navigator.clipboard.writeText(url); } catch { /* ignore */ }
  };

  return (
    <>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" fontWeight={700}>Institutes</Typography>
        <Button variant="contained" startIcon={<AddIcon />} onClick={openDialog}>
          New Institute
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
                <TableCell>Name</TableCell>
                <TableCell>Code</TableCell>
                <TableCell>Status</TableCell>
                <TableCell align="right">Admins</TableCell>
                <TableCell align="right">Teachers</TableCell>
                <TableCell align="right">Students</TableCell>
                <TableCell>Created</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {institutes.length === 0 && (
                <TableRow>
                  <TableCell colSpan={7} align="center">
                    <Typography color="text.secondary" py={3}>No institutes yet.</Typography>
                  </TableCell>
                </TableRow>
              )}
              {institutes.map((inst) => (
                <TableRow key={inst.id} hover>
                  <TableCell>{inst.name}</TableCell>
                  <TableCell><Chip label={inst.code} size="small" /></TableCell>
                  <TableCell>
                    <Chip label={inst.status} size="small" color={inst.status === 'active' ? 'success' : 'default'} />
                  </TableCell>
                  <TableCell align="right">{inst.admin_count}</TableCell>
                  <TableCell align="right">{inst.teacher_count}</TableCell>
                  <TableCell align="right">{inst.student_count}</TableCell>
                  <TableCell>{inst.created_at ? new Date(inst.created_at).toLocaleDateString() : '-'}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </Paper>
      )}

      {/* Create institute */}
      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} maxWidth="xs" fullWidth>
        <DialogTitle>Create a new institute</DialogTitle>
        <Box component="form" onSubmit={handleCreate}>
          <DialogContent>
            {formError && <Alert severity="error" sx={{ mb: 2 }}>{formError}</Alert>}
            <TextField
              label="Institute Name" fullWidth required margin="normal"
              value={form.name} onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
            />
            <TextField
              label="Institute Code" fullWidth required margin="normal"
              placeholder="e.g. bright-future"
              helperText="Lowercase letters, numbers and hyphens only"
              value={form.code} onChange={(e) => setForm((f) => ({ ...f, code: e.target.value }))}
            />
            <TextField
              label="First Admin's Name" fullWidth required margin="normal"
              value={form.adminName} onChange={(e) => setForm((f) => ({ ...f, adminName: e.target.value }))}
            />
            <TextField
              label="First Admin's Email" type="email" fullWidth required margin="normal"
              value={form.adminEmail} onChange={(e) => setForm((f) => ({ ...f, adminEmail: e.target.value }))}
            />
          </DialogContent>
          <DialogActions sx={{ px: 3, pb: 2 }}>
            <Button onClick={() => setDialogOpen(false)}>Cancel</Button>
            <Button type="submit" variant="contained" disabled={submitting}>
              {submitting ? 'Creating...' : 'Create Institute'}
            </Button>
          </DialogActions>
        </Box>
      </Dialog>

      {/* Show the first admin's invite link */}
      <Dialog open={!!result} onClose={() => setResult(null)} maxWidth="sm" fullWidth>
        <DialogTitle>Institute created</DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary" mb={2}>
            <strong>{result?.institute?.name}</strong> is ready. Send this link to{' '}
            <strong>{result?.admin_invitation?.name}</strong> ({result?.admin_invitation?.email}) so they can activate
            their Institute Admin account. It only works once.
          </Typography>
          <TextField
            fullWidth
            value={result?.admin_invitation?.invite_url || ''}
            InputProps={{
              readOnly: true,
              endAdornment: (
                <InputAdornment position="end">
                  <IconButton onClick={() => handleCopy(result?.admin_invitation?.invite_url)}>
                    <ContentCopyIcon fontSize="small" />
                  </IconButton>
                </InputAdornment>
              ),
            }}
          />
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2 }}>
          <Button variant="contained" onClick={() => setResult(null)}>Done</Button>
        </DialogActions>
      </Dialog>
    </>
  );
}
