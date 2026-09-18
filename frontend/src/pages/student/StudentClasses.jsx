import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Typography, Paper, Table, TableHead, TableBody, TableRow, TableCell,
  Chip, Button, CircularProgress, Alert,
} from '@mui/material';
import VideocamIcon from '@mui/icons-material/Videocam';
import { listClasses } from '../../services/api/classApi';

const STATUS_COLOR = { scheduled: 'default', live: 'success', ended: 'default' };

export default function StudentClasses() {
  const navigate = useNavigate();
  const [classes, setClasses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    listClasses()
      .then(setClasses)
      .catch(() => setError('Could not load classes.'))
      .finally(() => setLoading(false));
  }, []);

  return (
    <>
      <Typography variant="h4" mb={3}>Upcoming Classes</Typography>

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
                <TableCell>Teacher</TableCell>
                <TableCell>Scheduled</TableCell>
                <TableCell>Duration</TableCell>
                <TableCell>Status</TableCell>
                <TableCell align="right"></TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {classes.length === 0 && (
                <TableRow>
                  <TableCell colSpan={7} align="center">
                    <Typography color="text.secondary" py={3}>No classes scheduled yet.</Typography>
                  </TableCell>
                </TableRow>
              )}
              {classes.map((c) => (
                <TableRow key={c.id} hover>
                  <TableCell>{c.title}</TableCell>
                  <TableCell>{c.course_title}</TableCell>
                  <TableCell>{c.teacher_name}</TableCell>
                  <TableCell>{new Date(c.scheduled_at).toLocaleString()}</TableCell>
                  <TableCell>{c.duration_minutes} min</TableCell>
                  <TableCell><Chip label={c.status} size="small" color={STATUS_COLOR[c.status]} /></TableCell>
                  <TableCell align="right">
                    {c.status === 'live' && (
                      <Button
                        size="small"
                        variant="contained"
                        color="success"
                        startIcon={<VideocamIcon />}
                        onClick={() => navigate(`/meeting/${c.id}`)}
                      >
                        Join
                      </Button>
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </Paper>
      )}
    </>
  );
}
