import { useEffect, useState, useCallback } from 'react';
import {
  Typography, Paper, Table, TableHead, TableBody, TableRow, TableCell,
  Chip, Button, IconButton, CircularProgress, Alert, Tooltip, Snackbar, Box,
  Dialog, DialogTitle, DialogContent, DialogActions, TextField,
  ToggleButtonGroup, ToggleButton, Stack, InputAdornment,
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import RefreshIcon from '@mui/icons-material/Refresh';
import DeleteIcon from '@mui/icons-material/Delete';
import {
  listInvitations, createInvitation, regenerateInvitation, revokeInvitation,
} from '../../services/api/invitationApi';
import { apiErrorMessage } from '../../utils/roleHome';

const STATUS_COLOR = { pending: 'warning', accepted: 'success', revoked: 'default', expired: 'error' };

export default function InvitationsPage() {
  const [invitations, setInvitations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [toast, setToast] = useState('');
  const [actingOn, setActingOn] = useState(null);

  const [dialogOpen, setDialogOpen] = useState(false);
  const [form, setForm] = useState({ name: '', email: '', role: 'student' });
  const [formError, setFormError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const [linkDialog, setLinkDialog] = useState(null); // { name, email, invite_url }

  const load = useCallback(() => {
    setLoading(true);
    listInvitations()
      .then(setInvitations)
      .catch(() => setError('Could not load invitations.'))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => { load(); }, [load]);

  const openDialog = () => {
    setForm({ name: '', email: '', role: 'student' });
    setFormError('');
    setDialogOpen(true);
  };

  const handleCreate = async (e) => {
    e.preventDefault();
    setFormError('');
    setSubmitting(true);
    try {
      const created = await createInvitation(form);
      setDialogOpen(false);
      setLinkDialog(created);
      load();
    } catch (err) {
      setFormError(apiErrorMessage(err, 'Could not create the invitation.'));
    } finally {
      setSubmitting(false);
    }
  };

  const handleCopy = async (url) => {
    try {
      await navigator.clipboard.writeText(url);
      setToast('Invite link copied to clipboard');
    } catch {
      setToast('Could not copy automatically — copy the link manually');
    }
  };

  const handleRegenerate = async (invitation) => {
    setActingOn(invitation.id);
    try {
      const updated = await regenerateInvitation(invitation.id);
      setLinkDialog(updated);
      load();
    } catch (err) {
      setToast(apiErrorMessage(err, 'Could not regenerate the link.'));
    } finally {
      setActingOn(null);
    }
  };

  const handleRevoke = async (invitation) => {
    if (!window.confirm(`Revoke the invitation for ${invitation.email}? Their link will stop working.`)) return;
    setActingOn(invitation.id);
    try {
      await revokeInvitation(invitation.id);
      setToast('Invitation revoked');
      load();
    } catch (err) {
      setToast(apiErrorMessage(err, 'Could not revoke the invitation.'));
    } finally {
      setActingOn(null);
    }
  };

  return (
    <>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" fontWeight={700}>Invitations</Typography>
        <Button variant="contained" startIcon={<AddIcon />} onClick={openDialog}>
          Invite Teacher or Student
        </Button>
      </Box>

      <Typography variant="body2" color="text.secondary" mb={2}>
        Accounts are created only by invitation. Send someone the link below to let them set up their own account.
      </Typography>

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
                <TableCell>Role</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Expires</TableCell>
                <TableCell align="right">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {invitations.length === 0 && (
                <TableRow>
                  <TableCell colSpan={6} align="center">
                    <Typography color="text.secondary" py={3}>No invitations sent yet.</Typography>
                  </TableCell>
                </TableRow>
              )}
              {invitations.map((inv) => (
                <TableRow key={inv.id} hover>
                  <TableCell>{inv.name}</TableCell>
                  <TableCell>{inv.email}</TableCell>
                  <TableCell><Chip label={inv.role} size="small" sx={{ textTransform: 'capitalize' }} /></TableCell>
                  <TableCell>
                    <Chip label={inv.status} size="small" color={STATUS_COLOR[inv.status] || 'default'} sx={{ textTransform: 'capitalize' }} />
                  </TableCell>
                  <TableCell>{new Date(inv.expires_at).toLocaleDateString()}</TableCell>
                  <TableCell align="right">
                    <Stack direction="row" spacing={0.5} justifyContent="flex-end">
                      {(inv.status === 'pending' || inv.status === 'expired') && (
                        <>
                          <Tooltip title="Get a new link">
                            <IconButton size="small" disabled={actingOn === inv.id} onClick={() => handleRegenerate(inv)}>
                              <RefreshIcon fontSize="small" />
                            </IconButton>
                          </Tooltip>
                          <Tooltip title="Revoke">
                            <IconButton size="small" color="error" disabled={actingOn === inv.id} onClick={() => handleRevoke(inv)}>
                              <DeleteIcon fontSize="small" />
                            </IconButton>
                          </Tooltip>
                        </>
                      )}
                    </Stack>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </Paper>
      )}

      {/* Create invitation */}
      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} maxWidth="xs" fullWidth>
        <DialogTitle>Invite a teacher or student</DialogTitle>
        <Box component="form" onSubmit={handleCreate}>
          <DialogContent>
            {formError && <Alert severity="error" sx={{ mb: 2 }}>{formError}</Alert>}
            <ToggleButtonGroup
              value={form.role}
              exclusive
              fullWidth
              sx={{ mb: 2 }}
              onChange={(_e, role) => role && setForm((f) => ({ ...f, role }))}
            >
              <ToggleButton value="student">Student</ToggleButton>
              <ToggleButton value="teacher">Teacher</ToggleButton>
            </ToggleButtonGroup>
            <TextField
              label="Full Name" fullWidth required margin="normal"
              value={form.name} onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
            />
            <TextField
              label="Email" type="email" fullWidth required margin="normal"
              value={form.email} onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))}
            />
          </DialogContent>
          <DialogActions sx={{ px: 3, pb: 2 }}>
            <Button onClick={() => setDialogOpen(false)}>Cancel</Button>
            <Button type="submit" variant="contained" disabled={submitting}>
              {submitting ? 'Sending...' : 'Create Invitation'}
            </Button>
          </DialogActions>
        </Box>
      </Dialog>

      {/* Show the one-time link */}
      <Dialog open={!!linkDialog} onClose={() => setLinkDialog(null)} maxWidth="sm" fullWidth>
        <DialogTitle>Invitation ready</DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary" mb={2}>
            Send this link to <strong>{linkDialog?.name}</strong> ({linkDialog?.email}). It only works once and won't be shown again.
          </Typography>
          <TextField
            fullWidth
            value={linkDialog?.invite_url || ''}
            InputProps={{
              readOnly: true,
              endAdornment: (
                <InputAdornment position="end">
                  <IconButton onClick={() => handleCopy(linkDialog?.invite_url)}>
                    <ContentCopyIcon fontSize="small" />
                  </IconButton>
                </InputAdornment>
              ),
            }}
          />
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2 }}>
          <Button variant="contained" onClick={() => setLinkDialog(null)}>Done</Button>
        </DialogActions>
      </Dialog>

      <Snackbar open={!!toast} autoHideDuration={3000} onClose={() => setToast('')} message={toast} />
    </>
  );
}
