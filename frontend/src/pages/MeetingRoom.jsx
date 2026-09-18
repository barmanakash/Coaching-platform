import { useEffect, useRef, useState, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Box, IconButton, Typography, Tooltip, Alert } from '@mui/material';
import MicIcon from '@mui/icons-material/Mic';
import MicOffIcon from '@mui/icons-material/MicOff';
import VideocamIcon from '@mui/icons-material/Videocam';
import VideocamOffIcon from '@mui/icons-material/VideocamOff';
import CallEndIcon from '@mui/icons-material/CallEnd';
import { createSocket } from '../services/websocket/socketClient';
import { useAuth } from '../context/AuthContext';

const ICE_SERVERS = { iceServers: [{ urls: 'stun:stun.l.google.com:19302' }] };

/**
 * A functional first-version meeting room: mesh WebRTC over a signaling
 * WebSocket (/ws/meeting/{classId}). Good for a small class-sized call;
 * not a replacement for a full SFU-backed product like Google Meet.
 */
export default function MeetingRoom() {
  const { classId } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();

  const [micOn, setMicOn] = useState(true);
  const [camOn, setCamOn] = useState(true);
  const [error, setError] = useState('');
  const [remoteStreams, setRemoteStreams] = useState({}); // peerId -> {stream, name}

  const localVideoRef = useRef(null);
  const localStreamRef = useRef(null);
  const socketRef = useRef(null);
  const peersRef = useRef({}); // peerId -> RTCPeerConnection

  const createPeerConnection = useCallback((peerId, peerName) => {
    const pc = new RTCPeerConnection(ICE_SERVERS);

    localStreamRef.current?.getTracks().forEach((track) => {
      pc.addTrack(track, localStreamRef.current);
    });

    pc.onicecandidate = (event) => {
      if (event.candidate) {
        socketRef.current?.send(JSON.stringify({
          type: 'signal', to: peerId, signal: { type: 'candidate', candidate: event.candidate },
        }));
      }
    };

    pc.ontrack = (event) => {
      setRemoteStreams((prev) => ({
        ...prev,
        [peerId]: { stream: event.streams[0], name: peerName || prev[peerId]?.name || 'Participant' },
      }));
    };

    peersRef.current[peerId] = pc;
    return pc;
  }, []);

  const cleanupPeer = (peerId) => {
    peersRef.current[peerId]?.close();
    delete peersRef.current[peerId];
    setRemoteStreams((prev) => {
      const next = { ...prev };
      delete next[peerId];
      return next;
    });
  };

  useEffect(() => {
    let cancelled = false;

    (async () => {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
        if (cancelled) { stream.getTracks().forEach((t) => t.stop()); return; }
        localStreamRef.current = stream;
        if (localVideoRef.current) localVideoRef.current.srcObject = stream;
      } catch {
        setError('Could not access camera/microphone. Check browser permissions.');
        return;
      }

      const socket = createSocket(`/ws/meeting/${classId}`);
      socketRef.current = socket;

      socket.onclose = (event) => {
        if (event.code === 4403) setError('This class is not live, or you cannot join it.');
        if (event.code === 4404) setError('This class no longer exists.');
      };

      socket.onmessage = async (event) => {
        const data = JSON.parse(event.data);

        if (data.type === 'existing-peers') {
          for (const peerId of data.peers) {
            const pc = createPeerConnection(peerId);
            const offer = await pc.createOffer();
            await pc.setLocalDescription(offer);
            socket.send(JSON.stringify({ type: 'signal', to: peerId, signal: { type: 'offer', sdp: offer.sdp } }));
          }
        } else if (data.type === 'peer-joined') {
          setRemoteStreams((prev) => ({ ...prev, [data.user_id]: { stream: null, name: data.name } }));
        } else if (data.type === 'peer-left') {
          cleanupPeer(data.user_id);
        } else if (data.type === 'signal') {
          const { from, name, signal } = data;
          if (signal.type === 'offer') {
            const pc = createPeerConnection(from, name);
            await pc.setRemoteDescription({ type: 'offer', sdp: signal.sdp });
            const answer = await pc.createAnswer();
            await pc.setLocalDescription(answer);
            socket.send(JSON.stringify({ type: 'signal', to: from, signal: { type: 'answer', sdp: answer.sdp } }));
          } else if (signal.type === 'answer') {
            const pc = peersRef.current[from];
            if (pc) await pc.setRemoteDescription({ type: 'answer', sdp: signal.sdp });
          } else if (signal.type === 'candidate') {
            const pc = peersRef.current[from];
            if (pc) await pc.addIceCandidate(signal.candidate).catch(() => {});
          }
        }
      };
    })();

    return () => {
      cancelled = true;
      socketRef.current?.close();
      Object.keys(peersRef.current).forEach(cleanupPeer);
      localStreamRef.current?.getTracks().forEach((t) => t.stop());
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [classId, createPeerConnection]);

  const toggleMic = () => {
    localStreamRef.current?.getAudioTracks().forEach((t) => { t.enabled = !t.enabled; });
    setMicOn((v) => !v);
  };

  const toggleCam = () => {
    localStreamRef.current?.getVideoTracks().forEach((t) => { t.enabled = !t.enabled; });
    setCamOn((v) => !v);
  };

  const leaveCall = () => {
    navigate(-1);
  };

  const tiles = [{ id: 'local', name: `${user?.name} (You)`, stream: null, isLocal: true }, ...Object.entries(remoteStreams).map(([id, v]) => ({ id, name: v.name, stream: v.stream }))];

  return (
    <Box sx={{ minHeight: '100vh', bgcolor: '#0F0E1F', display: 'flex', flexDirection: 'column' }}>
      {error && <Alert severity="error" sx={{ m: 2 }}>{error}</Alert>}

      <Box sx={{ flexGrow: 1, display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 2, p: 2 }}>
        {tiles.map((tile) => (
          <VideoTile key={tile.id} tile={tile} localVideoRef={tile.isLocal ? localVideoRef : null} />
        ))}
      </Box>

      <Box sx={{ display: 'flex', justifyContent: 'center', gap: 2, p: 3 }}>
        <Tooltip title={micOn ? 'Mute' : 'Unmute'}>
          <IconButton onClick={toggleMic} sx={{ bgcolor: micOn ? 'rgba(255,255,255,0.1)' : 'error.main', color: '#fff' }}>
            {micOn ? <MicIcon /> : <MicOffIcon />}
          </IconButton>
        </Tooltip>
        <Tooltip title={camOn ? 'Turn off camera' : 'Turn on camera'}>
          <IconButton onClick={toggleCam} sx={{ bgcolor: camOn ? 'rgba(255,255,255,0.1)' : 'error.main', color: '#fff' }}>
            {camOn ? <VideocamIcon /> : <VideocamOffIcon />}
          </IconButton>
        </Tooltip>
        <Tooltip title="Leave call">
          <IconButton onClick={leaveCall} sx={{ bgcolor: 'error.main', color: '#fff' }}>
            <CallEndIcon />
          </IconButton>
        </Tooltip>
      </Box>
    </Box>
  );
}

function VideoTile({ tile, localVideoRef }) {
  const videoRef = useRef(null);

  useEffect(() => {
    if (!tile.isLocal && videoRef.current && tile.stream) {
      videoRef.current.srcObject = tile.stream;
    }
  }, [tile]);

  return (
    <Box sx={{ position: 'relative', bgcolor: '#1E1B4B', borderRadius: 2, overflow: 'hidden', aspectRatio: '16/10' }}>
      <video
        ref={tile.isLocal ? localVideoRef : videoRef}
        autoPlay
        playsInline
        muted={tile.isLocal}
        style={{ width: '100%', height: '100%', objectFit: 'cover' }}
      />
      <Typography
        variant="caption"
        sx={{ position: 'absolute', bottom: 8, left: 8, color: '#fff', bgcolor: 'rgba(0,0,0,0.5)', px: 1, borderRadius: 1 }}
      >
        {tile.name}
      </Typography>
    </Box>
  );
}
