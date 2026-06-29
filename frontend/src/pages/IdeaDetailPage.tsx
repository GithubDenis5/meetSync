import React, { useState, useEffect } from "react";
import {
  Box, Typography, Card, CardContent, Chip, Button, TextField,
  CircularProgress, IconButton, List, ListItem, ListItemText, Avatar, Alert,
  useMediaQuery,
} from "@mui/material";
import { useParams, useNavigate } from "react-router-dom";
import { ideasApi } from "../utils/api";
import { Idea, Comment } from "../types";
import { ArrowBack } from "@mui/icons-material";

const IdeaDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [idea, setIdea] = useState<Idea | null>(null);
  const [comments, setComments] = useState<Comment[]>([]);
  const [loading, setLoading] = useState(true);
  const [commentText, setCommentText] = useState("");
  const isMobile = useMediaQuery("(max-width:600px)");
  const [error, setError] = useState("");

  useEffect(() => {
    if (!id) return;
    Promise.all([
      ideasApi.get(Number(id)).then(({ data }) => setIdea(data)),
      ideasApi.comments(Number(id)).then(({ data }) => setComments(data)),
    ]).catch(() => navigate("/ideas")).finally(() => setLoading(false));
  }, [id]);

  const handleReact = async (reaction: string) => {
    if (!id) return;
    await ideasApi.react(Number(id), reaction);
    const { data } = await ideasApi.get(Number(id));
    setIdea(data);
  };

  const handleComment = async () => {
    if (!id || !commentText.trim()) return;
    await ideasApi.addComment(Number(id), commentText);
    setCommentText("");
    const { data } = await ideasApi.comments(Number(id));
    setComments(data);
  };

  const handleArchive = async () => {
    if (!id) return;
    if (idea?.is_archived) {
      await ideasApi.unarchive(Number(id));
    } else {
      await ideasApi.archive(Number(id));
    }
    const { data } = await ideasApi.get(Number(id));
    setIdea(data);
  };

  if (loading) return <Box sx={{ display: "flex", justifyContent: "center", mt: 4 }}><CircularProgress /></Box>;
  if (!idea) return <Typography>Idea not found</Typography>;

  return (
    <>
      <Button startIcon={<ArrowBack />} onClick={() => navigate(-1)} sx={{ mb: 2 }}>Back</Button>
      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Box sx={{ display: "flex", flexDirection: { xs: "column", sm: "row" }, justifyContent: "space-between", alignItems: { xs: "stretch", sm: "flex-start" }, gap: 1 }}>
            <Box>
              <Typography variant="h4" gutterBottom sx={{ fontSize: { xs: "1.5rem", sm: "2rem" } }}>{idea.title}</Typography>
              <Typography variant="body2" color="text.secondary">
                Suggested by {idea.suggestor_name || "Unknown"}
              </Typography>
            </Box>
            <Button size="small" variant="outlined" onClick={handleArchive} fullWidth={isMobile}>
              {idea.is_archived ? "Unarchive" : "Archive"}
            </Button>
          </Box>

          {idea.description && <Typography sx={{ mt: 2 }}>{idea.description}</Typography>}

          <Box sx={{ mt: 2, display: "flex", gap: 1, flexWrap: "wrap" }}>
            {idea.category && <Chip label={idea.category} />}
            {idea.cost && <Chip variant="outlined" label={idea.cost} />}
            {idea.location && <Chip icon={<span>📍</span>} label={idea.location} />}
            {idea.tags && idea.tags.split(",").map((t) => <Chip key={t} size="small" label={t.trim()} />)}
          </Box>

          <Box sx={{ mt: 3 }}>
            <Typography variant="subtitle1" gutterBottom>Reactions</Typography>
            {["👍", "❤️", "🔥", "👎"].map((r) => (
              <IconButton key={r} onClick={() => handleReact(r)}>
                {r} {idea.reactions[r] || 0}
              </IconButton>
            ))}
          </Box>
        </CardContent>
      </Card>

      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>Comments</Typography>
          {comments.length === 0 ? (
            <Typography color="text.secondary" sx={{ mb: 2 }}>No comments yet</Typography>
          ) : (
            <List>
              {comments.map((c) => (
                <ListItem key={c.id}>
                  <ListItemText primary={c.text} secondary={`— ${c.user_name || "Unknown"}`} />
                </ListItem>
              ))}
            </List>
          )}
          <Box sx={{ display: "flex", flexDirection: { xs: "column", sm: "row" }, gap: 1, mt: 2 }}>
            <TextField fullWidth size="small" placeholder="Add a comment..." value={commentText} onChange={(e) => setCommentText(e.target.value)} />
            <Button variant="contained" onClick={handleComment} fullWidth={isMobile}>Send</Button>
          </Box>
        </CardContent>
      </Card>
    </>
  );
};

export default IdeaDetailPage;
