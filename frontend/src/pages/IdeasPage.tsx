import React, { useState, useEffect } from "react";
import {
  Box, Typography, Card, CardContent, Grid, Chip, Button, Dialog,
  DialogTitle, DialogContent, DialogActions, TextField, Select,
  MenuItem, FormControl, InputLabel, CircularProgress, IconButton,
  Snackbar, Alert, useMediaQuery,
} from "@mui/material";
import { Add, Lightbulb, Archive, Event } from "@mui/icons-material";
import { ideasApi, groupApi, meetingApi } from "../utils/api";
import { Idea, Group } from "../types";
import { useNavigate, useSearchParams } from "react-router-dom";

const CATEGORIES = [
  "Outdoor", "Entertainment", "Food & Drink", "Sports", "Culture",
  "Travel", "Relaxation", "Education", "Other",
];

const IdeasPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const [ideas, setIdeas] = useState<Idea[]>([]);
  const [groups, setGroups] = useState<Group[]>([]);
  const [selectedGroup, setSelectedGroup] = useState<number>(Number(searchParams.get("group_id")) || 0);
  const [loading, setLoading] = useState(true);
  const [open, setOpen] = useState(false);
  const [showArchived, setShowArchived] = useState(false);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [cost, setCost] = useState("");
  const [category, setCategory] = useState("");
  const navigate = useNavigate();

  // Schedule dialog
  const [scheduleOpen, setScheduleOpen] = useState(false);
  const [scheduleIdea, setScheduleIdea] = useState<Idea | null>(null);
  const [scheduleDate, setScheduleDate] = useState("");
  const [scheduleTime, setScheduleTime] = useState("");
  const [scheduleLocation, setScheduleLocation] = useState("");
  const [snackbar, setSnackbar] = useState<{ open: boolean; message: string; severity: "success" | "error" }>({
    open: false, message: "", severity: "success",
  });
  const isMobile = useMediaQuery("(max-width:600px)");

  useEffect(() => {
    groupApi.list().then(({ data }) => setGroups(data)).catch(() => {});
  }, []);

  useEffect(() => {
    if (!selectedGroup) { setLoading(false); return; }
    ideasApi.list(selectedGroup, showArchived)
      .then(({ data }) => setIdeas(data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [selectedGroup, showArchived]);

  const handleCreate = async () => {
    if (!selectedGroup) return;
    await ideasApi.create(selectedGroup, { title, description: description || undefined, cost: cost || undefined, category: category || undefined });
    setOpen(false); setTitle(""); setDescription(""); setCost(""); setCategory("");
    const { data } = await ideasApi.list(selectedGroup, showArchived);
    setIdeas(data);
  };

  const handleScheduleOpen = (idea: Idea) => {
    setScheduleIdea(idea);
    setScheduleDate("");
    setScheduleTime("");
    setScheduleLocation(idea.location || "");
    setScheduleOpen(true);
  };

  const handleSchedule = async () => {
    if (!selectedGroup || !scheduleIdea || !scheduleDate) {
      setSnackbar({ open: true, message: "Date is required", severity: "error" });
      return;
    }
    try {
      await meetingApi.create({
        group_id: selectedGroup,
        title: scheduleIdea.title,
        description: scheduleIdea.description || undefined,
        date: scheduleDate,
        time: scheduleTime || undefined,
        location: scheduleLocation || undefined,
        idea_id: scheduleIdea.id,
      });
      setSnackbar({ open: true, message: `"${scheduleIdea.title}" scheduled on the calendar!`, severity: "success" });
      setScheduleOpen(false);
      setScheduleIdea(null);
    } catch {
      setSnackbar({ open: true, message: "Failed to schedule idea", severity: "error" });
    }
  };

  const reactionEmoji = (reactions: Record<string, number>) => {
    return Object.entries(reactions).map(([r, c]) => `${r} ${c}`).join(" ") || "No reactions";
  };

  if (loading) return <Box sx={{ display: "flex", justifyContent: "center", mt: 4 }}><CircularProgress /></Box>;

  return (
    <>
      <Box sx={{ display: "flex", flexDirection: { xs: "column", sm: "row" }, justifyContent: "space-between", alignItems: { xs: "stretch", sm: "center" }, mb: 2, gap: 1 }}>
        <Typography variant="h4" sx={{ fontSize: { xs: "1.5rem", sm: "2rem" } }}>Bank of Ideas</Typography>
        <Box sx={{ display: "flex", gap: 1 }}>
          <Button
            variant={showArchived ? "contained" : "outlined"}
            startIcon={<Archive />}
            onClick={() => setShowArchived(!showArchived)}
            fullWidth={isMobile}
            size="small"
          >
            {showArchived ? "Active" : "Archived"}
          </Button>
          <Button variant="contained" startIcon={<Add />} onClick={() => setOpen(true)} disabled={!selectedGroup}
            fullWidth={isMobile} size="small"
          >
            New
          </Button>
        </Box>
      </Box>

      <FormControl size="small" sx={{ minWidth: { xs: 1, sm: 200 }, mb: 3, width: { xs: "100%", sm: "auto" } }}>
        <InputLabel>Group</InputLabel>
        <Select value={selectedGroup} onChange={(e) => setSelectedGroup(e.target.value as number)} label="Group">
          {groups.map((g) => <MenuItem key={g.id} value={g.id}>{g.name}</MenuItem>)}
        </Select>
      </FormControl>

      {!selectedGroup ? (
        <Typography color="text.secondary">Select a group to view ideas</Typography>
      ) : ideas.length === 0 ? (
        <Typography color="text.secondary">No ideas yet. Add one!</Typography>
      ) : (
        <Grid container spacing={2}>
          {ideas.map((idea) => (
            <Grid item xs={12} sm={6} md={4} key={idea.id}>
              <Card sx={{ cursor: "pointer" }} onClick={() => navigate(`/ideas/${idea.id}`)}>
                <CardContent>
                  <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 1 }}>
                    <Lightbulb color="warning" />
                    <Typography variant="h6">{idea.title}</Typography>
                  </Box>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                    {idea.description || "No description"}
                  </Typography>
                  {idea.category && <Chip size="small" label={idea.category} sx={{ mr: 1 }} />}
                  {idea.cost && <Chip size="small" variant="outlined" label={idea.cost} />}
                  <Box sx={{ mt: 1, display: "flex", flexDirection: { xs: "column", sm: "row" }, alignItems: { xs: "stretch", sm: "center" }, gap: 0.5 }}>
                    <Typography variant="caption" sx={{ fontSize: { xs: "0.7rem", sm: "0.75rem" }, mb: { xs: 0.5, sm: 0 } }}>
                      {reactionEmoji(idea.reactions)} — by {idea.suggestor_name || "Unknown"}
                    </Typography>
                    <Button
                      size="small"
                      variant="outlined"
                      startIcon={<Event />}
                      onClick={(e) => { e.stopPropagation(); handleScheduleOpen(idea); }}
                      sx={{ alignSelf: { xs: "stretch", sm: "auto" } }}
                    >
                      Schedule
                    </Button>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}

      {/* Schedule dialog */}
      <Dialog open={scheduleOpen} onClose={() => { setScheduleOpen(false); setScheduleIdea(null); }} maxWidth="sm" fullWidth>
        <DialogTitle>Schedule Idea: {scheduleIdea?.title}</DialogTitle>
        <DialogContent>
          <TextField
            margin="dense"
            label="Date"
            type="date"
            fullWidth
            required
            value={scheduleDate}
            onChange={(e) => setScheduleDate(e.target.value)}
            InputLabelProps={{ shrink: true }}
          />
          <TextField
            margin="dense"
            label="Time"
            type="time"
            fullWidth
            value={scheduleTime}
            onChange={(e) => setScheduleTime(e.target.value)}
            InputLabelProps={{ shrink: true }}
          />
          <TextField
            margin="dense"
            label="Location"
            fullWidth
            value={scheduleLocation}
            onChange={(e) => setScheduleLocation(e.target.value)}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => { setScheduleOpen(false); setScheduleIdea(null); }}>Cancel</Button>
          <Button variant="contained" startIcon={<Event />} onClick={handleSchedule}>Schedule</Button>
        </DialogActions>
      </Dialog>

      {/* Snackbar */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={4000}
        onClose={() => setSnackbar((prev) => ({ ...prev, open: false }))}
        anchorOrigin={{ vertical: "bottom", horizontal: "center" }}
      >
        <Alert severity={snackbar.severity} variant="filled">{snackbar.message}</Alert>
      </Snackbar>

      <Dialog open={open} onClose={() => setOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>New Idea</DialogTitle>
        <DialogContent>
          <TextField fullWidth label="Title" value={title} onChange={(e) => setTitle(e.target.value)} sx={{ mt: 1 }} required />
          <TextField fullWidth label="Description" value={description} onChange={(e) => setDescription(e.target.value)} multiline rows={3} sx={{ mt: 2 }} />
          <Grid container spacing={2} sx={{ mt: 0.5 }}>
            <Grid item xs={6}>
              <TextField fullWidth label="Cost" value={cost} onChange={(e) => setCost(e.target.value)} placeholder="e.g. low, medium, high, or $50" />
            </Grid>
            <Grid item xs={6}>
              <FormControl fullWidth>
                <InputLabel>Category</InputLabel>
                <Select value={category} onChange={(e) => setCategory(e.target.value)} label="Category">
                  {CATEGORIES.map((c) => <MenuItem key={c} value={c}>{c}</MenuItem>)}
                </Select>
              </FormControl>
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleCreate}>Create</Button>
        </DialogActions>
      </Dialog>
    </>
  );
};

export default IdeasPage;
