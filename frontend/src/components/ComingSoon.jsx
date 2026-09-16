import { Typography, Paper, Box } from '@mui/material';
import ConstructionIcon from '@mui/icons-material/Construction';

export default function ComingSoon({ title, note }) {
  return (
    <>
      <Typography variant="h4" fontWeight={700} mb={3}>{title}</Typography>
      <Paper sx={{ p: 5, textAlign: 'center' }}>
        <Box sx={{ color: 'text.disabled', mb: 2 }}>
          <ConstructionIcon sx={{ fontSize: 48 }} />
        </Box>
        <Typography variant="h6" color="text.secondary">This feature is coming soon</Typography>
        {note && (
          <Typography variant="body2" color="text.disabled" mt={1}>
            {note}
          </Typography>
        )}
      </Paper>
    </>
  );
}
