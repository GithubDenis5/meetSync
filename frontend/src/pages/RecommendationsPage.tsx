import React, { useState } from "react";
import {
  Box, Typography, Card, CardContent, CardMedia, Grid, TextField,
  Button, CircularProgress, Chip, FormControl, InputLabel, Select, MenuItem,
} from "@mui/material";
import { recommendationApi } from "../utils/api";
import { Recommendation } from "../types";
import { Recommend } from "@mui/icons-material";

const CATEGORIES = ["concerts", "sports", "theatre", "arts", "family", "food", "outdoor"];

const RecommendationsPage: React.FC = () => {
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [city, setCity] = useState("Moscow");
  const [category, setCategory] = useState("");
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);

  const handleSearch = async () => {
    setLoading(true);
    setSearched(true);
    try {
      const { data } = await recommendationApi.list(city, category || undefined);
      setRecommendations(data);
    } catch {
      setRecommendations([]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <Typography variant="h4" gutterBottom>Recommendations</Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Discover events and activities near you
      </Typography>

      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={2} alignItems="flex-end">
            <Grid item xs={12} sm={4}>
              <TextField fullWidth size="small" label="City" value={city} onChange={(e) => setCity(e.target.value)} />
            </Grid>
            <Grid item xs={12} sm={4}>
              <FormControl fullWidth size="small">
                <InputLabel>Category</InputLabel>
                <Select value={category} onChange={(e) => setCategory(e.target.value)} label="Category">
                  <MenuItem value="">All</MenuItem>
                  {CATEGORIES.map((c) => <MenuItem key={c} value={c}>{c}</MenuItem>)}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={4}>
              <Button fullWidth variant="contained" startIcon={<Recommend />} onClick={handleSearch} disabled={loading}>
                {loading ? "Searching..." : "Find Events"}
              </Button>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {loading ? (
        <Box sx={{ display: "flex", justifyContent: "center", mt: 4 }}><CircularProgress /></Box>
      ) : recommendations.length === 0 && searched ? (
        <Typography color="text.secondary" align="center">No recommendations found for this city.</Typography>
      ) : (
        <Grid container spacing={2}>
          {recommendations.map((rec, i) => (
            <Grid item xs={12} sm={6} md={4} key={i}>
              <Card sx={{ height: "100%", display: "flex", flexDirection: "column" }}>
                {rec.image_url && (
                  <CardMedia component="img" height="140" image={rec.image_url} alt={rec.title} />
                )}
                <CardContent sx={{ flexGrow: 1 }}>
                  <Typography variant="h6" gutterBottom>{rec.title}</Typography>
                  {rec.description && (
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                      {rec.description}
                    </Typography>
                  )}
                  <Box sx={{ display: "flex", gap: 0.5, flexWrap: "wrap", mb: 1 }}>
                    {rec.category && <Chip size="small" label={rec.category} />}
                    {rec.source && <Chip size="small" variant="outlined" label={rec.source} />}
                  </Box>
                  {rec.date && <Typography variant="caption" display="block">{rec.date}</Typography>}
                  {rec.location && <Typography variant="caption" display="block" color="text.secondary">{rec.location}</Typography>}
                  {rec.url && (
                    <Button size="small" href={rec.url} target="_blank" sx={{ mt: 1 }}>
                      View Details
                    </Button>
                  )}
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}
    </>
  );
};

export default RecommendationsPage;
