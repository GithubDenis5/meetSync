import React, { useState } from "react";
import {
  Box, Typography, Card, CardContent, TextField, Button,
  Avatar, Grid, Alert, Divider,
} from "@mui/material";
import { useAuth } from "../context/AuthContext";
import { userApi } from "../utils/api";
import ImageUpload from "../components/ImageUpload";

const SettingsPage: React.FC = () => {
  const { user, logout } = useAuth();
  const [name, setName] = useState(user?.name || "");
  const [timezone, setTimezone] = useState(user?.timezone || "UTC");
  const [avatar, setAvatar] = useState(user?.avatar || "");
  const [success, setSuccess] = useState("");
  const [error, setError] = useState("");

  const handleSave = async () => {
    try {
      await userApi.updateMe({ name, timezone, avatar: avatar || undefined });
      setSuccess("Settings updated");
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to update settings");
    }
  };

  return (
    <>
      <Typography variant="h4" gutterBottom>Settings</Typography>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
      {success && <Alert severity="success" sx={{ mb: 2 }}>{success}</Alert>}

      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>Profile</Typography>
          <Box sx={{ display: "flex", alignItems: "center", gap: 2, mb: 3 }}>
            <Avatar src={avatar || user?.avatar} sx={{ width: 64, height: 64, bgcolor: "secondary.main", fontSize: 28 }}>
              {user?.name?.[0] || "U"}
            </Avatar>
            <Box sx={{ flex: 1 }}>
              <Typography variant="body1">{user?.name}</Typography>
              <Typography variant="body2" color="text.secondary">{user?.email}</Typography>
              {user?.telegram_id && <Typography variant="body2">Telegram: {user.telegram_id}</Typography>}
              <Box sx={{ mt: 1, maxWidth: 300 }}>
                <ImageUpload
                  label="Change avatar"
                  currentImage={avatar || user?.avatar}
                  onUploaded={(urls) => setAvatar(urls.medium)}
                  onRemove={() => setAvatar("")}
                />
              </Box>
            </Box>
          </Box>

          <Grid container spacing={2}>
            <Grid item xs={12} sm={6}>
              <TextField fullWidth label="Name" value={name} onChange={(e) => setName(e.target.value)} />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField fullWidth label="Timezone" value={timezone} onChange={(e) => setTimezone(e.target.value)} />
            </Grid>
          </Grid>

          <Box sx={{ mt: 3 }}>
            <Button variant="contained" onClick={handleSave}>Save Settings</Button>
          </Box>
        </CardContent>
      </Card>

      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom color="error">Danger Zone</Typography>
          <Divider sx={{ mb: 2 }} />
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Logging out will clear your session. You'll need to sign in again.
          </Typography>
          <Button variant="outlined" color="error" onClick={logout}>
            Logout
          </Button>
        </CardContent>
      </Card>
    </>
  );
};

export default SettingsPage;
