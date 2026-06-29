import React, { useState, useEffect } from "react";
import {
  Box, Typography, Card, CardContent, Grid, Button, Chip,
  Dialog, DialogTitle, DialogContent, DialogActions, TextField,
  Select, MenuItem, FormControl, InputLabel, CircularProgress,
  LinearProgress, Radio, RadioGroup, FormControlLabel, Alert,
  useMediaQuery,
} from "@mui/material";
import { votingApi, groupApi, ideasApi } from "../utils/api";
import { Vote, Group, Idea } from "../types";
import { HowToVote } from "@mui/icons-material";

const VotingPage: React.FC = () => {
  const [votes, setVotes] = useState<Vote[]>([]);
  const [groups, setGroups] = useState<Group[]>([]);
  const [selectedGroup, setSelectedGroup] = useState<number>(0);
  const [loading, setLoading] = useState(true);
  const [open, setOpen] = useState(false);
  const [title, setTitle] = useState("");
  const [voteType, setVoteType] = useState("random");
  const [duration, setDuration] = useState(24);
  const [selectedOption, setSelectedOption] = useState<number | null>(null);
  const [votingVote, setVotingVote] = useState<number | null>(null);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const isMobile = useMediaQuery("(max-width:600px)");

  useEffect(() => {
    groupApi.list().then(({ data }) => setGroups(data)).catch(() => {});
  }, []);

  useEffect(() => {
    if (!selectedGroup) { setLoading(false); return; }
    votingApi.list(selectedGroup, true)
      .then(({ data }) => setVotes(data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [selectedGroup]);

  const handleCreate = async () => {
    if (!selectedGroup) return;
    try {
      await votingApi.create({ group_id: selectedGroup, title, vote_type: voteType, duration_hours: duration });
      setOpen(false);
      setTitle("");
      setSuccess("Vote created!");
      const { data } = await votingApi.list(selectedGroup, true);
      setVotes(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to create vote");
    }
  };

  const handleVote = async () => {
    if (!votingVote || selectedOption === null) return;
    try {
      await votingApi.cast(votingVote, selectedOption);
      setSuccess("Vote cast!");
      setVotingVote(null);
      setSelectedOption(null);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to vote");
    }
  };

  const timeLeft = (endsAt: string) => {
    const diff = new Date(endsAt).getTime() - Date.now();
    if (diff <= 0) return "Ended";
    const hours = Math.floor(diff / 3600000);
    const mins = Math.floor((diff % 3600000) / 60000);
    return `${hours}h ${mins}m left`;
  };

  if (loading) return <Box sx={{ display: "flex", justifyContent: "center", mt: 4 }}><CircularProgress /></Box>;

  return (
    <>
      <Box sx={{ display: "flex", flexDirection: { xs: "column", sm: "row" }, justifyContent: "space-between", alignItems: { xs: "stretch", sm: "center" }, mb: 3, gap: 1 }}>
        <Typography variant="h4" sx={{ fontSize: { xs: "1.5rem", sm: "2rem" } }}>Voting</Typography>
        <Box sx={{ display: "flex", gap: 1 }}>
          <FormControl size="small" sx={{ minWidth: { xs: 140, sm: 200 }, flex: { xs: 1, sm: "none" } }}>
            <InputLabel>Group</InputLabel>
            <Select value={selectedGroup} onChange={(e) => setSelectedGroup(e.target.value as number)} label="Group">
              {groups.map((g) => <MenuItem key={g.id} value={g.id}>{g.name}</MenuItem>)}
            </Select>
          </FormControl>
          <Button variant="contained" startIcon={<HowToVote />} onClick={() => setOpen(true)} disabled={!selectedGroup}
            size="small">
            New Vote
          </Button>
        </Box>
      </Box>

      {error && <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError("")}>{error}</Alert>}
      {success && <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccess("")}>{success}</Alert>}

      {!selectedGroup ? (
        <Typography color="text.secondary">Select a group to see votes</Typography>
      ) : votes.length === 0 ? (
        <Typography color="text.secondary">No active votes</Typography>
      ) : (
        <Grid container spacing={3}>
          {votes.map((vote) => (
            <Grid item xs={12} md={6} key={vote.id}>
              <Card>
                <CardContent>
                  <Typography variant="h6">{vote.title}</Typography>
                  <Chip size="small" label={timeLeft(vote.ends_at)} color={timeLeft(vote.ends_at) === "Ended" ? "default" : "primary"} sx={{ mb: 2 }} />

                  {vote.options.map((opt) => (
                    <Box key={opt.id} sx={{ mb: 1 }}>
                      <Typography variant="body2">{opt.idea_title}</Typography>
                      <LinearProgress
                        variant="determinate"
                        value={vote.options.reduce((sum, o) => sum + o.votes_count, 0) > 0
                          ? (opt.votes_count / vote.options.reduce((sum, o) => sum + o.votes_count, 0)) * 100
                          : 0
                        }
                        sx={{ height: 8, borderRadius: 4 }}
                      />
                      <Typography variant="caption">{opt.votes_count} votes</Typography>
                    </Box>
                  ))}

                  <Button
                    size="small"
                    variant="outlined"
                    fullWidth={isMobile}
                    sx={{ mt: 1 }}
                    onClick={() => setVotingVote(vote.id)}
                  >
                    Vote
                  </Button>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}

      {/* Create dialog */}
      <Dialog open={open} onClose={() => setOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Create Vote</DialogTitle>
        <DialogContent>
          <TextField fullWidth label="Title" value={title} onChange={(e) => setTitle(e.target.value)} sx={{ mt: 1 }} required />
          <FormControl fullWidth sx={{ mt: 2 }}>
            <InputLabel>Vote Type</InputLabel>
            <Select value={voteType} onChange={(e) => setVoteType(e.target.value)} label="Vote Type">
              <MenuItem value="random">Random</MenuItem>
              <MenuItem value="popular">Most Popular</MenuItem>
              <MenuItem value="category">By Category</MenuItem>
            </Select>
          </FormControl>
          <TextField fullWidth type="number" label="Duration (hours)" value={duration} onChange={(e) => setDuration(Number(e.target.value))} sx={{ mt: 2 }} />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleCreate}>Create</Button>
        </DialogActions>
      </Dialog>

      {/* Vote dialog */}
      <Dialog open={votingVote !== null} onClose={() => setVotingVote(null)} maxWidth="sm" fullWidth>
        <DialogTitle>Cast Your Vote</DialogTitle>
        <DialogContent>
          <RadioGroup value={selectedOption} onChange={(e) => setSelectedOption(Number(e.target.value))}>
            {votes.find((v) => v.id === votingVote)?.options.map((opt) => (
              <FormControlLabel key={opt.id} value={opt.id} control={<Radio />} label={opt.idea_title} />
            ))}
          </RadioGroup>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setVotingVote(null)}>Cancel</Button>
          <Button variant="contained" onClick={handleVote}>Vote</Button>
        </DialogActions>
      </Dialog>
    </>
  );
};

export default VotingPage;
