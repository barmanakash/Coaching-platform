import { useEffect, useState, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Typography, Box, Button, Accordion, AccordionSummary, AccordionDetails,
  IconButton, Chip, CircularProgress, Alert, Snackbar, Dialog, DialogTitle,
  DialogContent, DialogActions, TextField, MenuItem, Tooltip, List, ListItem,
  ListItemText, ListItemIcon, Stack,
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import AddIcon from '@mui/icons-material/Add';
import DeleteIcon from '@mui/icons-material/Delete';
import EditIcon from '@mui/icons-material/Edit';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import PictureAsPdfIcon from '@mui/icons-material/PictureAsPdf';
import VideoLibraryIcon from '@mui/icons-material/VideoLibrary';
import ImageIcon from '@mui/icons-material/Image';
import DescriptionIcon from '@mui/icons-material/Description';
import LinkIcon from '@mui/icons-material/Link';
import AssignmentIcon from '@mui/icons-material/Assignment';
import { getCourse } from '../../services/api/courseApi';
import {
  listModules, createModule, deleteModule,
  listResources, createResource, deleteResource,
} from '../../services/api/moduleApi';

const RESOURCE_TYPES = [
  { value: 'link', label: 'Link', icon: LinkIcon },
  { value: 'pdf', label: 'PDF', icon: PictureAsPdfIcon },
  { value: 'video', label: 'Video', icon: VideoLibraryIcon },
  { value: 'image', label: 'Image', icon: ImageIcon },
  { value: 'document', label: 'Document', icon: DescriptionIcon },
  { value: 'assignment', label: 'Assignment', icon: AssignmentIcon },
];

const typeIcon = (type) => RESOURCE_TYPES.find((t) => t.value === type)?.icon || LinkIcon;

export default function TeacherCourseDetail() {
  const { courseId } = useParams();
  const navigate = useNavigate();

  const [course, setCourse] = useState(null);
  const [modules, setModules] = useState([]);
  const [resourcesByModule, setResourcesByModule] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [toast, setToast] = useState('');

  const [moduleDialogOpen, setModuleDialogOpen] = useState(false);
  const [moduleForm, setModuleForm] = useState({ title: '', description: '' });
  const [savingModule, setSavingModule] = useState(false);

  const [resourceDialogOpen, setResourceDialogOpen] = useState(false);
  const [activeModuleId, setActiveModuleId] = useState(null);
  const [resourceForm, setResourceForm] = useState({ title: '', description: '', type: 'link', url: '' });
  const [savingResource, setSavingResource] = useState(false);

  const loadResourcesForModule = useCallback(async (moduleId) => {
    const resources = await listResources(moduleId);
    setResourcesByModule((prev) => ({ ...prev, [moduleId]: resources }));
  }, []);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [courseData, moduleData] = await Promise.all([getCourse(courseId), listModules(courseId)]);
      setCourse(courseData);
      setModules(moduleData);
      await Promise.all(moduleData.map((m) => loadResourcesForModule(m.id)));
    } catch {
      setError('Could not load this course.');
    } finally {
      setLoading(false);
    }
  }, [courseId, loadResourcesForModule]);

  useEffect(() => { load(); }, [load]);

  const handleAddModule = async () => {
    if (!moduleForm.title.trim()) return;
    setSavingModule(true);
    try {
      await createModule(courseId, { title: moduleForm.title, description: moduleForm.description, order: modules.length });
      setToast('Module added');
      setModuleDialogOpen(false);
      setModuleForm({ title: '', description: '' });
      load();
    } catch {
      setToast('Failed to add module');
    } finally {
      setSavingModule(false);
    }
  };

  const handleDeleteModule = async (module) => {
    if (!window.confirm(`Delete module "${module.title}" and all its resources?`)) return;
    try {
      await deleteModule(module.id);
      setToast('Module deleted');
      load();
    } catch {
      setToast('Failed to delete module');
    }
  };

  const openResourceDialog = (moduleId) => {
    setActiveModuleId(moduleId);
    setResourceForm({ title: '', description: '', type: 'link', url: '' });
    setResourceDialogOpen(true);
  };

  const handleAddResource = async () => {
    if (!resourceForm.title.trim() || !resourceForm.url.trim()) return;
    setSavingResource(true);
    try {
      await createResource(activeModuleId, resourceForm);
      setToast('Resource added');
      setResourceDialogOpen(false);
      loadResourcesForModule(activeModuleId);
      setModules((prev) => prev.map((m) => (m.id === activeModuleId ? { ...m, resource_count: m.resource_count + 1 } : m)));
    } catch {
      setToast('Failed to add resource');
    } finally {
      setSavingResource(false);
    }
  };

  const handleDeleteResource = async (resource) => {
    if (!window.confirm(`Delete resource "${resource.title}"?`)) return;
    try {
      await deleteResource(resource.id);
      setToast('Resource deleted');
      loadResourcesForModule(resource.module_id);
      setModules((prev) => prev.map((m) => (m.id === resource.module_id ? { ...m, resource_count: Math.max(0, m.resource_count - 1) } : m)));
    } catch {
      setToast('Failed to delete resource');
    }
  };

  if (loading) return <CircularProgress />;
  if (error) return <Alert severity="error">{error}</Alert>;

  return (
    <>
      <Button startIcon={<ArrowBackIcon />} onClick={() => navigate('/teacher/courses')} sx={{ mb: 2 }}>
        Back to My Courses
      </Button>

      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 3 }}>
        <Box>
          <Typography variant="h4">{course.title}</Typography>
          <Typography variant="body2" color="text.secondary" mt={0.5}>{course.description}</Typography>
        </Box>
        <Button variant="contained" startIcon={<AddIcon />} onClick={() => setModuleDialogOpen(true)}>
          Add Module
        </Button>
      </Box>

      {modules.length === 0 && (
        <Alert severity="info">No modules yet. Add your first module to start organizing content.</Alert>
      )}

      {modules.map((m) => (
        <Accordion key={m.id} sx={{ mb: 1.5, borderRadius: 2, '&:before': { display: 'none' } }} elevation={1}>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', width: '100%', alignItems: 'center', pr: 2 }}>
              <Box>
                <Typography variant="subtitle1" fontWeight={700}>{m.title}</Typography>
                {m.description && (
                  <Typography variant="body2" color="text.secondary">{m.description}</Typography>
                )}
              </Box>
              <Chip label={`${m.resource_count} resources`} size="small" variant="outlined" />
            </Box>
          </AccordionSummary>
          <AccordionDetails>
            <List dense>
              {(resourcesByModule[m.id] || []).map((r) => {
                const Icon = typeIcon(r.type);
                return (
                  <ListItem
                    key={r.id}
                    secondaryAction={
                      <Tooltip title="Delete resource">
                        <IconButton edge="end" size="small" color="error" onClick={() => handleDeleteResource(r)}>
                          <DeleteIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                    }
                  >
                    <ListItemIcon sx={{ minWidth: 36 }}><Icon fontSize="small" color="primary" /></ListItemIcon>
                    <ListItemText
                      primary={r.title}
                      secondary={r.description || r.url}
                    />
                  </ListItem>
                );
              })}
              {(resourcesByModule[m.id] || []).length === 0 && (
                <Typography variant="body2" color="text.secondary" sx={{ py: 1 }}>
                  No resources in this module yet.
                </Typography>
              )}
            </List>
            <Stack direction="row" spacing={1} mt={1}>
              <Button size="small" startIcon={<AddIcon />} onClick={() => openResourceDialog(m.id)}>
                Add Resource
              </Button>
              <Button size="small" color="error" startIcon={<DeleteIcon />} onClick={() => handleDeleteModule(m)}>
                Delete Module
              </Button>
            </Stack>
          </AccordionDetails>
        </Accordion>
      ))}

      {/* Add Module Dialog */}
      <Dialog open={moduleDialogOpen} onClose={() => setModuleDialogOpen(false)} fullWidth maxWidth="sm">
        <DialogTitle>Add Module</DialogTitle>
        <DialogContent>
          <TextField
            label="Module Title" fullWidth required margin="normal"
            value={moduleForm.title} onChange={(e) => setModuleForm((f) => ({ ...f, title: e.target.value }))}
          />
          <TextField
            label="Description" fullWidth multiline rows={2} margin="normal"
            value={moduleForm.description} onChange={(e) => setModuleForm((f) => ({ ...f, description: e.target.value }))}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setModuleDialogOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleAddModule} disabled={savingModule || !moduleForm.title.trim()}>
            {savingModule ? 'Adding...' : 'Add'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Add Resource Dialog */}
      <Dialog open={resourceDialogOpen} onClose={() => setResourceDialogOpen(false)} fullWidth maxWidth="sm">
        <DialogTitle>Add Resource</DialogTitle>
        <DialogContent>
          <TextField
            label="Resource Title" fullWidth required margin="normal"
            value={resourceForm.title} onChange={(e) => setResourceForm((f) => ({ ...f, title: e.target.value }))}
          />
          <TextField
            select label="Type" fullWidth margin="normal"
            value={resourceForm.type} onChange={(e) => setResourceForm((f) => ({ ...f, type: e.target.value }))}
          >
            {RESOURCE_TYPES.map((t) => (
              <MenuItem key={t.value} value={t.value}>{t.label}</MenuItem>
            ))}
          </TextField>
          <TextField
            label="URL (link, or hosted file URL)" fullWidth required margin="normal"
            placeholder="https://..."
            value={resourceForm.url} onChange={(e) => setResourceForm((f) => ({ ...f, url: e.target.value }))}
          />
          <TextField
            label="Description (optional)" fullWidth multiline rows={2} margin="normal"
            value={resourceForm.description} onChange={(e) => setResourceForm((f) => ({ ...f, description: e.target.value }))}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setResourceDialogOpen(false)}>Cancel</Button>
          <Button
            variant="contained"
            onClick={handleAddResource}
            disabled={savingResource || !resourceForm.title.trim() || !resourceForm.url.trim()}
          >
            {savingResource ? 'Adding...' : 'Add'}
          </Button>
        </DialogActions>
      </Dialog>

      <Snackbar open={!!toast} autoHideDuration={3000} onClose={() => setToast('')} message={toast} />
    </>
  );
}
