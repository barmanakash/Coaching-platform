import { useEffect, useState, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Typography, Box, Button, Accordion, AccordionSummary, AccordionDetails,
  Chip, CircularProgress, Alert, List, ListItem, ListItemText, ListItemIcon,
  ListItemButton,
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import PictureAsPdfIcon from '@mui/icons-material/PictureAsPdf';
import VideoLibraryIcon from '@mui/icons-material/VideoLibrary';
import ImageIcon from '@mui/icons-material/Image';
import DescriptionIcon from '@mui/icons-material/Description';
import LinkIcon from '@mui/icons-material/Link';
import AssignmentIcon from '@mui/icons-material/Assignment';
import { getCourse } from '../../services/api/courseApi';
import { listModules, listResources } from '../../services/api/moduleApi';
import { resolveResourceUrl } from '../../services/api/axiosClient';

const TYPE_ICONS = {
  link: LinkIcon,
  pdf: PictureAsPdfIcon,
  video: VideoLibraryIcon,
  image: ImageIcon,
  document: DescriptionIcon,
  assignment: AssignmentIcon,
};

export default function StudentCourseDetail() {
  const { courseId } = useParams();
  const navigate = useNavigate();

  const [course, setCourse] = useState(null);
  const [modules, setModules] = useState([]);
  const [resourcesByModule, setResourcesByModule] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [courseData, moduleData] = await Promise.all([getCourse(courseId), listModules(courseId)]);
      setCourse(courseData);
      setModules(moduleData);
      const entries = await Promise.all(
        moduleData.map(async (m) => [m.id, await listResources(m.id)])
      );
      setResourcesByModule(Object.fromEntries(entries));
    } catch {
      setError('Could not load this course.');
    } finally {
      setLoading(false);
    }
  }, [courseId]);

  useEffect(() => { load(); }, [load]);

  if (loading) return <CircularProgress />;
  if (error) return <Alert severity="error">{error}</Alert>;

  return (
    <>
      <Button startIcon={<ArrowBackIcon />} onClick={() => navigate('/student/courses')} sx={{ mb: 2 }}>
        Back to My Courses
      </Button>

      <Typography variant="h4" mb={0.5}>{course.title}</Typography>
      <Typography variant="body2" color="text.secondary" mb={3}>{course.description}</Typography>

      {modules.length === 0 && (
        <Alert severity="info">This course doesn't have any content yet. Check back soon.</Alert>
      )}

      {modules.map((m) => {
        const resources = resourcesByModule[m.id] || [];
        return (
          <Accordion key={m.id} sx={{ mb: 1.5, borderRadius: 2, '&:before': { display: 'none' } }} elevation={1}>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', width: '100%', alignItems: 'center', pr: 2 }}>
                <Box>
                  <Typography variant="subtitle1" fontWeight={700}>{m.title}</Typography>
                  {m.description && (
                    <Typography variant="body2" color="text.secondary">{m.description}</Typography>
                  )}
                </Box>
                <Chip label={`${resources.length} items`} size="small" variant="outlined" />
              </Box>
            </AccordionSummary>
            <AccordionDetails>
              {resources.length === 0 ? (
                <Typography variant="body2" color="text.secondary" sx={{ py: 1 }}>
                  Nothing here yet.
                </Typography>
              ) : (
                <List dense>
                  {resources.map((r) => {
                    const Icon = TYPE_ICONS[r.type] || LinkIcon;
                    return (
                      <ListItem key={r.id} disablePadding>
                        <ListItemButton component="a" href={resolveResourceUrl(r.url)} target="_blank" rel="noopener noreferrer">
                          <ListItemIcon sx={{ minWidth: 36 }}><Icon fontSize="small" color="primary" /></ListItemIcon>
                          <ListItemText primary={r.title} secondary={r.description || 'Open resource'} />
                        </ListItemButton>
                      </ListItem>
                    );
                  })}
                </List>
              )}
            </AccordionDetails>
          </Accordion>
        );
      })}
    </>
  );
}
