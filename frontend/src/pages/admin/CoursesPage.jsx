import { useEffect, useState, useCallback } from 'react';
import {
  Typography, Paper, Table, TableHead, TableBody, TableRow, TableCell,
  Chip, IconButton, CircularProgress, Alert, Tooltip, Snackbar, Button,
  Dialog, DialogTitle, DialogContent, DialogActions, TextField, Box,
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import DeleteIcon from '@mui/icons-material/Delete';
import PublishIcon from '@mui/icons-material/Publish';
import UnpublishedIcon from '@mui/icons-material/Unpublished';
import { listCourses, createCourse, updateCourse, deleteCourse } from '../../services/api/adminApi';

export default function CoursesPage() {
  const [courses, setCourses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [toast, setToast] = useState('');

  const [dialogOpen, setDialogOpen] = useState(false);
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [saving, setSaving] = useState(false);

  const load = useCallback(() => {
    setLoading(true);
    listCourses()
      .then(setCourses)
      .catch(() => setError('Could not load courses.'))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => { load(); }, [load]);

  const handleCreate = async () => {
    if (!title.trim()) return;
    setSaving(true);
    try {
      await createCourse({ title, description, teacher_ids: [] });
      setToast('Course created');
      setDialogOpen(false);
      setTitle('');
      setDescription('');
      load();
    } catch {
      setToast('Failed to create course');
    } finally {
      setSaving(false);
    }
  };

  const togglePublish = async (course) => {
    const newStatus = course.status === 'published' ? 'draft' : 'published';
    try {
      await updateCourse(course.id, { status: newStatus });
      setToast(`Course ${newStatus === 'published' ? 'published' : 'unpublished'}`);
      load();
    } catch {
      setToast('Failed to update course');
    }
  };

  const handleDelete = async (course) => {
    if (!window.confirm(`Delete course "${course.title}"? This cannot be undone.`)) return;
    try {
      await deleteCourse(course.id);
      setToast('Course deleted');
      load();
    } catch {
      setToast('Failed to delete course');
    }
  };

  return (
    <>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" fontWeight={700}>Courses</Typography>
        <Button variant="contained" startIcon={<AddIcon />} onClick={() => setDialogOpen(true)}>
          New Course
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
                <TableCell>Description</TableCell>
                <TableCell>Teachers</TableCell>
                <TableCell>Students</TableCell>
                <TableCell>Status</TableCell>
                <TableCell align="right">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {courses.length === 0 && (
                <TableRow>
                  <TableCell colSpan={6} align="center">
                    <Typography color="text.secondary" py={3}>No courses yet. Create your first one.</Typography>
                  </TableCell>
                </TableRow>
              )}
              {courses.map((c) => (
                <TableRow key={c.id} hover>
                  <TableCell>{c.title}</TableCell>
                  <TableCell sx={{ maxWidth: 280 }}>
                    <Typography variant="body2" color="text.secondary" noWrap>
                      {c.description || '-'}
                    </Typography>
                  </TableCell>
                  <TableCell>{c.teacher_names?.length ? c.teacher_names.join(', ') : 'Unassigned'}</TableCell>
                  <TableCell>{c.student_count}</TableCell>
                  <TableCell>
                    <Chip
                      label={c.status}
                      color={c.status === 'published' ? 'success' : 'default'}
                      size="small"
                    />
                  </TableCell>
                  <TableCell align="right">
                    <Tooltip title={c.status === 'published' ? 'Unpublish' : 'Publish'}>
                      <IconButton onClick={() => togglePublish(c)} size="small">
                        {c.status === 'published' ? <UnpublishedIcon fontSize="small" /> : <PublishIcon fontSize="small" />}
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Delete">
                      <IconButton onClick={() => handleDelete(c)} size="small" color="error">
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
        <DialogTitle>Create Course</DialogTitle>
        <DialogContent>
          <TextField
            label="Course Title"
            fullWidth
            required
            margin="normal"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
          />
          <TextField
            label="Description"
            fullWidth
            multiline
            rows={3}
            margin="normal"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleCreate} disabled={saving || !title.trim()}>
            {saving ? 'Creating...' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>

      <Snackbar
        open={!!toast}
        autoHideDuration={3000}
        onClose={() => setToast('')}
        message={toast}
      />
    </>
  );
}
