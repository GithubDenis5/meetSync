import React, { useEffect, useRef, useState } from "react";
import {
  Box, Typography, Card, CardContent, List, ListItem, ListItemText,
  Chip, CircularProgress,
} from "@mui/material";
import { notificationApi } from "../utils/api";
import { Notification } from "../types";

interface GroupActivityFeedProps {
  groupId: number;
  token: string;
}

const EVENT_ICONS: Record<string, string> = {
  UserJoinedGroup: "👋",
  UserLeftGroup: "🚪",
  IdeaCreated: "💡",
  VotingStarted: "🗳️",
  VotingFinished: "✅",
  MeetingPossible: "📅",
  MeetingCancelled: "❌",
  ReminderNeeded: "⏰",
  AvailabilityConfirmed: "📋",
  GroupEvent: "🔔",
};

const GroupActivityFeed: React.FC<GroupActivityFeedProps> = ({ groupId, token }) => {
  const [events, setEvents] = useState<Notification[]>([]);
  const [loading, setLoading] = useState(true);
  const [connected, setConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout>>();

  // Load event history
  useEffect(() => {
    notificationApi.events(groupId, 30)
      .then(({ data }) => setEvents(data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [groupId]);

  // WebSocket connection
  useEffect(() => {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const wsUrl = `${protocol}//${window.location.host}/ws/group/${token}/${groupId}`;

    const connect = () => {
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        setConnected(true);
        // Send initial ping
        ws.send(JSON.stringify({ type: "ping" }));
      };

      ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);
          if (msg.type === "pong") return;
          if (msg.type === "notification") {
            const notification = msg.payload;
            // Extract user_id from notification data or set to 0
            setEvents((prev) => [notification, ...prev].slice(0, 50));
          }
        } catch {
          // ignore
        }
      };

      ws.onclose = () => {
        setConnected(false);
        wsRef.current = null;
        // Reconnect after 5s
        reconnectTimer.current = setTimeout(connect, 5000);
      };

      ws.onerror = () => {
        ws.close();
      };
    };

    connect();

    return () => {
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current);
      if (wsRef.current) wsRef.current.close();
    };
  }, [groupId, token]);

  return (
    <Card variant="outlined" sx={{ mb: 2 }}>
      <CardContent sx={{ p: 2, "&:last-child": { pb: 2 } }}>
        <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 1 }}>
          <Typography variant="subtitle2" sx={{ fontWeight: 600, flex: 1 }}>
            Activity Feed
          </Typography>
          <Chip
            label={connected ? "● Live" : "○ Disconnected"}
            size="small"
            color={connected ? "success" : "default"}
            sx={{ height: 20, fontSize: 10 }}
          />
        </Box>

        {loading ? (
          <Box sx={{ display: "flex", justifyContent: "center", p: 2 }}>
            <CircularProgress size={20} />
          </Box>
        ) : events.length === 0 ? (
          <Typography variant="caption" color="text.secondary">
            No recent activity.
          </Typography>
        ) : (
          <List disablePadding sx={{ maxHeight: 300, overflow: "auto" }}>
            {events.map((ev) => (
              <ListItem key={ev.id} disableGutters sx={{ py: 0.5 }}>
                <ListItemText
                  primary={
                    <Box sx={{ display: "flex", alignItems: "center", gap: 0.5 }}>
                      <Typography variant="body2" component="span">
                        {EVENT_ICONS[ev.type] || "🔔"}
                      </Typography>
                      <Typography variant="body2" component="span" sx={{ fontWeight: 500 }}>
                        {ev.title}
                      </Typography>
                    </Box>
                  }
                  secondary={
                    <Typography variant="caption" color="text.secondary">
                      {ev.message || new Date(ev.created_at).toLocaleString()}
                    </Typography>
                  }
                />
              </ListItem>
            ))}
          </List>
        )}
      </CardContent>
    </Card>
  );
};

export default GroupActivityFeed;
