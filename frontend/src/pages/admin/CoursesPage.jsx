import { useEffect, useState, useCallback } from 'react';
import {
  Typography, Paper, Table, TableHead, TableBody, TableRow, TableCell,
  Chip, IconButton, CircularProgress, Alert, Tooltip, Snackbar, Button,
  Dialog, DialogTitle, DialogContent, DialogActions, TextField, Box,
  Select, MenuItem, InputLabel, FormControl, OutlinedInput, List,
  ListItem, ListItemText, Divider,
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import PublishIcon from '@mui/icons-material/Publish';
import UnpublishedIcon from '@mui/icons-material/Unpublished';
import GroupIcon from '@mui/icons-material/Group';
import { listCourses, createCourse, updateCourse, deleteCourse, listTeachers, listStudents } from '../../services/api/adminApi';
import { listCourseEnrollments, enrollStudent, unenrollStudent } from '../../services/api/enrollmentApi';

const emptyForm = { title: '', description: '', teacherIds: [] };

export default function CoursesPage() {
  const [courses, setCourses] = useState([]);
  const [teachers, setTeachers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [toast, setToast] = useState('');

  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingCourseId, setEditingCourseId] = useState(null);
  const [form, setForm] = useState(emptyForm);
  const [saving, setSaving] = useState(false);

  const [studentsDialogOpen, setStudentsDialogOpen] = useState(false);
  const [activeCourse, setActiveCourse] = useState(null);
  const [enrolledStudents, setEnrolledStudents] = useState([]);
  const [allStudents, setAllStudents] = useState([]);
  const [studentToAdd, setStudentToAdd] = useState('');
  const [enrolling, setEnrolling] = useState(false);

  const load = useCallback(() => {
    setLoading(true);
    Promise.all([listCourses(), listTeachers()])
      .then(([courseData, teacherData]) => {
        setCourses(courseData);
        setTeachers(teacherData);
      })
      .catch(() => setError('Could not load courses.'))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => { load(); }, [load]);

  const openCreateDialog = () => {
    setEditingCourseId(null);
    setForm(emptyForm);
    setDialogOpen(true);
  };

  const openEditDialog = (course) => {
    setEditingCourseId(course.id);
    setForm({
      title: course.title,
      description: course.description || '',
      teacherIds: course.teacher_ids || [],
    });
    setDialogOpen(true);
  };

  const handleSave = async () => {
    if (!form.title.trim()) return;
    setSaving(true);
    try {
      if (editingCourseId) {
        await updateCourse(editingCourseId, {
          title: form.title,
          description: form.description,
          teacher_ids: form.teacherIds,
        });
        setToast('Course updated');
      } else {
        await createCourse({
          title: form.title,
          description: form.description,
          teacher_ids: form.teacherIds,
        });
        setToast('Course created');
      }
      setDialogOpen(false);
      load();
    } catch {
      setToast(editingCourseId ? 'Failed to update course' : 'Failed to create course');
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

  const teacherNameById = (id) => teachers.find((t) => t.id === id)?.name || id;

  const openStudentsDialog = async (course) => {
    setActiveCourse(course);
    setStudentsDialogOpen(true);
    setStudentToAdd('');
    const [enrolled, students] = await Promise.all([listCourseEnrollments(course.id), listStudents()]);
    setEnrolledStudents(enrolled);
    setAllStudents(students);
  };

  const availableStudents = allStudents.filter(
    (s) => !enrolledStudents.some((e) => e.id === s.id)
  );

  const handleEnroll = async () => {
    if (!studentToAdd) return;
    setEnrolling(true);
    try {
      await enrollStudent(activeCourse.id, studentToAdd);
      const enrolled = await listCourseEnrollments(activeCourse.id);
      setEnrolledStudents(enrolled);
      setStudentToAdd('');
      load();
    } catch {
      setToast('Failed to enroll student');
    } finally {
      setEnrolling(false);
    }
  };

  const handleUnenroll = async (student) => {
    try {
      await unenrollStudent(activeCourse.id, student.id);
      setEnrolledStudents((prev) => prev.filter((s) => s.id !== student.id));
      load();
    } catch {
      setToast('Failed to remove student');
    }
  };

  return (
    <>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" fontWeight={700}>Courses</Typography>
        <Button variant="contained" startIcon={<AddIcon />} onClick={openCreateDialog}>
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
                  <TableCell>
                    <Chip
                      label={`${c.student_count} enrolled`}
                      size="small"
                      variant="outlined"
                      onClick={() => openStudentsDialog(c)}
                      sx={{ cursor: 'pointer' }}
                    />
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={c.status}
                      color={c.status === 'published' ? 'success' : 'default'}
                      size="small"
                    />
                  </TableCell>
                  <TableCell align="right">
                    <Tooltip title="Manage Students">
                      <IconButton onClick={() => openStudentsDialog(c)} size="small">
                        <GroupIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Edit / Assign Teacher">
                      <IconButton onClick={() => openEditDialog(c)} size="small">
                        <EditIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
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

      {/* Create/Edit Course Dialog */}
      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} fullWidth maxWidth="sm">
        <DialogTitle>{editingCourseId ? 'Edit Course' : 'Create Course'}</DialogTitle>
        <DialogContent>
          <TextField
            label="Course Title"
            fullWidth
            required
            margin="normal"
            value={form.title}
            onChange={(e) => setForm((f) => ({ ...f, title: e.target.value }))}
          />
          <TextField
            label="Description"
            fullWidth
            multiline
            rows={3}
            margin="normal"
            value={form.description}
            onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))}
          />

          <FormControl fullWidth margin="normal">
            <InputLabel id="teacher-select-label">Assign Teacher(s)</InputLabel>
            <Select
              labelId="teacher-select-label"
              multiple
              value={form.teacherIds}
              onChange={(e) => {
                const value = e.target.value;
                setForm((f) => ({ ...f, teacherIds: typeof value === 'string' ? value.split(',') : value }));
              }}
              input={<OutlinedInput label="Assign Teacher(s)" />}
              renderValue={(selected) => selected.map(teacherNameById).join(', ') || 'Unassigned'}
            >
              {teachers.length === 0 && (
                <MenuItem disabled>No teachers have signed up yet</MenuItem>
              )}
              {teachers.map((t) => (
                <MenuItem key={t.id} value={t.id}>{t.name} ({t.email})</MenuItem>
              ))}
            </Select>
          </FormControl>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleSave} disabled={saving || !form.title.trim()}>
            {saving ? 'Saving...' : editingCourseId ? 'Save Changes' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Manage Students Dialog */}
      <Dialog open={studentsDialogOpen} onClose={() => setStudentsDialogOpen(false)} fullWidth maxWidth="sm">
        <DialogTitle>Manage Students {activeCourse ? `— ${activeCourse.title}` : ''}</DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', gap: 1, mb: 2, mt: 1 }}>
            <FormControl fullWidth size="small">
              <InputLabel id="add-student-label">Enroll a student</InputLabel>
              <Select
                labelId="add-student-label"
                label="Enroll a student"
                value={studentToAdd}
                onChange={(e) => setStudentToAdd(e.target.value)}
              >
                {availableStudents.length === 0 && (
                  <MenuItem disabled>No more students to add</MenuItem>
                )}
                {availableStudents.map((s) => (
                  <MenuItem key={s.id} value={s.id}>{s.name} ({s.email})</MenuItem>
                ))}
              </Select>
            </FormControl>
            <Button variant="contained" onClick={handleEnroll} disabled={!studentToAdd || enrolling}>
              Add
            </Button>
          </Box>

          <Divider sx={{ mb: 1 }} />

          <List dense>
            {enrolledStudents.length === 0 && (
              <Typography variant="body2" color="text.secondary" sx={{ p: 2 }}>
                No students enrolled yet.
              </Typography>
            )}
            {enrolledStudents.map((s) => (
              <ListItem
                key={s.id}
                secondaryAction={
                  <IconButton edge="end" size="small" color="error" onClick={() => handleUnenroll(s)}>
                    <DeleteIcon fontSize="small" />
                  </IconButton>
                }
              >
                <ListItemText primary={s.name} secondary={s.email} />
              </ListItem>
            ))}
          </List>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setStudentsDialogOpen(false)}>Close</Button>
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
