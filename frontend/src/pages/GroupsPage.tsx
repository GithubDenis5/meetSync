import React, { useState, useEffect } from "react";
import {
  Box, Button, Card, CardContent, Dialog, DialogTitle, DialogContent,
  DialogActions, Grid, TextField, Typography, Chip, CircularProgress, Alert,
  useMediaQuery,
} from "@mui/material";
import { Add, Group, ContentCopy } from "@mui/icons-material";
import { groupApi } from "../utils/api";
import { Group as GroupType } from "../types";
import { useNavigate } from "react-router-dom";

const GroupsPage: React.FC = () => {
  const [groups, setGroups] = useState<GroupType[]>([]);
  const [loading, setLoading] = useState(true);
  const [open, setOpen] = useState(false);
  const [joinOpen, setJoinOpen] = useState(false);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [inviteCode, setInviteCode] = useState("");
  const [error, setError] = useState("");
  const navigate = useNavigate();
  const isMobile = useMediaQuery("(max-width:600px)");

  const loadGroups = () => {
    groupApi.list().then(({ data }) => setGroups(data)).catch(() => {}).finally(() => setLoading(false));
  };

  useEffect(loadGroups, []);

  const handleCreate = async () => {
    try {
      await groupApi.create({ name, description });
      setOpen(false);
      setName("");
      setDescription("");
      loadGroups();
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to create group");
    }
  };

  const handleJoin = async () => {
    try {
      await groupApi.join(inviteCode);
      setJoinOpen(false);
      setInviteCode("");
      loadGroups();
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to join group");
    }
  };

  if (loading) return <Box sx={{ display: "flex", justifyContent: "center", mt: 4 }}><CircularProgress /></Box>;

  return (
    <>
      <Box sx={{ display: "flex", flexDirection: { xs: "column", sm: "row" }, justifyContent: "space-between", alignItems: { xs: "stretch", sm: "center" }, mb: 3, gap: 1 }}>
        <Typography variant="h4" sx={{ fontSize: { xs: "1.5rem", sm: "2rem" } }}>My Groups</Typography>
        <Box sx={{ display: "flex", gap: 1 }}>
          <Button variant="outlined" onClick={() => setJoinOpen(true)} fullWidth={isMobile}>Join Group</Button>
          <Button variant="contained" startIcon={<Add />} onClick={() => setOpen(true)} fullWidth={isMobile}>Create Group</Button>
        </Box>
      </Box>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      {groups.length === 0 ? (
        <Typography color="text.secondary" align="center" sx={{ mt: 4 }}>
          No groups yet. Create or join a group to get started!
        </Typography>
      ) : (
        <Grid container spacing={3}>
          {groups.map((g) => (
            <Grid item xs={12} sm={6} md={4} key={g.id}>
              <Card sx={{ cursor: "pointer" }} onClick={() => navigate(`/groups/${g.id}`)}>
                <CardContent>
                  <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 1 }}>
                    <Group color="primary" />
                    <Typography variant="h6">{g.name}</Typography>
                  </Box>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                    {g.description || "No description"}
                  </Typography>
                  <Chip
                    size="small"
                    icon={<ContentCopy fontSize="small" />}
                    label={g.invite_code}
                    onClick={(e) => {
                      e.stopPropagation();
                      navigator.clipboard.writeText(g.invite_code);
                    }}
                  />
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}

      {/* Create dialog */}
      <Dialog open={open} onClose={() => setOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Create Group</DialogTitle>
        <DialogContent>
          <TextField fullWidth label="Group Name" value={name} onChange={(e) => setName(e.target.value)} sx={{ mt: 1 }} required />
          <TextField fullWidth label="Description" value={description} onChange={(e) => setDescription(e.target.value)} multiline rows={3} sx={{ mt: 2 }} />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleCreate}>Create</Button>
        </DialogActions>
      </Dialog>

      {/* Join dialog */}
      <Dialog open={joinOpen} onClose={() => setJoinOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Join Group</DialogTitle>
        <DialogContent>
          <TextField fullWidth label="Invite Code" value={inviteCode} onChange={(e) => setInviteCode(e.target.value)} sx={{ mt: 1 }} />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setJoinOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleJoin}>Join</Button>
        </DialogActions>
      </Dialog>
    </>
  );
};

export default GroupsPage;
