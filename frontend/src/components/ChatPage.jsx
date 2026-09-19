import { useEffect, useRef, useState, useCallback } from 'react';
import {
  Box, Paper, List, ListItemButton, ListItemAvatar, Avatar, ListItemText,
  Badge, Divider, TextField, IconButton, Typography, CircularProgress, Dialog,
  DialogTitle, DialogContent, DialogActions, Button,
} from '@mui/material';
import SendIcon from '@mui/icons-material/Send';
import PersonAddIcon from '@mui/icons-material/PersonAdd';
import { listConversations, listContacts, startConversation, getMessages } from '../services/api/conversationApi';
import { createSocket } from '../services/websocket/socketClient';
import { usePresence } from '../context/PresenceContext';
import { useAuth } from '../context/AuthContext';

export default function ChatPage() {
  const { user } = useAuth();
  const { onlineUserIds } = usePresence();

  const [conversations, setConversations] = useState([]);
  const [loadingConvos, setLoadingConvos] = useState(true);
  const [activeConversation, setActiveConversation] = useState(null);
  const [messages, setMessages] = useState([]);
  const [draft, setDraft] = useState('');
  const [contactDialogOpen, setContactDialogOpen] = useState(false);
  const [contacts, setContacts] = useState([]);
  const [hasMore, setHasMore] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);

  const socketRef = useRef(null);
  const messagesEndRef = useRef(null);

  const loadConversations = useCallback(() => {
    setLoadingConvos(true);
    listConversations().then(setConversations).finally(() => setLoadingConvos(false));
  }, []);

  useEffect(() => { loadConversations(); }, [loadConversations]);

  const openConversation = useCallback((conv) => {
    setActiveConversation(conv);
    getMessages(conv.id).then((msgs) => {
      setMessages(msgs);
      setHasMore(msgs.length === 50);
    });

    if (socketRef.current) socketRef.current.close();
    const socket = createSocket(`/ws/chat/${conv.id}`);
    socket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'message' && data.conversation_id === conv.id) {
        setMessages((prev) => [...prev, data]);
      }
    };
    socketRef.current = socket;
  }, []);

  const loadEarlier = async () => {
    if (!activeConversation || messages.length === 0) return;
    setLoadingMore(true);
    try {
      const older = await getMessages(activeConversation.id, { before: messages[0].created_at });
      setMessages((prev) => [...older, ...prev]);
      setHasMore(older.length === 50);
    } finally {
      setLoadingMore(false);
    }
  };

  useEffect(() => () => { socketRef.current?.close(); }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = () => {
    if (!draft.trim() || !socketRef.current) return;
    socketRef.current.send(JSON.stringify({ content: draft }));
    setDraft('');
  };

  const openContactPicker = () => {
    listContacts().then(setContacts);
    setContactDialogOpen(true);
  };

  const handleStartChat = async (contact) => {
    const conv = await startConversation(contact.id);
    setContactDialogOpen(false);
    loadConversations();
    openConversation(conv);
  };

  return (
    <Box sx={{ display: 'flex', height: 'calc(100vh - 160px)', gap: 2 }}>
      <Paper sx={{ width: 300, display: 'flex', flexDirection: 'column', flexShrink: 0 }}>
        <Box sx={{ p: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Typography variant="h6">Chats</Typography>
          <IconButton onClick={openContactPicker} size="small" color="primary">
            <PersonAddIcon fontSize="small" />
          </IconButton>
        </Box>
        <Divider />
        {loadingConvos ? (
          <Box sx={{ p: 3, textAlign: 'center' }}><CircularProgress size={24} /></Box>
        ) : (
          <List sx={{ overflowY: 'auto', flexGrow: 1 }}>
            {conversations.length === 0 && (
              <Typography variant="body2" color="text.secondary" sx={{ p: 2 }}>
                No conversations yet. Tap + to start one.
              </Typography>
            )}
            {conversations.map((c) => {
              const online = onlineUserIds.has(c.other_user_id) || c.online;
              return (
                <ListItemButton
                  key={c.id}
                  selected={activeConversation?.id === c.id}
                  onClick={() => openConversation(c)}
                >
                  <ListItemAvatar>
                    <Badge
                      overlap="circular"
                      anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
                      variant="dot"
                      color={online ? 'success' : 'default'}
                    >
                      <Avatar>{c.other_user_name[0]?.toUpperCase()}</Avatar>
                    </Badge>
                  </ListItemAvatar>
                  <ListItemText
                    primary={c.other_user_name}
                    secondary={c.last_message_preview || 'Say hello!'}
                    secondaryTypographyProps={{ noWrap: true }}
                  />
                </ListItemButton>
              );
            })}
          </List>
        )}
      </Paper>

      <Paper sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column' }}>
        {!activeConversation ? (
          <Box sx={{ m: 'auto', textAlign: 'center', color: 'text.secondary' }}>
            <Typography>Select a conversation to start chatting</Typography>
          </Box>
        ) : (
          <>
            <Box sx={{ p: 2, borderBottom: '1px solid', borderColor: 'divider' }}>
              <Typography variant="subtitle1" fontWeight={700}>{activeConversation.other_user_name}</Typography>
              <Typography variant="caption" color="text.secondary">
                {(onlineUserIds.has(activeConversation.other_user_id) || activeConversation.online) ? 'Online' : 'Offline'}
              </Typography>
            </Box>
            <Box sx={{ flexGrow: 1, overflowY: 'auto', p: 2, display: 'flex', flexDirection: 'column', gap: 1 }}>
              {hasMore && (
                <Button size="small" onClick={loadEarlier} disabled={loadingMore} sx={{ alignSelf: 'center', mb: 1 }}>
                  {loadingMore ? 'Loading...' : 'Load earlier messages'}
                </Button>
              )}
              {messages.map((m, i) => {
                const isMine = m.sender_id === user.userId;
                return (
                  <Box
                    key={m.id || i}
                    sx={{
                      alignSelf: isMine ? 'flex-end' : 'flex-start',
                      bgcolor: isMine ? 'primary.main' : 'background.default',
                      color: isMine ? 'primary.contrastText' : 'text.primary',
                      px: 1.5, py: 1, borderRadius: 2, maxWidth: '70%',
                    }}
                  >
                    <Typography variant="body2">{m.content}</Typography>
                  </Box>
                );
              })}
              <div ref={messagesEndRef} />
            </Box>
            <Box sx={{ p: 2, borderTop: '1px solid', borderColor: 'divider', display: 'flex', gap: 1 }}>
              <TextField
                fullWidth
                size="small"
                placeholder="Type a message..."
                value={draft}
                onChange={(e) => setDraft(e.target.value)}
                onKeyDown={(e) => { if (e.key === 'Enter') handleSend(); }}
              />
              <IconButton color="primary" onClick={handleSend}><SendIcon /></IconButton>
            </Box>
          </>
        )}
      </Paper>

      <Dialog open={contactDialogOpen} onClose={() => setContactDialogOpen(false)} fullWidth maxWidth="xs">
        <DialogTitle>Start a Chat</DialogTitle>
        <DialogContent>
          <List>
            {contacts.map((c) => (
              <ListItemButton key={c.id} onClick={() => handleStartChat(c)}>
                <ListItemAvatar>
                  <Badge
                    overlap="circular"
                    anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
                    variant="dot"
                    color={(onlineUserIds.has(c.id) || c.online) ? 'success' : 'default'}
                  >
                    <Avatar>{c.name[0]?.toUpperCase()}</Avatar>
                  </Badge>
                </ListItemAvatar>
                <ListItemText primary={c.name} secondary={c.email} />
              </ListItemButton>
            ))}
            {contacts.length === 0 && (
              <Typography variant="body2" color="text.secondary" sx={{ p: 2 }}>
                No contacts available yet.
              </Typography>
            )}
          </List>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setContactDialogOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
