import React, { useState, useEffect } from "react";
import {
  Dialog, DialogTitle, DialogContent, DialogContentText, IconButton,
  Typography, Box, List, ListItem, ListItemIcon, ListItemText,
} from "@mui/material";
import {
  Close, Group, CalendarMonth, Lightbulb, HowToVote,
  Event, Notifications, Telegram,
} from "@mui/icons-material";
import { useAuth } from "../context/AuthContext";

const ONBOARDING_KEY = "meetsync_onboarded";

const FEATURES = [
  {
    icon: <Group color="primary" />,
    title: "Create or join a group",
    desc: "Start by creating a group or joining one via invite code. All activities happen inside groups.",
  },
  {
    icon: <Lightbulb color="warning" />,
    title: "Collect ideas",
    desc: "Add activity ideas to the bank. React with emojis and comment to discuss with friends.",
  },
  {
    icon: <CalendarMonth color="success" />,
    title: "Mark your availability",
    desc: "Use the calendar to show when you're free, busy, or maybe available. See your group's collective schedule.",
  },
  {
    icon: <HowToVote color="secondary" />,
    title: "Vote on what to do",
    desc: "Start a vote when it's time to pick. Random, most popular, or by category — the winner is chosen automatically.",
  },
  {
    icon: <Event color="info" />,
    title: "Schedule & RSVP",
    desc: "Turn a winning idea into a meeting. Mark going, not going, or maybe so everyone knows who's in.",
  },
  {
    icon: <Notifications />,
    title: "Stay notified",
    desc: "Get real-time WebSocket notifications in the app and optional Telegram messages so you never miss a thing.",
  },
];

const OnboardingDialog: React.FC = () => {
  const [open, setOpen] = useState(false);
  const { user } = useAuth();

  useEffect(() => {
    if (!user) return;
    const key = `${ONBOARDING_KEY}_${user.id}`;
    const seen = localStorage.getItem(key);
    if (!seen) {
      setOpen(true);
    }
  }, [user]);

  const handleClose = () => {
    if (!user) return;
    const key = `${ONBOARDING_KEY}_${user.id}`;
    localStorage.setItem(key, "true");
    setOpen(false);
  };

  return (
    <Dialog
      open={open}
      onClose={handleClose}
      maxWidth="sm"
      fullWidth
      PaperProps={{
        sx: {
          borderRadius: 4,
          maxHeight: "90vh",
        },
      }}
    >
      {/* Title with close button */}
      <DialogTitle sx={{ pb: 0, pr: 1 }}>
        <Box sx={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between" }}>
          <Box>
            <Typography variant="h5" sx={{ fontWeight: 700, letterSpacing: "-0.02em", mb: 0.5 }}>
              Welcome to MeetSync!
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Here's a quick tour of what you can do
            </Typography>
          </Box>
          <IconButton onClick={handleClose} size="small" sx={{ mt: 0.5 }}>
            <Close fontSize="small" />
          </IconButton>
        </Box>
      </DialogTitle>

      <DialogContent sx={{ pt: 2, pb: 3 }}>
        <DialogContentText component="div" sx={{ mt: 1 }}>
          <List disablePadding>
            {FEATURES.map((feature, i) => (
              <ListItem key={i} disableGutters sx={{ alignItems: "flex-start", mb: 1.5 }}>
                <ListItemIcon sx={{ mt: 0.5, minWidth: 40 }}>
                  {feature.icon}
                </ListItemIcon>
                <ListItemText
                  primary={
                    <Typography variant="body2" fontWeight={600}>
                      {feature.title}
                    </Typography>
                  }
                  secondary={
                    <Typography variant="body2" color="text.secondary" sx={{ mt: 0.25 }}>
                      {feature.desc}
                    </Typography>
                  }
                />
              </ListItem>
            ))}
          </List>

          <Box
            sx={{
              mt: 3,
              p: 2,
              borderRadius: 2,
              bgcolor: "rgba(99, 102, 241, 0.08)",
              display: "flex",
              alignItems: "center",
              gap: 1.5,
            }}
          >
            <Telegram sx={{ color: "#0088cc" }} />
            <Typography variant="caption" color="text.secondary">
              Tip: Connect your Telegram account in Settings to receive notifications on the go!
            </Typography>
          </Box>
        </DialogContentText>
      </DialogContent>
    </Dialog>
  );
};

export default OnboardingDialog;
