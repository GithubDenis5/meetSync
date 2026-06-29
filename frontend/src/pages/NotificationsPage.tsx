import React, { useState, useEffect } from "react";
import {
  Box, Typography, Card, CardContent, List, ListItem, ListItemText,
  Button, Chip, CircularProgress, IconButton, Divider,
} from "@mui/material";
import { DoneAll, Notifications as NotifIcon, Delete } from "@mui/icons-material";
import { notificationApi } from "../utils/api";
import { Notification } from "../types";

const NotificationsPage: React.FC = () => {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => { loadNotifications(); }, []);

  const loadNotifications = () => {
    notificationApi.list()
      .then(({ data }) => setNotifications(data))
      .catch(() => {})
      .finally(() => setLoading(false));
  };

  const handleMarkAllRead = async () => {
    await notificationApi.markAllRead();
    loadNotifications();
  };

  const handleMarkRead = async (id: number) => {
    await notificationApi.markRead(id);
    setNotifications((prev) => prev.map((n) => n.id === id ? { ...n, is_read: true } : n));
  };

  if (loading) return <Box sx={{ display: "flex", justifyContent: "center", mt: 4 }}><CircularProgress /></Box>;

  return (
    <>
      <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mb: 3 }}>
        <Typography variant="h4">Notifications</Typography>
        {notifications.some((n) => !n.is_read) && (
          <Button startIcon={<DoneAll />} onClick={handleMarkAllRead}>
            Mark All Read
          </Button>
        )}
      </Box>

      {notifications.length === 0 ? (
        <Card>
          <CardContent>
            <Box sx={{ textAlign: "center", py: 4 }}>
              <NotifIcon sx={{ fontSize: 64, color: "text.disabled", mb: 2 }} />
              <Typography color="text.secondary">No notifications yet</Typography>
            </Box>
          </CardContent>
        </Card>
      ) : (
        <Card>
          <List>
            {notifications.map((n, i) => (
              <React.Fragment key={n.id}>
                {i > 0 && <Divider />}
                <ListItem
                  sx={{ bgcolor: n.is_read ? "transparent" : "action.hover", cursor: "pointer" }}
                  secondaryAction={
                    !n.is_read && (
                      <IconButton edge="end" onClick={() => handleMarkRead(n.id)}>
                        <DoneAll fontSize="small" />
                      </IconButton>
                    )
                  }
                >
                  <ListItemText
                    primary={
                      <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                        {n.title}
                        {!n.is_read && <Chip size="small" color="primary" label="New" />}
                      </Box>
                    }
                    secondary={n.message || n.type}
                  />
                </ListItem>
              </React.Fragment>
            ))}
          </List>
        </Card>
      )}
    </>
  );
};

export default NotificationsPage;
