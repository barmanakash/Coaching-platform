import { Typography, Paper, List, ListItemButton, ListItemText, Chip, Box, Button } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { usePresence } from '../context/PresenceContext';

const TYPE_LABEL = {
  doubt_new: 'Doubt',
  doubt_reply: 'Reply',
  message: 'Message',
  signup_pending: 'Approval',
  account_approved: 'Account',
};

export default function NotificationsPage() {
  const navigate = useNavigate();
  const { notifications, unreadCount, markRead, markAllRead } = usePresence();

  const handleClick = (n) => {
    if (!n.read) markRead(n.id);
    if (n.link) navigate(n.link);
  };

  return (
    <>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">Notifications</Typography>
        {unreadCount > 0 && (
          <Button size="small" onClick={markAllRead}>Mark all as read</Button>
        )}
      </Box>

      <Paper>
        <List sx={{ p: 0 }}>
          {notifications.length === 0 && (
            <Typography variant="body2" color="text.secondary" sx={{ p: 4, textAlign: 'center' }}>
              You're all caught up — nothing here yet.
            </Typography>
          )}
          {notifications.map((n) => (
            <ListItemButton
              key={n.id}
              onClick={() => handleClick(n)}
              sx={{
                borderBottom: '1px solid', borderColor: 'divider',
                bgcolor: n.read ? 'transparent' : 'action.hover',
                py: 1.5,
              }}
            >
              <ListItemText
                primary={
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Typography variant="body1" fontWeight={n.read ? 500 : 700}>{n.title}</Typography>
                    <Chip label={TYPE_LABEL[n.type] || n.type} size="small" variant="outlined" />
                  </Box>
                }
                secondary={
                  <>
                    <Typography variant="body2" color="text.secondary">{n.message}</Typography>
                    <Typography variant="caption" color="text.disabled">
                      {new Date(n.created_at).toLocaleString()}
                    </Typography>
                  </>
                }
              />
            </ListItemButton>
          ))}
        </List>
      </Paper>
    </>
  );
}
