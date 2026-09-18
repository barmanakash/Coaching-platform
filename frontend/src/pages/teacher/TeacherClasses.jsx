import { useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Typography, Box, Button, Paper, Table, TableHead, TableBody, TableRow,
  TableCell, Chip, CircularProgress, Alert, Dialog, DialogTitle, DialogContent,
  DialogActions, TextField, MenuItem, IconButton, Tooltip, Snackbar,
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import StopIcon from '@mui/icons-material/Stop';
import VideocamIcon from '@mui/icons-material/Videocam';
import DeleteIcon from '@mui/icons-material/Delete';
import { listClasses, createClass, deleteClass, startClass, endClass } from '../../services/api/classApi';
import { listCourses } from '../../services/api/courseApi';

const STATUS_COLOR = { scheduled: 'default', live: 'success', ended: 'default' };

export default function TeacherClasses() {
  const navigate = useNavigate();
  const [classes, setClasses] = useState([]);
  const [courses, setCourses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [toast, setToast] = useState('');

  const [dialogOpen, setDialogOpen] = useState(false);
  const [form, setForm] = useState({ course_id: '', title: '', description: '', date: '', time: '', duration_minutes: 45 });
  const [saving, setSaving] = useState(false);

  const load = useCallback(() => {
    setLoading(true);
    Promise.all([listClasses(), listCourses()])
      .then(([classData, courseData]) => { setClasses(classData); setCourses(courseData); })
      .catch(() => setError('Could not load classes.'))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => { load(); }, [load]);

  const handleCreate = async () => {
    if (!form.course_id || !form.title.trim() || !form.date || !form.time) return;
    setSaving(true);
    try {
      const scheduled_at = new Date(`${form.date}T${form.time}`).toISOString();
      await createClass({
        course_id: form.course_id,
        title: form.title,
        description: form.description,
        scheduled_at,
        duration_minutes: Number(form.duration_minutes) || 45,
      });
      setToast('Class scheduled');
      setDialogOpen(false);
      setForm({ course_id: '', title: '', description: '', date: '', time: '', duration_minutes: 45 });
      load();
    } catch {
      setToast('Failed to schedule class');
    } finally {
      setSaving(false);
    }
  };

  const handleStart = async (cls) => {
    try {
      await startClass(cls.id);
      setToast('Class started');
      load();
    } catch {
      setToast('Failed to start class');
    }
  };

  const handleEnd = async (cls) => {
    try {
      await endClass(cls.id);
      setToast('Class ended');
      load();
    } catch {
      setToast('Failed to end class');
    }
  };

  const handleDelete = async (cls) => {
    if (!window.confirm(`Delete class "${cls.title}"?`)) return;
    try {
      await deleteClass(cls.id);
      setToast('Class deleted');
      load();
    } catch {
      setToast('Failed to delete class');
    }
  };

  return (
    <>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">Classes</Typography>
        <Button variant="contained" startIcon={<AddIcon />} onClick={() => setDialogOpen(true)}>
          Schedule Class
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
                <TableCell>Title</TableCell>
                <TableCell>Course</TableCell>
                <TableCell>Scheduled</TableCell>
                <TableCell>Duration</TableCell>
                <TableCell>Status</TableCell>
                <TableCell align="right">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {classes.length === 0 && (
                <TableRow>
                  <TableCell colSpan={6} align="center">
                    <Typography color="text.secondary" py={3}>No classes scheduled yet.</Typography>
                  </TableCell>
                </TableRow>
              )}
              {classes.map((c) => (
                <TableRow key={c.id} hover>
                  <TableCell>{c.title}</TableCell>
                  <TableCell>{c.course_title}</TableCell>
                  <TableCell>{new Date(c.scheduled_at).toLocaleString()}</TableCell>
                  <TableCell>{c.duration_minutes} min</TableCell>
                  <TableCell><Chip label={c.status} size="small" color={STATUS_COLOR[c.status]} /></TableCell>
                  <TableCell align="right">
                    {c.status === 'scheduled' && (
                      <Tooltip title="Start class">
                        <IconButton size="small" color="success" onClick={() => handleStart(c)}>
                          <PlayArrowIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                    )}
                    {c.status === 'live' && (
                      <>
                        <Tooltip title="Join meeting">
                          <IconButton size="small" color="primary" onClick={() => navigate(`/meeting/${c.id}`)}>
                            <VideocamIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="End class">
                          <IconButton size="small" color="error" onClick={() => handleEnd(c)}>
                            <StopIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                      </>
                    )}
                    <Tooltip title="Delete">
                      <IconButton size="small" color="error" onClick={() => handleDelete(c)}>
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

      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} fullWidth maxWidth="sm">
        <DialogTitle>Schedule a Class</DialogTitle>
        <DialogContent>
          <TextField
            select label="Course" fullWidth required margin="normal"
            value={form.course_id} onChange={(e) => setForm((f) => ({ ...f, course_id: e.target.value }))}
          >
            {courses.map((c) => <MenuItem key={c.id} value={c.id}>{c.title}</MenuItem>)}
          </TextField>
          <TextField
            label="Class Title" fullWidth required margin="normal"
            value={form.title} onChange={(e) => setForm((f) => ({ ...f, title: e.target.value }))}
          />
          <Box sx={{ display: 'flex', gap: 2 }}>
            <TextField
              label="Date" type="date" fullWidth required margin="normal" InputLabelProps={{ shrink: true }}
              value={form.date} onChange={(e) => setForm((f) => ({ ...f, date: e.target.value }))}
            />
            <TextField
              label="Time" type="time" fullWidth required margin="normal" InputLabelProps={{ shrink: true }}
              value={form.time} onChange={(e) => setForm((f) => ({ ...f, time: e.target.value }))}
            />
          </Box>
          <TextField
            label="Duration (minutes)" type="number" fullWidth margin="normal"
            value={form.duration_minutes} onChange={(e) => setForm((f) => ({ ...f, duration_minutes: e.target.value }))}
          />
          <TextField
            label="Description (optional)" fullWidth multiline rows={2} margin="normal"
            value={form.description} onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>Cancel</Button>
          <Button
            variant="contained"
            onClick={handleCreate}
            disabled={saving || !form.course_id || !form.title.trim() || !form.date || !form.time}
          >
            {saving ? 'Scheduling...' : 'Schedule'}
          </Button>
        </DialogActions>
      </Dialog>

      <Snackbar open={!!toast} autoHideDuration={3000} onClose={() => setToast('')} message={toast} />
    </>
  );
}
